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

from ..tools import group
from . import LogicType
from . import fde as FDE
from . import k3 as K3
from . import kfde as KFDE
from . import kk3 as KK3
from . import l3 as L3


class Meta(KK3.Meta):
    name = 'KL3'
    title = 'L3 with K modal'
    description = 'Modal version of L3 based on K normal modal logic'
    category_order = L3.Meta.category_order
    native_operators = KFDE.Meta.native_operators | L3.Meta.native_operators
    category_order = 16
    extension_of = ('L3')

class Model(KFDE.Model, L3.Model): pass
class System(FDE.System): pass

class Rules(LogicType.Rules):
    closure = K3.Rules.closure
    groups = (
        L3.Rules.groups[0] + group(
            # non-branching rules
            KFDE.Rules.PossibilityNegatedDesignated,
            KFDE.Rules.PossibilityNegatedUndesignated,
            KFDE.Rules.NecessityNegatedDesignated,
            KFDE.Rules.NecessityNegatedUndesignated),
        # branching rules
        L3.Rules.groups[1],
        group(
            KFDE.Rules.NecessityDesignated,
            KFDE.Rules.PossibilityUndesignated),
        group(
            KFDE.Rules.NecessityUndesignated,
            KFDE.Rules.PossibilityDesignated),
        # quantifier rules
        FDE.Rules.groups[-2],
        FDE.Rules.groups[-1])

    @classmethod
    def _check_groups(cls):
        for branching, group in zip(range(2), cls.groups):
            for rulecls in group:
                assert rulecls.branching == branching, f'{rulecls}'
