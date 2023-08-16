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
from ..proof import adds, sdnode
from ..tools import group
from . import LogicType
from . import fde as FDE
from . import k3 as K3

class Meta(K3.Meta):
    name = 'MH'
    title = 'Paracomplete Hybrid Logic'
    description = (
        'Three-valued logic (True, False, Neither) with non-standard disjunction, '
        'and a classical-like conditional')
    category_order = 70
    tags = ( # remove first-order
        'many-valued',
        'gappy',
        'non-modal')
    native_operators = K3.Meta.native_operators + (
        Operator.Conditional,
        Operator.Biconditional)

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

class System(K3.System):

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
        Operator.Biconditional: ((0, 0), (0, 0))}

class Rules(LogicType.Rules):

    class DisjunctionNegatedDesignated(FDE.OperatorNodeRule):
        """
        From an unticked, negated, designated disjunction node *n* on a branch *b*,
        make two branches *b'* and *b''* from *b*. On *b'* add four undesignated
        nodes, one for each disjunct and its negation. On *b''* add two designated
        nodes, one for the negation of each disjunct. Then tick *n*.
        """

        def _get_sd_targets(self, s, d, /):
            lhs, rhs = s
            yield adds(
                group(
                    sdnode( lhs, not d),
                    sdnode(~lhs, not d),
                    sdnode( rhs, not d),
                    sdnode(~rhs, not d)),
                group(
                    sdnode(~lhs, d),
                    sdnode(~rhs, d)))

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

        def _get_sd_targets(self, s, d, /):
            lhs, rhs = s
            yield adds(
                group(
                    sdnode(lhs, not d)),
                group(
                    sdnode(rhs, not d)),
                group(
                    sdnode(lhs, d), sdnode(~lhs, d), sdnode(~rhs, not d)),
                group(
                    sdnode(rhs, d), sdnode(~rhs, d), sdnode(~lhs, not d)))

    class MaterialConditionalDesignated(FDE.OperatorNodeRule):
        "This rule reduces to a disjunction."

        def _get_sd_targets(self, s, d, /):
            yield adds(group(sdnode(~s.lhs | s.rhs, d)))

    class MaterialConditionalNegatedDesignated(FDE.OperatorNodeRule):
        "This rule reduces to a negated disjunction."

        def _get_sd_targets(self, s, d, /):
            yield adds(group(sdnode(~(~s.lhs | s.rhs), d)))

    class MaterialConditionalUndesignated(MaterialConditionalDesignated):
        "This rule reduces to a disjunction."

    class MaterialConditionalNegatedUndesignated(MaterialConditionalNegatedDesignated):
        "This rule reduces to a negated disjunction."

    class MaterialBiconditionalDesignated(FDE.ConjunctionReducingRule):
        "This rule reduces to a conjunction of material conditionals."
        conjoined = Operator.MaterialConditional

    class MaterialBiconditionalNegatedDesignated(MaterialBiconditionalDesignated):
        "This rule reduces to a negated conjunction of material conditionals."

    class MaterialBiconditionalUndesignated(MaterialBiconditionalDesignated):
        "This rule reduces to a conjunction of material conditionals."

    class MaterialBiconditionalNegatedUndesignated(MaterialBiconditionalNegatedDesignated):
        "This rule reduces to a negated conjunction of material conditionals."

    class ConditionalDesignated(FDE.OperatorNodeRule):
        """
        From an unticked, designated conditional node *n* on a branch *b*, make
        two branches *b'* and *b''* from *b*. On *b'* add an undesignated node
        with the antecedent, and on *b''* add a designated node with the consequent.
        Then tick *n*.
        """

        def _get_sd_targets(self, s, d, /):
            # Keep designation fixed for inheritance below.
            yield adds(
                group(sdnode(s.lhs, False)),
                group(sdnode(s.rhs, True)))

    class ConditionalNegatedDesignated(FDE.OperatorNodeRule):
        """
        From an unticked, negated, desigated conditional node *n* on a branch *b*,
        add two nodes to *b*:

        - A designated node with the antecedent.
        - An undesignated node with the consequent.

        Then tick *n*.
        """

        def _get_sd_targets(self, s, d, /):
            # Keep designation fixed for inheritance below.
            yield adds(group(sdnode(s.lhs, True), sdnode(s.rhs, False)))

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

    class ConditionalNegatedUndesignated(ConditionalDesignated):
        """
        From an unticked, negated, undesignated conditional node *n* on a branch *b*,
        make two branches *b'* and *b''* from *b*. On *b'* add an undesignated node
        with the antecedent, and on *b''* add a designated node with the consequent.
        Then tick *n*.

        Note that the result is the same as for the above *ConditionalDesignated* rule.
        """

    class BiconditionalDesignated(FDE.ConjunctionReducingRule):
        "This rule reduces to a conjunction of conditionals."
        conjoined = Operator.Conditional

    class BiconditionalNegatedDesignated(BiconditionalDesignated):
        "This rule reduces to a negated conjunction of conditionals."

    class BiconditionalUndesignated(BiconditionalDesignated):
        "This rule reduces to a conjunction of conditionals."

    class BiconditionalNegatedUndesignated(BiconditionalNegatedDesignated):
        "This rule reduces to a negated conjunction of conditionals."

    closure = K3.Rules.closure

    groups = (
        # Non-branching rules.
        (
            FDE.Rules.AssertionDesignated,
            FDE.Rules.AssertionUndesignated,
            FDE.Rules.AssertionNegatedDesignated,
            FDE.Rules.AssertionNegatedUndesignated,
            FDE.Rules.ConjunctionDesignated,
            FDE.Rules.ConjunctionNegatedUndesignated,
            FDE.Rules.DisjunctionUndesignated,
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
            FDE.Rules.DoubleNegationDesignated,
            FDE.Rules.DoubleNegationUndesignated,
        ),
        # 1-branching rules.
        (
            FDE.Rules.ConjunctionUndesignated,
            FDE.Rules.ConjunctionNegatedDesignated,
            FDE.Rules.DisjunctionDesignated,
            DisjunctionNegatedDesignated,
            ConditionalDesignated,
            ConditionalNegatedUndesignated,
        ),
        # 3-branching rules.
        (
            DisjunctionNegatedUndesignated,
        ),
    )
