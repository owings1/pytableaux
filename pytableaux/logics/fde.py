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

from abc import abstractmethod
from itertools import chain, starmap

from ..lang import (Argument, Atomic, Operated, Operator, Quantified,
                    Quantifier, Sentence)
from ..models import ValueFDE
from ..proof import (Branch, Node, RulesRoot, SentenceNode, WorldNode, adds,
                     filters, rules, sdwgroup, sdwnode)
from ..tools import group, maxceil, minfloor, wraps, abcs
from . import LogicType


class Meta(LogicType.Meta):
    name = 'FDE'
    title = 'First Degree Entailment'
    modal = False
    quantified = True
    values = ValueFDE
    designated_values = frozenset({values.B, values.T})
    unassigned_value = values.N
    description = 'Four-valued logic (True, False, Neither, Both)'
    category_order = 1
    native_operators = (
        Operator.Negation,
        Operator.Conjunction,
        Operator.Disjunction,
        Operator.MaterialConditional,
        Operator.MaterialBiconditional)

class Model(LogicType.Model[ValueFDE]):
    'An FDE Model.'

    class TruthFunction(LogicType.Model.TruthFunction[ValueFDE]):

        def Assertion(self, a, /):
            return self.values[a]

        def Negation(self, a, /):
            if a == self.values.F:
                return self.values.T
            if a == self.values.T:
                return self.values.F
            return self.values[a]

        Conjunction = staticmethod(min)

        Disjunction = staticmethod(max)

        def MaterialConditional(self, a, b, /):
            return self.Disjunction(self.Negation(a), b)

        def MaterialBiconditional(self, a, b, /):
            return self.Conjunction(*starmap(self.MaterialConditional, ((a, b), (b, a))))

        Conditional = MaterialConditional

        def Biconditional(self, a, b, /):
            return self.Conjunction(*starmap(self.Conditional, ((a, b), (b, a))))

    def value_of_quantified(self, s: Quantified, /, **kw):
        """
        The value of a quantified sentence is determined from the values of
        sentences that result from replacing each constant for the quantified
        variable. For an existential quantifier, this is the max value, and
        for a universial quantifier, it is the min value.
        """
        self._check_finished()
        it = self._unquantify_values(s, **kw)
        if s.quantifier is Quantifier.Existential:
            return maxceil(self.maxval, it, self.minval)
        if s.quantifier is Quantifier.Universal:
            return minfloor(self.minval, it, self.maxval)
        raise NotImplementedError from ValueError(s.quantifier)

    def _read_node(self, node, branch, /):
        super()._read_node(node, branch)
        if not isinstance(node, SentenceNode):
            return
        s = node['sentence']
        is_literal = self.is_sentence_literal(s)
        is_opaque = self.is_sentence_opaque(s)
        if not is_literal and not is_opaque:
            return
        d = node['designated']
        s_negative = -s
        has_negative = branch.has(sdwnode(s_negative, d, node.get('world')))
        is_negated = type(s) is Operated and s.operator is Operator.Negation
        if is_negated:
            # If the sentence is negated, set the value of the negatum
            s = s_negative
            if d:
                if has_negative:
                    # If the node is designated, and the negatum is
                    # also designated on b, the value is B
                    value = 'B'
                else:
                    # If the node is designated, but the negatum is
                    # not also designated on b, the value is F
                    value = 'F'
            else:
                if has_negative:
                    # If the node is undesignated, and the negatum is
                    # also undesignated on b, the value is N
                    value = 'N'
                else:
                    # If the node is undesignated, but the negatum is
                    # not also undesignated on b, the value is T
                    value = 'T'
        else:
            # If the sentence is unnegated, set the value of the sentence
            if d:
                if has_negative:
                    # If the node is designated, and its negation is
                    # also designated on b, the value is B
                    value = 'B'
                else:
                    # If the node is designated, but the negation is
                    # not also designated on b, the value is T
                    value = 'T'
            else:
                if has_negative:
                    # If the node is undesignated, and its negation is
                    # also undesignated on b, the value is N
                    value = 'N'
                else:
                    # If the node is undesginated, but the negation is
                    # not also undesignated on b, the value is F
                    value = 'F'
        value = self.values[value]
        if isinstance(node, WorldNode):
            w = node['world']
        else:
            w = 0
        if is_opaque:
            self.set_opaque_value(s, value, world=w)
        else:
            self.set_literal_value(s, value, world=w)

class System(LogicType.System):

    @classmethod
    def build_trunk(cls, b: Branch, arg: Argument, /):
        w = 0 if cls.modal else None
        b += (sdwnode(s, True, w) for s in arg.premises)
        b += sdwnode(arg.conclusion, False, w)

    @classmethod
    def branching_complexity(cls, node: Node, rules: RulesRoot, /):
        try:
            s = node['sentence']
        except KeyError:
            return 0
        negated = False
        result = 0
        for oper in s.operators:
            if not negated and oper is Operator.Negation:
                negated = True
                continue
            if negated and oper is Operator.Negation:
                name = 'DoubleNegation'
            else:
                name = oper.name
                if negated:
                    name += 'Negated'
            if node['designated']:
                name += 'Designated'
            else:
                name += 'Undesignated'
            rulecls = rules.get(name, None)
            if rulecls:
                result += rulecls.branching
                negated = False
        return result

    @classmethod
    def branching_complexity_hashable(cls, node: Node, /):
        try:
            return node['sentence'].operators, node['designated']
        except KeyError:
            pass

    class DefaultNodeRule(rules.GetNodeTargetsRule, intermediate=True):
        """Default FDE node rule with:
        
        - BaseSimpleRule:
            - `_apply()` delegates to AdzHelper's `_apply()`. ticking is default True
            - `score_candidate()` delegates to AdzHelper's `closure_score()`
        - BaseNodeRule:
            - loads FilterHelper. ignore_ticked is default True
            - `example_nodes()` delegates to FilterHelper.
        - GetNodeTargetsRule:
            - `_get_targets()` wrapped by FilterHelper, then delegates to
            abstract `_get_node_targets()`.
        - DefaultNodeRule (this rule):
            - uses autoattrs to set attrs from the rule name.
            - implements `_get_node_targets()` with optional `_get_sd_targers()`.
                NB it is not marked as abstract but will throw NotImplementError.
            - adds a NodeDesignation filter.
        """
        NodeFilters = group(filters.NodeDesignation, filters.NodeType)
        autoattrs = True

        def _get_node_targets(self, node: Node, branch: Branch, /):
            return self._get_sdw_targets(self.sentence(node), node['designated'], node.get('world'))

        def _get_sdw_targets(self, s: Operated, d: bool, w: int|None, /):
            return self._get_sd_targets(s, d)

        def _get_sd_targets(self, s: Operated, d: bool, /):
            raise NotImplementedError

    class QuantifierNodeRule(DefaultNodeRule, rules.QuantifiedSentenceRule, intermediate=True): pass
    class QuantifierSkinnyRule(rules.NarrowQuantifierRule, QuantifierNodeRule, intermediate=True): pass
    class QuantifierFatRule(rules.ExtendedQuantifierRule, QuantifierNodeRule, intermediate=True): pass

    class OperatorNodeRule(DefaultNodeRule, rules.OperatedSentenceRule, intermediate=True):

        def __init_subclass__(cls) -> None:
            super().__init_subclass__()
            pass
            if abcs.isabstract(cls):
                return
            if all(
                getattr(cls, name) is getattr(__class__, name)
                for name in (
                    '_get_targets',
                    '_get_node_targets',
                    '_get_sdw_targets',
                    '_get_sd_targets')):
                    @abstractmethod
                    @wraps(cls._get_sd_targets)
                    def wrapped(self, s: Sentence, d: bool, /):
                        raise NotImplementedError
                    setattr(cls, '_get_sd_targets', wrapped)

    class FlippingRule(OperatorNodeRule, intermediate=True):

        def _get_sdw_targets(self, s, d, w, /):
            yield adds(sdwgroup((s, not d, w)))

    class NegatingFlippingRule(OperatorNodeRule, intermediate=True):

        def _get_sdw_targets(self, s, d, w, /):
            yield adds(sdwgroup((~s, not d, w)))

    class OperandsRule(OperatorNodeRule, intermediate=True):

        def _get_sdw_targets(self, s, d, w, /):
            yield adds(sdwgroup(*((s, d, w) for s in s)))

    class FlippingOperandsRule(OperatorNodeRule, intermediate=True):

        def _get_sdw_targets(self, s, d, w, /):
            yield adds(sdwgroup(*((s, not d, w) for s in s)))

    class NegatingOperandsRule(OperatorNodeRule, intermediate=True):

        def _get_sdw_targets(self, s, d, w, /):
            yield adds(sdwgroup(*((~s, d, w) for s in s)))

    class BranchingOperandsRule(OperatorNodeRule, intermediate=True):

        def _get_sdw_targets(self, s, d, w, /):
            yield adds(*(map(sdwgroup, ((s, d, w) for s in s))))

    class NegatingBranchingOperandsRule(OperatorNodeRule, intermediate=True):

        def _get_sdw_targets(self, s, d, w, /):
            yield adds(*(map(sdwgroup, ((~s, d, w) for s in s))))

    class ConjunctionReducingRule(OperatorNodeRule, intermediate=True):

        conjoined: Operator

        def _get_sdw_targets(self, s, d, w, /):
            oper = self.conjoined
            lhs, rhs = s
            s = oper(lhs, rhs) & oper(rhs, lhs)
            if self.negated:
                s = ~s
            yield adds(sdwgroup((s, d, w)))

    class MaterialConditionalConjunctsReducingRule(ConjunctionReducingRule, intermediate=True):
        conjoined = Operator.MaterialConditional

    class ConditionalConjunctsReducingRule(ConjunctionReducingRule, intermediate=True):
        conjoined = Operator.Conditional

    class MaterialConditionalReducingRule(OperatorNodeRule, intermediate=True):
        "This rule reduces to a disjunction."

        def _get_sdw_targets(self, s, d, w, /):
            sn = ~s.lhs | s.rhs
            if self.negated:
                sn = ~sn
            yield adds(sdwgroup((sn, d, w)))


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
            
    class DoubleNegationDesignated(System.OperandsRule): pass
    class DoubleNegationUndesignated(System.OperandsRule): pass
    class AssertionDesignated(System.OperandsRule): pass
    class AssertionUndesignated(System.OperandsRule): pass
    class AssertionNegatedDesignated(System.NegatingOperandsRule): pass
    class AssertionNegatedUndesignated(System.NegatingOperandsRule): pass
    class ConjunctionDesignated(System.OperandsRule): pass
    class ConjunctionUndesignated(System.BranchingOperandsRule): pass
    class ConjunctionNegatedDesignated(System.NegatingBranchingOperandsRule): pass
    class ConjunctionNegatedUndesignated(System.NegatingOperandsRule): pass
    class DisjunctionDesignated(System.BranchingOperandsRule): pass
    class DisjunctionNegatedDesignated(System.NegatingOperandsRule): pass
    class DisjunctionUndesignated(System.OperandsRule): pass
    class DisjunctionNegatedUndesignated(System.NegatingBranchingOperandsRule): pass

    class MaterialConditionalDesignated(System.OperatorNodeRule):
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

    class MaterialConditionalNegatedDesignated(System.OperatorNodeRule):
        """
        From an unticked designated negated material conditional node *n* on a
        branch *b*, add a designated node with the antecedent, and a designated
        node with the negation of the consequent to *b*, then tick *n*.
        """

        def _get_sdw_targets(self, s, d, w, /):
            yield adds(sdwgroup((s.lhs, d, w), (~s.rhs, d, w)))

    class MaterialConditionalUndesignated(System.OperatorNodeRule):
        """
        From an unticked undesignated material conditional node *n* on a branch *b*, add
        an undesignated node with the negation of the antecedent and an undesignated node
        with the consequent to *b*, then tick *n*.
        """

        def _get_sdw_targets(self, s, d, w, /):
            yield adds(sdwgroup((~s.lhs, d, w), (s.rhs, d, w)))

    class MaterialConditionalNegatedUndesignated(System.OperatorNodeRule):
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

    class MaterialBiconditionalDesignated(System.OperatorNodeRule):
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

    class MaterialBiconditionalNegatedDesignated(System.OperatorNodeRule):
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

    class ExistentialDesignated(System.QuantifierSkinnyRule):
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

    class UniversalDesignated(System.QuantifierFatRule):
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
    unquantifying_rules = tuple(chain(*unquantifying_groups))

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

    @classmethod
    def _check_groups(cls):
        for branching, group in zip(range(2), cls.groups):
            for rulecls in group:
                assert rulecls.branching == branching, f'{rulecls}'
