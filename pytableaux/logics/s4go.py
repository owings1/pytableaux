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
from itertools import chain

import operator as opr

from ..proof import rules
from ..tools import group
from . import go as GO
from . import s4fde as S4FDE


class Meta(GO.Meta, S4FDE.Meta):
    name = 'S4GO'
    title = 'GO S4 modal logic'
    description = 'Modal version of GO with S4 access'
    category_order = 59
    extension_of = ('GO')

class Model(GO.Model, S4FDE.Model):

    def unmodal_values(self, s, /, world:int=0):
        return map(self.truth_function.Assertion, super().unmodal_values(s, world))

class System(GO.System, S4FDE.System): pass

class Rules(GO.Rules, S4FDE.Rules):

    class PossibilityNegatedDesignated(S4FDE.Rules.NecessityDesignated):
        new_designation = new_negated = staticmethod(opr.not_)

    class NecessityNegatedDesignated(S4FDE.Rules.PossibilityDesignated):
        new_designation = new_negated = staticmethod(opr.not_)

    class PossibilityUndesignated(rules.NegatingFlippingRule): pass
    class NecessityUndesignated(rules.NegatingFlippingRule): pass
    class PossibilityNegatedUndesignated(rules.FlippingRule): pass
    class NecessityNegatedUndesignated(rules.FlippingRule): pass

    nonbranching_modal_group = group(
        PossibilityUndesignated,
        PossibilityNegatedUndesignated,
        NecessityUndesignated,
        NecessityNegatedUndesignated)

    nonbranching_groups = group(
        group(
            *chain(*GO.Rules.nonbranching_groups),
            *nonbranching_modal_group))

    unmodal_groups = (
        group(
            S4FDE.Rules.NecessityDesignated,
            PossibilityNegatedDesignated),
        group(
            S4FDE.Rules.PossibilityDesignated,
            NecessityNegatedDesignated))

    groups = (
        *nonbranching_groups,
        group(S4FDE.Rules.Transitive),
        *unmodal_groups,
        group(S4FDE.Rules.Reflexive),
        *GO.Rules.branching_groups,
        *GO.Rules.unquantifying_groups)
    