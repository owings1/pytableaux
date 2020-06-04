# pytableaux, a multi-logic proof generator.
# Copyright (C) 2014-2020 Doug Owings.
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
title = 'Classical First Order Logic'
description = 'Standard bivalent logic with full first-order quantification'
tags_list = ['bivalent', 'non-modal', 'first-order']
tags = set(tags_list)
category = 'Bivalent'
category_display_order = 2

import logic, examples
from logic import negate, NotImplementedError
from . import k, cpl

class Model(k.Model):
    """
    A CFOL Model is just a `K model`_ with the single world-0 frame. Sentences
    with modal operators are treated as opaque. See `K frame`_ for a description
    of the `atomics` and predicate `extensions`.

    .. _K model: k.html#logics.k.Model
    .. _K frame: k.html#logics.k.Model.Frame
    """

    def value_of_operated(self, sentence, **kw):
        """
        The value of a sentence with a truth-functional operator is determined by
        the values of its operands according to the following tables.

        //truth_tables//cfol//
        """
        return super(Model, self).value_of_operated(sentence, **kw)

    def is_sentence_opaque(self, sentence):
        """
        A sentence is opaque if its operator is either Necessity or Possibility.
        """
        if sentence.operator in self.modal_operators:
            return True
        return super(Model, self).is_sentence_opaque(sentence)

    def get_data(self):
        data = self.world_frame(0).get_data()['value']
        del data['world']
        return data

    def add_access(self, w1, w2):
        raise NotImplementedError(NotImplemented)

class TableauxSystem(cpl.TableauxSystem):
    """
    CFOL's Tableaux System inherits directly from `CPL`_'s.
    """

class TableauxRules(object):
    """
    The Tableaux System for CFOL contains all the rules from `CPL`_, including the
    `CPL closure rules`_, as well as additional rules for the quantifiers.

    .. _CPL closure rules: cpl.html#logics.cpl.TableauxRules.Closure
    """

    class DoubleNegation(cpl.TableauxRules.DoubleNegation):
        """
        This rule is the same as the `CPL DoubleNegation rule`_.

        .. _CPL DoubleNegation rule: cpl.html#logics.cpl.TableauxRules.DoubleNegation
        """
        pass

    class Assertion(cpl.TableauxRules.Assertion):
        """
        This rule is the same as the `CPL Assertion rule`_.

        .. _CPL Assertion rule: cpl.html#logics.cpl.TableauxRules.Assertion
        """
        pass

    class AssertionNegated(cpl.TableauxRules.AssertionNegated):
        """
        This rule is the same as the `CPL AssertionNegated rule`_.

        .. _CPL AssertionNegated rule: cpl.html#logics.cpl.TableauxRules.AssertionNegated
        """
        pass

    class Conjunction(cpl.TableauxRules.Conjunction):
        """
        This rule is the same as the `CPL Conjunction rule`_.

        .. _CPL Conjunction rule: cpl.html#logics.cpl.TableauxRules.Conjunction
        """
        pass

    class ConjunctionNegated(cpl.TableauxRules.ConjunctionNegated):
        """
        This rule is the same as the `CPL ConjunctionNegated rule`_.

        .. _CPL ConjunctionNegated rule: cpl.html#logics.cpl.TableauxRules.ConjunctionNegated
        """
        pass

    class Disjunction(cpl.TableauxRules.Disjunction):
        """
        This rule is the same as the `CPL Disjunction rule`_.

        .. _CPL Disjunction rule: cpl.html#logics.cpl.TableauxRules.Disjunction
        """
        pass

    class DisjunctionNegated(cpl.TableauxRules.DisjunctionNegated):
        """
        This rule is the same as the `CPL DisjunctionNegated rule`_.

        .. _CPL DisjunctionNegated rule: cpl.html#logics.cpl.TableauxRules.DisjunctionNegated
        """
        pass

    class MaterialConditional(cpl.TableauxRules.MaterialConditional):
        """
        This rule is the same as the `CPL MaterialConditional rule`_.

        .. _CPL MaterialConditional rule: cpl.html#logics.cpl.TableauxRules.MaterialConditional
        """
        pass

    class MaterialConditionalNegated(cpl.TableauxRules.MaterialConditionalNegated):
        """
        This rule is the same as the `CPL MaterialConditionalNegated rule`_.

        .. _CPL MaterialConditionalNegated rule: cpl.html#logics.cpl.TableauxRules.MaterialConditionalNegated
        """
        pass

    class MaterialBiconditional(cpl.TableauxRules.MaterialBiconditional):
        """
        This rule is the same as the `CPL DoubleNegation rule`_.

        .. _CPL MaterialBiconditional rule: cpl.html#logics.cpl.TableauxRules.MaterialBiconditional
        """
        pass

    class MaterialBiconditionalNegated(cpl.TableauxRules.MaterialBiconditionalNegated):
        """
        This rule is the same as the `CPL MaterialBiconditionalNegated rule`_.

        .. _CPL MaterialBiconditionalNegated rule: cpl.html#logics.cpl.TableauxRules.MaterialBiconditionalNegated
        """
        pass

    class Conditional(cpl.TableauxRules.Conditional):
        """
        This rule is the same as the `CPL Conditional rule`_.

        .. _CPL Conditional rule: cpl.html#logics.cpl.TableauxRules.Conditional
        """
        pass

    class ConditionalNegated(cpl.TableauxRules.ConditionalNegated):
        """
        This rule is the same as the `CPL ConditionalNegated rule`_.

        .. _CPL ConditionalNegated rule: cpl.html#logics.cpl.TableauxRules.ConditionalNegated
        """
        pass

    class Biconditional(cpl.TableauxRules.Biconditional):
        """
        This rule is the same as the `CPL Biconditional rule`_.

        .. _CPL Biconditional rule: cpl.html#logics.cpl.TableauxRules.Biconditional
        """
        pass

    class BiconditionalNegated(cpl.TableauxRules.BiconditionalNegated):
        """
        This rule is the same as the `CPL BiconditionalNegated rule`_.

        .. _CPL BiconditionalNegated rule: cpl.html#logics.cpl.TableauxRules.BiconditionalNegated
        """
        pass

    class Existential(cpl.NonModal, k.TableauxRules.Existential):
        """
        From an unticked existential node *n* on a branch *b*, quantifying over
        variable *v* into sentence *s*, add a node to *b* with the substitution
        into *s* of *v* with a constant new to *b*, then tick *n*.
        """
        pass

    class ExistentialNegated(cpl.NonModal, k.TableauxRules.ExistentialNegated):
        """
        From an unticked negated existential node *n* on a branch *b*,
        quantifying over variable *v* into sentence *s*, add a universally quantified
        node to *b* over *v* into the negation of *s*, then tick *n*.
        """
        pass

    class Universal(cpl.NonModal, k.TableauxRules.Universal):
        """
        From a universal node on a branch *b*, quantifying over variable *v* into
        sentence *s*, result *r* of substituting a constant *c* on *b* (or a new constant if none
        exists) for *v* into *s* does not appear on *b*, add a node with *r* to
        *b*. The node *n* is never ticked.
        """
        pass

    class UniversalNegated(cpl.NonModal, k.TableauxRules.UniversalNegated):
        """
        From an unticked negated universal node *n* on a branch *b*,
        quantifying over variable *v* into sentence *s*, add an existentially
        quantified node to *b* over *v* into the negation of *s*,
        then tick *n*.
        """
        pass

    class IdentityIndiscernability(cpl.TableauxRules.IdentityIndiscernability):
        """
        This rule is the same as the `CPL IdentityIndiscernability rule`_.

        .. _CPL IdentityIndiscernability rule: cpl.html#logics.cpl.TableauxRules.IdentityIndiscernability
        """
        pass

    closure_rules = list(cpl.TableauxRules.closure_rules)

    rule_groups = [
        [
            # non-branching rules

            IdentityIndiscernability,
            DoubleNegation,
            Assertion,
            AssertionNegated,
            Conjunction,
            DisjunctionNegated,
            MaterialConditionalNegated,
            ConditionalNegated,
            Existential,
            ExistentialNegated,
            Universal,
            UniversalNegated,
        ],
        [
            # branching rules
            ConjunctionNegated,
            Disjunction,
            MaterialConditional,
            MaterialBiconditional,
            MaterialBiconditionalNegated,
            Conditional,
            Biconditional,
            BiconditionalNegated,
        ],
    ]