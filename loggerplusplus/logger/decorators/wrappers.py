# ====== Code Summary ======
# This module defines `wrap_function`, a utility that wraps synchronous or
# asynchronous functions with pre-call, post-call, and error-handling hooks.
# It is used internally by decorators to standardize function instrumentation.

# ====== Standard Library Imports ======
import asyncio
import functools
from typing import Any, Callable


def wrap_function(
        func: Callable[..., Any],
        before_call: Callable[[tuple, dict], None],
        after_call: Callable[[Any, tuple, dict], None],
        on_error: Callable[[Exception, tuple, dict], None],
) -> Callable[..., Any]:
    """
    Wrap a function (sync or async) with hooks for before, after, and error events.

    Args:
        func (Callable[..., Any]): The function to wrap (maybe async or sync).
        before_call (Callable): Hook executed before function call.
            Receives (args, kwargs).
        after_call (Callable): Hook executed after successful call.
            Receives (result, args, kwargs).
        on_error (Callable): Hook executed if an exception occurs.
            Receives (exception, args, kwargs).

    Returns:
        Callable[..., Any]: The wrapped function with instrumentation.
    """
    if asyncio.iscoroutinefunction(func):

        @functools.wraps(func)
        async def wrapper(*args, **kwargs):
            # 1. Execute before-call hook
            before_call(args, kwargs)
            try:
                # 2. Await original function
                result = await func(*args, **kwargs)
            except Exception as e:
                # 3. Handle error via hook, then re-raise
                on_error(e, args, kwargs)
                raise
            # 4. Execute after-call hook
            after_call(result, args, kwargs)
            return result

        return wrapper

    else:

        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            # 1. Execute before-call hook
            before_call(args, kwargs)
            try:
                # 2. Call original function
                result = func(*args, **kwargs)
            except Exception as e:
                # 3. Handle error via hook, then re-raise
                on_error(e, args, kwargs)
                raise
            # 4. Execute after-call hook
            after_call(result, args, kwargs)
            return result

        return wrapper
