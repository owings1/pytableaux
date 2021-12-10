from __future__ import annotations

from callables import calls, gets, sets

from collections.abc import Callable
from typing import ParamSpec, TypeVar

T = TypeVar('T')

def _rename(fnew: T, forig) -> T:
    fnew.__qualname__ = forig.__qualname__
    fnew.__name__ = forig.__name__
    return fnew

def _argwrap(decorator):
    def wrapped(*args, **kw):
        if args and callable(args[0]):
            return decorator()(*args, **kw)
        return decorator(*args, *kw)
    return _rename(wrapped, decorator)


@_argwrap
def lazyget(name = None, attrset = None) -> Callable[..., Callable[..., T]]:
    def wrap(method: Callable[..., T]) -> Callable[..., T]:
        key = '_%s' % method.__name__ if name is None else name
        getter = gets.attr(key)
        fset = sets.attr(key) if attrset is None else attrset
        def fget(self) -> T:
            try: return getter(self)
            except AttributeError: val = method(self)
            fset(self, val)
            return val
        return _rename(fget, method)
    return wrap
