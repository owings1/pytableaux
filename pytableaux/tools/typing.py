# -*- coding: utf-8 -*-
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

import builtins
import enum as _enum
from collections.abc import Set
from types import FunctionType, MethodType, ModuleType
from typing import (TYPE_CHECKING, Any, Callable, ClassVar, Collection,
                    Mapping, ParamSpec, SupportsIndex, TypeVar)

#==========================+
#  No local dependencies!  |
#==========================+

if TYPE_CHECKING:
    from typing import (Generic, Hashable, Iterable, Iterator, Sequence,
                        overload)

    from pytableaux.models import BaseModel
    from pytableaux.proof import TableauxSystem, filters
    from pytableaux.proof.common import Branch, Node, Target
    from pytableaux.proof.tableaux import Rule
    from pytableaux.tools.hooks import HookConn
    from pytableaux.tools.hybrids import SequenceSet
    from pytableaux.tools.linked import Link, LinkSequence
    from pytableaux.tools.mappings import MappingApi
    from pytableaux.tools.sequences import MutableSequenceApi, SequenceApi
    from pytableaux.tools.sets import SetApi
    from pytableaux.tools.timing import TimingCommon

__all__ = ()

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
    if TYPE_CHECKING:
        class TableauxSystem(TableauxSystem): pass
        class Model(BaseModel): pass
    else:
        TableauxSystem: ClassVar[type[TableauxSystem]]
        Model: ClassVar[type[BaseModel]]
    class TabRules:
        closure_rules: ClassVar[tuple[type[Rule], ...]]
        rule_groups: ClassVar[tuple[ tuple[type[Rule], ...], ... ]]
        all_rules: ClassVar[tuple[type[Rule], ...]]

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
"Logic registry key. Module or string. See ``Registry.get()``."

HasModuleAttr = MethodType | FunctionType | type
"Supports the ``__module__`` attribute (class, method, or function."

LogicLocatorRef = LogicLookupKey | HasModuleAttr
"Either a logic registry key (string/module), or class, method, or function."

#======================+
#  Generic aliases     |
#======================+

RsetSectKT = _enum.Enum|tuple[_enum.Enum, bool]
"RenderSet key type."

if TYPE_CHECKING:

    IcmpFunc = Callable[[int, int], bool]
    "Function that compares two ints and returns a boolean, e.g. `>` or `<`."

    KeysFunc = Callable[[Any], Set[Hashable]]
    "Function that returns a Set."

    TargetsFn = Callable[[Rule, Branch], Sequence[Target]|None]
    "Function like ``Rule._get_targets()``."

    NodeTargetsFn  = Callable[[Rule, Iterable[Node], Branch], Any]
    "Node-iterating targets function."

    NodeTargetsGen = Callable[[Rule, Iterable[Node], Branch], Iterator[Target]]
    "Normalized node-iterating targets function."

    NodePredFunc = Callable[[Node], bool]
    "Function that takes a Node and returns a boolean."

    HkProviderInfo = Mapping[str, tuple[str, ...]]
    "Hook provider info, `hookname` -> `attrnames`."

    HkUserInfo = Mapping[type, Mapping[str, Callable]]
    "Hook user info, `provider` -> `hookname` -> `callback`."

    HkConns = Mapping[str, tuple[HookConn, ...]]
    "Hook connections, `hookname` -> `conns`."

    HkProviders = Mapping[type, HkProviderInfo]
    "All hook providers info mappings."

    HkProvsTable = dict[type, HkProviderInfo]
    "Hook providers dict."

    HkUsersTable = dict[type, HkUserInfo]
    "Hook users dict."

    HkConnsTable = dict[type, dict[type, HkConns]]
    "Hook conns dict."


else:

    IcmpFunc = KeysFunc = TargetsFn = NodeTargetsFn = NodeTargetsGen = \
        NodePredFunc = Callable

    HkProviderInfo = HkUserInfo = HkConns = HkProviders = Mapping

    HkProvsTable = HkUsersTable = HkConnsTable = dict

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

# ---- Bound TypeVars

EnumT = TypeVar('EnumT', bound = _enum.Enum)
"Bound to ``Enum``"

F = TypeVar('F', bound = Callable[..., Any])
"Bound to ``Callable``, decorator"

LinkSeqT = TypeVar('LinkSeqT', bound = 'LinkSequence')
"Bound to ``LinkSequence``"

LinkT = TypeVar('LinkT', bound = 'Link')
"Bound to ``Link``"

MapiT = TypeVar('MapiT', bound = 'MappingApi')
"Bound to ``MappingApi``"

MapT = TypeVar('MapT', bound = Mapping)
"Bound to ``Mapping``"

MutSeqT = TypeVar('MutSeqT', bound = 'MutableSequenceApi')
"Bound to ``MutableSequenceApi``"

RuleT = TypeVar('RuleT', bound = 'Rule')
"Bound to ``Rule``"

# SenT = TypeVar('SenT', bound = 'Sentence')
# "Bound to ``Sentence``"

# SenT2 = TypeVar('SenT2', bound = 'Sentence')
# "Bound to ``Sentence``"

SeqApiT = TypeVar('SeqApiT', bound = 'SequenceApi')
"Bound to ``SequenceApi``"

SeqSetT = TypeVar('SeqSetT', bound = 'SequenceSet')
"Bound to ``SequenceSet``"

SetApiT = TypeVar('SetApiT', bound = 'SetApi')
"Bound to ``SetApi``"

SetT = TypeVar('SetT', bound = Set)
"Bound to ``Set``"

SysRulesT = TypeVar('SysRulesT', bound = LogicType.TabRules)
"Bound to ``LogicType.TabRules``"

TimT = TypeVar('TimT', bound = 'TimingCommon')
"Bound to ``TimingCommon``"

TT = TypeVar('TT', bound = type)
"Bound to ``type``, class decorator"

# ----

P = ParamSpec('P')
"Param spec"

#==========================+
#  Stub/Hint classes       |
#==========================+

if TYPE_CHECKING:

    @overload
    def iter(__etype: type[EnumT]) -> Iterator[EnumT]: ...

    @overload
    def iter(__it: Iterable[T]) -> Iterator[T]: ...

    @overload
    def iter(__function: Callable[[], T], __sentinel: Any) -> Iterator[T]: ...

    class TypeInstDict(dict[type[VT], VT]):
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

    FiltersDict = TypeInstDict[filters.NodeCompare]
    "Dict of filter type to filter."

    class EnumDictType(_enum._EnumDict):
        'Stub type for annotation reference.'
        _member_names: list[str]
        _last_values : list[object]
        _ignore      : list[str]
        _auto_called : bool
        _cls_name    : str

    class _property(property, Generic[Self, T]):
        "Stub adapted from typing module with added annotations."
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
    iter = builtins.iter
    TypeInstDict = FiltersDict = dict
    EnumDictType = _enum._EnumDict
    _property = property
    
del(
    builtins,
)