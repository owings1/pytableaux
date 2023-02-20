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

from ..lang import Operator, Quantified, Sentence
from ..proof import Node, adds, group, sdnode
from . import fde as FDE
from . import k3 as K3

name = 'MH'

class Meta(K3.Meta):
    title       = 'Paracomplete Hybrid Logic'
    description = (
        'Three-valued logic (True, False, Neither) with non-standard disjunction, '
        'and a classical-like conditional'
    )
    category_order = 70
    tags = ( # remove first-order
        'many-valued',
        'gappy',
        'non-modal',
    )
    native_operators = K3.Meta.native_operators + (Operator.Conditional, Operator.Biconditional)

class Model(K3.Model):

    def is_sentence_opaque(self, s: Sentence, /):
        return type(s) is Quantified or super().is_sentence_opaque(s)

    def truth_function(self, oper: Operator, a, b = None, /):
        oper = Operator(oper)
        Value = self.Value
        if oper is Operator.Disjunction:
            if Value[a] is Value.N and Value[b] is Value.N:
                return Value.F
        elif oper is Operator.Conditional:
            if Value[a] is Value.T and Value[b] is not Value.T:
                return Value.F
            return Value.T
        return super().truth_function(oper, a, b)

class TableauxSystem(K3.TableauxSystem):

    # operator => negated => designated
    branchables = {
        Operator.Negation: (None, (0, 0)),
        Operator.Assertion: ((0, 0), (0, 0)),
        Operator.Conjunction: ((1, 0), (0, 1)),
        Operator.Disjunction: ((0, 1), (3, 1)),
        # for now, reduce to negated disjunction
        Operator.MaterialConditional: ((0, 0), (0, 0)),
        # for now, reduce to conjunction
        Operator.MaterialBiconditional: ((0, 0), (0, 0)),
        Operator.Conditional: ((0, 1), (1, 0)),
        # for now, reduce to conjunction
        Operator.Biconditional: ((0, 0), (0, 0)),
    }

@TableauxSystem.initialize
class TabRules(K3.TabRules):

    class DisjunctionNegatedDesignated(FDE.OperatorNodeRule):
        """
        From an unticked, negated, designated disjunction node *n* on a branch *b*,
        make two branches *b'* and *b''* from *b*. On *b'* add four undesignated
        nodes, one for each disjunct and its negation. On *b''* add two designated
        nodes, one for the negation of each disjunct. Then tick *n*.
        """
        designation = True
        negated     = True
        operator    = Operator.Disjunction
        branching   = 1

        def _get_node_targets(self, node: Node, _, /):
            s = self.sentence(node)
            lhs, rhs = s
            d = self.designation
            return adds(
                group(
                    sdnode( lhs, not d),
                    sdnode(~lhs, not d),
                    sdnode( rhs, not d),
                    sdnode(~rhs, not d),
                ),
                group(
                    sdnode(~lhs, d),
                    sdnode(~rhs, d),
                )
            )

    class DisjunctionNegatedUndesignated(FDE.OperatorNodeRule):
        """
        From an unticked, negated, undesignated disjunction node *n* on a branch
        *b*, make four branches from *b*: *b'*, *b''*, *b'''*, and *b''''*. On *b'*,
        add a designated node with the first disjunct, and on *b''*, add a designated
        node with the second disjunct.

        On *b'''* add three nodes:

        - An undesignated node with the first disjunct.
        - An undesignated node with the negation of the first disjunct.
        - A designated node with the negation of the second disjunct.

        On *b''''* add three nodes:

        - An undesignated node with the second disjunct.
        - An undesignated node with the negation of the second disjunct.
        - A designated node with the negation of the first disjunct.

        Then tick *n*.
        """
        designation = False
        negated     = True
        operator    = Operator.Disjunction
        branching   = 3

        def _get_node_targets(self, node: Node, _):
            lhs, rhs = self.sentence(node)
            d = self.designation
            return adds(
                group(
                    sdnode(lhs, not d)
                ),
                group(
                    sdnode(rhs, not d)
                ),
                group(
                    sdnode(lhs, d), sdnode(~lhs, d), sdnode(~rhs, not d)
                ),
                group(
                    sdnode(rhs, d), sdnode(~rhs, d), sdnode(~lhs, not d)
                ),
            )

    class MaterialConditionalDesignated(FDE.OperatorNodeRule):
        """
        This rule reduces to a disjunction.
        """
        designation  = True
        operator     = Operator.MaterialConditional

        def _get_node_targets(self, node: Node, _):
            lhs, rhs = self.sentence(node)
            return adds(
                group(sdnode(~lhs | rhs, self.designation))
            )

    class MaterialConditionalNegatedDesignated(FDE.OperatorNodeRule):
        """
        This rule reduces to a negated disjunction.
        """
        designation  = True
        negated      = True
        operator     = Operator.MaterialConditional

        def _get_node_targets(self, node: Node, _):
            s = self.sentence(node)
            return adds(
                group(sdnode(~(~s.lhs | s.rhs), self.designation))
            )

    class MaterialConditionalUndesignated(MaterialConditionalDesignated):
        """
        This rule reduces to a disjunction.
        """
        designation = False
        negated     = False

    class MaterialConditionalNegatedUndesignated(MaterialConditionalNegatedDesignated):
        """
        This rule reduces to a negated disjunction.
        """
        designation = False
        negated     = True

    class MaterialBiconditionalDesignated(FDE.ConjunctionReducingRule):
        """
        This rule reduces to a conjunction of material conditionals.
        """
        designation  = True
        operator     = Operator.MaterialBiconditional
        conjunct_op  = Operator.MaterialConditional

    class MaterialBiconditionalNegatedDesignated(MaterialBiconditionalDesignated):
        """
        This rule reduces to a negated conjunction of material conditionals.
        """
        negated = True

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

    class ConditionalDesignated(FDE.OperatorNodeRule):
        """
        From an unticked, designated conditional node *n* on a branch *b*, make
        two branches *b'* and *b''* from *b*. On *b'* add an undesignated node
        with the antecedent, and on *b''* add a designated node with the consequent.
        Then tick *n*.
        """
        designation = True
        operator    = Operator.Conditional
        branching   = 1

        def _get_node_targets(self, node: Node, _):
            s = self.sentence(node)
            # Keep designation fixed for inheritance below.
            return adds(
                group(sdnode(s.lhs, False)),
                group(sdnode(s.rhs, True)),
            )

    class ConditionalNegatedDesignated(FDE.OperatorNodeRule):
        """
        From an unticked, negated, desigated conditional node *n* on a branch *b*,
        add two nodes to *b*:

        - A designated node with the antecedent.
        - An undesignated node with the consequent.

        Then tick *n*.
        """
        designation  = True
        negated      = True
        operator     = Operator.Conditional

        def _get_node_targets(self, node: Node, _):
            s = self.sentence(node)
            # Keep designation fixed for inheritance below.
            return adds(
                group(sdnode(s.lhs, True), sdnode(s.rhs, False))
            )

    class ConditionalUndesignated(ConditionalNegatedDesignated):
        """
        From an unticked, undesignated conditional node *n* on a branch *b*, add
        two nodes to *b*:

        - A designated node with the antecedent.
        - An undesignated node with the consequent.

        Then tick *n*.

        Note that the nodes added are the same as for the above
        *ConditionalNegatedDesignated* rule.
        """
        designation = False
        negated     = False

    class ConditionalNegatedUndesignated(ConditionalDesignated):
        """
        From an unticked, negated, undesignated conditional node *n* on a branch *b*,
        make two branches *b'* and *b''* from *b*. On *b'* add an undesignated node
        with the antecedent, and on *b''* add a designated node with the consequent.
        Then tick *n*.

        Note that the result is the same as for the above *ConditionalDesignated* rule.
        """
        designation = False
        negated     = True

    class BiconditionalDesignated(FDE.ConjunctionReducingRule):
        """
        This rule reduces to a conjunction of conditionals.
        """
        designation = True
        operator    = Operator.Biconditional
        conjunct_op = Operator.Conditional

    class BiconditionalNegatedDesignated(BiconditionalDesignated):
        """
        This rule reduces to a negated conjunction of conditionals.
        """
        negated = True

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
            FDE.TabRules.ConjunctionNegatedUndesignated,
            FDE.TabRules.DisjunctionUndesignated,
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
            FDE.TabRules.ConjunctionNegatedDesignated,
            FDE.TabRules.DisjunctionDesignated,
            DisjunctionNegatedDesignated,
            ConditionalDesignated,
            ConditionalNegatedUndesignated,
        ),
        # 3-branching rules.
        (
            DisjunctionNegatedUndesignated,
        ),
    )
