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

from ..lang import Argument, Atomic, Operator
from ..models import ValueFDE
from ..proof import Branch, Node, adds, rules, sdwgroup, sdwnode
from ..tools import group
from . import LogicType


class Meta(LogicType.Meta):
    name = 'FDE'
    title = 'First Degree Entailment'
    quantified = True
    values: type[ValueFDE] = ValueFDE
    designated_values = 'BT'
    unassigned_value = 'N'
    description = 'Four-valued logic (True, False, Neither, Both)'
    category_order = 1
    native_operators = (
        Operator.Negation,
        Operator.Conjunction,
        Operator.Disjunction,
        Operator.MaterialConditional,
        Operator.MaterialBiconditional)

class Model(LogicType.Model[Meta.values]): pass

class System(LogicType.System):

    @classmethod
    def build_trunk(cls, b: Branch, arg: Argument, /):
        w = 0 if cls.modal else None
        b += (sdwnode(s, True, w) for s in arg.premises)
        b += sdwnode(arg.conclusion, False, w)

class Rules(LogicType.Rules):

    class DesignationClosure(rules.FindClosingNodeRule):
        """
        A branch closes when a sentence appears on a node marked *designated*,
        and the same sentence appears on a node marked *undesignated*.
        """

        def _find_closing_node(self, node: Node, branch: Branch, /):
            s = self.sentence(node)
            if s is not None:
                return branch.find(sdwnode(s, not node['designated'], node.get('world')))

        def example_nodes(self):
            s = Atomic.first()
            w = 0 if self.modal else None
            yield from sdwgroup((s, True, w), (s, False, w))
            
    class DoubleNegationDesignated(rules.OperandsRule): pass
    class DoubleNegationUndesignated(rules.OperandsRule): pass
    class AssertionDesignated(rules.OperandsRule): pass
    class AssertionUndesignated(rules.OperandsRule): pass
    class AssertionNegatedDesignated(rules.NegatingOperandsRule): pass
    class AssertionNegatedUndesignated(rules.NegatingOperandsRule): pass
    class ConjunctionDesignated(rules.OperandsRule): pass
    class ConjunctionUndesignated(rules.BranchingOperandsRule): pass
    class ConjunctionNegatedDesignated(rules.NegatingBranchingOperandsRule): pass
    class ConjunctionNegatedUndesignated(rules.NegatingOperandsRule): pass
    class DisjunctionDesignated(rules.BranchingOperandsRule): pass
    class DisjunctionNegatedDesignated(rules.NegatingOperandsRule): pass
    class DisjunctionUndesignated(rules.OperandsRule): pass
    class DisjunctionNegatedUndesignated(rules.NegatingBranchingOperandsRule): pass

    class MaterialConditionalDesignated(rules.OperatorNodeRule):
        """
        From an unticked designated material conditional node *n* on a branch *b*, make
        two new branches *b'* and *b''* from *b*, add a designated node with the negation
        of the antecedent to *b'*, add a designated node with the consequent to *b''*,
        then tick *n*.
        """

        def _get_sdw_targets(self, s, d, w, /):
            yield adds(
                sdwgroup((~s.lhs, d, w)),
                sdwgroup(( s.rhs, d, w)))

    class MaterialConditionalNegatedDesignated(rules.OperatorNodeRule):
        """
        From an unticked designated negated material conditional node *n* on a
        branch *b*, add a designated node with the antecedent, and a designated
        node with the negation of the consequent to *b*, then tick *n*.
        """

        def _get_sdw_targets(self, s, d, w, /):
            yield adds(sdwgroup((s.lhs, d, w), (~s.rhs, d, w)))

    class MaterialConditionalUndesignated(rules.OperatorNodeRule):
        """
        From an unticked undesignated material conditional node *n* on a branch *b*, add
        an undesignated node with the negation of the antecedent and an undesignated node
        with the consequent to *b*, then tick *n*.
        """

        def _get_sdw_targets(self, s, d, w, /):
            yield adds(sdwgroup((~s.lhs, d, w), (s.rhs, d, w)))

    class MaterialConditionalNegatedUndesignated(rules.OperatorNodeRule):
        """
        From an unticked undesignated negated material conditional node *n* on a branch *b*, make
        two new branches *b'* and *b''* from *b*, add an undesignated node with the antecedent to
        *b'*, and add an undesignated node with the negation of the consequent to *b''*, then
        tick *n*.
        """

        def _get_sdw_targets(self, s, d, w, /):
            yield adds(
                sdwgroup(( s.lhs, d, w)),
                sdwgroup((~s.rhs, d, w)))

    class MaterialBiconditionalDesignated(rules.OperatorNodeRule):
        """
        From an unticked designated material biconditional node *n* on a branch *b*, make
        two new branches *b'* and *b''* from *b*, add a designated node with the negation
        of the antecedent and a designated node with the negation of the consequent to *b'*,
        and add a designated node with the antecedent and a designated node with the
        consequent to *b''*, then tick *n*.
        """

        def _get_sdw_targets(self, s, d, w, /):
            yield adds(
                sdwgroup((~s.lhs, d, w), (~s.rhs, d, w)),
                sdwgroup(( s.rhs, d, w), ( s.lhs, d, w)))

    class MaterialBiconditionalNegatedDesignated(rules.OperatorNodeRule):
        """
        From an unticked designated negated material biconditional node *n* on a branch *b*, make
        two branches *b'* and *b''* from *b*, add a designated node with the antecedent and a
        designated node with the negation of the consequent to *b'*, and add a designated node
        with the negation of the antecedent and a designated node with the consequent to *b''*,
        then tick *n*.
        """

        def _get_sdw_targets(self, s, d, w, /):
            yield adds(
                sdwgroup(( s.lhs, d, w), (~s.rhs, d, w)),
                sdwgroup((~s.lhs, d, w), ( s.rhs, d, w)))

    class MaterialBiconditionalUndesignated(MaterialBiconditionalNegatedDesignated): pass
    class MaterialBiconditionalNegatedUndesignated(MaterialBiconditionalDesignated): pass
    class ConditionalDesignated(MaterialConditionalDesignated): pass
    class ConditionalNegatedDesignated(MaterialConditionalNegatedDesignated): pass
    class ConditionalUndesignated(MaterialConditionalUndesignated): pass
    class ConditionalNegatedUndesignated(MaterialConditionalNegatedUndesignated): pass
    class BiconditionalDesignated(MaterialBiconditionalDesignated): pass
    class BiconditionalNegatedDesignated(MaterialBiconditionalNegatedDesignated): pass
    class BiconditionalUndesignated(MaterialBiconditionalUndesignated): pass
    class BiconditionalNegatedUndesignated(MaterialBiconditionalNegatedUndesignated): pass

    class ExistentialDesignated(rules.QuantifierSkinnyRule):
        """
        From an unticked designated existential node *n* on a branch *b* quantifying over
        variable *v* into sentence *s*, add a designated node to *b* with the substitution
        into *s* of a new constant not yet appearing on *b* for *v*, then tick *n*.
        """

        def _get_node_targets(self, node, branch, /):
            s = branch.new_constant() >> self.sentence(node)
            if self.negated:
                s = ~s
            yield adds(
                sdwgroup((s, self.designation, node.get('world'))))

    class UniversalDesignated(rules.QuantifierFatRule):
        """
        From an undesignated existential node *n* on a branch *b*, for any constant *c* on
        *b* such that the result *r* of substituting *c* for the variable bound by the
        sentence of *n* does not appear on *b*, then add an undesignated node with *r* to *b*.
        If there are no constants yet on *b*, then instantiate with a new constant. The node
        *n* is never ticked.
        """

        def _get_constant_nodes(self, node, c, branch, /):
            s = c >> self.sentence(node)
            if self.negated:
                s = ~s
            yield sdwnode(s, self.designation, node.get('world'))

    class ExistentialNegatedDesignated(UniversalDesignated): pass
    class ExistentialNegatedUndesignated(ExistentialDesignated): pass
    class ExistentialUndesignated(UniversalDesignated): pass
    class UniversalNegatedDesignated(ExistentialDesignated): pass
    class UniversalUndesignated(ExistentialDesignated): pass
    class UniversalNegatedUndesignated(UniversalDesignated): pass

    unquantifying_groups = (
        group(
            UniversalDesignated,
            UniversalNegatedUndesignated,
            ExistentialNegatedDesignated,
            ExistentialUndesignated),
        group(
            ExistentialDesignated,
            ExistentialNegatedUndesignated,
            UniversalNegatedDesignated,
            UniversalUndesignated))

    closure = group(DesignationClosure)

    groups = (
        group(
            # non-branching rules
            AssertionDesignated,
            AssertionUndesignated,
            AssertionNegatedDesignated,
            AssertionNegatedUndesignated,
            ConjunctionDesignated, 
            ConjunctionNegatedUndesignated,
            DisjunctionNegatedDesignated,
            DisjunctionUndesignated,
            MaterialConditionalNegatedDesignated,
            MaterialConditionalUndesignated,
            ConditionalUndesignated, 
            ConditionalNegatedDesignated,
            DoubleNegationDesignated,
            DoubleNegationUndesignated),
        group(
            # branching rules
            ConjunctionNegatedDesignated,
            ConjunctionUndesignated,
            DisjunctionDesignated,
            DisjunctionNegatedUndesignated,
            MaterialConditionalDesignated,
            MaterialConditionalNegatedUndesignated,
            MaterialBiconditionalDesignated,
            MaterialBiconditionalNegatedDesignated,
            MaterialBiconditionalUndesignated,
            MaterialBiconditionalNegatedUndesignated,
            ConditionalDesignated,
            ConditionalNegatedUndesignated,
            BiconditionalDesignated,
            BiconditionalNegatedDesignated,
            BiconditionalUndesignated,
            BiconditionalNegatedUndesignated),
        *unquantifying_groups)

    @staticmethod
    def _check_groups():
        cls = __class__
        for branching, group in zip(range(2), cls.groups):
            for rulecls in group:
                assert rulecls.branching == branching, f'{rulecls}'
