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

from ..lang import Operator, Quantified, Quantifier
from ..proof import Branch, Node, adds, group, rules, sdnode
from ..tools import maxceil, minfloor
from . import b3e as B3E
from . import fde as FDE
from . import k3 as K3
from .b3e import crunch, gap

name = 'GO'

class Meta(K3.Meta):
    title       = 'Gappy Object 3-valued Logic'
    description = 'Three-valued logic (True, False, Neither) with classical-like binary operators'
    category_order = 60
    native_operators = FDE.Meta.native_operators + (Operator.Conditional, Operator.Biconditional)

class Model(K3.Model):

    def truth_function(self, oper, a, b=None):
        oper = Operator(oper)
        if oper is Operator.Assertion:
            return self.Value[crunch(self.Value[a].num)]
        elif oper is Operator.Disjunction:
            return self.Value[max(crunch(self.Value[a].num), crunch(self.Value[b].num))]
        elif oper is Operator.Conjunction:
            return self.Value[min(crunch(self.Value[a].num), crunch(self.Value[b].num))]
        elif oper is Operator.Conditional:
            return self.Value[
                crunch(
                    max(
                        1 - self.Value[a].num,
                        self.Value[b].num,
                        gap(self.Value[a].num) + gap(self.Value[b].num)
                    )
                )
            ]
        return super().truth_function(oper, a, b)

    def value_of_existential(self, sentence: Quantified, **kw):
        """
        The value of an existential sentence is the maximum of the *crunched
        values* of the sentences that result from replacing each constant for the
        quantified variable.
        """
        sub = sentence.sentence.substitute
        v = sentence.variable
        return self.Value[
            maxceil(
                self.Value.T,
                (
                    crunch(self.Value[self.value_of(sub(c, v), **kw)].num)
                    for c in self.constants
                ),
            )
        ]

    def value_of_universal(self, sentence: Quantified, **kw):
        """
        The value of an universal sentence is the minimum of the *crunched values*
        of the sentences that result from replacing each constant for the quantified
        variable.
        """
        sub = sentence.sentence.substitute
        v = sentence.variable
        return self.Value[
            minfloor(
                self.Value.F,
                (
                    crunch(self.Value[self.value_of(sub(c, v), **kw)].num)
                    for c in self.constants
                ),
            )
        ]

class TableauxSystem(K3.TableauxSystem):
    """
    GO's Tableaux System inherits directly from the :ref:`FDE system <fde-system>`,
    employing designation markers, and building the trunk in the same way.
    """
    # operator => negated => designated
    branchables = {
        Operator.Negation: (None, (0, 0)),
        Operator.Assertion: ((0, 0), (0, 0)),
        Operator.Conjunction: ((0, 0), (0, 1)),
        Operator.Disjunction: ((0, 1), (0, 0)),
        Operator.MaterialConditional: ((0, 1), (0, 0)),
        Operator.MaterialBiconditional: ((0, 1), (0, 1)),
        Operator.Conditional: ((0, 1), (0, 1)),
        Operator.Biconditional: ((0, 0), (0, 1)),
    }

@TableauxSystem.initialize
class TabRules(B3E.TabRules):

    class ConjunctionNegatedDesignated(FDE.OperatorNodeRule):
        """
        From an unticked, designated, negated conjunction node *n* on a branch *b*,
        make two new branches *b'* and *b''* from *b*, add an undesignated node to
        *b'* with one conjunct, and an undesignated node to *b''* with the other
        conjunct, then tick *n*.
        """
        designation = True
        negated     = True
        operator    = Operator.Conjunction
        branching   = 1

        def _get_sd_targets(self, s, d, /):
            yield adds(
                group(sdnode(s.lhs, not d)),
                group(sdnode(s.rhs, not d)))

    class ConjunctionUndesignated(FDE.OperatorNodeRule):
        """
        From an unticked, undesignated conjunction node *n* on a branch *b*, add a
        designated node to *b* with the negation of the conjunction, then tick *n*.
        """
        designation = False
        operator    = Operator.Conjunction

        def _get_sd_targets(self, s, d, /):
            yield adds(
                group(sdnode(~s, not d)))

    class ConjunctionNegatedUndesignated(FDE.OperatorNodeRule):
        """
        From an unticked, undesignated, negated conjunction node *n* on a branch *b*,
        add a designated node to *b* with the (un-negated) conjuction, then tick *n*.
        """
        designation = False
        negated     = True
        operator    = Operator.Conjunction

        def _get_sd_targets(self, s, d, /):
            yield adds(
                group(sdnode(s, not self.designation)))
        
    class DisjunctionNegatedDesignated(FDE.OperatorNodeRule):
        """
        From an unticked, designated, negated disjunction node *n* on a branch *b*,
        add an undesignated node to *b* for each disjunct, then tick *n*.
        """
        designation = True
        negated     = True
        operator    = Operator.Disjunction

        def _get_sd_targets(self, s, d, /):
            yield adds(
                group(sdnode(s.lhs, not d), sdnode(s.rhs, not d)))

    class DisjunctionUndesignated(ConjunctionUndesignated):
        """
        From an unticked, undesignated disjunction node *n* on a branch *b*, add a
        designated node to *b* with the negation of the disjunction, then tick *n*.
        """
        operator = Operator.Disjunction

    class DisjunctionNegatedUndesignated(ConjunctionNegatedUndesignated):
        """
        From an unticked, undesignated, negated disjunction node *n* on a branch *b*,
        add a designated node to *b* with the (un-negated) disjunction, then tick *n*.
        """
        operator = Operator.Disjunction
        
    class MaterialConditionalNegatedDesignated(FDE.OperatorNodeRule):
        """
        From an unticked, designated, negated material conditional node *n* on a branch
        *b*, add an undesignated node with the negation of the antecedent, and an
        undesignated node with the consequent to *b*, then tick *n*.
        """
        negated     = True
        operator    = Operator.MaterialConditional
        designation = True

        def _get_sd_targets(self, s, d, /):
            yield adds(
                group(sdnode(~s.lhs, not d), sdnode(s.rhs, not d)))

    class MaterialConditionalUndesignated(ConjunctionUndesignated):
        """
        From an unticked, undesignated, material conditional node *n* on a branch *b*,
        add a designated node to *b* with the negation of the conditional, then tick *n*.
        """
        operator = Operator.MaterialConditional

    class MaterialConditionalNegatedUndesignated(ConjunctionNegatedUndesignated):
        """
        From an unticked, undesignated, negated material conditional node *n* on a branch
        *b*, add a designated node with the (un-negated) conditional to *b*, then tick *n*.
        """
        operator = Operator.MaterialConditional
        
    class MaterialBiconditionalNegatedDesignated(FDE.OperatorNodeRule):
        """
        From an unticked, designated, negated, material biconditional node *n* on a branch
        *b*, make two branches *b'* and *b''* from *b*. On *b'* add undesignated nodes for
        the negation of the antecent, and for the consequent. On *b''* add undesignated
        nodes for the antecedent, and for the negation of the consequent. Then tick *n*.
        """
        designation = True
        negated     = True
        operator    = Operator.MaterialBiconditional
        branching   = 1

        def _get_sd_targets(self, s, d, /):
            yield adds(
                group(sdnode(~s.lhs, not d), sdnode( s.rhs, not d)),
                group(sdnode( s.lhs, not d), sdnode(~s.rhs, not d)))

    class MaterialBiconditionalUndesignated(ConjunctionUndesignated):
        """
        From an unticked, undesignated, material biconditional node *n* on a branch *b*,
        add a designated node to *b* with the negation of the biconditional, then tick *n*.
        """
        operator = Operator.MaterialBiconditional

    class MaterialBiconditionalNegatedUndesignated(ConjunctionNegatedUndesignated):
        """
        From an unticked, undesignated, negated material biconditional node *n* on a branch
        *b*, add a designated node to *b* with the (un-negated) biconditional, then tick *n*.
        """
        operator = Operator.MaterialBiconditional

    class ConditionalDesignated(FDE.OperatorNodeRule):
        """
        From an unticked, designated, conditional node *n* on a branch *b*, make two branches
        *b'* and *b''* from *b*. On *b'* add a designated node with a disjunction of the
        negated antecedent and the consequent. On *b''* add undesignated nodes for the
        antecedent, consequent, and their negations. Then tick *n*.
        """
        designation = True
        operator    = Operator.Conditional
        branching   = 1

        def _get_sd_targets(self, s, d, /):
            lhs, rhs = s
            yield adds(
                group(
                    sdnode(~lhs | rhs, d)),
                group(
                    sdnode( lhs, not d),
                    sdnode( rhs, not d),
                    sdnode(~lhs, not d),
                    sdnode(~rhs, not d)))

    class ConditionalNegatedDesignated(FDE.OperatorNodeRule):
        """
        From an unticked, designated, negated conditional node *n* on a branch *b*, make
        two branches *b'* and *b''* from *b*. On *b'* add a designated node with the
        antecedent, and an undesignated node with the consequent. On *b''* add an
        undesignated node with the negation of the antencedent, and a designated node
        with the negation of the consequent. Then tick *n*.
        """
        designation = True
        negated     = True
        operator    = Operator.Conditional
        branching   = 1

        def _get_sd_targets(self, s, d, /):
            lhs, rhs = s
            yield adds(
                group(sdnode( lhs,     d), sdnode( rhs, not d)),
                group(sdnode(~lhs, not d), sdnode(~rhs,     d)))

    class ConditionalUndesignated(ConjunctionUndesignated):
        """
        From an unticked, undesignated conditional node *n* on a branch *b*, add a
        designated node to *b* with the negation of the conditional, then tick *n*.
        """
        designation = False
        negated     = None
        operator    = Operator.Conditional

    class ConditionalNegatedUndesignated(ConjunctionNegatedUndesignated):
        """
        From an unticked, undesignated, negated conditional node *n* on a branch *b*,
        add a designated node to *b* with the (un-negated) conditional, then tick *n*.
        """
        designation = False
        negated     = True
        operator    = Operator.Conditional

    class BiconditionalDesignated(FDE.OperatorNodeRule):
        """
        From an unticked, designated biconditional node *n* on a branch *b*, add two
        designated conditional nodes to *b*, one with the operands of the biconditional,
        and the other with the reversed operands. Then tick *n*.
        """
        designation = True
        operator    = Operator.Biconditional

        def _get_sd_targets(self, s, d, /):
            lhs, rhs = s
            Cond = Operator.Conditional
            yield adds(
                group(sdnode(Cond(lhs, rhs), d), sdnode(Cond(rhs, lhs), d)))

    class BiconditionalNegatedDesignated(FDE.OperatorNodeRule):
        """
        From an unticked, designated, negated biconditional node *n* on a branch *b*, make
        two branches *b'* and *b''* from *b*. On *b'* add a designated negated conditional
        node with the operands of the biconditional. On *b''* add a designated negated
        conditional node with the reversed operands of the biconditional. Then tick *n*.
        """
        designation = True
        negated     = True
        operator    = Operator.Biconditional
        branching   = 1

        def _get_sd_targets(self, s, d, /):
            lhs, rhs = s
            Cond = Operator.Conditional
            yield adds(
                group(sdnode(~Cond(lhs, rhs), d)),
                group(sdnode(~Cond(rhs, lhs), d)))

    class BiconditionalUndesignated(ConjunctionUndesignated):
        """
        From an unticked, undesignated biconditional node *n* on a branch *b*, add a
        designated node to *b* with the negation of the biconditional, then tick *n*.
        """
        operator = Operator.Biconditional

    class BiconditionalNegatedUndesignated(ConjunctionNegatedUndesignated):
        """
        From an unticked, undesignated, negated biconditional node *n* on a branch *b*,
        add a designated node to *b* with the (un-negated) biconditional, then tick *n*.
        """
        operator = Operator.Biconditional
        
    class ExistentialNegatedDesignated(FDE.DefaultNodeRule, rules.QuantifiedSentenceRule):
        """
        From an unticked, designated negated existential node *n* on a branch *b*,
        add a designated node *n'* to *b* with a universal sentence consisting of
        disjunction, whose first disjunct is the negated inner sentence of *n*,
        and whose second disjunct is the negation of a disjunction *d*, where the
        first disjunct of *d* is the inner sentence of *n*, and the second disjunct
        of *d* is the negation of the inner sentence of *n*. Then tick *n*.
        """
        designation = True
        negated     = True
        quantifier  = Quantifier.Existential
        convert     = Quantifier.Universal

        def _get_sd_targets(self, s, d, /):
            v, si = s[1:]
            yield adds(
                group(sdnode(self.convert(v, ~si | ~(si | ~si)), d)))

    class ExistentialUndesignated(ConjunctionUndesignated):
        """
        From an unticked, undesignated existential node *n* on a branch *b*, add a
        designated node to *b* with the negation of the existential sentence, then
        tick *n*.
        """
        designation = False
        negated     = None
        operator    = None
        quantifier  = Quantifier.Existential

    class ExistentialNegatedUndesignated(ConjunctionNegatedUndesignated):
        """
        From an unticked, undesignated negated existential node *n* on a branch *b*,
        add a designated node to *b* with the negated existential sentence (negatum),
        then tick *n*.
        """
        designation = False
        negated     = True
        operator    = None
        quantifier  = Quantifier.Existential
        
    class UniversalNegatedDesignated(FDE.QuantifierSkinnyRule):
        """
        From an unticked, designated universal existential node *n* on a branch *b*,
        make two branches *b'* and *b''* from *b*. On *b'*, add a designtated node
        with the standard translation of the sentence on *b*. For *b''*, substitute
        a new constant *c* for the quantified variable, and add two undesignated
        nodes to *b''*, one with the substituted inner sentence, and one with its
        negation, then tick *n*.
        """
        designation = True
        negated     = True
        quantifier  = Quantifier.Universal
        convert     = Quantifier.Existential
        branching   = 1

        def _get_node_targets(self, node: Node, branch: Branch):
            s = self.sentence(node)
            v = s.variable
            si = s.sentence
            r = branch.new_constant() >> s
            d = self.designation
            yield adds(
                group(sdnode(self.convert(v, ~si), d)),
                group(sdnode(r, not d), sdnode(~r, not d)))
            
    class UniversalUndesignated(ExistentialUndesignated):
        """
        From an unticked, undesignated universal node *n* on a branch *b*, add a designated
        node to *b* with the negation of the universal sentence, then tick *n*.
        """
        designation = False
        negated     = None
        quantifier  = Quantifier.Universal

    class UniversalNegatedUndesignated(ExistentialNegatedUndesignated):
        """
        From an unticked, undesignated negated universal node *n* on a branch *b*,
        add a designated node to *b* with the negated universal sentence (negatum),
        then tick *n*.
        """
        designation = False
        negated     = True
        quantifier  = Quantifier.Universal

    rule_groups = (
        (
            # non-branching rules
            FDE.TabRules.AssertionDesignated,
            B3E.TabRules.AssertionUndesignated,
            B3E.TabRules.AssertionNegatedDesignated,
            B3E.TabRules.AssertionNegatedUndesignated,
            FDE.TabRules.ConjunctionDesignated,
            ConjunctionUndesignated,
            ConjunctionNegatedUndesignated,
            DisjunctionNegatedDesignated,
            DisjunctionUndesignated,
            DisjunctionNegatedUndesignated,
            MaterialConditionalNegatedDesignated,
            MaterialConditionalUndesignated,
            MaterialConditionalNegatedUndesignated,
            MaterialBiconditionalUndesignated,
            MaterialBiconditionalNegatedUndesignated,
            ConditionalUndesignated,
            ConditionalNegatedUndesignated,
            BiconditionalUndesignated,
            BiconditionalNegatedUndesignated,
            BiconditionalDesignated,
            FDE.TabRules.ExistentialDesignated,
            ExistentialNegatedDesignated,
            ExistentialUndesignated,
            ExistentialNegatedUndesignated,
            FDE.TabRules.UniversalDesignated,
            UniversalUndesignated,
            UniversalNegatedUndesignated,
            FDE.TabRules.DoubleNegationDesignated,
            FDE.TabRules.DoubleNegationUndesignated,
        ),
        (
            # branching rules
            FDE.TabRules.DisjunctionDesignated,
            ConjunctionNegatedDesignated,
            FDE.TabRules.MaterialConditionalDesignated,
            FDE.TabRules.MaterialBiconditionalDesignated,
            MaterialBiconditionalNegatedDesignated,
            ConditionalDesignated,
            ConditionalNegatedDesignated,
            BiconditionalNegatedDesignated,
            UniversalNegatedDesignated,
        ),
    )
