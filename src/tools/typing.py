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
#
# ------------------
#
# pytableaux - tools.typing module
from __future__ import annotations
from collections.abc import Set
from typing import Any, Callable, Mapping, ParamSpec, SupportsIndex, TypeVar, overload

T = TypeVar('T')
T1 = TypeVar('T1')
T2 = TypeVar('T2')
# Key type
KT = TypeVar('KT')
# Value type
VT = TypeVar('VT')
# Return type
RT = TypeVar('RT')
# Comparer
LHS = TypeVar('LHS')
RHS = TypeVar('RHS')
# Callable bound, use for decorator, etc.
F = TypeVar('F',  bound = Callable[..., Any])
P = ParamSpec('P')
# Self type
Self = TypeVar('Self')

T_co  = TypeVar('T_co',  covariant = True)
KT_co = TypeVar('KT_co', covariant = True)
VT_co = TypeVar('VT_co', covariant = True)
T_contra = TypeVar('T_contra', contravariant = True)
# Exception bound
ExT = TypeVar('ExT', bound = Exception)
# Type bound, use for class decorator, etc.
TT    = TypeVar('TT',    bound = type)
TT_co = TypeVar('TT_co', bound = type, covariant = True)
IndexType = SupportsIndex | slice
NotImplType = type(NotImplemented)

MapT  = TypeVar('MapT',  bound = 'Mapping')
SetT  = TypeVar('SetT',  bound = 'Set')

class TypeInstDict(dict[type[VT], VT],
    metaclass = type('TidMeta', (type,), dict(__call__ = dict))):
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