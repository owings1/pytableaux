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
from . import lp as LP
from . import kfde as KFDE
from . import klp as KLP
from . import rm3 as RM3


class Meta(KLP.Meta):
    name = 'KRM3'
    title = 'RM3 with K modal'
    description = 'Modal version of RM3 based on K normal modal logic'
    category_order = RM3.Meta.category_order
    native_operators = KFDE.Meta.native_operators | RM3.Meta.native_operators
    category_order = 21
    extension_of = ('RM3')

class Model(KFDE.Model, RM3.Model): pass
class System(FDE.System): pass

class Rules(LogicType.Rules):
    closure = LP.Rules.closure
    groups = (
        RM3.Rules.groups[0] + group(
            # non-branching rules
            KFDE.Rules.PossibilityNegatedDesignated,
            KFDE.Rules.PossibilityNegatedUndesignated,
            KFDE.Rules.NecessityNegatedDesignated,
            KFDE.Rules.NecessityNegatedUndesignated),
        # branching rules
        *RM3.Rules.groups[1:3],
        # modal operator rules
        *KFDE.Rules.groups[2:4],
        # quantifier rules
        *FDE.Rules.groups[-2:])

    @classmethod
    def _check_groups(cls):
        for branching, group in zip(range(3), cls.groups):
            for rulecls in group:
                assert rulecls.branching == branching, f'{rulecls}'
