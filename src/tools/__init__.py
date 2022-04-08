from __future__ import annotations

from typing import Any, Callable, TypeVar


def closure(func: Callable[..., T]) -> T:
    return func()


T = TypeVar('T')
# Callable bound, use for decorator, etc.
F   = TypeVar('F',  bound = Callable[..., Any])
