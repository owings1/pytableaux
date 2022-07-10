# -*- coding: utf-8 -*-
# pytableaux, a multi-logic proof generator.
# Copyright (C) 2014-2022 Doug Owings.
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

import pytableaux.logics.cpl as CPL
import pytableaux.logics.k as K
from pytableaux.lang import Quantified

name = 'CFOL'

class Meta(CPL.Meta):
    title       = 'Classical First Order Logic'
    category    = 'Bivalent'
    description = 'Standard bivalent logic with full first-order quantification'
    category_order = 2
    tags = (
        'bivalent',
        'non-modal',
        'first-order',
    )

class Model(CPL.Model):

    def is_sentence_opaque(self, s, /) -> bool:
        """
        A sentence is opaque if its operator is either Necessity or Possibility.
        """
        return type(s) is not Quantified and super().is_sentence_opaque(s)

class TableauxSystem(CPL.TableauxSystem):
    pass

@TableauxSystem.initialize
class TabRules(CPL.TabRules):
    """
    The Tableaux System for CFOL contains all the rules from :ref:`CPL <CPL>`,
    including the CPL closure rules, and adds additional rules for the quantifiers.
    """
    class Existential(K.TabRules.Existential, modal = False):
        """
        From an unticked existential node *n* on a branch *b*, quantifying over
        variable *v* into sentence *s*, add a node to *b* with the substitution
        into *s* of *v* with a constant new to *b*, then tick *n*.
        """

    class ExistentialNegated(K.TabRules.ExistentialNegated, modal = False):
        """
        From an unticked negated existential node *n* on a branch *b*,
        quantifying over variable *v* into sentence *s*, add a universally quantified
        node to *b* over *v* into the negation of *s*, then tick *n*.
        """

    class Universal(K.TabRules.Universal, modal = False):
        """
        From a universal node on a branch *b*, quantifying over variable *v* into
        sentence *s*, result *r* of substituting a constant *c* on *b* (or a new constant if none
        exists) for *v* into *s* does not appear on *b*, add a node with *r* to
        *b*. The node *n* is never ticked.
        """

    class UniversalNegated(K.TabRules.UniversalNegated, modal = False):
        """
        From an unticked negated universal node *n* on a branch *b*,
        quantifying over variable *v* into sentence *s*, add an existentially
        quantified node to *b* over *v* into the negation of *s*,
        then tick *n*.
        """

    rule_groups = (
        (
            # non-branching rules
            CPL.TabRules.IdentityIndiscernability,
            CPL.TabRules.DoubleNegation,
            CPL.TabRules.Assertion,
            CPL.TabRules.AssertionNegated,
            CPL.TabRules.Conjunction,
            CPL.TabRules.DisjunctionNegated,
            CPL.TabRules.MaterialConditionalNegated,
            CPL.TabRules.ConditionalNegated,
            ExistentialNegated,
            UniversalNegated,
        ),
        (
            # branching rules
            CPL.TabRules.ConjunctionNegated,
            CPL.TabRules.Disjunction,
            CPL.TabRules.MaterialConditional,
            CPL.TabRules.MaterialBiconditional,
            CPL.TabRules.MaterialBiconditionalNegated,
            CPL.TabRules.Conditional,
            CPL.TabRules.Biconditional,
            CPL.TabRules.BiconditionalNegated,
        #),
        #(

            Existential,
            Universal,
        ),
    )

