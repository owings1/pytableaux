# pytableaux, a multi-logic proof generator.
# Copyright (C) 2014-2022 Doug Owings.
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
pytableaux.tools.typing
^^^^^^^^^^^^^^^^^^^^^^^

"""
from __future__ import annotations

__all__ = ()
#==========================+
#  No local dependencies!  |
#==========================+

import enum as _enum
from collections.abc import Set
from types import FunctionType, MethodType, ModuleType
from typing import (TYPE_CHECKING, Any, Callable, ClassVar, Collection,
                    Generic, Mapping, ParamSpec, SupportsIndex, TypeVar,
                    overload)

if TYPE_CHECKING:
    from pytableaux.models import BaseModel
    from pytableaux.proof.tableaux import Rule, TableauxSystem
    from pytableaux.tools.sets import SetApi

class LogicType(
    metaclass = type('LogicTypeMeta', (type,), dict(__call__ = None))
):
    "Stub class definition for a logic interface."
    name: str
    class Meta:
        category: str
        description: str
        category_order: int
        tags: Collection[str]
    TableauxSystem: ClassVar[type[TableauxSystem]]
    Model: ClassVar[type[BaseModel]]
    class TabRules:
        closure_rules: ClassVar[tuple[type[Rule], ...]]
        rule_groups: ClassVar[tuple[ tuple[type[Rule], ...], ... ]]

#==================================================+
#  Type aliases -- used a runtime with isinstance  |
#==================================================+

IndexType = SupportsIndex | slice
"Integer or slice type"

NotImplType = type(NotImplemented)
"NotImplemented type"

LogicModule = LogicType | ModuleType
"Logic module alias for type hinting."

LogicLookupKey = ModuleType | str
"""Logic registry key. Module or string. See ``Registry.get()``."""

HasModuleAttr = MethodType | FunctionType | type
"Supports the ``__module__`` attribute (class, method, or function."

LogicLocatorRef = LogicLookupKey | HasModuleAttr
"""Either a logic registry key (string/module), or class, method, or function."""

#==============================================+
#  Generic aliases -- no 'isinstance' support  |
#==============================================+

IcmpFunc = Callable[[int, int], bool]
"Function that compares two ints and returns a boolean value, e.g. `>` or `<`."

#==========================+
#  Type variables          |
#==========================+

T = TypeVar('T')
"Generic, any type"

T1 = TypeVar('T1')
"Generic, any type"

KT = TypeVar('KT')
"Generic, key type"

VT = TypeVar('VT')
"Generic, value type"

RT = TypeVar('RT')
"Generic, return type"

LHS = TypeVar('LHS')
"Generic, left compare"

RHS = TypeVar('RHS')
"Generic, right compare"

Self = TypeVar('Self')
"Generic, self"

F = TypeVar('F', bound = Callable[..., Any])
"Callable bound, decorator"

TT = TypeVar('TT',    bound = type)
"Type bound, class decorator"

MapT = TypeVar('MapT', bound = Mapping)
"Mapping bound"

SetT = TypeVar('SetT', bound = Set)
"Set bound"

EnumT = TypeVar('EnumT', bound = _enum.Enum)
"Enum bound"

SetApiT = TypeVar('SetApiT', bound = 'SetApi')
"Bound to ``SetApi``"

RuleT = TypeVar('RuleT', bound = 'Rule')
"Bound to ``Rule``"

P = ParamSpec('P')
"Param spec"

#==========================+
#  Stub/Hint classes       |
#==========================+

if TYPE_CHECKING:

    class TypeInstDict(dict[type[VT], VT],
        metaclass = type('TidMeta', (type,), dict(__call__ = dict))):
        'Stub type for mapping of ``type[T]`` -> ``T``.'
        @overload
        def __getitem__(self, key: type[T]) -> T: ...
        @overload
        def get(self, key: type[T], default = None) -> T|None: ...
        @overload
        def copy(self: T) -> T: ...
        @overload
        def setdefault(self, key: type[T], value: Any) -> T:...
        @overload
        def pop(self, key: type[T]) -> T:...

    class EnumDictType(_enum._EnumDict):
        'Stub type for annotation reference.'
        _member_names: list[str]
        _last_values : list[object]
        _ignore      : list[str]
        _auto_called : bool
        _cls_name    : str

    # Stub adapted from typing module with added annotations.
    class _property(property, Generic[Self, T]):
        fget: Callable[[Self], Any] | None
        fset: Callable[[Self, Any], None] | None
        fdel: Callable[[Self], None] | None
        @overload
        def __init__(
            self,
            fget: Callable[[Self], T] | None = ...,
            fset: Callable[[Self, Any], None] | None = ...,
            fdel: Callable[[Self], None] | None = ...,
            doc: str | None = ...,
        ) -> None: ...
        __init__ = NotImplemented
        def getter(self, __fget: Callable[[Self], T]) -> _property[Self, T]: ...
        def setter(self, __fset: Callable[[Self, Any], None]) -> _property[Self, T]: ...
        def deleter(self, __fdel: Callable[[Self], None]) -> _property[Self, T]: ...
        def __get__(self, __obj: Self, __type: type | None = ...) -> T: ...
        def __set__(self, __obj: Self, __value: Any) -> None: ...
        def __delete__(self, __obj: Self) -> None: ...

else:
    TypeInstDict = dict
    EnumDictType = _enum._EnumDict
    _property = property
    
