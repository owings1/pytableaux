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

from ..lang import Operator, Quantified
from ..proof import adds, sdnode
from ..tools import group
from . import LogicType
from . import fde as FDE
from . import lp as LP
from . import mh as MH

class Meta(LP.Meta):
    name = 'NH'
    title = 'Paraconsistent Hybrid Logic'
    description = (
        'Three-valued logic (True, False, Both) with non-standard conjunction, '
        'and a classical-like conditional')
    category_order = 110
    tags = ( # remove first-order
        'many-valued',
        'glutty',
        'non-modal')
    native_operators = FDE.Meta.native_operators + (
        Operator.Conditional,
        Operator.Biconditional)

class Model(LP.Model):

    def is_sentence_opaque(self, s,/):
        return type(s) is Quantified or super().is_sentence_opaque(s)

    def truth_function(self, oper, a, b = None, /):
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

class System(LP.System):
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
        Operator.Biconditional: ((0, 0), (0, 0))}

class Rules(LogicType.Rules):

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

        def _get_sd_targets(self, s, d, /):
            lhs, rhs = s
            yield adds(
                group(sdnode(lhs, False)),
                group(sdnode(rhs, False)),
                group(
                    sdnode(lhs, True),
                    sdnode(~lhs, True),
                    sdnode(~rhs, False)),
                group(
                    sdnode(rhs, True),
                    sdnode(~rhs, True),
                    sdnode(~lhs, False)))

    class ConjunctionNegatedUndesignated(FDE.OperatorNodeRule):
        """
        From an unticked, negated, undesignated conjunction node *n* on a branch *b*,
        make two branches *b'* and *b''* from *b*. On *b'*, add two undesignated nodes,
        one for the negation of each conjunct. On *b''*, add four designated nodes, one
        for each of the conjuncts and its negation. Then tick *n*.
        """

        def _get_sd_targets(self, s, d, /):
            lhs, rhs = s
            yield adds(
                group(
                    sdnode(~lhs, False),
                    sdnode(~rhs, False)),
                group(
                    sdnode( lhs, True),
                    sdnode(~lhs, True),
                    sdnode( rhs, True),
                    sdnode(~rhs, True)))

    class MaterialConditionalDesignated(FDE.OperatorNodeRule):
        "This rule reduces to a disjunction."

        def _get_sd_targets(self, s, d, /):
            yield adds(group(sdnode(~s.lhs | s.rhs, d)))

    class MaterialConditionalNegatedDesignated(FDE.OperatorNodeRule):
        "This rule reduces to a negated disjunction."

        def _get_sd_targets(self, s, d, /):
            yield adds(group(sdnode(~(~s.lhs | s.rhs), d)))

    class MaterialConditionalUndesignated(MaterialConditionalDesignated): pass
    class MaterialConditionalNegatedUndesignated(MaterialConditionalNegatedDesignated): pass
    class MaterialBiconditionalDesignated(FDE.MaterialConditionalConjunctsReducingRule): pass
    class MaterialBiconditionalNegatedDesignated(FDE.MaterialConditionalConjunctsReducingRule): pass
    class MaterialBiconditionalUndesignated(MaterialBiconditionalDesignated): pass
    class MaterialBiconditionalNegatedUndesignated(MaterialBiconditionalNegatedDesignated): pass
    class BiconditionalDesignated(FDE.ConditionalConjunctsReducingRule): pass
    class BiconditionalNegatedDesignated(FDE.ConditionalConjunctsReducingRule): pass
    class BiconditionalUndesignated(BiconditionalDesignated): pass
    class BiconditionalNegatedUndesignated(BiconditionalNegatedDesignated): pass

    closure_rules = LP.Rules.closure_rules

    rule_groups = (
        # Non-branching rules.
        (
            FDE.Rules.AssertionDesignated,
            FDE.Rules.AssertionUndesignated,
            FDE.Rules.AssertionNegatedDesignated,
            FDE.Rules.AssertionNegatedUndesignated,
            FDE.Rules.ConjunctionDesignated,
            FDE.Rules.DisjunctionUndesignated,
            FDE.Rules.DisjunctionNegatedDesignated,
            MaterialConditionalDesignated,
            MaterialConditionalNegatedDesignated,
            MaterialConditionalUndesignated,
            MaterialConditionalNegatedUndesignated,
            MaterialBiconditionalDesignated,
            MaterialBiconditionalNegatedDesignated,
            MaterialBiconditionalUndesignated,
            MaterialBiconditionalNegatedUndesignated,
            MH.Rules.ConditionalUndesignated,
            MH.Rules.ConditionalNegatedDesignated,
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
            ConjunctionNegatedUndesignated,
            FDE.Rules.DisjunctionDesignated,
            FDE.Rules.DisjunctionNegatedUndesignated,
            MH.Rules.ConditionalDesignated,
            MH.Rules.ConditionalNegatedUndesignated,
        ),
        # 3-branching rules.
        (
            ConjunctionNegatedDesignated,
        ),
    )
