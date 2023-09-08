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
from . import kk3w as KK3W
from . import k3w as K3W


class Meta(KK3W.Meta):
    name = 'S4K3W'
    title = 'K3W with S4 modal'
    description = 'Modal version of K3W based on S4 normal modal logic'
    category_order = 29
    extension_of = ('TK3W')

class Model(S4FDE.Model, K3W.Model): pass
class System(FDE.System): pass

class Rules(LogicType.Rules):
    closure = K3.Rules.closure
    groups = (
        # non-branching rules
        KK3W.Rules.groups[0],
        # modal rules
        *S4FDE.Rules.groups[1:5],
        # branching rules
        *K3W.Rules.groups[1:3],
        # quantifier rules
        *FDE.Rules.groups[-2:])

    @classmethod
    def _check_groups(cls):
        for branching, i in zip(range(2), (0, -4, -3)):
            for rulecls in cls.groups[i]:
                assert rulecls.branching == branching, f'{rulecls}'
