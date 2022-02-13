# -*- coding: utf-8 -*-
# pytableaux, a multi-logic proof generator.
# Copyright (C) 2014-2021 Doug Owings.
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

from tools.abcs import T
name = 'FDE'

class Meta:
    title    = 'First Degree Entailment'
    category = 'Many-valued'
    description = 'Four-valued logic (True, False, Neither, Both)'
    tags = ['many-valued', 'gappy', 'glutty', 'non-modal', 'first-order']
    category_display_order = 10

from errors import ModelValueError
from tools.decorators import abstract, static
from tools.sets import setf, EMPTY_SET
from tools.hybrids import qsetf
from models import BaseModel
from lexicals import Constant, Predicate, Operator as Oper, Quantifier, \
    Sentence, Atomic, Predicated, Quantified, Operated, Argument
from proof.tableaux import (
    Tableau,
    TableauxSystem as BaseSystem,
)
from proof.baserules import (
    BaseClosureRule,
    BaseNodeRule,
    GetNodeTargetsRule,
    OperatedSentenceRule,
    QuantifiedSentenceRule,
    NarrowQuantifierRule,
    ExtendedQuantifierRule,
)
from proof.common import Branch, Node, Target
from proof.filters import NodeFilters

from typing import Any

Identity:  Predicate = Predicate.System.Identity
Existence: Predicate = Predicate.System.Existence

class Model(BaseModel):
    'An FDE Model.'

    #: The set of admissible values for sentences.
    #:
    #: :type: set
    #: :value: {T, B, N, F}
    #: :meta hide-value:
    truth_values = qsetf(('F', 'N', 'B', 'T'))

    #: The set of designated values.
    #:
    #: :type: set
    #: :value: {T, B}
    #: :meta hide-value:
    designated_values = setf({'B', 'T'})

    unassigned_value = 'N'

    nvals = {
        'F': 0    ,
        'N': 0.25 ,
        'B': 0.75 ,
        'T': 1    ,
    }

    cvals = {
        0    : 'F',
        0.25 : 'N',
        0.75 : 'B',
        1    : 'T',
    }

    def __init__(self):

        super().__init__()

        #: A mapping from each predicate to its extension. An extension for an
        #: *n*-ary predicate is a set of *n*-tuples of constants.
        #:
        #: :type: dict
        self.extensions: dict[Predicate, set[tuple[Constant, ...]]] = {}

        #: A map of predicates to their anti-extension.
        #:
        #: :type: dict
        self.anti_extensions: dict[Predicate, set[tuple[Constant, ...]]] = {}

        #: An assignment of each atomic sentence to an admissible truth value.
        #:
        #: :type: dict
        self.atomics: dict[Atomic, Any] = {}

        #: An assignment of each opaque (un-interpreted) sentence to a value.
        #:
        #: :type: dict
        self.opaques: dict[Sentence, Any] = {}

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
                return 'B'
            return 'T'
        if params in anti_extension:
            return 'F'
        return 'N'

    def value_of_existential(self, s: Quantified, /, **kw):
        """
        The value of an existential sentence is the maximum value of the sentences that
        result from replacing each constant for the quantified variable. The ordering of
        the values from least to greatest is: :m:`F`, :m:`N`, :m:`B`, :m:`T`.
        """
        values = {self.value_of(s.unquantify(c), **kw) for c in self.constants}
        return self.cvals[max({self.nvals[value] for value in values})]

    def value_of_universal(self, s: Quantified, /, **kw):
        """
        The value of an universal sentence is the minimum value of the sentences that
        result from replacing each constant for the quantified variable. The ordering of
        the values from least to greatest is: :m:`F`, :m:`N`, :m:`B`, :m:`T`.
        """
        values = {self.value_of(s.unquantify(c), **kw) for c in self.constants}
        return self.cvals[min({self.nvals[value] for value in values})]

    def is_sentence_opaque(self, s: Sentence) -> bool:
        """
        A sentence is opaque if its operator is Necessity or Possibility, or if it is
        a negated sentence whose negatum has the operator Necessity or Possibility.
        """
        return (
            type(s) is Operated and
            s.operator in self.modal_operators
         ) or super().is_sentence_opaque(s)

    def is_countermodel_to(self, argument: Argument) -> bool:
        """
        A model is a countermodel to an argument iff the value of every premise
        is in the set of designated values, and the value of the conclusion
        is not in the set of designated values.
        """
        for premise in argument.premises:
            if self.value_of(premise) not in self.designated_values:
                return False
        return self.value_of(argument.conclusion) not in self.designated_values

    def get_data(self) -> dict[str, dict]:
        data: dict[str, dict] = {}
        data.update({
            'Atomics' : {
                'description'     : 'atomic values',
                'datatype'        : 'function',
                'typehint'        : 'truth_function',
                'input_datatype'  : 'sentence',
                'output_datatype' : 'string',
                'output_typehint' : 'truth_value',
                'symbol'          : 'v',
                'values'          : [
                    {
                        'input'  : s,
                        'output' : self.atomics[s]
                    }
                    for s in sorted(self.atomics)
                ]
            },
            'Opaques' : {
                'description'     : 'opaque values',
                'datatype'        : 'function',
                'typehint'        : 'truth_function',
                'input_datatype'  : 'sentence',
                'output_datatype' : 'string',
                'output_typehint' : 'truth_value',
                'symbol'          : 'v',
                'values'          : [
                    {
                        'input'  : s,
                        'output' : self.opaques[s]
                    }
                    for s in sorted(self.opaques)
                ]
            },
            'Predicates' : {
                'description' : 'predicate extensions/anti-extensions',
                'in_summary'  : True,
                'datatype'    : 'list',
                'values'      : list()
            }
        })
        for predicate in sorted(list(self.predicates)):
            pdata = [
                {
                    'description'     : 'predicate extension',
                    'datatype'        : 'function',
                    'typehint'        : 'extension',
                    'input_datatype'  : 'predicate',
                    'output_datatype' : 'set',
                    'output_typehint' : 'extension',
                    'symbol'          : 'P+',
                    'values'          : [
                        {
                            'input'  : predicate,
                            'output' : self.get_extension(predicate),
                        }
                    ]
                },
                {
                    'description'     : 'predicate anti-extension',
                    'datatype'        : 'function',
                    'typehint'        : 'extension',
                    'input_datatype'  : 'predicate',
                    'output_datatype' : 'set',
                    'output_typehint' : 'extension',
                    'symbol'          : 'P-',
                    'values'          : [
                        {
                            'input'  : predicate,
                            'output' : self.get_anti_extension(predicate),
                        }
                    ]
                }
            ]
            data['Predicates']['values'].extend(pdata)
        return data

    def read_branch(self, branch: Branch):
        for node in branch:
            s: Sentence = node.get('sentence')
            if not s:
                continue
            self._collect_node(node)
            is_literal = self.is_sentence_literal(s)
            is_opaque = self.is_sentence_opaque(s)
            if is_literal or is_opaque:
                if type(s) is Operated and s.operator == Oper.Negation:
                    # If the sentence is negated, set the value of the negatum
                    s = s.lhs
                    if node['designated']:
                        if branch.has({'sentence': s, 'designated': True}):
                            # If the node is designated, and the negatum is
                            # also designated on b, the value is B
                            value = 'B'
                        else:
                            # If the node is designated, but the negatum is
                            # not also designated on b, the value is F
                            value = 'F'
                    else:
                        if branch.has({'sentence': s, 'designated': False}):
                            # If the node is undesignated, and the negatum is
                            # also undesignated on b, the value is N
                            value = 'N'
                        else:
                            # If the node is undesignated, but the negatum is
                            # not also undesignated on b, the value is T
                            value = 'T'
                else:
                    # If the sentence is unnegated, set the value of the sentence
                    if node['designated']:
                        if branch.has({'sentence': s.negate(), 'designated': True}):
                            # If the node is designated, and its negation is
                            # also designated on b, the value is B
                            value = 'B'
                        else:
                            # If the node is designated, but the negation is
                            # not also designated on b, the value is T
                            value = 'T'
                    else:
                        if branch.has({'sentence': s.negate(), 'designated': False}):
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
        self.finish()

    def _collect_node(self, node: Node):
        s: Sentence = node.get('sentence')
        if s is not None:
            self.predicates.update(s.predicates)
            self.all_atomics.update(s.atomics)
            self.constants.update(s.constants)

    def finish(self):
        # TODO: consider augmenting the logic with Identity and Existence predicate
        #       restrictions. In that case, new tableaux rules need to be written.
        for s in self.all_atomics:
            if s not in self.atomics:
                self.set_literal_value(s, self.unassigned_value)

    def set_literal_value(self, s: Sentence, value):
        if value not in self.truth_values:
            self._raise_value('UnknownForSentence', value, s)
        cls = s.TYPE.cls
        if self.is_sentence_opaque(s):
            self.set_opaque_value(s, value)
        elif cls is Operated and s.operator is Oper.Negation:
            self.set_literal_value(
                s.lhs,
                self.truth_function(s.operator, value)
            )
        elif cls is Atomic:
            self.set_atomic_value(s, value)
        elif cls is Predicated:
            self.set_predicated_value(s, value)
        else:
            raise NotImplementedError()

    def set_opaque_value(self, s: Sentence, value):
        if value not in self.truth_values:
            self._raise_value('UnknownForSentence', value, s)
        if s in self.opaques and self.opaques[s] != value:
            self._raise_value('ConflictForSentence', value, s)
        # We might have a quantified opaque sentence, in which case we will need
        # to still check every subsitution, so we want the constants, as well
        # as other lexical items.
        self.predicates.update(s.predicates)
        self.all_atomics.update(s.atomics)
        self.constants.update(s.constants)
        self.opaques[s] = value
        
    def set_atomic_value(self, s: Atomic, value):
        if value not in self.truth_values:
            self._raise_value('UnknownForSentence', value, s)
        if s in self.atomics and self.atomics[s] != value:
            self._raise_value('ConflictForSentence', value, s)
        self.atomics[s] = value

    def set_predicated_value(self, s: Predicated, value):
        if value not in self.truth_values:
            self._raise_value('UnknownForSentence', value, s)
        predicate = s.predicate
        params = s.params
        for param in params:
            if param.is_constant:
                self.constants.add(param)
        extension = self.get_extension(predicate)
        anti_extension = self.get_anti_extension(predicate)
        if value == 'N':
            if params in extension:
                self._raise_value('ConflictForExtension', value, params)
            if params in anti_extension:
                self._raise_value('ConflictForAntiExtension', value, params)
        elif value == 'T':
            if params in anti_extension:
                self._raise_value('ConflictForAntiExtension', value, params)
            extension.add(params)
        elif value == 'F':
            if params in extension:
                self._raise_value('ConflictForExtension', value, params)
            anti_extension.add(params)
        elif value == 'B':
            extension.add(params)
            anti_extension.add(params)
        self.predicates.add(predicate)

    def get_extension(self, pred: Predicate) -> set[tuple[Constant, ...]]:
        if pred not in self.extensions:
            self.extensions[pred] = set()
            self.predicates.add(pred)
        return self.extensions[pred]

    def get_anti_extension(self, pred: Predicate) -> set[tuple[Constant, ...]]:
        if pred not in self.anti_extensions:
            self.anti_extensions[pred] = set()
            self.predicates.add(pred)
        return self.anti_extensions[pred]

    def value_of_atomic(self, s: Sentence, **kw):
        return self.atomics.get(s, self.unassigned_value)

    def value_of_opaque(self, s: Sentence, **kw):
        return self.opaques.get(s, self.unassigned_value)

    def value_of_quantified(self, s: Quantified, **kw):
        try:
            q = s.quantifier
        except AttributeError:
            raise TypeError
        if q == Quantifier.Existential:
            return self.value_of_existential(s, **kw)
        elif q == Quantifier.Universal:
            return self.value_of_universal(s, **kw)
        return super().value_of_quantified(s, **kw)

    def truth_function(self, operator: Oper, a, b = None):

        # Define as generically as possible for reuse.
        if operator == Oper.Assertion:
            return a
        if operator == Oper.Negation:
            if a == 'F':
                return 'T'
            if a == 'T':
                return 'F'
            return a
        elif operator == Oper.Conjunction:
            return self.cvals[min(self.nvals[a], self.nvals[b])]
        elif operator == Oper.Disjunction:
            return self.cvals[max(self.nvals[a], self.nvals[b])]
        elif operator == Oper.MaterialConditional:
            return self.truth_function(
                Oper.Disjunction,
                self.truth_function(Oper.Negation, a),
                b
            )
        elif operator == Oper.MaterialBiconditional:
            return self.truth_function(
                Oper.Conjunction,
                self.truth_function(Oper.MaterialConditional, a, b),
                self.truth_function(Oper.MaterialConditional, b, a)
            )
        elif operator == Oper.Conditional:
            return self.truth_function(Oper.MaterialConditional, a, b)
        elif operator == Oper.Biconditional:
            return self.truth_function(
                Oper.Conjunction,
                self.truth_function(Oper.Conditional, a, b),
                self.truth_function(Oper.Conditional, b, a)
            )
        else:
            raise NotImplementedError

    _error_formats = {
        ModelValueError: {
            'UnknownForSentence':
                'Non-existent value {0} for sentence {1}',
            'ConflictForSentence':
                'Inconsistent value {0} for sentence {1}',
            'ConflictForExtension':
                'Cannot set value {0} for tuple {1} already in extension',
            'ConflictForAnitExtension':
                'Cannot set value {0} for tuple {1} already in anti-extension',
        },
    }

    def _raise_value(self, fmt, *args):
        ErrorClass = ModelValueError
        if fmt in self._error_formats[ErrorClass]:
            fmt = self._error_formats[ErrorClass][fmt]
        raise ErrorClass(fmt, *(str(arg) for arg in args))

@static
class TableauxSystem(BaseSystem):
    """
    Nodes for FDE have a boolean *designation* property, and a branch is closed iff
    the same sentence appears on both a designated and undesignated node. This allows
    for both a sentence and its negation to appear as designated (xor undesignated)
    on an open branch.
    """

    # operator => negated => designated
    branchables = {
        Oper.Negation: {
            True: {True: 0, False: 0},
        },
        Oper.Assertion: {
            False : {True: 0, False: 0},
            True  : {True: 0, False: 0},
        },
        Oper.Conjunction: {
            False : {True: 0, False: 1},
            True  : {True: 1, False: 0},
        },
        Oper.Disjunction: {
            False : {True: 1, False: 0},
            True  : {True: 0, False: 1},
        },
        Oper.MaterialConditional: {
            False : {True: 1, False: 0},
            True  : {True: 0, False: 1},
        },
        Oper.MaterialBiconditional: {
            False : {True: 1, False: 1},
            True  : {True: 1, False: 1},
        },
        Oper.Conditional: {
            False : {True: 1, False: 0},
            True  : {True: 0, False: 1},
        },
        Oper.Biconditional: {
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
        add = tab.branch().append
        for premise in arg.premises:
            add(sdnode(premise, True))
        add(sdnode(arg.conclusion, False))

    @classmethod
    def branching_complexity(cls, node: Node, /):
        s: Sentence = node.get('sentence')
        if s is None:
            return 0
        d: bool = node['designated']
        last_is_negated = False
        complexity = 0
        for oper in s.operators:
            if oper is Oper.Negation:
                if not last_is_negated:
                    last_is_negated = True
                    continue
            if oper in cls.branchables:
                complexity += cls.branchables[oper][last_is_negated][d]
                last_is_negated = False
        return complexity

class DefaultNodeRule(GetNodeTargetsRule):
    NodeFilters = NodeFilters.Designation,
    designation: bool|None = None

class OperSentenceRule(OperatedSentenceRule, DefaultNodeRule):
    pass
class QuantSentenceRule(QuantifiedSentenceRule, DefaultNodeRule):
    pass

class QuantifierSkinnyRule(NarrowQuantifierRule, DefaultNodeRule):
    pass
class QuantifierFatRule(ExtendedQuantifierRule, DefaultNodeRule):
    pass

def sdnode(s: Sentence, d: bool):
    return dict(sentence = s, designated = d)

def group(*items: T) -> tuple[T, ...]:
    return items

def adds(*groups: tuple[dict, ...]):
    return dict(adds = groups)

class ConjunctionReducingRule(OperSentenceRule):

    conjunct_op: Oper
    branch_level = 1

    def _get_node_targets(self, node: Node, _):
        oper = self.conjunct_op
        lhs, rhs = self.sentence(node)
        s = oper((lhs, rhs)) & oper((rhs, lhs))
        if self.negated:
            s = ~s
        return adds(group(sdnode(s, self.designation)))

@static
class TabRules:
    """
    In general, rules for connectives consist of four rules per connective:
    a designated rule, an undesignated rule, a negated designated rule, and a negated
    undesignated rule. The special case of negation has a total of two rules which apply
    to double negation only, one designated rule, and one undesignated rule.
    """

    class DesignationClosure(BaseClosureRule):
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

        def example_nodes(self):
            s = Atomic.first()
            return sdnode(s, True), sdnode(s, False)

        # private util

        def _find_closing_node(self, node: Node, branch: Branch, /):
            s = self.sentence(node)
            if s is not None:
                return branch.find(sdnode(s, not node['designated']))
            
    class DoubleNegationDesignated(OperSentenceRule):
        """
        From an unticked designated negated negation node *n* on a branch *b*,
        add a designated node to *b* with the double-negatum of *n*, then tick *n*.
        """

        designation = True
        negated     = True
        operator    = Oper.Negation
        branch_level = 1

        def _get_node_targets(self, node: Node, _):
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

    class AssertionDesignated(OperSentenceRule):
        """
        From an unticked, designated, assertion node *n* on a branch *b*, add a designated
        node to *b* with the operand of *b*, then tick *n*.
        """
        designation = True
        operator    = Oper.Assertion
        branch_level = 1

        def _get_node_targets(self, node: Node, _):
            return adds(
                group(sdnode(self.sentence(node).lhs, self.designation))
            )

    class AssertionUndesignated(AssertionDesignated):
        """
        From an unticked, undesignated, assertion node *n* on a branch *b*, add an undesignated
        node to *b* with the operand of *n*, then tick *n*.
        """
        designation = False

    class AssertionNegatedDesignated(OperSentenceRule):
        """
        From an unticked, designated, negated assertion node *n* on branch *b*, add a designated
        node to *b* with the negation of the assertion's operand to *b*, then tick *n*.
        """
        designation = True
        negated     = True
        operator    = Oper.Assertion
        branch_level = 1

        def _get_node_targets(self, node: Node, _):
            return adds(
                group(sdnode(~self.sentence(node).lhs, self.designation))
            )

    class AssertionNegatedUndesignated(AssertionNegatedDesignated):
        """
        From an unticked, undesignated, negated assertion node *n* on branch *b*, add an undesignated
        node to *b* with the negation of the assertion's operand to *b*, then tick *n*.
        """
        designation = False

    class ConjunctionDesignated(OperSentenceRule):
        """
        From an unticked designated conjunction node *n* on a branch *b*, for each conjunct
        *c*, add a designated node with *c* to *b*, then tick *n*.
        """
        designation = True
        operator    = Oper.Conjunction
        branch_level = 1

        def _get_node_targets(self, node: Node, _):
            s = self.sentence(node)
            d = self.designation
            return adds(
                group(sdnode(s.lhs, d), sdnode(s.rhs, d))
            )

    class ConjunctionNegatedDesignated(OperSentenceRule):
        """
        From an unticked designated negated conjunction node *n* on a branch *b*,
        for each conjunct *c*, make a new branch *b'* from *b* and add a designated
        node with the negation of *c* to *b'*, then tick *n*.
        """
        designation = True
        negated     = True
        operator    = Oper.Conjunction
        branch_level = 2

        def _get_node_targets(self, node: Node, _):
            s = self.sentence(node)
            d = self.designation
            return adds(
                group(sdnode(~s.lhs, d)),
                group(sdnode(~s.rhs, d)),
            )

    class ConjunctionUndesignated(OperSentenceRule):
        """
        From an unticked undesignated conjunction node *n* on a branch *b*,
        for each conjunct *c*, make a new branch *b'* from *b* and add an
        undesignated node with *c* to *b'*, then tick *n*.
        """
        designation = False
        operator    = Oper.Conjunction
        branch_level = 2

        def _get_node_targets(self, node: Node, _):
            s = self.sentence(node)
            d = self.designation
            return adds(
                group(sdnode(s.lhs, d)),
                group(sdnode(s.rhs, d)),
            )

    class ConjunctionNegatedUndesignated(OperSentenceRule):
        """
        From an unticked undesignated negated conjunction node *n* on a branch
        *b*, for each conjunct *c*, add an undesignated node with the negation
        of *c* to *b*, then tick *n*.
        """
        designation = False
        negated     = True
        operator    = Oper.Conjunction
        branch_level = 1

        def _get_node_targets(self, node: Node, _):
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
        operator    = Oper.Disjunction

    class DisjunctionNegatedDesignated(ConjunctionNegatedUndesignated):
        """
        From an unticked designated negated disjunction node *n* on a branch *b*, for each disjunct
        *d*, add a designated node with the negation of *d* to *b*, then tick *n*.
        """
        designation = True
        operator    = Oper.Disjunction

    class DisjunctionUndesignated(ConjunctionDesignated):
        """
        From an unticked undesignated disjunction node *n* on a branch *b*, for each disjunct
        *d*, add an undesignated node with *d* to *b*, then tick *n*.
        """
        designation = False
        operator    = Oper.Disjunction

    class DisjunctionNegatedUndesignated(ConjunctionNegatedDesignated):
        """
        From an unticked undesignated negated disjunction node *n* on a branch *b*, for each disjunct
        *d*, make a new branch *b'* from *b* and add an undesignated node with the negation of *d* to
        *b'*, then tick *n*.
        """
        designation = False
        operator    = Oper.Disjunction

    class MaterialConditionalDesignated(OperSentenceRule):
        """
        From an unticked designated material conditional node *n* on a branch *b*, make
        two new branches *b'* and *b''* from *b*, add a designated node with the negation
        of the antecedent to *b'*, add a designated node with the consequent to *b''*,
        then tick *n*.
        """
        designation = True
        operator    = Oper.MaterialConditional
        branch_level = 2

        def _get_node_targets(self, node: Node, _):
            s = self.sentence(node)
            d = self.designation
            return adds(
                group(sdnode(~s.lhs, d)),
                group(sdnode( s.rhs, d)),
            )

    class MaterialConditionalNegatedDesignated(OperSentenceRule):
        """
        From an unticked designated negated material conditional node *n* on a
        branch *b*, add a designated node with the antecedent, and a designated
        node with the negation of the consequent to *b*, then tick *n*.
        """
        designation = True
        negated     = True
        operator    = Oper.MaterialConditional
        branch_level = 1

        def _get_node_targets(self, node: Node, _):
            s = self.sentence(node)
            d = self.designation
            return adds(
                group(sdnode(s.lhs, d), sdnode(~s.rhs, d))
            )

    class MaterialConditionalUndesignated(OperSentenceRule):
        """
        From an unticked undesignated material conditional node *n* on a branch *b*, add
        an undesignated node with the negation of the antecedent and an undesignated node
        with the consequent to *b*, then tick *n*.
        """
        designation = False
        operator    = Oper.MaterialConditional
        branch_level = 1

        def _get_node_targets(self, node: Node, _):
            s = self.sentence(node)
            d = self.designation
            return adds(
                group(sdnode(~s.lhs, d), sdnode(s.rhs, d))
            )

    class MaterialConditionalNegatedUndesignated(OperSentenceRule):
        """
        From an unticked undesignated negated material conditional node *n* on a branch *b*, make
        two new branches *b'* and *b''* from *b*, add an undesignated node with the antecedent to
        *b'*, and add an undesignated node with the negation of the consequent to *b''*, then
        tick *n*.
        """
        designation = False
        negated     = True
        operator    = Oper.MaterialConditional
        branch_level = 2

        def _get_node_targets(self, node: Node, _):
            s = self.sentence(node)
            d = self.designation
            return adds(
                group(sdnode( s.lhs, d)),
                group(sdnode(~s.rhs, d)),
            )

    class MaterialBiconditionalDesignated(OperSentenceRule):
        """
        From an unticked designated material biconditional node *n* on a branch *b*, make
        two new branches *b'* and *b''* from *b*, add a designated node with the negation
        of the antecedent and a designated node with the negation of the consequent to *b'*,
        and add a designated node with the antecedent and a designated node with the
        consequent to *b''*, then tick *n*.
        """
        designation = True
        operator    = Oper.MaterialBiconditional
        branch_level = 2

        def _get_node_targets(self, node: Node, _):
            s = self.sentence(node)
            d = self.designation
            return adds(
                group(sdnode(~s.lhs, d), sdnode(~s.rhs, d)),
                group(sdnode( s.rhs, d), sdnode( s.lhs, d)),
            )

    class MaterialBiconditionalNegatedDesignated(OperSentenceRule):
        """
        From an unticked designated negated material biconditional node *n* on a branch *b*, make
        two branches *b'* and *b''* from *b*, add a designated node with the antecedent and a
        designated node with the negation of the consequent to *b'*, and add a designated node
        with the negation of the antecedent and a designated node with the consequent to *b''*,
        then tick *n*.
        """
        designation = True
        negated     = True
        operator    = Oper.MaterialBiconditional
        branch_level = 2

        def _get_node_targets(self, node: Node, _):
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
        operator = Oper.Conditional

    class ConditionalNegatedDesignated(MaterialConditionalNegatedDesignated):
        """
        This rule functions the same as the corresponding material conditional rule.

        From an unticked designated negated conditional node *n* on a branch *b*, add a
        designated node with the antecedent, and a designated node with the negation of
        the consequent to *b*, then tick *n*.
        """
        operator = Oper.Conditional

    class ConditionalUndesignated(MaterialConditionalUndesignated):
        """
        This rule functions the same as the corresponding material conditional rule.

        From an unticked undesignated conditional node *n* on a branch *b*, add an
        undesignated node with the negation of the antecedent and an undesignated node
        with the consequent to *b*, then tick *n*.
        """
        operator = Oper.Conditional

    class ConditionalNegatedUndesignated(MaterialConditionalNegatedUndesignated):
        """
        This rule functions the same as the corresponding material conditional rule.

        From an unticked undesignated negated conditional node *n* on a branch *b*, make two
        new branches *b'* and *b''* from *b*, add an undesignated node with the antecedent to
        *b'*, and add an undesignated node with the negation of the consequent to *b''*, then
        tick *n*.
        """
        operator = Oper.Conditional

    class BiconditionalDesignated(MaterialBiconditionalDesignated):
        """
        This rule functions the same as the corresponding material biconditional rule.

        From an unticked designated biconditional node *n* on a branch *b*, make two new
        branches *b'* and *b''* from *b*, add a designated node with the negation of the
        antecedent and a designated node with the negation of the consequent to *b'*,
        and add a designated node with the antecedent and a designated node with the
        consequent to *b''*, then tick *n*.
        """
        operator = Oper.Biconditional

    class BiconditionalNegatedDesignated(MaterialBiconditionalNegatedDesignated):
        """
        This rule functions the same as the corresponding material biconditional rule.

        From an unticked designated negated biconditional node *n* on a branch *b*, make two
        branches *b'* and *b''* from *b*, add a designated node with the antecedent and a
        designated node with the negation of the consequent to *b'*, and add a designated node
        with the negation of the antecedent and a designated node with the consequent to *b''*,
        then tick *n*.
        """
        operator = Oper.Biconditional

    class BiconditionalUndesignated(MaterialBiconditionalUndesignated):
        """
        This rule functions the same as the corresponding material biconditional rule.

        From an unticked undesignated material biconditional node *n* on a branch *b*, make
        two new branches *b'* and *b''* from *b*, add an undesignated node with the negation
        of the antecedent and an undesignated node with the consequent to *b'*, and add an
        undesignated node with the antecedent and an undesignated node with the negation of
        the consequent to *b''*, then tick *n*.
        """
        operator = Oper.Biconditional

    class BiconditionalNegatedUndesignated(MaterialBiconditionalNegatedUndesignated):
        """
        This rule functions the same as the corresponding material biconditional rule.

        From an undesignated negated biconditional node *n* on a branch *b*, make two
        branches *b'* and *b''* from *b*, add an undesignated node with the negation of the
        antecendent and an undesignated node with the negation of the consequent to *b'*,
        and add an undesignated node with the antecedent and an undesignated node with the
        consequent to *b''*, then tick *n*.
        """
        operator = Oper.Biconditional

    class ExistentialDesignated(QuantifierSkinnyRule):
        """
        From an unticked designated existential node *n* on a branch *b* quantifying over
        variable *v* into sentence *s*, add a designated node to *b* with the substitution
        into *s* of a new constant not yet appearing on *b* for *v*, then tick *n*.
        """
        designation = True
        quantifier  = Quantifier.Existential
        branch_level = 1

        def _get_node_targets(self, node: Node, branch: Branch):
            s = self.sentence(node)
            c = branch.new_constant()
            return adds(
                group(sdnode(s.unquantify(c), self.designation))
            )

    class ExistentialNegatedDesignated(QuantSentenceRule):
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

        def _get_node_targets(self, node: Node, _):
            s = self.sentence(node)
            sq = self.convert(s.variable, ~s.sentence)
            return adds(
                group(sdnode(sq, self.designation))
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
            s = self.sentence(node)
            return sdnode(s.unquantify(c), self.designation),

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

    closure_rules = (DesignationClosure,)

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
