# -*- coding: utf-8 -*-
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
from __future__ import annotations

from . import LogicType
from . import fde as FDE
from . import k3 as K3
from . import s4fde as S4FDE
from . import kb3e as KB3E
from . import b3e as B3E


class Meta(KB3E.Meta):
    name = 'S4B3E'
    title = 'B3E with S4 modal'
    description = 'Modal version of B3E based on S4 normal modal logic'
    category_order = 34
    extension_of = ('TB3E')

class Model(S4FDE.Model, B3E.Model): pass
class System(FDE.System): pass

class Rules(LogicType.Rules):
    closure = K3.Rules.closure
    groups = (
        # non-branching rules
        KB3E.Rules.groups[0],
        # modal rules
        *S4FDE.Rules.groups[1:5],
        # branching rules
        *B3E.Rules.groups[1:4],
        # quantifier rules
        *FDE.Rules.groups[-2:])

    @classmethod
    def _check_groups(cls):
        for branching, i in zip(range(4), (0, -5, -4, -3)):
            for rulecls in cls.groups[i]:
                assert rulecls.branching == branching, f'{rulecls}'
