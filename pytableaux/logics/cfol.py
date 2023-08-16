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

from ..lang import Quantified
from . import cpl as CPL
from . import k as K

class Meta(CPL.Meta):
    name = 'CFOL'
    title = 'Classical First Order Logic'
    category = 'Bivalent'
    description = 'Standard bivalent logic with full first-order quantification'
    category_order = 2
    tags = (
        'bivalent',
        'non-modal',
        'first-order')

class Model(CPL.Model):

    def is_sentence_opaque(self, s, /) -> bool:
        "A sentence is opaque if its operator is either Necessity or Possibility."
        return type(s) is not Quantified and super().is_sentence_opaque(s)

class System(CPL.System):
    pass

class Rules(CPL.Rules):

    groups = (
        (
            # non-branching rules
            K.Rules.IdentityIndiscernability,
            K.Rules.DoubleNegation,
            K.Rules.Assertion,
            K.Rules.AssertionNegated,
            K.Rules.Conjunction,
            K.Rules.DisjunctionNegated,
            K.Rules.MaterialConditionalNegated,
            K.Rules.ConditionalNegated,
            K.Rules.ExistentialNegated,
            K.Rules.UniversalNegated),
        (
            # branching rules
            K.Rules.ConjunctionNegated,
            K.Rules.Disjunction,
            K.Rules.MaterialConditional,
            K.Rules.MaterialBiconditional,
            K.Rules.MaterialBiconditionalNegated,
            K.Rules.Conditional,
            K.Rules.Biconditional,
            K.Rules.BiconditionalNegated,
        #),
        #(
            K.Rules.Existential,
            K.Rules.Universal))

