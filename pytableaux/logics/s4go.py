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
from . import go as GO
from . import kfde as KFDE
from . import s4fde as S4FDE


class Meta(GO.Meta, S4FDE.Meta):
    name = 'S4GO'
    title = 'GO S4 modal logic'
    description = 'Modal version of GO with S4 access'
    category_order = 59
    extension_of = ('GO')

class Model(GO.Model, S4FDE.Model):

    def _unmodal_values(self, s, /, **kw):
        return map(self.truth_function.Assertion, super()._unmodal_values(s, **kw))

class System(GO.System, S4FDE.System): pass

class Rules(GO.Rules):

    Reflexive = S4FDE.Rules.Reflexive
    Transitive = S4FDE.Rules.Transitive

    class PossibilityNegatedDesignated(KFDE.Rules.NecessityDesignated):
        new_designation = staticmethod(opr.not_)

    class NecessityNegatedDesignated(KFDE.Rules.PossibilityDesignated):
        new_designation = staticmethod(opr.not_)

    class PossibilityUndesignated(rules.NegatingFlippingRule): pass
    class NecessityUndesignated(rules.NegatingFlippingRule): pass
    class PossibilityNegatedUndesignated(rules.FlippingRule): pass
    class NecessityNegatedUndesignated(rules.FlippingRule): pass

    unmodal_groups = (
        group(
            KFDE.Rules.NecessityDesignated,
            PossibilityNegatedDesignated),
        group(
            KFDE.Rules.PossibilityDesignated,
            NecessityNegatedDesignated))

    groups = (
        # non-branching rules
        tuple(qset(GO.Rules.groups[0]) - GO.Rules.unquantifying_rules) + (
            PossibilityUndesignated,
            PossibilityNegatedUndesignated,
            NecessityUndesignated,
            NecessityNegatedUndesignated),
        group(Transitive),
        *unmodal_groups,
        group(Reflexive),
        # branching rules
        tuple(qset(GO.Rules.groups[1]) - GO.Rules.unquantifying_rules),
        *GO.Rules.unquantifying_groups)
    
    @staticmethod
    def _check_groups():
        cls = __class__
        for branching, i in zip(range(2), (0, -4)):
            for rulecls in cls.groups[i]:
                assert rulecls.branching == branching, f'{rulecls}'
