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

from . import k, cpl

class Model(k.Model):
    """
    A CFOL Model is just a `K model`_ with the single world-0 frame. Sentences
    with modal operators are treated as opaque. See `K frame`_ for a description
    of the `atomics` and predicate `extensions`.

    .. _K model: k.html#logics.k.Model
    .. _K frame: k.html#logics.k.Frame
    """

    def value_of_operated(self, sentence, **kw):
        """
        The value of a sentence with a truth-functional operator is determined by
        the values of its operands according to the following tables.

        //truth_tables//cfol//
        """
        return super().value_of_operated(sentence, **kw)

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

class TableauxSystem(cpl.TableauxSystem):
    """
    CFOL's Tableaux System inherits directly from :ref:`CPL`'s.
    """

class TableauxRules(object):
    """
    The Tableaux System for CFOL contains all the rules from :ref:`CPL`, including the
    CPL closure rules, as well as additional rules for the quantifiers.
    """

    class ContradictionClosure(cpl.TableauxRules.ContradictionClosure):
        pass

    class SelfIdentityClosure(cpl.TableauxRules.SelfIdentityClosure):
        pass

    class NonExistenceClosure(cpl.TableauxRules.NonExistenceClosure):
        pass

    class DoubleNegation(cpl.TableauxRules.DoubleNegation):
        pass

    class Assertion(cpl.TableauxRules.Assertion):
        pass

    class AssertionNegated(cpl.TableauxRules.AssertionNegated):
        pass

    class Conjunction(cpl.TableauxRules.Conjunction):
        pass

    class ConjunctionNegated(cpl.TableauxRules.ConjunctionNegated):
        pass

    class Disjunction(cpl.TableauxRules.Disjunction):
        pass

    class DisjunctionNegated(cpl.TableauxRules.DisjunctionNegated):
        pass

    class MaterialConditional(cpl.TableauxRules.MaterialConditional):
        pass

    class MaterialConditionalNegated(cpl.TableauxRules.MaterialConditionalNegated):
        pass

    class MaterialBiconditional(cpl.TableauxRules.MaterialBiconditional):
        pass

    class MaterialBiconditionalNegated(cpl.TableauxRules.MaterialBiconditionalNegated):
        pass

    class Conditional(cpl.TableauxRules.Conditional):
        pass

    class ConditionalNegated(cpl.TableauxRules.ConditionalNegated):
        pass

    class Biconditional(cpl.TableauxRules.Biconditional):
        pass

    class BiconditionalNegated(cpl.TableauxRules.BiconditionalNegated):
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