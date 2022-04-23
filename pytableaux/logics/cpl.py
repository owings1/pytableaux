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
#
# ------------------
#
# pytableaux - Classical Predicate Logic
from __future__ import annotations

name = 'CPL'

class Meta:
    title    = 'Classical Predicate Logic'
    category = 'Bivalent'
    description = 'Standard bivalent logic with predication, without quantification'
    tags = ['bivalent', 'non-modal']
    category_order = 1

from pytableaux.lang.collect import Argument
from pytableaux.lang.lex import Operated, Quantified, Sentence
from pytableaux.logics import k as K
from pytableaux.proof.common import Branch, Node
from pytableaux.proof.tableaux import Tableau
from pytableaux.tools.abcs import Abc, abcf

class Model(K.Model):
    """
    A CPL Model is just a :ref:`K model <k-model>` with a single :ref:`frame <k-frame>`.
    """

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
        data = self.world_frame(0).get_data()['value']
        del data['world']
        return data

    def add_access(self, *_):
        raise TypeError("Non-modal model: '%s'" % type(self))

class TableauxSystem(K.TableauxSystem):

    modal = False

    @classmethod
    def build_trunk(cls, tab: Tableau, arg: Argument, /):
        """
        To build the trunk for an argument, add a node for each premise, and
        a node with the negation of the conclusion.        
        """
        add = tab.branch().append
        for premise in arg.premises:
            add(dict(sentence = premise))
        add(dict(sentence = ~arg.conclusion))


class TabRules(Abc):
    """
    In general, rules for connectives consist of two rules per connective:
    a "plain" rule, and a negated rule. The special case of negation has only
    one rule for double negation. There is also a special rule for Identity
    predicate.
    """

    @abcf.after
    def clearmodal(cls):
        'Remove Modal filter from NodeFilters, and clear modal attribute.'
        from itertools import chain

        from pytableaux.proof.types import demodalize_rules
        demodalize_rules(chain(
            cls.closure_rules,
            chain.from_iterable(cls.rule_groups)
        ))

    class ContradictionClosure(K.TabRules.ContradictionClosure):
        """
        A branch is closed if a sentence and its negation appear on the branch.
        """
        def _find_closing_node(self, node: Node, branch: Branch, /):
            s = self.sentence(node)
            if s is not None:
                return branch.find(dict(sentence = s.negative()))

    class SelfIdentityClosure(K.TabRules.SelfIdentityClosure):
        """
        A branch is closed if a sentence of the form :s:`~ a = a` appears on the branch.
        """

    class NonExistenceClosure(K.TabRules.NonExistenceClosure):
        """
        A branch is closed if a sentence of the form :s:`~!a` appears on the branch.
        """

    class DoubleNegation(K.TabRules.DoubleNegation):
        """
        From an unticked double negation node *n* on a branch *b*, add a
        node to *b* with the double-negatum of *n*, then tick *n*.
        """

    class Assertion(K.TabRules.Assertion):
        """
        From an unticked assertion node *n* on a branch *b*,
        add a node to *b* with the operand of *n*, then tick *n*.
        """

    class AssertionNegated(K.TabRules.AssertionNegated):
        """
        From an unticked, negated assertion node *n* on a branch *b*,
        add a node to *b* with the negation of the assertion of *n*,
        then tick *n*.
        """

    class Conjunction(K.TabRules.Conjunction):
        """
        From an unticked conjunction node *n* on a branch *b*, for each conjunct,
        add a node to *b* with the conjunct, then tick *n*.
        """

    class ConjunctionNegated(K.TabRules.ConjunctionNegated):
        """
        From an unticked negated conjunction node *n* on a branch *b*, for each
        conjunct, make a new branch *b'* from *b* and add a node with the negation of
        the conjunct to *b*, then tick *n*.
        """

    class Disjunction(K.TabRules.Disjunction):
        """
        From an unticked disjunction node *n* on a branch *b*, for each disjunct,
        make a new branch *b'* from *b* and add a node with the disjunct to *b'*,
        then tick *n*.
        """

    class DisjunctionNegated(K.TabRules.DisjunctionNegated):
        """
        From an unticked negated disjunction node *n* on a branch *b*, for each
        disjunct, add a node with the negation of the disjunct to *b*, then tick *n*.
        """

    class MaterialConditional(K.TabRules.MaterialConditional):
        """
        From an unticked material conditional node *n*on a branch *b*, make two
        new branches *b'* and *b''* from *b*, add a node with the negation of the
        antecedent to *b'*, and add a node with the conequent to *b''*, then tick
        *n*.
        """

    class MaterialConditionalNegated(K.TabRules.MaterialConditionalNegated):
        """
        From an unticked negated material conditional node *n* on a branch *b*,
        add two nodes to *b*, one with the antecedent and the other with the negation
        of the consequent, then tick *n*.
        """

    class MaterialBiconditional(K.TabRules.MaterialBiconditional):
        """
        From an unticked material biconditional node *n* on a branch *b*, make
        two new branches *b'* and *b''* from *b*, add two nodes to *b'*, one with
        the negation of the antecedent and one with the negation of the consequent,
        and add two nodes to *b''*, one with the antecedent and one with the consequent,
        then tick *n*.
        """

    class MaterialBiconditionalNegated(K.TabRules.MaterialBiconditionalNegated):
        """
        From an unticked negated material biconditional node *n* on a branch *b*,
        make two new branches *b'* and *b''* from *b*, add two nodes to *b'*, one with
        the antecedent and the other with the negation of the consequent, and add two nodes
        to *b''*, one with the negation of the antecedent and the other with the consequent,
        then tick *n*.
        """

    class Conditional(K.TabRules.Conditional):
        """
        The rule functions the same as the corresponding material conditional rule.

        From an unticked conditional node *n* on a branch *b*, make two
        new branches *b'* and *b''* from *b*, add a node with the negation of the
        antecedent to *b'*, and add a node with the conequent to *b''*, then tick
        *n*.
        """

    class ConditionalNegated(K.TabRules.ConditionalNegated):
        """
        The rule functions the same as the corresponding material conditional rule.

        From an unticked negated conditional node *n* on a branch *b*,
        add two nodes to *b*, one with the antecedent and the other with the negation
        of the consequent, then tick *n*.
        """

    class Biconditional(K.TabRules.Biconditional):
        """
        The rule functions the same as the corresponding material biconditional rule.

        From an unticked biconditional node *n* on a branch *b*, make
        two new branches *b'* and *b''* from *b*, add two nodes to *b'*, one with
        the negation of the antecedent and one with the negation of the consequent, and add two
        nodes to *b''*, one with the antecedent and one with the consequent, then
        tick *n*.
        """

    class BiconditionalNegated(K.TabRules.BiconditionalNegated):
        """
        The rule functions the same as the corresponding material biconditional rule.

        From an unticked negated biconditional node *n* on a branch *b*,
        make two new branches *b'* and *b''* from *b*, add two nodes to *b'*, one with
        the antecedent and the other with the negation of the consequent, and add two nodes
        to *b''*, one with the negation of the antecedent and the other with the consequent,
        then tick *n*.
        """

    class IdentityIndiscernability(K.TabRules.IdentityIndiscernability):
        """
        From an unticked node *n* having an Identity sentence *s* on an open branch *b*,
        and a predicated node *n'* whose sentence *s'* has a constant that is a parameter of *s*,
        if the replacement of that constant for the other constant of *s* is a sentence that does
        not appear on *b*, then add it.
        """

    closure_rules = (
        ContradictionClosure,
        SelfIdentityClosure,
        NonExistenceClosure,
    )

    rule_groups = (
        (
            # non-branching rules
            IdentityIndiscernability,
            Assertion,
            AssertionNegated,
            Conjunction,
            DisjunctionNegated,
            MaterialConditionalNegated,
            ConditionalNegated,
            DoubleNegation,
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
        ),
    )
