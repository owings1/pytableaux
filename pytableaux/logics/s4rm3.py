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
from . import lp as LP
from . import s4fde as S4FDE
from . import krm3 as KRM3
from . import rm3 as RM3


class Meta(KRM3.Meta):
    name = 'S4RM3'
    title = 'RM3 with S4 modal'
    description = 'Modal version of RM3 based on S4 normal modal logic'
    category_order = 24
    extension_of = ('TRM3')

class Model(S4FDE.Model, RM3.Model): pass
class System(FDE.System): pass

class Rules(LogicType.Rules):
    closure = LP.Rules.closure
    groups = (
        # non-branching rules
        KRM3.Rules.groups[0],
        # modal rules
        *S4FDE.Rules.groups[1:5],
        # branching rules
        *RM3.Rules.groups[1:3],
        # quantifier rules
        *FDE.Rules.groups[-2:])

    @classmethod
    def _check_groups(cls):
        for branching, i in zip(range(3), (0, -4, -3)):
            for rulecls in cls.groups[i]:
                assert rulecls.branching == branching, f'{rulecls}'
