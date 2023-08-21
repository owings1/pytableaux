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

from ..lang import Operated, Quantified, Sentence
from . import fde as FDE
from . import k as K
from . import LogicType

class Meta(K.Meta):
    name = 'CPL'
    title = 'Classical Predicate Logic'
    modal = False
    category = 'Bivalent'
    description = 'Standard bivalent logic with predication, without quantification'
    category_order = 1
    tags = (
        'bivalent',
        'non-modal')
    native_operators = FDE.Meta.native_operators

class Model(K.Model):

    def is_sentence_opaque(self, s: Sentence, /):
        """
        A sentence is opaque if it is a quantified sentence, or its operator is
        either Necessity or Possibility.
        """
        stype = type(s)
        if stype is Quantified:
            return True
        if stype is Operated and s.operator in self.modal_operators:
            return True
        return super().is_sentence_opaque(s)

    def get_data(self) -> dict:
        data = self.frames[0].get_data()['value']
        del data['world']
        return data

class Rules(LogicType.Rules):

    closure = K.Rules.closure

    groups = (
        (
            # non-branching rules
            K.Rules.IdentityIndiscernability,
            K.Rules.Assertion,
            K.Rules.AssertionNegated,
            K.Rules.Conjunction,
            K.Rules.DisjunctionNegated,
            K.Rules.MaterialConditionalNegated,
            K.Rules.ConditionalNegated,
            K.Rules.DoubleNegation),
        (
            # branching rules
            K.Rules.ConjunctionNegated,
            K.Rules.Disjunction,
            K.Rules.MaterialConditional,
            K.Rules.MaterialBiconditional,
            K.Rules.MaterialBiconditionalNegated,
            K.Rules.Conditional,
            K.Rules.Biconditional,
            K.Rules.BiconditionalNegated))

class System(K.System):
    pass
