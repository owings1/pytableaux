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

from types import MappingProxyType as MapProxy
from typing import Any, Optional

from ..errors import Emsg
from ..lang import (Argument, Atomic, Constant, Operated, Operator, Predicate,
                    Predicated, Quantified, Quantifier, Sentence)
from ..models import BaseModel, ValueFDE
from ..proof import (Branch, Node, Tableau, System, Target, adds,
                     filters, rules, sdnode)
from ..tools import closure, group, qsetf
from . import LogicType

class Meta(LogicType.Meta):
    name = 'FDE'
    title = 'First Degree Entailment'
    modal = False
    values = ValueFDE
    designated_values = frozenset({values.B, values.T})
    unassigned_value = values.N
    category = 'Many-valued'
    description = 'Four-valued logic (True, False, Neither, Both)'
    category_order = 10
    tags = (
        'many-valued',
        'gappy',
        'glutty',
        'non-modal',
        'first-order')
    native_operators = (
        Operator.Negation,
        Operator.Conjunction,
        Operator.Disjunction,
        Operator.MaterialConditional,
        Operator.MaterialBiconditional)

class Model(BaseModel[ValueFDE]):
    'An FDE Model.'

    Value = Meta.values

    designated_values = Meta.designated_values
    "The set of designated values."

    unassigned_value = Meta.unassigned_value

    extensions: dict[Predicate, set[tuple[Constant, ...]]]
    """A mapping from each predicate to its extension.
    
    :type: dict[Predicate, set[tuple[Constant, ...]]]
    """

    anti_extensions: dict[Predicate, set[tuple[Constant, ...]]]
    """A map of predicates to their anti-extension.
    
    :type: dict[Predicate, set[tuple[Constant, ...]]]
    """

    atomics: dict[Atomic, ValueFDE]
    "An assignment of each atomic sentence to a value."

    opaques: dict[Sentence, ValueFDE]
    "An assignment of each opaque (un-interpreted) sentence to a value."

    def __init__(self):
        super().__init__()
        self.extensions = {}
        self.anti_extensions = {}
        self.atomics = {}
        self.opaques = {}
        #: Track set of atomics for performance.
        self.all_atomics: set[Atomic] = set()
        #: Track set of constants for performance.
        self.constants: set[Constant] = set()
        #: Track set of predicates for performance.
        self.predicates: set[Predicate] = set()

    def value_of_predicated(self, s: Predicated, /, **kw):
        params = s.params
        pred = s.predicate
        extension = self.get_extension(pred)
        anti_extension = self.get_anti_extension(pred)
        if params in extension:
            if params in anti_extension:
                return self.Value.B
            return self.Value.T
        if params in anti_extension:
            return self.Value.F
        return self.Value.N

    def value_of_existential(self, s: Quantified, /, **kw):
        """
        The value of an existential sentence is the maximum value of the sentences that
        result from replacing each constant for the quantified variable. The ordering of
        the values from least to greatest is: V{F}, V{N}, V{B}, V{T}.
        """
        maxval = max(self.Value)
        value = min(self.Value)
        value_of = self.value_of
        for c in self.constants:
            v = value_of(c >> s, **kw)
            if v > value:
                value = v
                if value is maxval:
                    break
        return value

    def value_of_universal(self, s: Quantified, /, **kw):
        """
        The value of an universal sentence is the minimum value of the sentences that
        result from replacing each constant for the quantified variable. The ordering of
        the values from least to greatest is: V{F}, V{N}, V{B}, V{T}.
        """
        minval = min(self.Value)
        value = max(self.Value)
        for c in self.constants:
            v = self.value_of(c >> s, **kw)
            if v < value:
                value = v
                if value is minval:
                    break
        return value

    def is_sentence_opaque(self, s: Sentence, /) -> bool:
        """
        A sentence is opaque if its operator is Necessity or Possibility, or if it is
        a negated sentence whose negatum has the operator Necessity or Possibility.
        """
        return (
            type(s) is Operated and
            s.operator in self.modal_operators
        ) or super().is_sentence_opaque(s)

    def is_countermodel_to(self, a: Argument, /) -> bool:
        """
        A model is a countermodel to an argument iff the value of every premise
        is in the set of designated values, and the value of the conclusion
        is not in the set of designated values.
        """
        for premise in a.premises:
            if self.value_of(premise) not in self.designated_values:
                return False
        return self.value_of(a.conclusion) not in self.designated_values

    def get_data(self) -> dict[str, Any]:
        return dict(
            Atomics = dict(
                description     = 'atomic values',
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
                description     = 'opaque values',
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
                description = 'predicate extensions/anti-extensions',
                in_summary  = True,
                datatype    = 'list',
                values      = [
                    [
                        dict(
                            description     = 'predicate extension',
                            datatype        = 'function',
                            typehint        = 'extension',
                            input_datatype  = 'predicate',
                            output_datatype = 'set',
                            output_typehint = 'extension',
                            symbol = 'P+',
                            values = [
                                dict(
                                    input  = predicate,
                                    output = self.get_extension(predicate))]),
                        dict(
                            description     = 'predicate anti-extension',
                            datatype        = 'function',
                            typehint        = 'extension',
                            input_datatype  = 'predicate',
                            output_datatype = 'set',
                            output_typehint = 'extension',
                            symbol = 'P-',
                            values = [
                                dict(
                                    input  = predicate,
                                    output = self.get_anti_extension(predicate))])
                    ]
                    for predicate in sorted(self.predicates)]))

    def read_branch(self, branch: Branch, /):
        for node in branch:
            s = node.get('sentence')
            if s is None:
                continue
            self._collect_sentence(s)
            is_literal = self.is_sentence_literal(s)
            is_opaque = self.is_sentence_opaque(s)
            if is_literal or is_opaque:
                if type(s) is Operated and s.operator is Operator.Negation:
                    # If the sentence is negated, set the value of the negatum
                    s = s.lhs
                    if node['designated']:
                        if branch.has(sdnode(s, True)):
                            # If the node is designated, and the negatum is
                            # also designated on b, the value is B
                            value = self.Value.B
                        else:
                            # If the node is designated, but the negatum is
                            # not also designated on b, the value is F
                            value = self.Value.F
                    else:
                        if branch.has(sdnode(s, False)):
                            # If the node is undesignated, and the negatum is
                            # also undesignated on b, the value is N
                            value = self.Value.N
                        else:
                            # If the node is undesignated, but the negatum is
                            # not also undesignated on b, the value is T
                            value = self.Value.T
                else:
                    # If the sentence is unnegated, set the value of the sentence
                    if node['designated']:
                        if branch.has(sdnode(~s, True)):
                            # If the node is designated, and its negation is
                            # also designated on b, the value is B
                            value = self.Value.B
                        else:
                            # If the node is designated, but the negation is
                            # not also designated on b, the value is T
                            value = self.Value.T
                    else:
                        if branch.has(sdnode(~s, False)):
                            # If the node is undesignated, and its negation is
                            # also undesignated on b, the value is N
                            value = self.Value.N
                        else:
                            # If the node is undesginated, but the negation is
                            # not also undesignated on b, the value is F
                            value = self.Value.F
                if is_opaque:
                    self.set_opaque_value(s, value)
                else:
                    self.set_literal_value(s, value)
        self.finish()

    def _collect_sentence(self, s: Sentence, /):
        self.predicates.update(s.predicates)
        self.all_atomics.update(s.atomics)
        self.constants.update(s.constants)

    def finish(self):
        # TODO: consider augmenting the logic with Identity and Existence predicate
        #       restrictions. In that case, new tableaux rules need to be written.
        for s in self.all_atomics:
            if s not in self.atomics:
                self.set_literal_value(s, self.unassigned_value)

    def set_literal_value(self, s: Sentence, value, /):
        try:
            value = self.Value[value]
        except KeyError:
            raise Emsg.UnknownForSentence(value, s)
        if self.is_sentence_opaque(s):
            self.set_opaque_value(s, value)
        else:
            stype = type(s)
            if stype is Operated and s.operator is Operator.Negation:
                self.set_literal_value(
                    s.lhs,
                    self.truth_function(s.operator, value))
            elif stype is Atomic:
                self.set_atomic_value(s, value)
            elif stype is Predicated:
                self.set_predicated_value(s, value)
            else:
                raise NotImplementedError()

    def set_opaque_value(self, s: Sentence, value, /):
        try:
            value = self.Value[value]
        except KeyError:
            raise Emsg.UnknownForSentence(value, s)
        if s in self.opaques and self.opaques[s] is not value:
            raise Emsg.ConflictForSentence(value, s)
        # We might have a quantified opaque sentence, in which case we will need
        # to still check every subsitution, so we want the constants, as well
        # as other lexical items.
        self._collect_sentence(s)
        self.opaques[s] = value
        
    def set_atomic_value(self, s: Atomic, value, /):
        try:
            value = self.Value[value]
        except KeyError:
            raise Emsg.UnknownForSentence(value, s)
        if s in self.atomics and self.atomics[s] is not value:
            raise Emsg.ConflictForSentence(value, s)
        self.atomics[s] = value

    def set_predicated_value(self, s: Predicated, value, /):
        Value = self.Value
        try:
            value = Value[value]
        except KeyError:
            raise Emsg.UnknownForSentence(value, s)
        for param in s:
            if type(param) is Constant:
                self.constants.add(param)
        extension = self.get_extension(s.predicate)
        anti_extension = self.get_anti_extension(s.predicate)
        if value is Value.N:
            if s.params in extension:
                raise Emsg.ConflictForExtension(value, s.params)
            if s.params in anti_extension:
                raise Emsg.ConflictForAntiExtension(value, s.params)
        elif value is Value.T:
            if s.params in anti_extension:
                raise Emsg.ConflictForAntiExtension(value, s.params)
            extension.add(s.params)
        elif value is Value.F:
            if s.params in extension:
                raise Emsg.ConflictForExtension(value, s.params)
            anti_extension.add(s.params)
        elif value is Value.B:
            extension.add(s.params)
            anti_extension.add(s.params)
        self.predicates.add(s.predicate)

    def get_extension(self, pred: Predicate, /) -> set[tuple[Constant, ...]]:
        if pred not in self.extensions:
            self.extensions[pred] = set()
            self.predicates.add(pred)
        return self.extensions[pred]

    def get_anti_extension(self, pred: Predicate, /) -> set[tuple[Constant, ...]]:
        if pred not in self.anti_extensions:
            self.anti_extensions[pred] = set()
            self.predicates.add(pred)
        return self.anti_extensions[pred]

    def value_of_atomic(self, s: Sentence, /, **kw) -> ValueFDE:
        return self.atomics.get(s, self.unassigned_value)

    def value_of_opaque(self, s: Sentence, /, **kw) -> ValueFDE:
        return self.opaques.get(s, self.unassigned_value)

    value_of_possibility = value_of_opaque
    value_of_necessity = value_of_opaque

    @closure
    def truth_function():

        # Define as generically as possible for reuse.

        def assertion(self: Model, a, _, /):
            return self.Value[a]

        def negation(self: Model, a, _, /):
            Value = self.Value
            if a == Value.F:
                return Value.T
            if a == Value.T:
                return Value.F
            return Value[a]

        def conjunction(self: Model, a, b, /):
            return min(self.Value[a], self.Value[b])

        def disjunction(self: Model, a, b, /):
            return max(self.Value[a], self.Value[b])

        def conditional(self: Model, a, b, /):
            return self.truth_function(Operator.MaterialConditional, a, b)

        def biconditional(self: Model, a, b, /):
            return self.truth_function(
                Operator.Conjunction,
                self.truth_function(Operator.Conditional, a, b),
                self.truth_function(Operator.Conditional, b, a) )

        def material_conditional(self: Model, a, b, /):
            return self.truth_function(
                Operator.Disjunction,
                self.truth_function(Operator.Negation, a),
                b)

        def material_biconditional(self: Model, a, b, /):
            return self.truth_function(
                Operator.Conjunction,
                self.truth_function(Operator.MaterialConditional, a, b),
                self.truth_function(Operator.MaterialConditional, b, a))

        _funcmap = MapProxy({
            Operator.Assertion: assertion,
            Operator.Negation: negation,
            Operator.Conjunction: conjunction,
            Operator.Disjunction: disjunction,
            Operator.Conditional: conditional,
            Operator.Biconditional: biconditional,
            Operator.MaterialConditional: material_conditional,
            Operator.MaterialBiconditional: material_biconditional})

        def func_mapper(self: Model, oper: Operator, a, b = None, /):
            try:
                return _funcmap[Operator(oper)](self, a, b)
            except KeyError:
                raise NotImplementedError(oper)

        return func_mapper

class System(System):

    # operator => negated => designated
    branchables = {
        Operator.Assertion: ((0, 0), (0, 0)),
        Operator.Negation: (None, (0, 0)),
        Operator.Conjunction: ((1, 0), (0, 1)),
        Operator.Disjunction: ((0, 1), (1, 0)),
        Operator.MaterialConditional: ((0, 1), (1, 0)),
        Operator.MaterialBiconditional: ((0, 1), (1, 0)),
        Operator.Conditional: ((0, 1), (1, 0)),
        Operator.Biconditional: ((1, 1), (1, 1))}

    @classmethod
    def build_trunk(cls, tab: Tableau, arg: Argument, /):
        b = tab.branch()
        b.extend(sdnode(s, True) for s in arg.premises)
        b.append(sdnode(arg.conclusion, False))

    @classmethod
    def branching_complexity(cls, node: Node, /) -> int:
        lastneg = False
        result = 0
        for oper in node['sentence'].operators:
            if not lastneg and oper is Operator.Negation:
                lastneg = True
                continue
            if oper in cls.branchables:
                result += cls.branchables[oper][lastneg][node['designated']]
                lastneg = False
        return result

    @classmethod
    def branching_complexity_hashable(cls, node: Node, /):
        return node['sentence'], node['designated']

class DefaultNodeRule(rules.GetNodeTargetsRule):
    """Default FDE node rule with:
    
    - filters.NodeDesignation with defaults: designation = `None`
    - AdzHelper implements `_apply()` with its `_apply()` method.
    - NodeFilter implements `_get_targets()` with abstract `_get_node_targets()`.
    - This class implements `_get_node_targets() defaulting to `_get_sd_targers()`,
        which raises NotImplementedError.
    - FilterHelper implements `example_nodes()` with its `example_node()` method.
    - AdzHelper implements `score_candidate()` with its `closure_score()` method.
    - autoattrs = True to induce rule properties from the name.
    """
    NodeFilters = filters.NodeDesignation,
    designation: Optional[bool] = None
    autoattrs = True

    def _get_node_targets(self, node: Node, branch: Branch, /):
        return self._get_sd_targets(self.sentence(node), node['designated'])

    def _get_sd_targets(self, s: Operated, d: bool, /):
        raise NotImplementedError

class OperatorNodeRule(rules.OperatedSentenceRule, DefaultNodeRule):
    'Mixin class for typical operator rules.'
    pass

class QuantifierSkinnyRule(rules.NarrowQuantifierRule, DefaultNodeRule):
    'Mixin class for "narrow" quantifier rules.'
    pass

class QuantifierFatRule(rules.ExtendedQuantifierRule, DefaultNodeRule):
    'Mixin class for "extended" quantifier rules.'
    pass

class ConjunctionReducingRule(OperatorNodeRule):

    conjoined: Operator

    def _get_sd_targets(self, s, d, /):
        oper = self.conjoined
        lhs, rhs = s
        s = oper(lhs, rhs) & oper(rhs, lhs)
        if self.negated:
            s = ~s
        yield adds(group(sdnode(s, d)))

class MaterialConditionalConjunctsReducingRule(ConjunctionReducingRule):
    conjoined = Operator.MaterialConditional

class ConditionalConjunctsReducingRule(ConjunctionReducingRule):
    conjoined = Operator.Conditional

class Rules(LogicType.Rules):

    class DesignationClosure(rules.BaseClosureRule):
        """
        A branch closes when a sentence appears on a node marked *designated*,
        and the same sentence appears on a node marked *undesignated*.
        """

        def _branch_target_hook(self, node: Node, branch: Branch, /):
            nnode = self._find_closing_node(node, branch)
            if nnode is not None:
                return Target(
                    nodes = qsetf((node, nnode)),
                    branch = branch)

        def node_will_close_branch(self, node: Node, branch: Branch, /):
            return bool(self._find_closing_node(node, branch))

        def example_nodes(self):
            s = Atomic.first()
            yield sdnode(s, True)
            yield sdnode(s, False)

        def _find_closing_node(self, node: Node, branch: Branch, /):
            s = self.sentence(node)
            if s is not None:
                return branch.find(sdnode(s, not node['designated']))
            
    class DoubleNegationDesignated(OperatorNodeRule):
        """
        From an unticked designated negated negation node *n* on a branch *b*,
        add a designated node to *b* with the double-negatum of *n*, then tick *n*.
        """

        def _get_sd_targets(self, s, d, /):
            yield adds(group(sdnode(s.lhs, d)))

    class DoubleNegationUndesignated(DoubleNegationDesignated):
        """
        From an unticked undesignated negated negation node *n* on a branch *b*, add an
        undesignated node to *b* with the double-negatum of *n*, then tick *n*.
        """

    class AssertionDesignated(OperatorNodeRule):
        """
        From an unticked, designated, assertion node *n* on a branch *b*, add a designated
        node to *b* with the operand of *b*, then tick *n*.
        """

        def _get_sd_targets(self, s, d, /):
            yield adds(group(sdnode(s.lhs, d)))

    class AssertionUndesignated(AssertionDesignated):
        """
        From an unticked, undesignated, assertion node *n* on a branch *b*, add an undesignated
        node to *b* with the operand of *n*, then tick *n*.
        """

    class AssertionNegatedDesignated(OperatorNodeRule):
        """
        From an unticked, designated, negated assertion node *n* on branch *b*, add a designated
        node to *b* with the negation of the assertion's operand to *b*, then tick *n*.
        """

        def _get_sd_targets(self, s, d, /):
            yield adds(group(sdnode(~s.lhs, d)))

    class AssertionNegatedUndesignated(AssertionNegatedDesignated):
        """
        From an unticked, undesignated, negated assertion node *n* on branch *b*, add an undesignated
        node to *b* with the negation of the assertion's operand to *b*, then tick *n*.
        """

    class ConjunctionDesignated(OperatorNodeRule):
        """
        From an unticked designated conjunction node *n* on a branch *b*, for each conjunct
        *c*, add a designated node with *c* to *b*, then tick *n*.
        """

        def _get_sd_targets(self, s, d, /):
            yield adds(group(sdnode(s.lhs, d), sdnode(s.rhs, d)))

    class ConjunctionNegatedDesignated(OperatorNodeRule):
        """
        From an unticked designated negated conjunction node *n* on a branch *b*,
        for each conjunct *c*, make a new branch *b'* from *b* and add a designated
        node with the negation of *c* to *b'*, then tick *n*.
        """

        def _get_sd_targets(self, s, d, /):
            yield adds(
                group(sdnode(~s.lhs, d)),
                group(sdnode(~s.rhs, d)))

    class ConjunctionUndesignated(OperatorNodeRule):
        """
        From an unticked undesignated conjunction node *n* on a branch *b*,
        for each conjunct *c*, make a new branch *b'* from *b* and add an
        undesignated node with *c* to *b'*, then tick *n*.
        """

        def _get_sd_targets(self, s, d, /):
            yield adds(
                group(sdnode(s.lhs, d)),
                group(sdnode(s.rhs, d)))

    class ConjunctionNegatedUndesignated(OperatorNodeRule):
        """
        From an unticked undesignated negated conjunction node *n* on a branch
        *b*, for each conjunct *c*, add an undesignated node with the negation
        of *c* to *b*, then tick *n*.
        """

        def _get_sd_targets(self, s, d, /):
            yield adds(group(sdnode(~s.lhs, d), sdnode(~s.rhs, d)))

    class DisjunctionDesignated(ConjunctionUndesignated):
        """
        From an unticked designated disjunction node *n* on a branch *b*, for each disjunct
        *d*, make a new branch *b'* from *b* and add a designated node with *d* to *b'*,
        then tick *n*.
        """

    class DisjunctionNegatedDesignated(ConjunctionNegatedUndesignated):
        """
        From an unticked designated negated disjunction node *n* on a branch *b*, for each disjunct
        *d*, add a designated node with the negation of *d* to *b*, then tick *n*.
        """

    class DisjunctionUndesignated(ConjunctionDesignated):
        """
        From an unticked undesignated disjunction node *n* on a branch *b*, for each disjunct
        *d*, add an undesignated node with *d* to *b*, then tick *n*.
        """

    class DisjunctionNegatedUndesignated(ConjunctionNegatedDesignated):
        """
        From an unticked undesignated negated disjunction node *n* on a branch *b*, for each disjunct
        *d*, make a new branch *b'* from *b* and add an undesignated node with the negation of *d* to
        *b'*, then tick *n*.
        """

    class MaterialConditionalDesignated(OperatorNodeRule):
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

    class MaterialConditionalNegatedDesignated(OperatorNodeRule):
        """
        From an unticked designated negated material conditional node *n* on a
        branch *b*, add a designated node with the antecedent, and a designated
        node with the negation of the consequent to *b*, then tick *n*.
        """

        def _get_sd_targets(self, s, d, /):
            yield adds(group(sdnode(s.lhs, d), sdnode(~s.rhs, d)))

    class MaterialConditionalUndesignated(OperatorNodeRule):
        """
        From an unticked undesignated material conditional node *n* on a branch *b*, add
        an undesignated node with the negation of the antecedent and an undesignated node
        with the consequent to *b*, then tick *n*.
        """

        def _get_sd_targets(self, s, d, /):
            yield adds(group(sdnode(~s.lhs, d), sdnode(s.rhs, d)))

    class MaterialConditionalNegatedUndesignated(OperatorNodeRule):
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

    class MaterialBiconditionalDesignated(OperatorNodeRule):
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

    class MaterialBiconditionalNegatedDesignated(OperatorNodeRule):
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

    class MaterialBiconditionalUndesignated(MaterialBiconditionalNegatedDesignated):
        """
        From an unticked undesignated material biconditional node *n* on a branch *b*, make
        two new branches *b'* and *b''* from *b*, add an undesignated node with the negation
        of the antecedent and an undesignated node with the consequent to *b'*, and add an
        undesignated node with the antecedent and an undesignated node with the negation of
        the consequent to *b''*, then tick *n*.
        """

    class MaterialBiconditionalNegatedUndesignated(MaterialBiconditionalDesignated):
        """
        From an undesignated negated material biconditional node *n* on a branch *b*, make
        two branches *b'* and *b''* from *b*, add an undesignated node with the negation of
        the antecendent and an undesignated node with the negation of the consequent to *b'*,
        and add an undesignated node with the antecedent and an undesignated node with the
        consequent to *b''*, then tick *n*.
        """

    class ConditionalDesignated(MaterialConditionalDesignated):
        """
        This rule functions the same as the corresponding material conditional rule.

        From an unticked designated conditional node *n* on a branch *b*, make two new
        branches *b'* and *b''* from *b*, add a designated node with the negation of
        the antecedent to *b'*, add a designated node with the consequent to *b''*,
        then tick *n*.
        """

    class ConditionalNegatedDesignated(MaterialConditionalNegatedDesignated):
        """
        This rule functions the same as the corresponding material conditional rule.

        From an unticked designated negated conditional node *n* on a branch *b*, add a
        designated node with the antecedent, and a designated node with the negation of
        the consequent to *b*, then tick *n*.
        """

    class ConditionalUndesignated(MaterialConditionalUndesignated):
        """
        This rule functions the same as the corresponding material conditional rule.

        From an unticked undesignated conditional node *n* on a branch *b*, add an
        undesignated node with the negation of the antecedent and an undesignated node
        with the consequent to *b*, then tick *n*.
        """

    class ConditionalNegatedUndesignated(MaterialConditionalNegatedUndesignated):
        """
        This rule functions the same as the corresponding material conditional rule.

        From an unticked undesignated negated conditional node *n* on a branch *b*, make two
        new branches *b'* and *b''* from *b*, add an undesignated node with the antecedent to
        *b'*, and add an undesignated node with the negation of the consequent to *b''*, then
        tick *n*.
        """

    class BiconditionalDesignated(MaterialBiconditionalDesignated):
        """
        This rule functions the same as the corresponding material biconditional rule.

        From an unticked designated biconditional node *n* on a branch *b*, make two new
        branches *b'* and *b''* from *b*, add a designated node with the negation of the
        antecedent and a designated node with the negation of the consequent to *b'*,
        and add a designated node with the antecedent and a designated node with the
        consequent to *b''*, then tick *n*.
        """

    class BiconditionalNegatedDesignated(MaterialBiconditionalNegatedDesignated):
        """
        This rule functions the same as the corresponding material biconditional rule.

        From an unticked designated negated biconditional node *n* on a branch *b*, make two
        branches *b'* and *b''* from *b*, add a designated node with the antecedent and a
        designated node with the negation of the consequent to *b'*, and add a designated node
        with the negation of the antecedent and a designated node with the consequent to *b''*,
        then tick *n*.
        """

    class BiconditionalUndesignated(MaterialBiconditionalUndesignated):
        """
        This rule functions the same as the corresponding material biconditional rule.

        From an unticked undesignated material biconditional node *n* on a branch *b*, make
        two new branches *b'* and *b''* from *b*, add an undesignated node with the negation
        of the antecedent and an undesignated node with the consequent to *b'*, and add an
        undesignated node with the antecedent and an undesignated node with the negation of
        the consequent to *b''*, then tick *n*.
        """

    class BiconditionalNegatedUndesignated(MaterialBiconditionalNegatedUndesignated):
        """
        This rule functions the same as the corresponding material biconditional rule.

        From an undesignated negated biconditional node *n* on a branch *b*, make two
        branches *b'* and *b''* from *b*, add an undesignated node with the negation of the
        antecendent and an undesignated node with the negation of the consequent to *b'*,
        and add an undesignated node with the antecedent and an undesignated node with the
        consequent to *b''*, then tick *n*.
        """

    class ExistentialDesignated(rules.NarrowQuantifierRule, DefaultNodeRule):
        """
        From an unticked designated existential node *n* on a branch *b* quantifying over
        variable *v* into sentence *s*, add a designated node to *b* with the substitution
        into *s* of a new constant not yet appearing on *b* for *v*, then tick *n*.
        """

        def _get_node_targets(self, node: Node, branch: Branch,/):
            s = self.sentence(node)
            yield adds(
                group(sdnode(branch.new_constant() >> s, self.designation)))

    class ExistentialNegatedDesignated(rules.QuantifiedSentenceRule, DefaultNodeRule):
        """
        From an unticked designated negated existential node *n* on a branch *b*,
        quantifying over variable *v* into sentence *s*, add a designated node to *b*
        that universally quantifies over *v* into the negation of *s* (i.e. change
        :s:`~XxFx` to :s:`Lx~Fx`), then tick *n*.
        """
        convert = Quantifier.Universal

        def _get_sd_targets(self, s, d, /):
            v, si = s[1:]
            yield adds(group(sdnode(self.convert(v, ~si), d)))

    class ExistentialUndesignated(QuantifierFatRule):
        """
        From an undesignated existential node *n* on a branch *b*, for any constant *c* on
        *b* such that the result *r* of substituting *c* for the variable bound by the
        sentence of *n* does not appear on *b*, then add an undesignated node with *r* to *b*.
        If there are no constants yet on *b*, then instantiate with a new constant. The node
        *n* is never ticked.
        """

        def _get_constant_nodes(self, node: Node, c: Constant, _, /):
            yield sdnode(c >> self.sentence(node), self.designation)

    class ExistentialNegatedUndesignated(ExistentialNegatedDesignated):
        """
        From an unticked undesignated negated existential node *n* on a branch *b*,
        quantifying over variable *v* into sentence *s*, add an undesignated node to *b*
        that universally quantifies over *v* into the negation of *s* (e.g. change
        :s:`~XxFx` to :s:`Lx~Fx`), then tick *n*.
        """

    class UniversalDesignated(ExistentialUndesignated):
        """
        From a designated universal node *n* on a branch *b*, for any constant *c* on *b*
        such that the result *r* of substituting *c* for the variable bound by the sentence
        of *n* does not appear on *b*, then add a designated node with *r* to *b*. If there
        are no constants yet on *b*, then instantiate with a new constant. The node *n* is
        never ticked.
        """

    class UniversalNegatedDesignated(ExistentialNegatedDesignated):
        """
        From an unticked designated negated universal node *n* on a branch *b*,
        quantifying over variable *v* into sentence *s*, add a designated node to *b*
        with the existential quantifier over *v* into the negation of *s* (e.g. change
        :s:`~LxFx` to :s:`Xx~Fx`), then tick *n*.
        """
        convert = Quantifier.Existential

    class UniversalUndesignated(ExistentialDesignated):
        """
        From an unticked undesignated universal node *n* on a branch *b* quantifying over *v*
        into sentence *s*, add an undesignated node to *b* with the result of substituting into
        *s* a constant new to *b* for *v*, then tick *n*.
        """

    class UniversalNegatedUndesignated(ExistentialNegatedDesignated):
        """
        From an unticked undesignated negated universal node *n* on a branch *b*,
        quantifying over variable *v* into sentence *s*, add an undesignated node to *b*
        with the existential quantifier over *v* into the negation of *s* (e.g. change
        :s:`~LxFx` to :s:`Xx~Fx`), then tick *n*.
        """
        convert = Quantifier.Existential

    closure_rules = group(DesignationClosure)

    rule_groups = (
        (
            # non-branching rules
            AssertionDesignated,
            AssertionUndesignated,
            AssertionNegatedDesignated,
            AssertionNegatedUndesignated,
            ConjunctionDesignated, 
            DisjunctionNegatedDesignated,
            DisjunctionUndesignated,
            DisjunctionNegatedUndesignated,
            MaterialConditionalNegatedDesignated,
            MaterialConditionalUndesignated,
            ConditionalUndesignated, 
            ConditionalNegatedDesignated,
            ExistentialNegatedDesignated,
            ExistentialNegatedUndesignated,
            UniversalNegatedDesignated,
            UniversalNegatedUndesignated,
            DoubleNegationDesignated,
            DoubleNegationUndesignated,
        ),
        (
            # branching rules
            ConjunctionNegatedDesignated,
            ConjunctionUndesignated,
            ConjunctionNegatedUndesignated,
            DisjunctionDesignated,
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
            BiconditionalNegatedUndesignated,
        ),
        (
            ExistentialDesignated,
            ExistentialUndesignated,
        ),
        (
            UniversalDesignated,
            UniversalUndesignated,
        ),
    )

