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
from typing import TYPE_CHECKING

import pytableaux.logics.k as K
from pytableaux.lang import Operated, Quantified, Sentence, Operator
from pytableaux.proof import Branch, Node, Tableau, snode

if TYPE_CHECKING:
    from pytableaux.lang import Argument

name = 'CPL'

class Meta:
    title       = 'Classical Predicate Logic'
    category    = 'Bivalent'
    description = 'Standard bivalent logic with predication, without quantification'
    category_order = 1
    tags = (
        'bivalent',
        'non-modal',
    )
    native_operators = (
        Operator.Negation, Operator.Conjunction, Operator.Disjunction,
        Operator.MaterialConditional, Operator.MaterialBiconditional,
    )

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

    def add_access(self, *_):
        raise TypeError("Non-modal model: '%s'" % type(self))

class TableauxSystem(K.TableauxSystem):

    modal = False

    @classmethod
    def build_trunk(cls, tab: Tableau, arg: Argument, /):
        b = tab.branch()
        b.extend(map(snode, arg.premises))
        b.append(snode(~arg.conclusion))


@TableauxSystem.initialize
class TabRules:

    class ContradictionClosure(K.TabRules.ContradictionClosure, modal = False):
        """
        A branch is closed if a sentence and its negation appear on the branch.
        """
        def _find_closing_node(self, node: Node, branch: Branch, /):
            s = self.sentence(node)
            if s is not None:
                return branch.find(dict(sentence = s.negative()))

    class SelfIdentityClosure(K.TabRules.SelfIdentityClosure, modal = False):
        """
        A branch is closed if a sentence of the form :s:`~ a = a` appears on the branch.
        """

    class NonExistenceClosure(K.TabRules.NonExistenceClosure, modal = False):
        """
        A branch is closed if a sentence of the form :s:`~!a` appears on the branch.
        """

    class DoubleNegation(K.TabRules.DoubleNegation, modal = False):
        """
        From an unticked double negation node *n* on a branch *b*, add a
        node to *b* with the double-negatum of *n*, then tick *n*.
        """

    class Assertion(K.TabRules.Assertion, modal = False):
        """
        From an unticked assertion node *n* on a branch *b*,
        add a node to *b* with the operand of *n*, then tick *n*.
        """

    class AssertionNegated(K.TabRules.AssertionNegated, modal = False):
        """
        From an unticked, negated assertion node *n* on a branch *b*,
        add a node to *b* with the negation of the assertion of *n*,
        then tick *n*.
        """

    class Conjunction(K.TabRules.Conjunction, modal = False):
        """
        From an unticked conjunction node *n* on a branch *b*, for each conjunct,
        add a node to *b* with the conjunct, then tick *n*.
        """

    class ConjunctionNegated(K.TabRules.ConjunctionNegated, modal = False):
        """
        From an unticked negated conjunction node *n* on a branch *b*, for each
        conjunct, make a new branch *b'* from *b* and add a node with the negation of
        the conjunct to *b*, then tick *n*.
        """

    class Disjunction(K.TabRules.Disjunction, modal = False):
        """
        From an unticked disjunction node *n* on a branch *b*, for each disjunct,
        make a new branch *b'* from *b* and add a node with the disjunct to *b'*,
        then tick *n*.
        """

    class DisjunctionNegated(K.TabRules.DisjunctionNegated, modal = False):
        """
        From an unticked negated disjunction node *n* on a branch *b*, for each
        disjunct, add a node with the negation of the disjunct to *b*, then tick *n*.
        """

    class MaterialConditional(K.TabRules.MaterialConditional, modal = False):
        """
        From an unticked material conditional node *n*on a branch *b*, make two
        new branches *b'* and *b''* from *b*, add a node with the negation of the
        antecedent to *b'*, and add a node with the conequent to *b''*, then tick
        *n*.
        """

    class MaterialConditionalNegated(K.TabRules.MaterialConditionalNegated, modal = False):
        """
        From an unticked negated material conditional node *n* on a branch *b*,
        add two nodes to *b*, one with the antecedent and the other with the negation
        of the consequent, then tick *n*.
        """

    class MaterialBiconditional(K.TabRules.MaterialBiconditional, modal = False):
        """
        From an unticked material biconditional node *n* on a branch *b*, make
        two new branches *b'* and *b''* from *b*, add two nodes to *b'*, one with
        the negation of the antecedent and one with the negation of the consequent,
        and add two nodes to *b''*, one with the antecedent and one with the consequent,
        then tick *n*.
        """

    class MaterialBiconditionalNegated(K.TabRules.MaterialBiconditionalNegated, modal = False):
        """
        From an unticked negated material biconditional node *n* on a branch *b*,
        make two new branches *b'* and *b''* from *b*, add two nodes to *b'*, one with
        the antecedent and the other with the negation of the consequent, and add two nodes
        to *b''*, one with the negation of the antecedent and the other with the consequent,
        then tick *n*.
        """

    class Conditional(K.TabRules.Conditional, modal = False):
        """
        The rule functions the same as the corresponding material conditional rule.

        From an unticked conditional node *n* on a branch *b*, make two
        new branches *b'* and *b''* from *b*, add a node with the negation of the
        antecedent to *b'*, and add a node with the conequent to *b''*, then tick
        *n*.
        """

    class ConditionalNegated(K.TabRules.ConditionalNegated, modal = False):
        """
        The rule functions the same as the corresponding material conditional rule.

        From an unticked negated conditional node *n* on a branch *b*,
        add two nodes to *b*, one with the antecedent and the other with the negation
        of the consequent, then tick *n*.
        """

    class Biconditional(K.TabRules.Biconditional, modal = False):
        """
        The rule functions the same as the corresponding material biconditional rule.

        From an unticked biconditional node *n* on a branch *b*, make
        two new branches *b'* and *b''* from *b*, add two nodes to *b'*, one with
        the negation of the antecedent and one with the negation of the consequent, and add two
        nodes to *b''*, one with the antecedent and one with the consequent, then
        tick *n*.
        """

    class BiconditionalNegated(K.TabRules.BiconditionalNegated, modal = False):
        """
        The rule functions the same as the corresponding material biconditional rule.

        From an unticked negated biconditional node *n* on a branch *b*,
        make two new branches *b'* and *b''* from *b*, add two nodes to *b'*, one with
        the antecedent and the other with the negation of the consequent, and add two nodes
        to *b''*, one with the negation of the antecedent and the other with the consequent,
        then tick *n*.
        """

    class IdentityIndiscernability(K.TabRules.IdentityIndiscernability, modal = False):
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
