import inspect
from functools import wraps
from typing import Any, Awaitable, Callable, Protocol, TypeVar, TypeVarTuple, overload

import sentry_sdk

ReturnType = TypeVar("ReturnType", covariant=True)
Ts = TypeVarTuple("Ts")


class AsyncCallable(Protocol[ReturnType]):
    def __call__(self, *args: Any, **kwargs: Any) -> Awaitable[ReturnType]: ...


class SyncCallable(Protocol[ReturnType]):
    def __call__(self, *args: Any, **kwargs: Any) -> ReturnType: ...


@overload
def monitor_transaction(  # type: ignore[misc]
    name: str | None = None,
    op: str | None = None,
    tags: dict[str, Any] | None = None,
) -> Callable[[AsyncCallable[ReturnType]], AsyncCallable[ReturnType]]: ...


@overload
def monitor_transaction(  # type: ignore[misc]
    name: str | None = None,
    op: str | None = None,
    tags: dict[str, Any] | None = None,
) -> Callable[[SyncCallable[ReturnType]], SyncCallable[ReturnType]]: ...


def monitor_transaction(
    name: str | None = None,
    op: str | None = None,
    tags: dict[str, Any] | None = None,
) -> Callable[..., Any]:
    """
    A decorator that monitors function execution with Sentry transactions.

    Args:
        name: Custom name for the transaction. Defaults to function name.
        op: Operation type for the transaction. Defaults to "function".
        tags: Additional tags for the transaction.
    """

    def decorator(func: Callable[..., Any]) -> Callable[..., Any]:
        @wraps(func)
        async def async_wrapper(*args: Any, **kwargs: Any) -> Any:
            transaction_name = name or f"{func.__module__}.{func.__name__}"
            with sentry_sdk.start_transaction(
                name=transaction_name, op=op or "function"
            ) as transaction:
                if tags:
                    for key, value in tags.items():
                        transaction.set_tag(key, value)
                try:
                    return await func(*args, **kwargs)
                except Exception as e:
                    sentry_sdk.capture_exception(e)
                    raise

        @wraps(func)
        def sync_wrapper(*args: Any, **kwargs: Any) -> Any:
            transaction_name = name or f"{func.__module__}.{func.__name__}"
            with sentry_sdk.start_transaction(
                name=transaction_name, op=op or "function"
            ) as transaction:
                if tags:
                    for key, value in tags.items():
                        transaction.set_tag(key, value)
                try:
                    return func(*args, **kwargs)
                except Exception as e:
                    sentry_sdk.capture_exception(e)
                    raise

        return async_wrapper if inspect.iscoroutinefunction(func) else sync_wrapper

    return decorator
