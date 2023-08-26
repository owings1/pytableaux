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
from collections import defaultdict
from itertools import starmap
from typing import Any

from ..errors import Emsg, check
from ..lang import (Atomic, Constant, Operated, Operator, Predicate,
                    Predicated, Quantified, Quantifier, Sentence)
from ..models import PredicateInterpretation, ValueFDE
from ..proof import Branch, Node, SentenceNode, adds, filters, rules, sdnode
from ..tools import group, maxceil, minfloor, wraps
from . import LogicType


class Meta(LogicType.Meta):
    name = 'FDE'
    title = 'First Degree Entailment'
    modal = False
    quantified = True
    values = ValueFDE
    designated_values = frozenset({values.B, values.T})
    unassigned_value = values.N
    category = 'Many-valued'
    description = 'Four-valued logic (True, False, Neither, Both)'
    category_order = 10
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

    predicates: dict[Predicate, PredicateInterpretation]
    "A mapping of each predicate to its interpretation."

    atomics: dict[Atomic, ValueFDE]
    "An assignment of each atomic sentence to a value."

    opaques: dict[Sentence, ValueFDE]
    "An assignment of each opaque (un-interpreted) sentence to a value."

    sentences: set[Sentence]

    __slots__ = ('predicates', 'atomics', 'opaques', 'constants', 'sentences')

    def __init__(self):
        super().__init__()
        self.predicates = defaultdict(PredicateInterpretation)
        self.atomics = {}
        self.opaques = {}
        #: Track set of constants for performance.
        self.constants: set[Constant] = set()
        self.sentences = set()

    def value_of_atomic(self, s: Sentence, /):
        self._check_finished()
        return self.atomics.get(s, self.Meta.unassigned_value)

    def value_of_opaque(self, s: Sentence, /):
        self._check_finished()
        return self.opaques.get(s, self.Meta.unassigned_value)

    def value_of_predicated(self, s: Predicated, /):
        self._check_finished()
        interp = self.predicates[s.predicate]
        if s.params in interp.pos:
            if s.params in interp.neg:
                return self.values.B
            return self.values.T
        if s.params in interp.neg:
            return self.values.F
        return self.values.N

    def _unquantify_value_map(self, s: Quantified, /):
        try:
            return map(self.value_of, map(s.unquantify, self.constants))
        except AttributeError:
            check.inst(s, Quantified)
            raise # pragma: no cover

    def value_of_quantified(self, s: Quantified, /):
        """
        The value of a quantified sentence is determined from the values of
        sentences that result from replacing each constant for the quantified
        variable. For an existential quantifier, this is the max value, and
        for a universial quantifier, it is the min value.
        """
        self._check_finished()
        it = self._unquantify_value_map(s)
        if s.quantifier is Quantifier.Existential:
            return maxceil(self.maxval, it, self.minval)
        if s.quantifier is Quantifier.Universal:
            return minfloor(self.minval, it, self.maxval)
        raise NotImplementedError from ValueError(s.quantifier)

    def set_opaque_value(self, s: Sentence, value, /):
        self._check_not_finished()
        value = self.values[value]
        if self.opaques.get(s) not in (value, None):
            raise Emsg.ConflictForSentence(value, s)
        self.opaques[s] = value
        # We might have a quantified opaque sentence, in which case we will need
        # to still check every subsitution, so we want the constants and predicates.
        for pred in s.predicates:
            self.predicates[pred]
        self.constants.update(s.constants)
        self.sentences.add(s)
        
    def set_atomic_value(self, s: Atomic, value, /):
        self._check_not_finished()
        value = self.values[value]
        if self.atomics.get(s) not in (value, None):
            raise Emsg.ConflictForSentence(value, s)
        self.atomics[s] = value
        self.sentences.add(s)

    def set_predicated_value(self, s: Predicated, value, /):
        self._check_not_finished()
        value = self.values[value]
        if len(s.variables):
            raise ValueError(f'Free variables not allowed')
        self.predicates[s.predicate].set_value(s.params, self.values[value])
        self.constants.update(s.constants)
        self.sentences.add(s)

    def read_branch(self, branch, /):
        self._check_not_finished()
        for node in branch:
            if not isinstance(node, SentenceNode):
                continue
            s = node['sentence']
            self.sentences.add(s)
            is_literal = self.is_sentence_literal(s)
            is_opaque = self.is_sentence_opaque(s)
            if not is_literal and not is_opaque:
                continue
            d = node['designated']
            s_negative = -s
            has_negative = branch.has(sdnode(s_negative, d))
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
            if is_opaque:
                self.set_opaque_value(s, value)
            else:
                self.set_literal_value(s, value)
        return super().read_branch(branch)


    def finish(self):
        # TODO: consider augmenting the logic with Identity and Existence predicate
        #       restrictions. In that case, new tableaux rules need to be written.
        atomics = set()
        for s in self.sentences:
            atomics.update(s.atomics)
        unass = self.Meta.unassigned_value
        for s in atomics:
            if s not in self.atomics:
                self.atomics[s] = unass
        return super().finish()

    def get_data(self) -> dict[str, Any]:
        return dict(
            Atomics = dict(
                datatype        = 'function',
                typehint        = 'truth_function',
                input_datatype  = 'sentence',
                output_datatype = 'string',
                output_typehint = 'truth_value',
                symbol = 'v',
                values = [
                    dict(
                        input  = s,
                        output = self.atomics[s])
                    for s in sorted(self.atomics)]),
            Opaques = dict(
                datatype        = 'function',
                typehint        = 'truth_function',
                input_datatype  = 'sentence',
                output_datatype = 'string',
                output_typehint = 'truth_value',
                symbol = 'v',
                values = [
                    dict(
                        input  = s,
                        output = self.opaques[s])
                    for s in sorted(self.opaques)]),
            Predicates = dict(
                in_summary  = True,
                datatype    = 'list',
                values      = [
                    v for predicate in sorted(self.predicates) for v in
                    [
                        dict(
                            datatype        = 'function',
                            typehint        = 'extension',
                            input_datatype  = 'predicate',
                            output_datatype = 'set',
                            output_typehint = 'extension',
                            symbol = 'P+',
                            values = [
                                dict(
                                    input  = predicate,
                                    output = sorted(self.predicates[predicate].pos))]),
                        dict(
                            datatype        = 'function',
                            typehint        = 'extension',
                            input_datatype  = 'predicate',
                            output_datatype = 'set',
                            output_typehint = 'extension',
                            symbol = 'P-',
                            values = [
                                dict(
                                    input  = predicate,
                                    output = sorted(self.predicates[predicate].neg))])]]))


class System(LogicType.System):

    @classmethod
    def build_trunk(cls, b, arg, /):
        b += (sdnode(s, True) for s in arg.premises)
        b += sdnode(arg.conclusion, False)

    @classmethod
    def branching_complexity(cls, node, rules, /):
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
    def branching_complexity_hashable(cls, node, /):
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
        NodeFilters = group(filters.NodeDesignation)
        autoattrs = True

        def _get_node_targets(self, node: Node, branch: Branch, /):
            return self._get_sd_targets(self.sentence(node), node['designated'])

        def _get_sd_targets(self, s: Operated, d: bool, /):
            raise NotImplementedError

    class OperatorNodeRule(DefaultNodeRule, rules.OperatedSentenceRule, intermediate=True):

        def __init_subclass__(cls) -> None:
            super().__init_subclass__()
            if cls._get_node_targets is __class__._get_node_targets:
                if cls._get_sd_targets is __class__._get_sd_targets:
                    @abstractmethod
                    @wraps(cls._get_sd_targets)
                    def wrapped(self, s: Sentence, d: bool, /):
                        raise NotImplementedError
                    setattr(cls, '_get_sd_targets', wrapped)

    class QuantifierSkinnyRule(rules.NarrowQuantifierRule, DefaultNodeRule, intermediate=True): pass
    class QuantifierFatRule(rules.ExtendedQuantifierRule, DefaultNodeRule, intermediate=True): pass

    class ConjunctionReducingRule(OperatorNodeRule, intermediate=True):

        conjoined: Operator

        def _get_sd_targets(self, s, d, /):
            oper = self.conjoined
            lhs, rhs = s
            s = oper(lhs, rhs) & oper(rhs, lhs)
            if self.negated:
                s = ~s
            yield adds(group(sdnode(s, d)))

    class MaterialConditionalConjunctsReducingRule(ConjunctionReducingRule, intermediate=True):
        conjoined = Operator.MaterialConditional

    class ConditionalConjunctsReducingRule(ConjunctionReducingRule, intermediate=True):
        conjoined = Operator.Conditional

    class MaterialConditionalReducingRule(OperatorNodeRule, intermediate=True):
        "This rule reduces to a disjunction."

        def _get_sd_targets(self, s, d, /):
            sn = ~s.lhs | s.rhs
            if self.negated:
                sn = ~sn
            yield adds(group(sdnode(sn, d)))


class Rules(LogicType.Rules):

    class DesignationClosure(rules.FindClosingNodeRule):
        """
        A branch closes when a sentence appears on a node marked *designated*,
        and the same sentence appears on a node marked *undesignated*.
        """

        def _find_closing_node(self, node: Node, branch: Branch, /):
            s = self.sentence(node)
            if s is not None:
                return branch.find(sdnode(s, not node['designated']))

        def example_nodes(self):
            s = Atomic.first()
            yield sdnode(s, True)
            yield sdnode(s, False)
            
    class DoubleNegationDesignated(System.OperatorNodeRule):
        """
        From an unticked designated negated negation node *n* on a branch *b*,
        add a designated node to *b* with the double-negatum of *n*, then tick *n*.
        """

        def _get_sd_targets(self, s, d, /):
            yield adds(group(sdnode(s.lhs, d)))

    class DoubleNegationUndesignated(DoubleNegationDesignated): pass

    class AssertionDesignated(System.OperatorNodeRule):
        """
        From an unticked, designated, assertion node *n* on a branch *b*, add a designated
        node to *b* with the operand of *b*, then tick *n*.
        """

        def _get_sd_targets(self, s, d, /):
            yield adds(group(sdnode(s.lhs, d)))

    class AssertionUndesignated(AssertionDesignated): pass

    class AssertionNegatedDesignated(System.OperatorNodeRule):
        """
        From an unticked, designated, negated assertion node *n* on branch *b*, add a designated
        node to *b* with the negation of the assertion's operand to *b*, then tick *n*.
        """

        def _get_sd_targets(self, s, d, /):
            yield adds(group(sdnode(~s.lhs, d)))

    class AssertionNegatedUndesignated(AssertionNegatedDesignated): pass

    class ConjunctionDesignated(System.OperatorNodeRule):
        """
        From an unticked designated conjunction node *n* on a branch *b*, for each conjunct
        *c*, add a designated node with *c* to *b*, then tick *n*.
        """

        def _get_sd_targets(self, s, d, /):
            yield adds(group(sdnode(s.lhs, d), sdnode(s.rhs, d)))

    class ConjunctionNegatedDesignated(System.OperatorNodeRule):
        """
        From an unticked designated negated conjunction node *n* on a branch *b*,
        for each conjunct *c*, make a new branch *b'* from *b* and add a designated
        node with the negation of *c* to *b'*, then tick *n*.
        """

        def _get_sd_targets(self, s, d, /):
            yield adds(
                group(sdnode(~s.lhs, d)),
                group(sdnode(~s.rhs, d)))

    class ConjunctionUndesignated(System.OperatorNodeRule):
        """
        From an unticked undesignated conjunction node *n* on a branch *b*,
        for each conjunct *c*, make a new branch *b'* from *b* and add an
        undesignated node with *c* to *b'*, then tick *n*.
        """

        def _get_sd_targets(self, s, d, /):
            yield adds(
                group(sdnode(s.lhs, d)),
                group(sdnode(s.rhs, d)))

    class ConjunctionNegatedUndesignated(System.OperatorNodeRule):
        """
        From an unticked undesignated negated conjunction node *n* on a branch
        *b*, for each conjunct *c*, add an undesignated node with the negation
        of *c* to *b*, then tick *n*.
        """

        def _get_sd_targets(self, s, d, /):
            yield adds(group(sdnode(~s.lhs, d), sdnode(~s.rhs, d)))

    class DisjunctionDesignated(ConjunctionUndesignated): pass
    class DisjunctionNegatedDesignated(ConjunctionNegatedUndesignated): pass
    class DisjunctionUndesignated(ConjunctionDesignated): pass
    class DisjunctionNegatedUndesignated(ConjunctionNegatedDesignated): pass

    class MaterialConditionalDesignated(System.OperatorNodeRule):
        """
        From an unticked designated material conditional node *n* on a branch *b*, make
        two new branches *b'* and *b''* from *b*, add a designated node with the negation
        of the antecedent to *b'*, add a designated node with the consequent to *b''*,
        then tick *n*.
        """

        def _get_sd_targets(self, s, d, /):
            yield adds(
                group(sdnode(~s.lhs, d)),
                group(sdnode( s.rhs, d)))

    class MaterialConditionalNegatedDesignated(System.OperatorNodeRule):
        """
        From an unticked designated negated material conditional node *n* on a
        branch *b*, add a designated node with the antecedent, and a designated
        node with the negation of the consequent to *b*, then tick *n*.
        """

        def _get_sd_targets(self, s, d, /):
            yield adds(group(sdnode(s.lhs, d), sdnode(~s.rhs, d)))

    class MaterialConditionalUndesignated(System.OperatorNodeRule):
        """
        From an unticked undesignated material conditional node *n* on a branch *b*, add
        an undesignated node with the negation of the antecedent and an undesignated node
        with the consequent to *b*, then tick *n*.
        """

        def _get_sd_targets(self, s, d, /):
            yield adds(group(sdnode(~s.lhs, d), sdnode(s.rhs, d)))

    class MaterialConditionalNegatedUndesignated(System.OperatorNodeRule):
        """
        From an unticked undesignated negated material conditional node *n* on a branch *b*, make
        two new branches *b'* and *b''* from *b*, add an undesignated node with the antecedent to
        *b'*, and add an undesignated node with the negation of the consequent to *b''*, then
        tick *n*.
        """

        def _get_sd_targets(self, s, d, /):
            yield adds(
                group(sdnode( s.lhs, d)),
                group(sdnode(~s.rhs, d)))

    class MaterialBiconditionalDesignated(System.OperatorNodeRule):
        """
        From an unticked designated material biconditional node *n* on a branch *b*, make
        two new branches *b'* and *b''* from *b*, add a designated node with the negation
        of the antecedent and a designated node with the negation of the consequent to *b'*,
        and add a designated node with the antecedent and a designated node with the
        consequent to *b''*, then tick *n*.
        """

        def _get_sd_targets(self, s, d, /):
            yield adds(
                group(sdnode(~s.lhs, d), sdnode(~s.rhs, d)),
                group(sdnode( s.rhs, d), sdnode( s.lhs, d)))

    class MaterialBiconditionalNegatedDesignated(System.OperatorNodeRule):
        """
        From an unticked designated negated material biconditional node *n* on a branch *b*, make
        two branches *b'* and *b''* from *b*, add a designated node with the antecedent and a
        designated node with the negation of the consequent to *b'*, and add a designated node
        with the negation of the antecedent and a designated node with the consequent to *b''*,
        then tick *n*.
        """

        def _get_sd_targets(self, s, d, /):
            yield adds(
                group(sdnode( s.lhs, d), sdnode(~s.rhs, d)),
                group(sdnode(~s.lhs, d), sdnode( s.rhs, d)))

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

    class ExistentialDesignated(System.DefaultNodeRule, rules.NarrowQuantifierRule):
        """
        From an unticked designated existential node *n* on a branch *b* quantifying over
        variable *v* into sentence *s*, add a designated node to *b* with the substitution
        into *s* of a new constant not yet appearing on *b* for *v*, then tick *n*.
        """

        def _get_node_targets(self, node, branch, /):
            s = self.sentence(node)
            yield adds(
                group(sdnode(branch.new_constant() >> s, self.designation)))

    class ExistentialNegatedDesignated(System.DefaultNodeRule, rules.QuantifiedSentenceRule):
        """
        From an unticked designated negated existential node *n* on a branch *b*,
        quantifying over variable *v* into sentence *s*, add a designated node to *b*
        that universally quantifies over *v* into the negation of *s* (i.e. change
        :s:`~XxFx` to :s:`Lx~Fx`), then tick *n*.
        """

        def _get_sd_targets(self, s, d, /):
            v, si = s[1:]
            yield adds(group(sdnode(self.quantifier.other(v, ~si), d)))

    class ExistentialUndesignated(System.QuantifierFatRule):
        """
        From an undesignated existential node *n* on a branch *b*, for any constant *c* on
        *b* such that the result *r* of substituting *c* for the variable bound by the
        sentence of *n* does not appear on *b*, then add an undesignated node with *r* to *b*.
        If there are no constants yet on *b*, then instantiate with a new constant. The node
        *n* is never ticked.
        """

        def _get_constant_nodes(self, node, c, branch, /):
            yield sdnode(c >> self.sentence(node), self.designation)

    class ExistentialNegatedUndesignated(ExistentialNegatedDesignated): pass
    class UniversalDesignated(ExistentialUndesignated): pass
    class UniversalNegatedDesignated(ExistentialNegatedDesignated): pass
    class UniversalUndesignated(ExistentialDesignated): pass
    class UniversalNegatedUndesignated(ExistentialNegatedDesignated): pass

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
            ExistentialNegatedDesignated,
            ExistentialNegatedUndesignated,
            UniversalNegatedDesignated,
            UniversalNegatedUndesignated,
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
        group(
            ExistentialDesignated,
            ExistentialUndesignated),
        group(
            UniversalDesignated,
            UniversalUndesignated))

    @classmethod
    def _check_groups(cls):
        for branching, group in zip(range(2), cls.groups):
            for rulecls in group:
                assert rulecls.branching == branching, f'{rulecls}'