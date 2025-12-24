import time
from typing import Awaitable, Callable

import sentry_sdk
from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import Response


class SentryContextMiddleware(BaseHTTPMiddleware):
    async def dispatch(
        self, request: Request, call_next: Callable[[Request], Awaitable[Response]]
    ) -> Response:
        with sentry_sdk.configure_scope() as scope:
            scope.set_extra("request_id", request.state.request_id)
            scope.set_tag("http_method", request.method)
            scope.set_tag("path", request.url.path)

            if hasattr(request.state, "user"):
                scope.set_user({"id": request.state.user.id, "email": request.state.user.email})

            start_time = time.time()
            try:
                response = await call_next(request)
                scope.set_tag("status_code", response.status_code)
                return response
            except Exception as e:
                scope.set_tag("error_type", type(e).__name__)
                raise
            finally:
                scope.set_extra("response_time", time.time() - start_time)
