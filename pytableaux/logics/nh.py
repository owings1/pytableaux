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
#
# ------------------
#
# pytableaux - Paraconsistent Hybrid 3-valued Logic
from __future__ import annotations

import pytableaux.logics.fde as FDE
import pytableaux.logics.lp as LP
import pytableaux.logics.mh as MH
from pytableaux.lang.lex import Quantified, Sentence, Operator
from pytableaux.proof.common import Branch, Node
from pytableaux.proof import adds, group, sdnode

name = 'NH'

class Meta(LP.Meta):
    title       = 'Paraconsistent Hybrid Logic'
    description = (
        'Three-valued logic (True, False, Both) with non-standard conjunction, '
        'and a classical-like conditional'
    )
    category_order = 110
    native_operators = FDE.Meta.native_operators + (Operator.Conditional, Operator.Biconditional)

class Model(LP.Model):

    def is_sentence_opaque(self, s: Sentence):
        return isinstance(s, Quantified) or super().is_sentence_opaque(s)

    def truth_function(self, oper: Operator, a, b = None, /):
        oper = Operator(oper)
        Value = self.Value
        if oper is Operator.Conjunction:
            if Value[a] is Value.B and Value[b] is Value.B:
                return Value.T
        elif oper is Operator.Conditional:
            if Value[a] is not Value.F and Value[b] is Value.F:
                return Value.F
            return Value.T
        return super().truth_function(oper, a, b)

class TableauxSystem(LP.TableauxSystem):
    """
    NH's Tableaux System inherits directly from the {@FDE} system, employing
    designation markers, and building the trunk in the same way.
    """
    # operator => negated => designated
    branchables = {
        Operator.Negation: (None, (0, 0)),
        Operator.Assertion: ((0, 0), (0, 0)),
        Operator.Conjunction: ((1, 0), (1, 3)),
        Operator.Disjunction: ((0, 1), (1, 0)),
        # for now, reduce to negated disjunction
        Operator.MaterialConditional: ((0, 0), (0, 0)),
        # for now, reduce to conjunction
        Operator.MaterialBiconditional: ((0, 0), (0, 0)),
        Operator.Conditional: ((0, 1), (1, 0)),
        # for now, reduce to conjunction
        Operator.Biconditional: ((0, 0), (0, 0)),
    }

@TableauxSystem.initialize
class TabRules(LP.TabRules):

    class ConjunctionNegatedDesignated(FDE.OperatorNodeRule):
        """
        From an unticked, negated, designated conjunction node *n* on a branch *b*,
        make four new branches from *b*: *b'*, *b''*, *b'''*, *b''''*. On *b'*, add
        an undesignated node with the first conjunct. On *b''*, add an undesignated
        node with the second conjunct.

        On *b'''*, add three nodes:

        - A designated node with the first conjunct.
        - A designated node with the negation of the first conjunct.
        - An undesignated node with the negation of the second conjunct.

        On *b''''*, add three nodes:

        - A designated node with the second conjunct.
        - A designated node with the negation of the second conjunct.
        - An undesignated node with the negation of the first conjunct.

        Then, tick *n*.
        """
        negated     = True
        operator    = Operator.Conjunction
        designation = True
        branching   = 3

        def _get_node_targets(self, node: Node, _,/):
            lhs, rhs = self.sentence(node)
            return adds(
                group(sdnode(lhs, False)),
                group(sdnode(rhs, False)),
                group(
                    sdnode(lhs, True), sdnode(~lhs, True), sdnode(~rhs, False)
                ),
                group(
                    sdnode(rhs, True), sdnode(~rhs, True), sdnode(~lhs, False)
                )
            )

    class ConjunctionNegatedUndesignated(FDE.OperatorNodeRule):
        """
        From an unticked, negated, undesignated conjunction node *n* on a branch *b*,
        make two branches *b'* and *b''* from *b*. On *b'*, add two undesignated nodes,
        one for the negation of each conjunct. On *b''*, add four designated nodes, one
        for each of the conjuncts and its negation. Then tick *n*.
        """
        negated     = True
        operator    = Operator.Conjunction
        designation = False
        branching   = 1

        def _get_node_targets(self, node: Node, _,/):
            lhs, rhs = self.sentence(node)
            return adds(
                group(sdnode(~lhs, False), sdnode(~rhs, False)),
                group(
                    sdnode( lhs, True),
                    sdnode(~lhs, True),
                    sdnode( rhs, True),
                    sdnode(~rhs, True),
                )
            )

    class MaterialConditionalDesignated(FDE.OperatorNodeRule):
        """
        This rule reduces to a disjunction.
        """
        operator     = Operator.MaterialConditional
        designation  = True

        def _get_node_targets(self, node: Node, _,/):
            s = self.sentence(node)
            return adds(
                group(sdnode(~s.lhs | s.rhs, self.designation))
            )

    class MaterialConditionalNegatedDesignated(FDE.OperatorNodeRule):
        """
        This rule reduces to a negated disjunction.
        """
        negated      = True
        operator     = Operator.MaterialConditional
        designation  = True

        def _get_node_targets(self, node: Node, _: Branch):
            s = self.sentence(node)
            return adds(
                group(sdnode(~(~s.lhs | s.rhs), self.designation))
            )

    class MaterialConditionalUndesignated(MaterialConditionalDesignated):
        """
        This rule reduces to a disjunction.
        """
        negated     = False
        designation = False

    class MaterialConditionalNegatedUndesignated(MaterialConditionalNegatedDesignated):
        """
        This rule reduces to a negated disjunction.
        """
        negated     = True
        designation = False

    class MaterialBiconditionalDesignated(FDE.ConjunctionReducingRule):
        """
        This rule reduces to a conjunction of material conditionals.
        """
        operator     = Operator.MaterialBiconditional
        designation  = True
        conjunct_op  = Operator.MaterialConditional

    class MaterialBiconditionalNegatedDesignated(FDE.ConjunctionReducingRule):
        """
        This rule reduces to a negated conjunction of material conditionals.
        """
        negated      = True
        operator     = Operator.MaterialBiconditional
        designation  = True
        conjunct_op  = Operator.MaterialConditional

    class MaterialBiconditionalUndesignated(MaterialBiconditionalDesignated):
        """
        This rule reduces to a conjunction of material conditionals.
        """
        designation = False

    class MaterialBiconditionalNegatedUndesignated(MaterialBiconditionalNegatedDesignated):
        """
        This rule reduces to a negated conjunction of material conditionals.
        """
        designation = False

    ConditionalDesignated = MH.TabRules.ConditionalDesignated
    ConditionalNegatedDesignated = MH.TabRules.ConditionalNegatedDesignated
    ConditionalUndesignated = MH.TabRules.ConditionalUndesignated
    ConditionalNegatedUndesignated = MH.TabRules.ConditionalNegatedUndesignated

    class BiconditionalDesignated(FDE.ConjunctionReducingRule):
        """
        This rule reduces to a conjunction of conditionals.
        """
        operator    = Operator.Biconditional
        designation = True
        conjunct_op = Operator.Conditional

    class BiconditionalNegatedDesignated(FDE.ConjunctionReducingRule):
        """
        This rule reduces to a negated conjunction of conditionals.
        """
        negated     = True
        operator    = Operator.Biconditional
        designation = True
        conjunct_op = Operator.Conditional

    class BiconditionalUndesignated(BiconditionalDesignated):
        """
        This rule reduces to a conjunction of conditionals.
        """
        designation = False

    class BiconditionalNegatedUndesignated(BiconditionalNegatedDesignated):
        """
        This rule reduces to a negated conjunction of conditionals.
        """
        designation = False

    ExistentialDesignated = None
    ExistentialNegatedDesignated = None
    ExistentialUndesignated = None
    ExistentialNegatedUndesignated = None
    UniversalDesignated = None
    UniversalNegatedDesignated = None
    UniversalUndesignated = None
    UniversalNegatedUndesignated = None

    rule_groups = (
        # Non-branching rules.
        (
            FDE.TabRules.AssertionDesignated,
            FDE.TabRules.AssertionUndesignated,
            FDE.TabRules.AssertionNegatedDesignated,
            FDE.TabRules.AssertionNegatedUndesignated,
            FDE.TabRules.ConjunctionDesignated,
            FDE.TabRules.DisjunctionUndesignated,
            FDE.TabRules.DisjunctionNegatedDesignated,
            MaterialConditionalDesignated,
            MaterialConditionalNegatedDesignated,
            MaterialConditionalUndesignated,
            MaterialConditionalNegatedUndesignated,
            MaterialBiconditionalDesignated,
            MaterialBiconditionalNegatedDesignated,
            MaterialBiconditionalUndesignated,
            MaterialBiconditionalNegatedUndesignated,
            ConditionalUndesignated,
            ConditionalNegatedDesignated,
            BiconditionalDesignated,
            BiconditionalNegatedDesignated,
            BiconditionalUndesignated,
            BiconditionalNegatedUndesignated,
            FDE.TabRules.DoubleNegationDesignated,
            FDE.TabRules.DoubleNegationUndesignated,
        ),
        # 1-branching rules.
        (
            FDE.TabRules.ConjunctionUndesignated,
            ConjunctionNegatedUndesignated,
            FDE.TabRules.DisjunctionDesignated,
            FDE.TabRules.DisjunctionNegatedUndesignated,
            ConditionalDesignated,
            ConditionalNegatedUndesignated,
        ),
        # 3-branching rules.
        (
            ConjunctionNegatedDesignated,
        ),
    )
