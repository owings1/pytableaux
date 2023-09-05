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
from . import tfde as TFDE
from . import kfde as KFDE
from . import s4 as S4
from . import t as T
from ..tools import group


class Meta(KFDE.Meta):
    name = 'S4FDE'
    title = 'FDE with S4 modal'
    description = 'Modal version of FDE based on S4 normal modal logic'
    category_order = 4
    extension_of = ('TFDE')

class Model(TFDE.Model):

    _ensure_reflexive_transitive = S4.Model._ensure_reflexive_transitive

    def finish(self):
        self._check_not_finished()
        self._ensure_reflexive_transitive()
        return super().finish()

class System(FDE.System): pass

class Rules(LogicType.Rules):
    closure = KFDE.Rules.closure

    groups = (
        KFDE.Rules.groups[0],
        group(S4.Rules.Transitive),
        # modal operator rules
        KFDE.Rules.groups[2],
        KFDE.Rules.groups[3],
        group(T.Rules.Reflexive),
        # branching rules
        FDE.Rules.groups[1],
        # quantifier rules
        FDE.Rules.groups[-2],
        FDE.Rules.groups[-1])

    @classmethod
    def _check_groups(cls):
        for branching, i in zip(range(2), (0, 5)):
            for rulecls in cls.groups[i]:
                assert rulecls.branching == branching, f'{rulecls}'
