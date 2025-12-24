import asyncio
import json
import logging
import time
import uuid
from datetime import datetime
from typing import List, Optional

from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
from starlette.types import ASGIApp

logger = logging.getLogger(__name__)


class RequestIDMiddleware(BaseHTTPMiddleware):
    def __init__(
        self,
        app: ASGIApp,
        header_name: str = "X-Request-ID",
        validate_uuid: bool = True,
    ):
        super().__init__(app)
        self.header_name = header_name
        self.validate_uuid = validate_uuid

    async def dispatch(self, request: Request, call_next: RequestResponseEndpoint) -> Response:
        request_id = request.headers.get(self.header_name)

        if not request_id or (self.validate_uuid and not self._is_valid_uuid(request_id)):
            request_id = str(uuid.uuid4())

        request.state.request_id = request_id

        response = await call_next(request)

        if self.header_name not in response.headers:
            response.headers[self.header_name] = request_id

        return response

    @staticmethod
    def _is_valid_uuid(uuid_string: str) -> bool:
        try:
            uuid.UUID(str(uuid_string))
            return True
        except ValueError:
            return False


class RequestLoggingMiddleware(BaseHTTPMiddleware):
    def __init__(
        self,
        app: ASGIApp,
        exclude_paths: Optional[List[str]] = None,
        exclude_methods: Optional[List[str]] = None,
    ):
        super().__init__(app)
        self.exclude_paths = exclude_paths or ["/health", "/metrics"]
        self.exclude_methods = exclude_methods or ["OPTIONS"]
        self.log_queue: asyncio.Queue = asyncio.Queue()
        asyncio.create_task(self._process_logs())

    async def dispatch(self, request: Request, call_next: RequestResponseEndpoint) -> Response:
        if request.url.path in self.exclude_paths or request.method in self.exclude_methods:
            return await call_next(request)

        start_time = time.time()
        request_details = self._get_request_details(request)

        try:
            response = await call_next(request)
            process_time = time.time() - start_time

            await self.log_queue.put(
                {
                    "level": "info",
                    "message": "Request processed",
                    "details": {
                        **request_details,
                        "status_code": response.status_code,
                        "process_time": process_time,
                    },
                }
            )

            return response

        except Exception as e:
            await self.log_queue.put(
                {
                    "level": "error",
                    "message": "Request failed",
                    "details": {
                        **request_details,
                        "error": str(e),
                        "process_time": time.time() - start_time,
                    },
                    "exc_info": True,
                }
            )
            raise

    def _get_request_details(self, request: Request) -> dict:
        return {
            "request_id": getattr(request.state, "request_id", None),
            "method": request.method,
            "path": request.url.path,
            "query_params": dict(request.query_params),
            "client_ip": request.client.host,
            "user_agent": request.headers.get("user-agent"),
            "timestamp": datetime.utcnow().isoformat(),
        }

    async def _process_logs(self) -> None:
        while True:
            try:
                log_entry = await self.log_queue.get()
                log_level = log_entry["level"]

                if log_level == "info":
                    logger.info(log_entry["message"], extra=log_entry["details"])
                else:
                    logger.error(
                        log_entry["message"],
                        extra=log_entry["details"],
                        exc_info=log_entry.get("exc_info", False),
                    )

                self.log_queue.task_done()
            except Exception as e:
                logger.error(f"Error processing log: {str(e)}")
                await asyncio.sleep(0.1)


class ResponseTimeMiddleware(BaseHTTPMiddleware):
    def __init__(self, app: ASGIApp, slow_request_threshold: float = 0.5):
        super().__init__(app)
        self.slow_request_threshold = slow_request_threshold

    async def dispatch(self, request: Request, call_next: RequestResponseEndpoint) -> Response:
        start_time = time.time()

        response = await call_next(request)

        process_time = time.time() - start_time

        response.headers["X-Process-Time"] = f"{process_time:.4f}"

        if process_time > self.slow_request_threshold:
            logger.warning(
                "Slow request detected",
                extra={
                    "request_id": getattr(request.state, "request_id", None),
                    "path": request.url.path,
                    "method": request.method,
                    "process_time": process_time,
                    "threshold": self.slow_request_threshold,
                },
            )

        return response


class RateLimitMiddleware(BaseHTTPMiddleware):
    def __init__(
        self,
        app: ASGIApp,
        rate_limit: int = 60,
        window_size: int = 60,
        exclude_paths: Optional[List[str]] = None,
    ):
        super().__init__(app)
        self.rate_limit = rate_limit
        self.window_size = window_size
        self.exclude_paths = exclude_paths or ["/health", "/metrics"]
        self.requests: dict[str, list[float]] = {}

    async def dispatch(self, request: Request, call_next: RequestResponseEndpoint) -> Response:
        if request.url.path in self.exclude_paths:
            return await call_next(request)

        client_id = self._get_client_id(request)

        current_time = time.time()
        if not self._check_rate_limit(client_id, current_time):
            logger.warning(
                "Rate limit exceeded",
                extra={"client_id": client_id, "path": request.url.path},
            )

            retry_after = self._get_retry_after(client_id)

            return Response(
                content=json.dumps(
                    {
                        "message": f"Rate limit exceeded, retry after {retry_after} sec",
                        "status_code": 429,
                    }
                ),
                status_code=429,
                media_type="application/json",
            )

        return await call_next(request)

    def _get_client_id(self, request: Request) -> str:
        api_key = request.headers.get("X-API-Key")
        if api_key:
            return f"api_key:{api_key}"

        return f"ip:{request.client.host}"

    def _check_rate_limit(self, client_id: str, current_time: float) -> bool:
        if client_id not in self.requests:
            self.requests[client_id] = []

        self.requests[client_id] = [
            req_time
            for req_time in self.requests[client_id]
            if current_time - req_time <= self.window_size
        ]

        if len(self.requests[client_id]) >= self.rate_limit:
            return False

        self.requests[client_id].append(current_time)
        return True

    def _get_retry_after(self, client_id: str) -> int:
        if not self.requests[client_id]:
            return 0
        oldest_request = min(self.requests[client_id])
        return int(oldest_request + self.window_size - time.time())


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    def __init__(self, app: ASGIApp, csp_policy: Optional[str] = None, hsts_age: int = 31536000):
        super().__init__(app)
        self.security_headers = {
            "X-Frame-Options": "DENY",
            "X-Content-Type-Options": "nosniff",
            "X-XSS-Protection": "1; mode=block",
            "Strict-Transport-Security": f"max-age={hsts_age}; includeSubDomains",
            "Content-Security-Policy": csp_policy or "default-src 'self'",
            "Referrer-Policy": "strict-origin-when-cross-origin",
            "Permissions-Policy": "geolocation=(), microphone=(), camera=()",
        }

    async def dispatch(self, request: Request, call_next: RequestResponseEndpoint) -> Response:
        response = await call_next(request)

        for header_name, header_value in self.security_headers.items():
            response.headers[header_name] = header_value

        return response
