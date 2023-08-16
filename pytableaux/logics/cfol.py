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

class TableauxSystem(CPL.TableauxSystem):
    pass

@TableauxSystem.initialize
class TabRules(CPL.TabRules):

    rule_groups = (
        (
            # non-branching rules
            K.TabRules.IdentityIndiscernability,
            K.TabRules.DoubleNegation,
            K.TabRules.Assertion,
            K.TabRules.AssertionNegated,
            K.TabRules.Conjunction,
            K.TabRules.DisjunctionNegated,
            K.TabRules.MaterialConditionalNegated,
            K.TabRules.ConditionalNegated,
            K.TabRules.ExistentialNegated,
            K.TabRules.UniversalNegated,
        ),
        (
            # branching rules
            K.TabRules.ConjunctionNegated,
            K.TabRules.Disjunction,
            K.TabRules.MaterialConditional,
            K.TabRules.MaterialBiconditional,
            K.TabRules.MaterialBiconditionalNegated,
            K.TabRules.Conditional,
            K.TabRules.Biconditional,
            K.TabRules.BiconditionalNegated,
        #),
        #(

            K.TabRules.Existential,
            K.TabRules.Universal,
        ),
    )

