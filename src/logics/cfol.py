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

from . import k as K, cpl as CPL

class Model(K.Model):
    """
    A CFOL Model is just like :ref:`CPL model <cpl-model>` but with quantification.
    """

    def is_sentence_opaque(self, sentence):
        """
        A sentence is opaque if its operator is either Necessity or Possibility.
        """
        if sentence.operator in self.modal_operators:
            return True
        return super().is_sentence_opaque(sentence)

    def get_data(self):
        data = self.world_frame(0).get_data()['value']
        del data['world']
        return data

    def add_access(self, w1, w2):
        raise NotImplementedError()

class TableauxSystem(CPL.TableauxSystem):
    """
    CFOL's Tableaux System inherits directly from :ref:`CPL <CPL>`'s.
    """

class TableauxRules(object):
    """
    The Tableaux System for CFOL contains all the rules from :ref:`CPL <CPL>`,
    including the CPL closure rules, and adds additional rules for the quantifiers.
    """

    class ContradictionClosure(CPL.TableauxRules.ContradictionClosure):
        pass

    class SelfIdentityClosure(CPL.TableauxRules.SelfIdentityClosure):
        pass

    class NonExistenceClosure(CPL.TableauxRules.NonExistenceClosure):
        pass

    class DoubleNegation(CPL.TableauxRules.DoubleNegation):
        pass

    class Assertion(CPL.TableauxRules.Assertion):
        pass

    class AssertionNegated(CPL.TableauxRules.AssertionNegated):
        pass

    class Conjunction(CPL.TableauxRules.Conjunction):
        pass

    class ConjunctionNegated(CPL.TableauxRules.ConjunctionNegated):
        pass

    class Disjunction(CPL.TableauxRules.Disjunction):
        pass

    class DisjunctionNegated(CPL.TableauxRules.DisjunctionNegated):
        pass

    class MaterialConditional(CPL.TableauxRules.MaterialConditional):
        pass

    class MaterialConditionalNegated(CPL.TableauxRules.MaterialConditionalNegated):
        pass

    class MaterialBiconditional(CPL.TableauxRules.MaterialBiconditional):
        pass

    class MaterialBiconditionalNegated(CPL.TableauxRules.MaterialBiconditionalNegated):
        pass

    class Conditional(CPL.TableauxRules.Conditional):
        pass

    class ConditionalNegated(CPL.TableauxRules.ConditionalNegated):
        pass

    class Biconditional(CPL.TableauxRules.Biconditional):
        pass

    class BiconditionalNegated(CPL.TableauxRules.BiconditionalNegated):
        pass

    class Existential(K.TableauxRules.Existential):
        """
        From an unticked existential node *n* on a branch *b*, quantifying over
        variable *v* into sentence *s*, add a node to *b* with the substitution
        into *s* of *v* with a constant new to *b*, then tick *n*.
        """
        modal = False

    class ExistentialNegated(K.TableauxRules.ExistentialNegated):
        """
        From an unticked negated existential node *n* on a branch *b*,
        quantifying over variable *v* into sentence *s*, add a universally quantified
        node to *b* over *v* into the negation of *s*, then tick *n*.
        """
        modal = False

    class Universal(K.TableauxRules.Universal):
        """
        From a universal node on a branch *b*, quantifying over variable *v* into
        sentence *s*, result *r* of substituting a constant *c* on *b* (or a new constant if none
        exists) for *v* into *s* does not appear on *b*, add a node with *r* to
        *b*. The node *n* is never ticked.
        """
        modal = False

    class UniversalNegated(K.TableauxRules.UniversalNegated):
        """
        From an unticked negated universal node *n* on a branch *b*,
        quantifying over variable *v* into sentence *s*, add an existentially
        quantified node to *b* over *v* into the negation of *s*,
        then tick *n*.
        """
        modal = False

    class IdentityIndiscernability(CPL.TableauxRules.IdentityIndiscernability):
        pass

    closure_rules = [
        ContradictionClosure,
        SelfIdentityClosure,
        NonExistenceClosure,
    ]

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
            ExistentialNegated,
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
        #],
        #[

            Existential,
            Universal,
        ]
    ]