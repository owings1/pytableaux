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
# pytableaux - Classical Predicate Logic
name = 'CPL'

class Meta(object):

    title    = 'Classical Predicate Logic'
    category = 'Bivalent'

    description = 'Standard bivalent logic with predication, without quantification'

    tags = ['bivalent', 'non-modal']

    category_display_order = 1

import logic, examples
from logic import negate
from . import k

class Model(k.Model):
    """
    A CPL Model is just a `K model`_ with the single world-0 frame. Sentences
    with quantifiers or modal operators are treated as opaque. See `K frame`_
    for a description of the `atomics` and predicate `extensions`.

    .. _K model: k.html#logics.k.Model
    .. _K frame: k.html#logics.k.Model.Frame
    """

    def value_of_operated(self, sentence, **kw):
        """
        The value of a sentence with a truth-functional operator is determined by
        the values of its operands according to the following tables.

        //truth_tables//cpl//
        """
        return super(Model, self).value_of_operated(sentence, **kw)

    def is_sentence_opaque(self, sentence):
        """
        A sentence is opaque if it is a quantified sentence, or its operator is
        either Necessity or Possibility.
        """
        if sentence.is_quantified():
            return True
        if sentence.operator in self.modal_operators:
            return True
        return super(Model, self).is_sentence_opaque(sentence)

    def get_data(self):
        data = self.world_frame(0).get_data()['value']
        del data['world']
        return data

    def add_access(self, w1, w2):
        raise NotImplementedError()

class TableauxSystem(k.TableauxSystem):
    """
    A branch can be thought of as representing a case where each node's sentence
    is true.
    """

    @classmethod
    def build_trunk(cls, tableau, argument):
        """
        To build the trunk for an argument, add a node for each premise, and
        a node with the negation of the conclusion.        
        """
        branch = tableau.branch()
        for premise in argument.premises:
            branch.add({'sentence': premise})
        branch.add({'sentence': negate(argument.conclusion)})

class NonModal(object):
    modal = False

class TableauxRules(object):
    """
    In general, rules for connectives consist of two rules per connective:
    a "plain" rule, and a negated rule. The special case of negation has only
    one rule for double negation. There is also a special rule for Identity
    predicate.
    """

    class ContradictionClosure(NonModal, k.TableauxRules.ContradictionClosure):
        """
        A branch is closed if a sentence and its negation appear on the branch.
        """
        pass

    class SelfIdentityClosure(NonModal, k.TableauxRules.SelfIdentityClosure):
        """
        A branch is closed if a sentence of the form P{~ a = a} appears on the branch.
        """
        pass

    class NonExistenceClosure(NonModal, k.TableauxRules.NonExistenceClosure):
        """
        A branch is closed if a sentence of the form P{~!a} appears on the branch.
        """
        pass

    class DoubleNegation(NonModal, k.TableauxRules.DoubleNegation):
        """
        From an unticked double negation node *n* on a branch *b*, add a
        node to *b* with the double-negatum of *n*, then tick *n*.
        """
        pass

    class Assertion(NonModal, k.TableauxRules.Assertion):
        """
        From an unticked assertion node *n* on a branch *b*,
        add a node to *b* with the operand of *n*, then tick *n*.
        """
        pass

    class AssertionNegated(NonModal, k.TableauxRules.AssertionNegated):
        """
        From an unticked, negated assertion node *n* on a branch *b*,
        add a node to *b* with the negation of the assertion of *n*,
        then tick *n*.
        """
        pass

    class Conjunction(NonModal, k.TableauxRules.Conjunction):
        """
        From an unticked conjunction node *n* on a branch *b*, for each conjunct,
        add a node to *b* with the conjunct, then tick *n*.
        """
        pass

    class ConjunctionNegated(NonModal, k.TableauxRules.ConjunctionNegated):
        """
        From an unticked negated conjunction node *n* on a branch *b*, for each
        conjunct, make a new branch *b'* from *b* and add a node with the negation of
        the conjunct to *b*, then tick *n*.
        """
        pass

    class Disjunction(NonModal, k.TableauxRules.Disjunction):
        """
        From an unticked disjunction node *n* on a branch *b*, for each disjunct,
        make a new branch *b'* from *b* and add a node with the disjunct to *b'*,
        then tick *n*.
        """
        pass

    class DisjunctionNegated(NonModal, k.TableauxRules.DisjunctionNegated):
        """
        From an unticked negated disjunction node *n* on a branch *b*, for each
        disjunct, add a node with the negation of the disjunct to *b*, then tick *n*.
        """
        pass

    class MaterialConditional(NonModal, k.TableauxRules.MaterialConditional):
        """
        From an unticked material conditional node *n*on a branch *b*, make two
        new branches *b'* and *b''* from *b*, add a node with the negation of the
        antecedent to *b'*, and add a node with the conequent to *b''*, then tick
        *n*.
        """
        pass

    class MaterialConditionalNegated(NonModal, k.TableauxRules.MaterialConditionalNegated):
        """
        From an unticked negated material conditional node *n* on a branch *b*,
        add two nodes to *b*, one with the antecedent and the other with the negation
        of the consequent, then tick *n*.
        """
        pass

    class MaterialBiconditional(NonModal, k.TableauxRules.MaterialBiconditional):
        """
        From an unticked material biconditional node *n* on a branch *b*, make
        two new branches *b'* and *b''* from *b*, add two nodes to *b'*, one with
        the negation of the antecedent and one with the negation of the consequent,
        and add two nodes to *b''*, one with the antecedent and one with the consequent,
        then tick *n*.
        """
        pass

    class MaterialBiconditionalNegated(NonModal, k.TableauxRules.MaterialBiconditionalNegated):
        """
        From an unticked negated material biconditional node *n* on a branch *b*,
        make two new branches *b'* and *b''* from *b*, add two nodes to *b'*, one with
        the antecedent and the other with the negation of the consequent, and add two nodes
        to *b''*, one with the negation of the antecedent and the other with the consequent,
        then tick *n*.
        """
        pass

    class Conditional(NonModal, k.TableauxRules.Conditional):
        """
        The rule functions the same as the corresponding material conditional rule.

        From an unticked conditional node *n* on a branch *b*, make two
        new branches *b'* and *b''* from *b*, add a node with the negation of the
        antecedent to *b'*, and add a node with the conequent to *b''*, then tick
        *n*.
        """
        pass

    class ConditionalNegated(NonModal, k.TableauxRules.ConditionalNegated):
        """
        The rule functions the same as the corresponding material conditional rule.

        From an unticked negated conditional node *n* on a branch *b*,
        add two nodes to *b*, one with the antecedent and the other with the negation
        of the consequent, then tick *n*.
        """
        pass

    class Biconditional(NonModal, k.TableauxRules.Biconditional):
        """
        The rule functions the same as the corresponding material biconditional rule.

        From an unticked biconditional node *n* on a branch *b*, make
        two new branches *b'* and *b''* from *b*, add two nodes to *b'*, one with
        the negation of the antecedent and one with the negation of the consequent, and add two
        nodes to *b''*, one with the antecedent and one with the consequent, then
        tick *n*.
        """
        pass

    class BiconditionalNegated(NonModal, k.TableauxRules.BiconditionalNegated):
        """
        The rule functions the same as the corresponding material biconditional rule.

        From an unticked negated biconditional node *n* on a branch *b*,
        make two new branches *b'* and *b''* from *b*, add two nodes to *b'*, one with
        the antecedent and the other with the negation of the consequent, and add two nodes
        to *b''*, one with the negation of the antecedent and the other with the consequent,
        then tick *n*.
        """
        pass

    class IdentityIndiscernability(NonModal, k.TableauxRules.IdentityIndiscernability):
        """
        From an unticked node *n* having an Identity sentence *s* on an open branch *b*,
        and a predicated node *n'* whose sentence *s'* has a constant that is a parameter of *s*,
        if the replacement of that constant for the other constant of *s* is a sentence that does
        not appear on *b*, then add it.
        """
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
            Assertion,
            AssertionNegated,
            Conjunction,
            DisjunctionNegated,
            MaterialConditionalNegated,
            ConditionalNegated,
            DoubleNegation,
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
        ]
    ]