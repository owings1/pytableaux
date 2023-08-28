# pytableaux, a multi-logic proof generator.
# Copyright (C) 2014-2023 Doug Owings.
# 
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
# 
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Affero General Public License for more details.
# 
# You should have received a copy of the GNU Affero General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.
"""
pytableaux.tools.lazy
---------------------
"""
from __future__ import annotations

import builtins
from typing import TYPE_CHECKING, Any, Callable, Generic, TypeVar

from ..errors import check
from . import EMPTY_SET, wraps

__all__ = ('get', 'prop')

_T = TypeVar('_T')
_F = TypeVar('_F', bound=Callable)
_Self = TypeVar('_Self')

NOARG = object()

if TYPE_CHECKING:
    from typing import overload
    class property(builtins.property, Generic[_Self, _T]):
        fget: Callable[[_Self], Any] | None
        fset: Callable[[_Self, Any], None] | None
        fdel: Callable[[_Self], None] | None
        @overload
        def __init__(
            self,
            fget: Callable[[_Self], _T] | None = ...,
            fset: Callable[[_Self, Any], None] | None = ...,
            fdel: Callable[[_Self], None] | None = ...,
            doc: str | None = ...,
        ) -> None: ...
        def getter(self, __fget: Callable[[_Self], _T]) -> property[_Self, _T]: ...
        def setter(self, __fset: Callable[[_Self, Any], None]) -> property[_Self, _T]: ...
        def deleter(self, __fdel: Callable[[_Self], None]) -> property[_Self, _T]: ...
        def __get__(self, __obj: _Self, __type: type | None = ...) -> _T: ...
        def __set__(self, __obj: _Self, __value: Any) -> None: ...
        def __delete__(self, __obj: _Self) -> None: ...


class get:
    """Return a lazy caching getter.

    Usage::

        class Spam:

            @lazy.get
            def eggs(self):
               return 'scrambled'

            @lazy.get(attr='_realham')
            def ham(self):
               return 'baked'
    """

    attr: str|None
    wrapped: Callable

    __slots__ = ('attr', 'wrapped')

    def __new__(cls, wrapped=NOARG, /, *, attr=None):
        """If only argument to constructor is callable, construct and call the
        instance. Otherwise create normally.
        """
        self = object.__new__(cls)
        self.attr = attr
        if wrapped is NOARG:
            self.wrapped = None
            return self
        return self(check.callable(wrapped))

    def __call__(self, wrapped: _F, /, *, name=None) -> _F:
        name = name or wrapped.__name__
        attr = (self.attr or '_{name}').format(name=name)
        @wraps(wrapped)
        def wrapper(self):
            try:
                return getattr(self, attr)
            except AttributeError:
                pass
            setattr(self, attr, value := wrapped(self))
            return value
        return wrapper

class prop(get):
    """Return a property with the getter. NB: a setter/deleter should be
    sure to use the correct attribute.
    """

    __slots__ = EMPTY_SET

    @property
    def propclass(self) -> type[property]:
        return property

    if TYPE_CHECKING:
        @overload
        def __new__(cls, func: Callable[[_Self], _T]) -> property[_Self, _T]: ...

    def __call__(self, method: Callable[[_Self], _T]) -> property[_Self, _T]:
        fget = super().__call__(method)
        return self.propclass(fget, doc = method.__doc__)