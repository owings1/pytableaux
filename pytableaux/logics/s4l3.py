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
from . import kl3 as KL3
from . import l3 as L3


class Meta(KL3.Meta):
    name = 'S4L3'
    title = 'L3 with S4 modal'
    description = 'Modal version of L3 based on S4 normal modal logic'
    category_order = 19
    extension_of = ('TL3')

class Model(S4FDE.Model, L3.Model): pass
class System(FDE.System): pass

class Rules(LogicType.Rules):
    closure = K3.Rules.closure
    groups = (
        # non-branching rules
        KL3.Rules.groups[0],
        # modal rules
        *S4FDE.Rules.groups[1:5],
        # branching rules
        L3.Rules.groups[1],
        # quantifier rules
        *FDE.Rules.groups[-2:])

    @classmethod
    def _check_groups(cls):
        for branching, i in zip(range(2), (0, -3)):
            for rulecls in cls.groups[i]:
                assert rulecls.branching == branching, f'{rulecls}'
