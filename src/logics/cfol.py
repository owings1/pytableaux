# pytableaux, a multi-logic proof generator.
# Copyright (C) 2014-2021 Doug Owings.
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
#
# ------------------
#
# pytableaux - Classical First-Order Logic
name = 'CFOL'

class Meta(object):
    title    = 'Classical First Order Logic'
    category = 'Bivalent'
    description = 'Standard bivalent logic with full first-order quantification'
    tags = ['bivalent', 'non-modal', 'first-order']
    category_display_order = 2

from lexicals import Sentence, Quantified
from . import k as K, cpl as CPL
from itertools import chain

class Model(CPL.Model):
    """
    A CFOL Model is just like :ref:`CPL model <cpl-model>` but with quantification.
    """

    def is_sentence_opaque(self, s: Sentence):
        """
        A sentence is opaque if its operator is either Necessity or Possibility.
        """
        if isinstance(s, Quantified):
            return False
        return super().is_sentence_opaque(s)

class TableauxSystem(CPL.TableauxSystem):
    """
    CFOL's Tableaux System inherits directly from :ref:`CPL <CPL>`'s.
    """

class TabRules(object):
    """
    The Tableaux System for CFOL contains all the rules from :ref:`CPL <CPL>`,
    including the CPL closure rules, and adds additional rules for the quantifiers.
    """

    class ContradictionClosure(CPL.TabRules.ContradictionClosure):
        pass

    class SelfIdentityClosure(CPL.TabRules.SelfIdentityClosure):
        pass

    class NonExistenceClosure(CPL.TabRules.NonExistenceClosure):
        pass

    class DoubleNegation(CPL.TabRules.DoubleNegation):
        pass

    class Assertion(CPL.TabRules.Assertion):
        pass

    class AssertionNegated(CPL.TabRules.AssertionNegated):
        pass

    class Conjunction(CPL.TabRules.Conjunction):
        pass

    class ConjunctionNegated(CPL.TabRules.ConjunctionNegated):
        pass

    class Disjunction(CPL.TabRules.Disjunction):
        pass

    class DisjunctionNegated(CPL.TabRules.DisjunctionNegated):
        pass

    class MaterialConditional(CPL.TabRules.MaterialConditional):
        pass

    class MaterialConditionalNegated(CPL.TabRules.MaterialConditionalNegated):
        pass

    class MaterialBiconditional(CPL.TabRules.MaterialBiconditional):
        pass

    class MaterialBiconditionalNegated(CPL.TabRules.MaterialBiconditionalNegated):
        pass

    class Conditional(CPL.TabRules.Conditional):
        pass

    class ConditionalNegated(CPL.TabRules.ConditionalNegated):
        pass

    class Biconditional(CPL.TabRules.Biconditional):
        pass

    class BiconditionalNegated(CPL.TabRules.BiconditionalNegated):
        pass

    class Existential(K.TabRules.Existential):
        """
        From an unticked existential node *n* on a branch *b*, quantifying over
        variable *v* into sentence *s*, add a node to *b* with the substitution
        into *s* of *v* with a constant new to *b*, then tick *n*.
        """

    class ExistentialNegated(K.TabRules.ExistentialNegated):
        """
        From an unticked negated existential node *n* on a branch *b*,
        quantifying over variable *v* into sentence *s*, add a universally quantified
        node to *b* over *v* into the negation of *s*, then tick *n*.
        """

    class Universal(K.TabRules.Universal):
        """
        From a universal node on a branch *b*, quantifying over variable *v* into
        sentence *s*, result *r* of substituting a constant *c* on *b* (or a new constant if none
        exists) for *v* into *s* does not appear on *b*, add a node with *r* to
        *b*. The node *n* is never ticked.
        """

    class UniversalNegated(K.TabRules.UniversalNegated):
        """
        From an unticked negated universal node *n* on a branch *b*,
        quantifying over variable *v* into sentence *s*, add an existentially
        quantified node to *b* over *v* into the negation of *s*,
        then tick *n*.
        """

    class IdentityIndiscernability(CPL.TabRules.IdentityIndiscernability):
        pass

    closure_rules = (
        ContradictionClosure,
        SelfIdentityClosure,
        NonExistenceClosure,
    )

    rule_groups = (
        (
            # non-branching rules
            IdentityIndiscernability,
            DoubleNegation,
            Assertion,
            AssertionNegated,
            Conjunction,
            DisjunctionNegated,
            MaterialConditionalNegated,
            ConditionalNegated,
            ExistentialNegated,
            UniversalNegated,
        ),
        (
            # branching rules
            ConjunctionNegated,
            Disjunction,
            MaterialConditional,
            MaterialBiconditional,
            MaterialBiconditionalNegated,
            Conditional,
            Biconditional,
            BiconditionalNegated,
        #),
        #(

            Existential,
            Universal,
        ),
    )
    for cls in chain(closure_rules, chain.from_iterable(rule_groups)):
        cls.modal = False

TableauxRules = TabRules