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
# pytableaux - First Degree Entailment Logic
from __future__ import annotations

from typing import Any, ClassVar

from pytableaux.errors import Emsg
from pytableaux.lang.collect import Argument
from pytableaux.lang.lex import (Atomic, Constant, Operated, Operator,
                                 Predicate, Predicated, Quantified, Quantifier,
                                 Sentence)
from pytableaux.models import BaseModel, ValueFDE
from pytableaux.proof import TableauxSystem as BaseSystem
from pytableaux.proof import filters, rules
from pytableaux.proof.common import Branch, Node, Target
from pytableaux.proof.tableaux import Tableau
from pytableaux.proof.util import adds, group, sdnode
from pytableaux.tools import MapProxy, closure
from pytableaux.tools.hybrids import qsetf
from pytableaux.tools.sets import setf

name = 'FDE'

class Meta:
    title       = 'First Degree Entailment'
    category    = 'Many-valued'
    description = 'Four-valued logic (True, False, Neither, Both)'
    category_order = 10
    tags = (
        'many-valued',
        'gappy',
        'glutty',
        'non-modal',
        'first-order',
    )

class Model(BaseModel[ValueFDE]):
    'An FDE Model.'

    Value = ValueFDE

    designated_values = setf({Value.B, Value.T})
    "The set of designated values."

    unassigned_value = Value.N

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
                symbol          = 'v',
                values          = [
                    dict(
                        input  = s,
                        output = self.atomics[s]
                    )
                    for s in sorted(self.atomics)
                ]
            ),
            Opaques = dict(
                description     = 'opaque values',
                datatype        = 'function',
                typehint        = 'truth_function',
                input_datatype  = 'sentence',
                output_datatype = 'string',
                output_typehint = 'truth_value',
                symbol          = 'v',
                values          = [
                    dict(
                        input  = s,
                        output = self.opaques[s]
                    )
                    for s in sorted(self.opaques)
                ]
            ),
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
                            symbol          = 'P+',
                            values          = [
                                dict(
                                    input  = predicate,
                                    output = self.get_extension(predicate),
                                )
                            ]
                        ),
                        dict(
                            description     = 'predicate anti-extension',
                            datatype        = 'function',
                            typehint        = 'extension',
                            input_datatype  = 'predicate',
                            output_datatype = 'set',
                            output_typehint = 'extension',
                            symbol          = 'P-',
                            values          = [
                                dict(
                                    input  = predicate,
                                    output = self.get_anti_extension(predicate),
                                )
                            ]
                        )
                    ]
                    for predicate in sorted(self.predicates)
                ]
            )
        )

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
                    self.truth_function(s.operator, value)
                )
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
        predicate = s.predicate
        params = s.params
        for param in params:
            if param.is_constant:
                self.constants.add(param)
        extension = self.get_extension(predicate)
        anti_extension = self.get_anti_extension(predicate)
        if value is Value.N:
            if params in extension:
                raise Emsg.ConflictForExtension(value, params)
            if params in anti_extension:
                raise Emsg.ConflictForAntiExtension(value, params)
        elif value is Value.T:
            if params in anti_extension:
                raise Emsg.ConflictForAntiExtension(value, params)
            extension.add(params)
        elif value is Value.F:
            if params in extension:
                raise Emsg.ConflictForExtension(value, params)
            anti_extension.add(params)
        elif value is Value.B:
            extension.add(params)
            anti_extension.add(params)
        self.predicates.add(predicate)

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
                self.truth_function(Operator.Conditional, b, a)
            )

        def material_conditional(self: Model, a, b, /):
            return self.truth_function(
                Operator.Disjunction,
                self.truth_function(Operator.Negation, a),
                b
            )

        def material_biconditional(self: Model, a, b, /):
            return self.truth_function(
                Operator.Conjunction,
                self.truth_function(Operator.MaterialConditional, a, b),
                self.truth_function(Operator.MaterialConditional, b, a)
            )

        _funcmap = MapProxy({
            Operator.Assertion : assertion,
            Operator.Negation  : negation,
            Operator.Conjunction : conjunction,
            Operator.Disjunction : disjunction,
            Operator.Conditional : conditional,
            Operator.Biconditional : biconditional,
            Operator.MaterialConditional   : material_conditional,
            Operator.MaterialBiconditional : material_biconditional,
        })

        def func_mapper(self: Model, oper: Operator, a, b = None, /):
            try:
                return _funcmap[Operator(oper)](self, a, b)
            except KeyError:
                raise NotImplementedError(oper)

        return func_mapper

class TableauxSystem(BaseSystem):
    """
    Nodes for FDE have a boolean *designation* property, and a branch is closed iff
    the same sentence appears on both a designated and undesignated node. This allows
    for both a sentence and its negation to appear as designated (xor undesignated)
    on an open branch.
    """

    # operator => negated => designated
    branchables = {
        Operator.Negation: {
            True: {True: 0, False: 0},
        },
        Operator.Assertion: {
            False : {True: 0, False: 0},
            True  : {True: 0, False: 0},
        },
        Operator.Conjunction: {
            False : {True: 0, False: 1},
            True  : {True: 1, False: 0},
        },
        Operator.Disjunction: {
            False : {True: 1, False: 0},
            True  : {True: 0, False: 1},
        },
        Operator.MaterialConditional: {
            False : {True: 1, False: 0},
            True  : {True: 0, False: 1},
        },
        Operator.MaterialBiconditional: {
            False : {True: 1, False: 1},
            True  : {True: 1, False: 1},
        },
        Operator.Conditional: {
            False : {True: 1, False: 0},
            True  : {True: 0, False: 1},
        },
        Operator.Biconditional: {
            False : {True: 1, False: 1},
            True  : {True: 1, False: 1},
        },
    }

    @classmethod
    def build_trunk(cls, tab: Tableau, arg: Argument, /):
        """
        To build the trunk for an argument, add a designated node for each premise, and
        an undesignated node for the conclusion.
        """
        append = tab.branch().append
        for premise in arg.premises:
            append(sdnode(premise, True))
        append(sdnode(arg.conclusion, False))

    @classmethod
    def branching_complexity(cls, node: Node, /) -> int:
        s = node.get('sentence')
        if s is None:
            return 0
        d = node['designated']
        last_is_negated = False
        complexity = 0
        for oper in s.operators:
            if oper is Operator.Negation:
                if not last_is_negated:
                    last_is_negated = True
                    continue
            if oper in cls.branchables:
                complexity += cls.branchables[oper][last_is_negated][d]
                last_is_negated = False
        return complexity

class DefaultNodeRule(rules.GetNodeTargetsRule):
    """Default FDE node rule with:
    
    - filters.DesignationNode with defaults: designation = `None`
    - NodeFilter implements `_get_targets()` with abstract `_get_node_targets()`.
    - FilterHelper implements `example_nodes()` with its `example_node()` method.
    - AdzHelper implements `_apply()` with its `_apply()` method.
    - AdzHelper implements `score_candidate()` with its `closure_score()` method.
    """
    NodeFilters = filters.DesignationNode,
    designation: bool|None = None

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

    conjunct_op: Operator
    branch_level = 1

    def _get_node_targets(self, node: Node, _, /):
        oper = self.conjunct_op
        lhs, rhs = self.sentence(node)
        s = oper(lhs, rhs) & oper(rhs, lhs)
        if self.negated:
            s = ~s
        return adds(group(sdnode(s, self.designation)))

class TabRules:
    """
    In general, rules for connectives consist of four rules per connective:
    a designated rule, an undesignated rule, a negated designated rule, and a negated
    undesignated rule. The special case of negation has a total of two rules which apply
    to double negation only, one designated rule, and one undesignated rule.
    """

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
                    branch = branch,
                )

        def node_will_close_branch(self, node: Node, branch: Branch, /):
            return bool(self._find_closing_node(node, branch))

        @staticmethod
        def example_nodes():
            s = Atomic.first()
            return sdnode(s, True), sdnode(s, False)

        def _find_closing_node(self, node: Node, branch: Branch, /):
            s = self.sentence(node)
            if s is not None:
                return branch.find(sdnode(s, not node['designated']))
            
    class DoubleNegationDesignated(OperatorNodeRule):
        """
        From an unticked designated negated negation node *n* on a branch *b*,
        add a designated node to *b* with the double-negatum of *n*, then tick *n*.
        """

        designation = True
        negated     = True
        operator    = Operator.Negation
        branch_level = 1

        def _get_node_targets(self, node: Node, _, /):
            return adds(
                group(sdnode(self.sentence(node).lhs, self.designation))
            )

    class DoubleNegationUndesignated(DoubleNegationDesignated):
        """
        From an unticked undesignated negated negation node *n* on a branch *b*, add an
        undesignated node to *b* with the double-negatum of *n*, then tick *n*.
        """
        designation = False
        negated     = True

    class AssertionDesignated(OperatorNodeRule):
        """
        From an unticked, designated, assertion node *n* on a branch *b*, add a designated
        node to *b* with the operand of *b*, then tick *n*.
        """
        designation = True
        operator    = Operator.Assertion
        branch_level = 1

        def _get_node_targets(self, node: Node, _, /):
            return adds(
                group(sdnode(self.sentence(node).lhs, self.designation))
            )

    class AssertionUndesignated(AssertionDesignated):
        """
        From an unticked, undesignated, assertion node *n* on a branch *b*, add an undesignated
        node to *b* with the operand of *n*, then tick *n*.
        """
        designation = False

    class AssertionNegatedDesignated(OperatorNodeRule):
        """
        From an unticked, designated, negated assertion node *n* on branch *b*, add a designated
        node to *b* with the negation of the assertion's operand to *b*, then tick *n*.
        """
        designation = True
        negated     = True
        operator    = Operator.Assertion
        branch_level = 1

        def _get_node_targets(self, node: Node, _, /):
            return adds(
                group(sdnode(~self.sentence(node).lhs, self.designation))
            )

    class AssertionNegatedUndesignated(AssertionNegatedDesignated):
        """
        From an unticked, undesignated, negated assertion node *n* on branch *b*, add an undesignated
        node to *b* with the negation of the assertion's operand to *b*, then tick *n*.
        """
        designation = False

    class ConjunctionDesignated(OperatorNodeRule):
        """
        From an unticked designated conjunction node *n* on a branch *b*, for each conjunct
        *c*, add a designated node with *c* to *b*, then tick *n*.
        """
        designation = True
        operator    = Operator.Conjunction
        branch_level = 1

        def _get_node_targets(self, node: Node, _, /):
            s = self.sentence(node)
            d = self.designation
            return adds(
                group(sdnode(s.lhs, d), sdnode(s.rhs, d))
            )

    class ConjunctionNegatedDesignated(OperatorNodeRule):
        """
        From an unticked designated negated conjunction node *n* on a branch *b*,
        for each conjunct *c*, make a new branch *b'* from *b* and add a designated
        node with the negation of *c* to *b'*, then tick *n*.
        """
        designation = True
        negated     = True
        operator    = Operator.Conjunction
        branch_level = 2

        def _get_node_targets(self, node: Node, _, /):
            s = self.sentence(node)
            d = self.designation
            return adds(
                group(sdnode(~s.lhs, d)),
                group(sdnode(~s.rhs, d)),
            )

    class ConjunctionUndesignated(OperatorNodeRule):
        """
        From an unticked undesignated conjunction node *n* on a branch *b*,
        for each conjunct *c*, make a new branch *b'* from *b* and add an
        undesignated node with *c* to *b'*, then tick *n*.
        """
        designation = False
        operator    = Operator.Conjunction
        branch_level = 2

        def _get_node_targets(self, node: Node, _, /):
            s = self.sentence(node)
            d = self.designation
            return adds(
                group(sdnode(s.lhs, d)),
                group(sdnode(s.rhs, d)),
            )

    class ConjunctionNegatedUndesignated(OperatorNodeRule):
        """
        From an unticked undesignated negated conjunction node *n* on a branch
        *b*, for each conjunct *c*, add an undesignated node with the negation
        of *c* to *b*, then tick *n*.
        """
        designation = False
        negated     = True
        operator    = Operator.Conjunction
        branch_level = 1

        def _get_node_targets(self, node: Node, _, /):
            s = self.sentence(node)
            d = self.designation
            return adds(
                group(sdnode(~s.lhs, d), sdnode(~s.rhs, d))
            )

    class DisjunctionDesignated(ConjunctionUndesignated):
        """
        From an unticked designated disjunction node *n* on a branch *b*, for each disjunt
        *d*, make a new branch *b'* from *b* and add a designated node with *d* to *b'*,
        then tick *n*.
        """
        designation = True
        operator    = Operator.Disjunction

    class DisjunctionNegatedDesignated(ConjunctionNegatedUndesignated):
        """
        From an unticked designated negated disjunction node *n* on a branch *b*, for each disjunct
        *d*, add a designated node with the negation of *d* to *b*, then tick *n*.
        """
        designation = True
        operator    = Operator.Disjunction

    class DisjunctionUndesignated(ConjunctionDesignated):
        """
        From an unticked undesignated disjunction node *n* on a branch *b*, for each disjunct
        *d*, add an undesignated node with *d* to *b*, then tick *n*.
        """
        designation = False
        operator    = Operator.Disjunction

    class DisjunctionNegatedUndesignated(ConjunctionNegatedDesignated):
        """
        From an unticked undesignated negated disjunction node *n* on a branch *b*, for each disjunct
        *d*, make a new branch *b'* from *b* and add an undesignated node with the negation of *d* to
        *b'*, then tick *n*.
        """
        designation = False
        operator    = Operator.Disjunction

    class MaterialConditionalDesignated(OperatorNodeRule):
        """
        From an unticked designated material conditional node *n* on a branch *b*, make
        two new branches *b'* and *b''* from *b*, add a designated node with the negation
        of the antecedent to *b'*, add a designated node with the consequent to *b''*,
        then tick *n*.
        """
        designation = True
        operator    = Operator.MaterialConditional
        branch_level = 2

        def _get_node_targets(self, node: Node, _, /):
            s = self.sentence(node)
            d = self.designation
            return adds(
                group(sdnode(~s.lhs, d)),
                group(sdnode( s.rhs, d)),
            )

    class MaterialConditionalNegatedDesignated(OperatorNodeRule):
        """
        From an unticked designated negated material conditional node *n* on a
        branch *b*, add a designated node with the antecedent, and a designated
        node with the negation of the consequent to *b*, then tick *n*.
        """
        designation = True
        negated     = True
        operator    = Operator.MaterialConditional
        branch_level = 1

        def _get_node_targets(self, node: Node, _, /):
            s = self.sentence(node)
            d = self.designation
            return adds(
                group(sdnode(s.lhs, d), sdnode(~s.rhs, d))
            )

    class MaterialConditionalUndesignated(OperatorNodeRule):
        """
        From an unticked undesignated material conditional node *n* on a branch *b*, add
        an undesignated node with the negation of the antecedent and an undesignated node
        with the consequent to *b*, then tick *n*.
        """
        designation = False
        operator    = Operator.MaterialConditional
        branch_level = 1

        def _get_node_targets(self, node: Node, _, /):
            s = self.sentence(node)
            d = self.designation
            return adds(
                group(sdnode(~s.lhs, d), sdnode(s.rhs, d))
            )

    class MaterialConditionalNegatedUndesignated(OperatorNodeRule):
        """
        From an unticked undesignated negated material conditional node *n* on a branch *b*, make
        two new branches *b'* and *b''* from *b*, add an undesignated node with the antecedent to
        *b'*, and add an undesignated node with the negation of the consequent to *b''*, then
        tick *n*.
        """
        designation = False
        negated     = True
        operator    = Operator.MaterialConditional
        branch_level = 2

        def _get_node_targets(self, node: Node, _, /):
            s = self.sentence(node)
            d = self.designation
            return adds(
                group(sdnode( s.lhs, d)),
                group(sdnode(~s.rhs, d)),
            )

    class MaterialBiconditionalDesignated(OperatorNodeRule):
        """
        From an unticked designated material biconditional node *n* on a branch *b*, make
        two new branches *b'* and *b''* from *b*, add a designated node with the negation
        of the antecedent and a designated node with the negation of the consequent to *b'*,
        and add a designated node with the antecedent and a designated node with the
        consequent to *b''*, then tick *n*.
        """
        designation = True
        operator    = Operator.MaterialBiconditional
        branch_level = 2

        def _get_node_targets(self, node: Node, _, /):
            s = self.sentence(node)
            d = self.designation
            return adds(
                group(sdnode(~s.lhs, d), sdnode(~s.rhs, d)),
                group(sdnode( s.rhs, d), sdnode( s.lhs, d)),
            )

    class MaterialBiconditionalNegatedDesignated(OperatorNodeRule):
        """
        From an unticked designated negated material biconditional node *n* on a branch *b*, make
        two branches *b'* and *b''* from *b*, add a designated node with the antecedent and a
        designated node with the negation of the consequent to *b'*, and add a designated node
        with the negation of the antecedent and a designated node with the consequent to *b''*,
        then tick *n*.
        """
        designation = True
        negated     = True
        operator    = Operator.MaterialBiconditional
        branch_level = 2

        def _get_node_targets(self, node: Node, _, /):
            s = self.sentence(node)
            d = self.designation
            return adds(
                group(sdnode( s.lhs, d), sdnode(~s.rhs, d)),
                group(sdnode(~s.lhs, d), sdnode( s.rhs, d)),
            )

    class MaterialBiconditionalUndesignated(MaterialBiconditionalNegatedDesignated):
        """
        From an unticked undesignated material biconditional node *n* on a branch *b*, make
        two new branches *b'* and *b''* from *b*, add an undesignated node with the negation
        of the antecedent and an undesignated node with the consequent to *b'*, and add an
        undesignated node with the antecedent and an undesignated node with the negation of
        the consequent to *b''*, then tick *n*.
        """
        designation = False
        negated     = False

    class MaterialBiconditionalNegatedUndesignated(MaterialBiconditionalDesignated):
        """
        From an undesignated negated material biconditional node *n* on a branch *b*, make
        two branches *b'* and *b''* from *b*, add an undesignated node with the negation of
        the antecendent and an undesignated node with the negation of the consequent to *b'*,
        and add an undesignated node with the antecedent and an undesignated node with the
        consequent to *b''*, then tick *n*.
        """
        designation = False
        negated     = True

    class ConditionalDesignated(MaterialConditionalDesignated):
        """
        This rule functions the same as the corresponding material conditional rule.

        From an unticked designated conditional node *n* on a branch *b*, make two new
        branches *b'* and *b''* from *b*, add a designated node with the negation of
        the antecedent to *b'*, add a designated node with the consequent to *b''*,
        then tick *n*.
        """
        operator = Operator.Conditional

    class ConditionalNegatedDesignated(MaterialConditionalNegatedDesignated):
        """
        This rule functions the same as the corresponding material conditional rule.

        From an unticked designated negated conditional node *n* on a branch *b*, add a
        designated node with the antecedent, and a designated node with the negation of
        the consequent to *b*, then tick *n*.
        """
        operator = Operator.Conditional

    class ConditionalUndesignated(MaterialConditionalUndesignated):
        """
        This rule functions the same as the corresponding material conditional rule.

        From an unticked undesignated conditional node *n* on a branch *b*, add an
        undesignated node with the negation of the antecedent and an undesignated node
        with the consequent to *b*, then tick *n*.
        """
        operator = Operator.Conditional

    class ConditionalNegatedUndesignated(MaterialConditionalNegatedUndesignated):
        """
        This rule functions the same as the corresponding material conditional rule.

        From an unticked undesignated negated conditional node *n* on a branch *b*, make two
        new branches *b'* and *b''* from *b*, add an undesignated node with the antecedent to
        *b'*, and add an undesignated node with the negation of the consequent to *b''*, then
        tick *n*.
        """
        operator = Operator.Conditional

    class BiconditionalDesignated(MaterialBiconditionalDesignated):
        """
        This rule functions the same as the corresponding material biconditional rule.

        From an unticked designated biconditional node *n* on a branch *b*, make two new
        branches *b'* and *b''* from *b*, add a designated node with the negation of the
        antecedent and a designated node with the negation of the consequent to *b'*,
        and add a designated node with the antecedent and a designated node with the
        consequent to *b''*, then tick *n*.
        """
        operator = Operator.Biconditional

    class BiconditionalNegatedDesignated(MaterialBiconditionalNegatedDesignated):
        """
        This rule functions the same as the corresponding material biconditional rule.

        From an unticked designated negated biconditional node *n* on a branch *b*, make two
        branches *b'* and *b''* from *b*, add a designated node with the antecedent and a
        designated node with the negation of the consequent to *b'*, and add a designated node
        with the negation of the antecedent and a designated node with the consequent to *b''*,
        then tick *n*.
        """
        operator = Operator.Biconditional

    class BiconditionalUndesignated(MaterialBiconditionalUndesignated):
        """
        This rule functions the same as the corresponding material biconditional rule.

        From an unticked undesignated material biconditional node *n* on a branch *b*, make
        two new branches *b'* and *b''* from *b*, add an undesignated node with the negation
        of the antecedent and an undesignated node with the consequent to *b'*, and add an
        undesignated node with the antecedent and an undesignated node with the negation of
        the consequent to *b''*, then tick *n*.
        """
        operator = Operator.Biconditional

    class BiconditionalNegatedUndesignated(MaterialBiconditionalNegatedUndesignated):
        """
        This rule functions the same as the corresponding material biconditional rule.

        From an undesignated negated biconditional node *n* on a branch *b*, make two
        branches *b'* and *b''* from *b*, add an undesignated node with the negation of the
        antecendent and an undesignated node with the negation of the consequent to *b'*,
        and add an undesignated node with the antecedent and an undesignated node with the
        consequent to *b''*, then tick *n*.
        """
        operator = Operator.Biconditional

    class ExistentialDesignated(rules.NarrowQuantifierRule, DefaultNodeRule):
        """
        From an unticked designated existential node *n* on a branch *b* quantifying over
        variable *v* into sentence *s*, add a designated node to *b* with the substitution
        into *s* of a new constant not yet appearing on *b* for *v*, then tick *n*.
        """
        designation = True
        quantifier  = Quantifier.Existential
        branch_level = 1

        def _get_node_targets(self, node: Node, branch: Branch,/):
            s = self.sentence(node)
            return adds(
                group(sdnode(branch.new_constant() >> s, self.designation))
            )

    class ExistentialNegatedDesignated(rules.QuantifiedSentenceRule, DefaultNodeRule):
        """
        From an unticked designated negated existential node *n* on a branch *b*,
        quantifying over variable *v* into sentence *s*, add a designated node to *b*
        that universally quantifies over *v* into the negation of *s* (i.e. change
        :s:`~XxFx` to :s:`Lx~Fx`), then tick *n*.
        """
        designation = True
        negated     = True
        quantifier  = Quantifier.Existential
        convert     = Quantifier.Universal
        branch_level = 1

        def _get_node_targets(self, node: Node, _, /):
            v, si = self.sentence(node)[1:]
            return adds(
                group(sdnode(self.convert(v, ~si), self.designation))
            )

    class ExistentialUndesignated(QuantifierFatRule):
        """
        From an undesignated existential node *n* on a branch *b*, for any constant *c* on
        *b* such that the result *r* of substituting *c* for the variable bound by the
        sentence of *n* does not appear on *b*, then add an undesignated node with *r* to *b*.
        If there are no constants yet on *b*, then instantiate with a new constant. The node
        *n* is never ticked.
        """
        designation = False
        quantifier  = Quantifier.Existential
        branch_level = 1

        def _get_constant_nodes(self, node: Node, c: Constant, _, /):
            return group(sdnode(c >> self.sentence(node), self.designation))

    class ExistentialNegatedUndesignated(ExistentialNegatedDesignated):
        """
        From an unticked undesignated negated existential node *n* on a branch *b*,
        quantifying over variable *v* into sentence *s*, add an undesignated node to *b*
        that universally quantifies over *v* into the negation of *s* (e.g. change
        :s:`~XxFx` to :s:`Lx~Fx`), then tick *n*.
        """
        designation = False

    class UniversalDesignated(ExistentialUndesignated):
        """
        From a designated universal node *n* on a branch *b*, for any constant *c* on *b*
        such that the result *r* of substituting *c* for the variable bound by the sentence
        of *n* does not appear on *b*, then add a designated node with *r* to *b*. If there
        are no constants yet on *b*, then instantiate with a new constant. The node *n* is
        never ticked.
        """
        designation = True
        quantifier  = Quantifier.Universal

    class UniversalNegatedDesignated(ExistentialNegatedDesignated):
        """
        From an unticked designated negated universal node *n* on a branch *b*,
        quantifying over variable *v* into sentence *s*, add a designated node to *b*
        with the existential quantifier over *v* into the negation of *s* (e.g. change
        :s:`~LxFx` to :s:`Xx~Fx`), then tick *n*.
        """
        quantifier = Quantifier.Universal
        convert    = Quantifier.Existential

    class UniversalUndesignated(ExistentialDesignated):
        """
        From an unticked undesignated universal node *n* on a branch *b* quantifying over *v*
        into sentence *s*, add an undesignated node to *b* with the result of substituting into
        *s* a constant new to *b* for *v*, then tick *n*.
        """
        designation = False
        quantifier  = Quantifier.Universal

    class UniversalNegatedUndesignated(ExistentialNegatedDesignated):
        """
        From an unticked undesignated negated universal node *n* on a branch *b*,
        quantifying over variable *v* into sentence *s*, add an undesignated node to *b*
        with the existential quantifier over *v* into the negation of *s* (e.g. change
        :s:`~LxFx` to :s:`Xx~Fx`), then tick *n*.
        """
        designation = False
        quantifier  = Quantifier.Universal
        convert     = Quantifier.Existential

    closure_rules = DesignationClosure,

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
