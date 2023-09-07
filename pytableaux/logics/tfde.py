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
from . import t as T
from . import kfde as KFDE
from ..tools import group


class Meta(KFDE.Meta):
    name = 'TFDE'
    title = 'FDE with T modal'
    description = 'Modal version of FDE based on T normal modal logic'
    category_order = T.Meta.category_order * 10 + 100 * KFDE.Meta.category_order
    category_order = 3
    extension_of = ('KFDE')

class Model(KFDE.Model):

    _ensure_reflexive = T.Model._ensure_reflexive

    def finish(self):
        self._check_not_finished()
        self._ensure_reflexive()
        return super().finish()

class System(FDE.System): pass

class Rules(LogicType.Rules):
    closure = KFDE.Rules.closure

    groups = (
        # non-branching rules
        KFDE.Rules.groups[0],
        # modal operator rules
        *KFDE.Rules.groups[2:4],
        group(T.Rules.Reflexive),
        # branching rules
        FDE.Rules.groups[1],
        # quantifier rules
        *FDE.Rules.groups[-2:])

    @classmethod
    def _check_groups(cls):
        for branching, i in zip(range(2), (0, 4)):
            for rulecls in cls.groups[i]:
                assert rulecls.branching == branching, f'{rulecls}'