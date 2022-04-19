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
    -----------------------
"""
from __future__ import annotations

import enum as _enum
from collections.abc import Set
from typing import Any, Callable, Mapping, ParamSpec, SupportsIndex, TypeVar, overload

#==========================+
#  Type variables          |
#==========================+

T = TypeVar('T')
"Generic, any type"

T1 = TypeVar('T1')
"Generic, any type"

T2 = TypeVar('T2')
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

T_co = TypeVar('T_co', covariant = True)
"Covariant, any type"

KT_co = TypeVar('KT_co', covariant = True)
"Covariant, key type"

VT_co = TypeVar('VT_co', covariant = True)
"Covariant, value type"

T_contra = TypeVar('T_contra', contravariant = True)
"Contravariant, any type"

F = TypeVar('F', bound = Callable[..., Any])
"Callable bound, decorator"

TT = TypeVar('TT',    bound = type)
"Type bound, class decorator"

TT_co = TypeVar('TT_co', bound = type, covariant = True)
"Type bound, covariant"

ExT = TypeVar('ExT', bound = Exception)
"Exception bound"

MapT = TypeVar('MapT', bound = Mapping)
"Mapping bound"

SetT = TypeVar('SetT', bound = Set)
"Set bound"

EnumT = TypeVar('EnumT', bound = _enum.Enum)
"Enum bound"

P = ParamSpec('P')
"Param spec"

#==========================+
#  Type aliases            |
#==========================+

IndexType = SupportsIndex | slice
"Integer or slice type"

NotImplType = type(NotImplemented)
"NotImplemented type"

#==========================+
#  Stub classes            |
#==========================+

class TypeInstDict(dict[type[VT], VT],
    metaclass = type('TidMeta', (type,), dict(__call__ = dict))
):
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