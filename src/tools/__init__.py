from __future__ import annotations

from typing import Any, Callable, TypeVar

from abc import abstractmethod as abstract

def closure(func: Callable[..., T]) -> T:
    return func()


T = TypeVar('T')
# Callable bound, use for decorator, etc.
F   = TypeVar('F',  bound = Callable[..., Any])
