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

import operator as opr

from ..proof import rules
from ..tools import group, qset
from . import LogicType
from . import fde as FDE
from . import go as GO
from . import k3 as K3
from . import kfde as KFDE
from . import s4 as S4
from . import s4fde as S4FDE
from . import t as T


class Meta(GO.Meta):
    name = 'S4GO'
    modal = True
    title = 'GO S4 modal logic'
    description = 'Modal version of GO with S4 access'
    category_order = 59
    extension_of = ('GO')

class Model(S4FDE.Model, GO.Model):

    def _unmodal_values(self, s, w1, /):
        return map(self.truth_function.Assertion, super()._unmodal_values(s, w1))

class System(FDE.System): pass

class Rules(LogicType.Rules):

    closure = K3.Rules.closure

    class PossibilityNegatedDesignated(KFDE.Rules.NecessityDesignated):
        new_designation = staticmethod(opr.not_)

    class NecessityNegatedDesignated(KFDE.Rules.PossibilityDesignated):
        new_designation = staticmethod(opr.not_)

    class PossibilityUndesignated(rules.NegatingFlippingRule): pass
    class NecessityUndesignated(rules.NegatingFlippingRule): pass
    class PossibilityNegatedUndesignated(rules.FlippingRule): pass
    class NecessityNegatedUndesignated(rules.FlippingRule): pass

    groups = (
        # non-branching rules
        tuple(qset(GO.Rules.groups[0]) - GO.Rules.unquantifying_rules) + (
            PossibilityUndesignated,
            PossibilityNegatedUndesignated,
            NecessityUndesignated,
            NecessityNegatedUndesignated),
        group(S4.Rules.Transitive),
        # modal operator rules
        group(
            KFDE.Rules.NecessityDesignated,
            PossibilityNegatedDesignated),
        group(
            KFDE.Rules.PossibilityDesignated,
            NecessityNegatedDesignated),
        group(T.Rules.Reflexive),
        # branching rules
        tuple(qset(GO.Rules.groups[1]) - GO.Rules.unquantifying_rules),
        # quantifier rules
        *GO.Rules.unquantifying_groups)
    
    @classmethod
    def _check_groups(cls):
        for branching, i in zip(range(2), (0, -4)):
            for rulecls in cls.groups[i]:
                assert rulecls.branching == branching, f'{rulecls}'
