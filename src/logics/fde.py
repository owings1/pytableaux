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
name = 'FDE'

class Meta(object):
    title    = 'First Degree Entailment'
    category = 'Many-valued'
    description = 'Four-valued logic (True, False, Neither, Both)'
    tags = ['many-valued', 'gappy', 'glutty', 'non-modal', 'first-order']
    category_display_order = 10

from models import BaseModel
from lexicals import Atomic, Operated, Quantified, Predicate, Operator as Oper, Quantifier
from proof.tableaux import TableauxSystem as BaseSystem, Rule
from proof.rules import AllConstantsStoppingRule, ClosureRule, FilterNodeRule, \
    NewConstantStoppingRule
from proof.common import Branch, Node, Filters, Target
from proof.helpers import AdzHelper, FilterHelper, clshelpers
from errors import ModelValueError

Identity = Predicate.Identity
Existence = Predicate.Existence

class Model(BaseModel):
    """
    An FDE model 
    """

    #: Ordered truth values.
    truth_values_list = ['F', 'N', 'B', 'T']

    #: The set of admissible values for sentences.
    #:
    #: :type: set
    #: :value: {T, B, N, F}
    #: :meta hide-value:
    truth_values = set(truth_values_list)

    #: The set of designated values.
    #:
    #: :type: set
    #: :value: {T, B}
    #: :meta hide-value:
    designated_values = {'B', 'T'}


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
        self.extensions = {}

        #: A map of predicates to their anti-extension.
        #:
        #: :type: dict
        self.anti_extensions = {}

        #: An assignment of each atomic sentence to an admissible truth value.
        #:
        #: :type: dict
        self.atomics = {}

        #: An assignment of each opaque (un-interpreted) sentence to a value.
        #:
        #: :type: dict
        self.opaques = {}

        #: Track set of atomics for performance.
        self.all_atomics = set()
        #: Track set of constants for performance.
        self.constants = set()
        #: Track set of predicates for performance.
        self.predicates = set()

    def value_of_predicated(self, sentence, **kw):
        params = sentence.params
        predicate = sentence.predicate
        extension = self.get_extension(predicate)
        anti_extension = self.get_anti_extension(predicate)
        if params in extension and params in anti_extension:
            return 'B'
        elif params in extension:
            return 'T'
        elif params in anti_extension:
            return 'F'
        return 'N'

    def value_of_existential(self, sentence, **kw):
        """
        The value of an existential sentence is the maximum value of the sentences that
        result from replacing each constant for the quantified variable. The ordering of
        the values from least to greatest is: :m:`F`, :m:`N`, :m:`B`, :m:`T`.
        """
        v = sentence.variable
        si = sentence.sentence
        values = {self.value_of(si.substitute(c, v), **kw) for c in self.constants}
        return self.cvals[max({self.nvals[value] for value in values})]

    def value_of_universal(self, sentence, **kw):
        """
        The value of an universal sentence is the minimum value of the sentences that
        result from replacing each constant for the quantified variable. The ordering of
        the values from least to greatest is: :m:`F`, :m:`N`, :m:`B`, :m:`T`.
        """
        v = sentence.variable
        si = sentence.sentence
        values = {self.value_of(si.substitute(c, v), **kw) for c in self.constants}
        return self.cvals[min({self.nvals[value] for value in values})]

    def is_sentence_opaque(self, sentence):
        """
        A sentence is opaque if its operator is Necessity or Possibility, or if it is
        a negated sentence whose negatum has the operator Necessity or Possibility.
        """
        if sentence.operator in self.modal_operators:
            return True
        return super().is_sentence_opaque(sentence)

    def is_countermodel_to(self, argument):
        """
        A model is a countermodel to an argument iff the value of every premise
        is in the set of designated values, and the value of the conclusion
        is not in the set of designated values.
        """
        for premise in argument.premises:
            if self.value_of(premise) not in self.designated_values:
                return False
        return self.value_of(argument.conclusion) not in self.designated_values

    def get_data(self):
        data = dict()
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
                        'input'  : sentence,
                        'output' : self.atomics[sentence]
                    }
                    for sentence in sorted(self.atomics)
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
                        'input'  : sentence,
                        'output' : self.opaques[sentence]
                    }
                    for sentence in sorted(self.opaques)
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

    def read_branch(self, branch):
        for node in branch:
            if node.has('sentence'):
                self._collect_node(node)
                sentence = node['sentence']
                is_literal = self.is_sentence_literal(sentence)
                is_opaque = self.is_sentence_opaque(sentence)
                if is_literal or is_opaque:
                    if sentence.operator == Oper.Negation:
                        # If the sentence is negated, set the value of the negatum
                        sentence = sentence.negatum
                        if node['designated']:
                            if branch.has({'sentence': sentence, 'designated': True}):
                                # If the node is designated, and the negatum is
                                # also designated on b, the value is B
                                value = 'B'
                            else:
                                # If the node is designated, but the negatum is
                                # not also designated on b, the value is F
                                value = 'F'
                        else:
                            if branch.has({'sentence': sentence, 'designated': False}):
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
                            if branch.has({'sentence': sentence.negate(), 'designated': True}):
                                # If the node is designated, and its negation is
                                # also designated on b, the value is B
                                value = 'B'
                            else:
                                # If the node is designated, but the negation is
                                # not also designated on b, the value is T
                                value = 'T'
                        else:
                            if branch.has({'sentence': sentence.negate(), 'designated': False}):
                                # If the node is undesignated, and its negation is
                                # also undesignated on b, the value is N
                                value = 'N'
                            else:
                                # If the node is undesginated, but the negation is
                                # not also undesignated on b, the value is F
                                value = 'F'
                    if is_opaque:
                        self.set_opaque_value(sentence, value)
                    else:
                        self.set_literal_value(sentence, value)
        self.finish()
        return self

    def _collect_node(self, node):
        s = node.get('sentence')
        if s:
            self.predicates.update(s.predicates)
            self.all_atomics.update(s.atomics)
            self.constants.update(s.constants)

    def finish(self):
        # TODO: consider augmenting the logic with Identity and Existence predicate
        #       restrictions. In that case, new tableaux rules need to be written.
        for s in self.all_atomics:
            if s not in self.atomics:
                self.set_literal_value(s, self.unassigned_value)
        pass

    def is_sentence_literal(self, sentence):
        if sentence.operator == Oper.Negation and self.is_sentence_opaque(sentence.operand):
            return True
        return sentence.is_literal

    def set_literal_value(self, sentence, value):
        if value not in self.truth_values:
            self._raise_value('UnknownForSentence', value, sentence)
        if self.is_sentence_opaque(sentence):
            self.set_opaque_value(sentence, value)
        elif sentence.is_operated and sentence.operator == Oper.Negation:
            self.set_literal_value(sentence.operand, self.truth_function(Oper.Negation, value))
        elif sentence.is_atomic:
            self.set_atomic_value(sentence, value)
        elif sentence.is_predicated:
            self.set_predicated_value(sentence, value)
        else:
            raise NotImplementedError()

    def set_opaque_value(self, sentence, value):
        if value not in self.truth_values:
            self._raise_value('UnknownForSentence', value, sentence)
        if sentence in self.opaques and self.opaques[sentence] != value:
            self._raise_value('ConflictForSentence', value, sentence)
        # We might have a quantified opaque sentence, in which case we will need
        # to still check every subsitution, so we want the constants, as well
        # as other lexical items.
        self.predicates.update(sentence.predicates)
        self.all_atomics.update(sentence.atomics)
        self.constants.update(sentence.constants)
        self.opaques[sentence] = value
        
    def set_atomic_value(self, sentence, value):
        if value not in self.truth_values:
            self._raise_value('UnknownForSentence', value, sentence)
        if sentence in self.atomics and self.atomics[sentence] != value:
            self._raise_value('ConflictForSentence', value, sentence)
        self.atomics[sentence] = value

    def set_predicated_value(self, sentence, value):
        if value not in self.truth_values:
            self._raise_value('UnknownForSentence', value, sentence)
        predicate = sentence.predicate
        params = sentence.params
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

    def get_extension(self, predicate):
        name = predicate.name
        if name not in self.extensions:
            self.extensions[name] = set()
            self.predicates.add(predicate)
        return self.extensions[name]

    def get_anti_extension(self, predicate):
        name = predicate.name
        if name not in self.anti_extensions:
            self.anti_extensions[name] = set()
            self.predicates.add(predicate)
        return self.anti_extensions[name]

    def value_of_atomic(self, sentence, **kw):
        if sentence in self.atomics:
            return self.atomics[sentence]
        return self.unassigned_value

    def value_of_opaque(self, sentence, **kw):
        if sentence in self.opaques:
            return self.opaques[sentence]
        return self.unassigned_value

    def value_of_quantified(self, sentence, **kw):
        q = sentence.quantifier
        if q == Quantifier.Existential:
            return self.value_of_existential(sentence, **kw)
        elif q == Quantifier.Universal:
            return self.value_of_universal(sentence, **kw)
        return super().value_of_quantified(sentence, **kw)

    def truth_function(self, operator, a, b=None):

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
            return self.truth_function(Oper.Disjunction, self.truth_function(Oper.Negation, a), b)
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
            raise NotImplementedError()

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
    def build_trunk(cls, tableau, argument):
        """
        To build the trunk for an argument, add a designated node for each premise, and
        an undesignated node for the conclusion.
        """
        branch = tableau.branch()
        for premise in argument.premises:
            branch.add({'sentence': premise, 'designated': True, 'world': None})
        branch.add({'sentence' : argument.conclusion, 'designated': False, 'world': None})

    @classmethod
    def branching_complexity(cls, node):
        sentence = node.get('sentence')
        if not sentence:
            return 0
        designated = node['designated']
        last_is_negated = False
        complexity = 0
        # operators = list(sentence.operators)
        # while len(operators):
        #     operator = operators.pop(0)
        for operator in sentence.operators:
            if operator == Oper.Negation:
                #if last_is_negated:
                #    last_is_negated = False
                #    continue
                #last_is_negated = True
                if not last_is_negated:
                    last_is_negated = True
                    continue
            if operator in cls.branchables:
                complexity += cls.branchables[operator][last_is_negated][designated]
                last_is_negated = False
        return complexity


@FilterHelper.clsfilters(
    designation = Filters.Node.Designation,
    sentence    = Filters.Node.Sentence,
)
# @clshelpers(nf = FilterHelper)
class DefaultRule(Rule):
    Helpers = (FilterHelper,)
    # FilterHelper
    # ----------------
    ignore_ticked = True
    # Filters.Node.Sentence
    negated = operator = quantifier = predicate = None
    # Filters.Node.Designation
    designation = None

    def sentence(self, node: Node):
        """
        :overrides: Rule
        """
        return self.nf.filters.sentence.get(node)

    def example_nodes(self):
        """
        :implements: Rule
        """
        return (self.nf.example_node(),)

# @clshelpers(nf = FilterHelper)
class GetNodeTargets(Rule):
    Helpers = (FilterHelper,)
    # :implements: Rule, delegates to _get_node_targets
    @FilterHelper.node_targets
    def _get_targets(self, node: Node, branch: Branch):
        return self._get_node_targets(node, branch)
    # :abstract:
    def _get_node_targets(self, node: Node, branch: Branch):
        raise NotImplementedError()

# @clshelpers()
class DefaultNodeRule(GetNodeTargets, DefaultRule, AdzHelper.ClosureScore, AdzHelper.Apply):
    pass

class OldDefaultNodeRule(FilterNodeRule):

    ticking = True

    def _apply(self, target):
        self.adz._apply(target)

    def score_candidate(self, target):
        return self.adz.closure_score(target)

class DefaultNewConstantRule(OldDefaultNodeRule, NewConstantStoppingRule):

    def score_candidate(self, target):
        return -1 * self.tableau.branching_complexity(target.node)

class DefaultAllConstantsRule(OldDefaultNodeRule, AllConstantsStoppingRule):

    ticking = False

    def score_candidate(self, target):
        if target.get('flag'):
            return 1
        if self.adz.closure_score(target) == 1:
            return 1
        node_apply_count = self.node_application_count(target.node, target.branch)
        return float(1 / (node_apply_count + 1))

class ConjunctionReducingRule(DefaultNodeRule):

    branch_level = 1

    conjunct_op = NotImplemented

    def _get_node_targets(self, node, branch):

        if self.conjunct_op is NotImplemented:
            raise NotImplementedError()

        lhs, rhs = self.sentence(node)
        cond1 = Operated(self.conjunct_op, (lhs, rhs))
        cond2 = Operated(self.conjunct_op, (rhs, lhs))
        sc = cond1.conjoin(cond2)

        if self.negated:
            sc = sc.negate()

        return {
            'adds': [
                [
                    {'sentence': sc, 'designated': self.designation},
                ],
            ],
        }

class TableauxRules(object):
    """
    In general, rules for connectives consist of four rules per connective:
    a designated rule, an undesignated rule, a negated designated rule, and a negated
    undesignated rule. The special case of negation has a total of two rules which apply
    to double negation only, one designated rule, and one undesignated rule.
    """

    class DesignationClosure(ClosureRule):
        """
        A branch closes when a sentence appears on a node marked *designated*,
        and the same sentence appears on a node marked *undesignated*.
        """

        # tracker implementation

        def check_for_target(self, node, branch):
            nnode = self._find_closing_node(node, branch)
            if nnode:
                return {'nodes': {node, nnode}}

        # rule implementation

        def node_will_close_branch(self, node, branch):
            if self._find_closing_node(node, branch):
                return True
            return False

        def applies_to_branch(self, branch):
            # Delegate to tracker
            return self.ntch.cached_target(branch)

        def example_nodes(self, branch = None):
            a = Atomic.first()
            return [
                {'sentence': a, 'designated': True },
                {'sentence': a, 'designated': False},
            ]

        # private util

        def _find_closing_node(self, node, branch):
            if node.has('sentence', 'designated'):
                return branch.find({
                    'sentence'   : node['sentence'],
                    'designated' : not node['designated'],
                })
            
    class DoubleNegationDesignated(DefaultNodeRule):
        """
        From an unticked designated negated negation node *n* on a branch *b*, add a designated
        node to *b* with the double-negatum of *n*, then tick *n*.
        """
        negated     = True
        operator    = Oper.Negation
        designation = True
        branch_level = 1

        def _get_node_targets(self, node, branch):
            s = self.sentence(node)
            return {
                'adds': [
                    [
                        # keep designation neutral for inheritance below
                        {'sentence': s.operand, 'designated': self.designation}
                    ]
                ]
            }

    class DoubleNegationUndesignated(DoubleNegationDesignated):
        """
        From an unticked undesignated negated negation node *n* on a branch *b*, add an
        undesignated node to *b* with the double-negatum of *n*, then tick *n*.
        """
        negated     = True
        designation = False

    class AssertionDesignated(DefaultNodeRule):
        """
        From an unticked, designated, assertion node *n* on a branch *b*, add a designated
        node to *b* with the operand of *b*, then tick *n*.
        """
        operator   = Oper.Assertion
        designation = True
        branch_level = 1

        def _get_node_targets(self, node, branch):
            s = self.sentence(node)
            return {
                'adds': [
                    [
                        # keep designation neutral for inheritance below
                        {'sentence': s.operand, 'designated': self.designation}
                    ]
                ]
            }

    class AssertionUndesignated(AssertionDesignated):
        """
        From an unticked, undesignated, assertion node *n* on a branch *b*, add an undesignated
        node to *b* with the operand of *n*, then tick *n*.
        """
        negated     = False
        designation = False

    class AssertionNegatedDesignated(DefaultNodeRule):
        """
        From an unticked, designated, negated assertion node *n* on branch *b*, add a designated
        node to *b* with the negation of the assertion's operand to *b*, then tick *n*.
        """
        negated     = True
        operator    = Oper.Assertion
        designation = True
        branch_level = 1

        def _get_node_targets(self, node, branch):
            s = self.sentence(node)
            return {
                'adds': [
                    [
                        # keep designation neutral for inheritance below
                        {'sentence': s.operand.negate(), 'designated': self.designation}
                    ]
                ]
            }

    class AssertionNegatedUndesignated(AssertionNegatedDesignated):
        """
        From an unticked, undesignated, negated assertion node *n* on branch *b*, add an undesignated
        node to *b* with the negation of the assertion's operand to *b*, then tick *n*.
        """
        negated     = True
        designation = False

    class ConjunctionDesignated(DefaultNodeRule):
        """
        From an unticked designated conjunction node *n* on a branch *b*, for each conjunct
        *c*, add a designated node with *c* to *b*, then tick *n*.
        """
        operator    = Oper.Conjunction
        designation = True
        branch_level = 1

        def _get_node_targets(self, node, branch):
            return {
                'adds': [
                    [
                        # keep designation neutral for inheritance below
                        {'sentence': operand, 'designated': self.designation}
                        for operand in self.sentence(node)
                    ]
                ]
            }

    class ConjunctionNegatedDesignated(DefaultNodeRule):
        """
        From an unticked designated negated conjunction node *n* on a branch *b*, for each conjunct
        *c*, make a new branch *b'* from *b* and add a designated node with the negation of *c* to *b'*,
        then tick *n*.
        """
        negated     = True
        operator    = Oper.Conjunction
        designation = True
        branch_level = 2

        @FilterHelper.node_targets
        def _get_targets(self, node, branch):
            return {
                'adds': [
                    [
                        # keep designation neutral for inheritance below
                        {'sentence': operand.negate(), 'designated': self.designation},
                    ]
                    for operand in self.sentence(node)
                ]
            }

    class ConjunctionUndesignated(DefaultNodeRule):
        """
        From an unticked undesignated conjunction node *n* on a branch *b*, for each conjunct
        *c*, make a new branch *b'* from *b* and add an undesignated node with *c* to *b'*,
        then tick *n*.
        """
        operator    = Oper.Conjunction
        designation = False
        branch_level = 2

        def _get_node_targets(self, node, branch):
            return {
                'adds': [
                    [
                        # keep designation neutral for inheritance below
                        {'sentence': operand, 'designated': self.designation},
                    ]
                    for operand in self.sentence(node)
                ]
            }

    class ConjunctionNegatedUndesignated(DefaultNodeRule):
        """
        From an unticked undesignated negated conjunction node *n* on a branch *b*, for each conjunct
        *c*, add an undesignated node with the negation of *c* to *b*, then tick *n*.
        """
        negated     = True
        operator    = Oper.Conjunction
        designation = False
        branch_level = 1

        def _get_node_targets(self, node, branch):
            return {
                'adds': [
                    [
                        # keep designation neutral for inheritance below
                        {'sentence': operand.negate(), 'designated': self.designation}
                        for operand in self.sentence(node)
                    ]
                ]
            }

    class DisjunctionDesignated(ConjunctionUndesignated):
        """
        From an unticked designated disjunction node *n* on a branch *b*, for each disjunt
        *d*, make a new branch *b'* from *b* and add a designated node with *d* to *b'*,
        then tick *n*.
        """
        operator    = Oper.Disjunction
        designation = True

    class DisjunctionNegatedDesignated(ConjunctionNegatedUndesignated):
        """
        From an unticked designated negated disjunction node *n* on a branch *b*, for each disjunct
        *d*, add a designated node with the negation of *d* to *b*, then tick *n*.
        """
        operator    = Oper.Disjunction
        designation = True

    class DisjunctionUndesignated(ConjunctionDesignated):
        """
        From an unticked undesignated disjunction node *n* on a branch *b*, for each disjunct
        *d*, add an undesignated node with *d* to *b*, then tick *n*.
        """
        operator    = Oper.Disjunction
        designation = False

    class DisjunctionNegatedUndesignated(ConjunctionNegatedDesignated):
        """
        From an unticked undesignated negated disjunction node *n* on a branch *b*, for each disjunct
        *d*, make a new branch *b'* from *b* and add an undesignated node with the negation of *d* to
        *b'*, then tick *n*.
        """
        operator    = Oper.Disjunction
        designation = False

    class MaterialConditionalDesignated(DefaultNodeRule):
        """
        From an unticked designated material conditional node *n* on a branch *b*, make
        two new branches *b'* and *b''* from *b*, add a designated node with the negation
        of the antecedent to *b'*, add a designated node with the consequent to *b''*,
        then tick *n*.
        """
        operator    = Oper.MaterialConditional
        designation = True
        branch_level = 2

        def _get_node_targets(self, node, branch):
            s = self.sentence(node)
            d = self.designation
            return {
                'adds': [
                    [
                        {'sentence': s.lhs.negate(), 'designated': d},
                    ],
                    [
                        {'sentence': s.rhs         , 'designated': d},
                    ],
                ],
            }

    class MaterialConditionalNegatedDesignated(DefaultNodeRule):
        """
        From an unticked designated negated material conditional node *n* on a branch *b*, add
        a designated node with the antecedent, and a designated node with the negation of the
        consequent to *b*, then tick *n*.
        """
        negated     = True
        operator    = Oper.MaterialConditional
        designation = True
        branch_level = 1

        def _get_node_targets(self, node, branch):
            s = self.sentence(node)
            d = self.designation
            return {
                'adds': [
                    [
                        {'sentence': s.lhs          , 'designated': d},
                        {'sentence': s.rhs.negate() , 'designated': d},
                    ],
                ],
            }

    class MaterialConditionalUndesignated(DefaultNodeRule):
        """
        From an unticked undesignated material conditional node *n* on a branch *b*, add
        an undesignated node with the negation of the antecedent and an undesignated node
        with the consequent to *b*, then tick *n*.
        """
        operator    = Oper.MaterialConditional
        designation = False
        branch_level = 1

        def _get_node_targets(self, node, branch):
            s = self.sentence(node)
            d = self.designation
            return {
                'adds': [
                    [
                        {'sentence': s.lhs.negate(), 'designated': d},
                        {'sentence': s.rhs         , 'designated': d},
                    ],
                ],
            }

    class MaterialConditionalNegatedUndesignated(DefaultNodeRule):
        """
        From an unticked undesignated negated material conditional node *n* on a branch *b*, make
        two new branches *b'* and *b''* from *b*, add an undesignated node with the antecedent to
        *b'*, and add an undesignated node with the negation of the consequent to *b''*, then
        tick *n*.
        """
        negated     = True
        operator    = Oper.MaterialConditional
        designation = False
        branch_level = 2

        def _get_node_targets(self, node, branch):
            s = self.sentence(node)
            d = self.designation
            return {
                'adds': [
                    [
                        {'sentence': s.lhs        , 'designated': d},
                    ],
                    [
                        {'sentence': s.rhs.negate(), 'designated': d},
                    ],
                ],
            }

    class MaterialBiconditionalDesignated(DefaultNodeRule):
        """
        From an unticked designated material biconditional node *n* on a branch *b*, make
        two new branches *b'* and *b''* from *b*, add a designated node with the negation
        of the antecedent and a designated node with the negation of the consequent to *b'*,
        and add a designated node with the antecedent and a designated node with the
        consequent to *b''*, then tick *n*.
        """
        operator    = Oper.MaterialBiconditional
        designation = True
        branch_level = 2

        def _get_node_targets(self, node, branch):
            s = self.sentence(node)
            d = self.designation
            return {
                'adds': [
                    [
                        {'sentence': s.lhs.negate(), 'designated': d},
                        {'sentence': s.rhs.negate(), 'designated': d},
                    ],
                    [
                        {'sentence': s.rhs, 'designated': d},
                        {'sentence': s.lhs, 'designated': d},
                    ],
                ],
            }

    class MaterialBiconditionalNegatedDesignated(DefaultNodeRule):
        """
        From an unticked designated negated material biconditional node *n* on a branch *b*, make
        two branches *b'* and *b''* from *b*, add a designated node with the antecedent and a
        designated node with the negation of the consequent to *b'*, and add a designated node
        with the negation of the antecedent and a designated node with the consequent to *b''*,
        then tick *n*.
        """
        negated     = True
        operator    = Oper.MaterialBiconditional
        designation = True
        branch_level = 2

        def _get_node_targets(self, node, branch):
            s = self.sentence(node)
            d = self.designation
            return {
                'adds': [
                    [
                        {'sentence': s.lhs         , 'designated': d},
                        {'sentence': s.rhs.negate(), 'designated': d},
                    ],
                    [
                        {'sentence': s.lhs.negate(), 'designated': d},
                        {'sentence': s.rhs         , 'designated': d},
                    ],
                ],
            }

    class MaterialBiconditionalUndesignated(MaterialBiconditionalNegatedDesignated):
        """
        From an unticked undesignated material biconditional node *n* on a branch *b*, make
        two new branches *b'* and *b''* from *b*, add an undesignated node with the negation
        of the antecedent and an undesignated node with the consequent to *b'*, and add an
        undesignated node with the antecedent and an undesignated node with the negation of
        the consequent to *b''*, then tick *n*.
        """
        negated     = False
        designation = False

    class MaterialBiconditionalNegatedUndesignated(MaterialBiconditionalDesignated):
        """
        From an undesignated negated material biconditional node *n* on a branch *b*, make
        two branches *b'* and *b''* from *b*, add an undesignated node with the negation of
        the antecendent and an undesignated node with the negation of the consequent to *b'*,
        and add an undesignated node with the antecedent and an undesignated node with the
        consequent to *b''*, then tick *n*.
        """
        negated     = True
        designation = False

    class ConditionalDesignated(MaterialConditionalDesignated):
        """
        This rule functions the same as the corresponding material conditional rule.

        From an unticked designated conditional node *n* on a branch *b*, make two new
        branches *b'* and *b''* from *b*, add a designated node with the negation of
        the antecedent to *b'*, add a designated node with the consequent to *b''*,
        then tick *n*.
        """
        negated     = False
        operator    = Oper.Conditional
        designation = True

    class ConditionalNegatedDesignated(MaterialConditionalNegatedDesignated):
        """
        This rule functions the same as the corresponding material conditional rule.

        From an unticked designated negated conditional node *n* on a branch *b*, add a
        designated node with the antecedent, and a designated node with the negation of
        the consequent to *b*, then tick *n*.
        """
        negated     = True
        operator    = Oper.Conditional
        designation = True

    class ConditionalUndesignated(MaterialConditionalUndesignated):
        """
        This rule functions the same as the corresponding material conditional rule.

        From an unticked undesignated conditional node *n* on a branch *b*, add an
        undesignated node with the negation of the antecedent and an undesignated node
        with the consequent to *b*, then tick *n*.
        """
        negated     = False
        operator    = Oper.Conditional
        designation = False

    class ConditionalNegatedUndesignated(MaterialConditionalNegatedUndesignated):
        """
        This rule functions the same as the corresponding material conditional rule.

        From an unticked undesignated negated conditional node *n* on a branch *b*, make two
        new branches *b'* and *b''* from *b*, add an undesignated node with the antecedent to
        *b'*, and add an undesignated node with the negation of the consequent to *b''*, then
        tick *n*.
        """
        negated     = True
        operator    = Oper.Conditional
        designation = False

    class BiconditionalDesignated(MaterialBiconditionalDesignated):
        """
        This rule functions the same as the corresponding material biconditional rule.

        From an unticked designated biconditional node *n* on a branch *b*, make two new
        branches *b'* and *b''* from *b*, add a designated node with the negation of the
        antecedent and a designated node with the negation of the consequent to *b'*,
        and add a designated node with the antecedent and a designated node with the
        consequent to *b''*, then tick *n*.
        """
        negated     = False
        operator    = Oper.Biconditional
        designation = True

    class BiconditionalNegatedDesignated(MaterialBiconditionalNegatedDesignated):
        """
        This rule functions the same as the corresponding material biconditional rule.

        From an unticked designated negated biconditional node *n* on a branch *b*, make two
        branches *b'* and *b''* from *b*, add a designated node with the antecedent and a
        designated node with the negation of the consequent to *b'*, and add a designated node
        with the negation of the antecedent and a designated node with the consequent to *b''*,
        then tick *n*.
        """
        negated     = True
        operator    = Oper.Biconditional
        designation = True

    class BiconditionalUndesignated(MaterialBiconditionalUndesignated):
        """
        This rule functions the same as the corresponding material biconditional rule.

        From an unticked undesignated material biconditional node *n* on a branch *b*, make
        two new branches *b'* and *b''* from *b*, add an undesignated node with the negation
        of the antecedent and an undesignated node with the consequent to *b'*, and add an
        undesignated node with the antecedent and an undesignated node with the negation of
        the consequent to *b''*, then tick *n*.
        """
        negated     = False
        operator    = Oper.Biconditional
        designation = False

    class BiconditionalNegatedUndesignated(MaterialBiconditionalNegatedUndesignated):
        """
        This rule functions the same as the corresponding material biconditional rule.

        From an undesignated negated biconditional node *n* on a branch *b*, make two
        branches *b'* and *b''* from *b*, add an undesignated node with the negation of the
        antecendent and an undesignated node with the negation of the consequent to *b'*,
        and add an undesignated node with the antecedent and an undesignated node with the
        consequent to *b''*, then tick *n*.
        """
        negated     = True
        operator    = Oper.Biconditional
        designation = False

    class ExistentialDesignated(DefaultNewConstantRule):
        """
        From an unticked designated existential node *n* on a branch *b* quantifying over
        variable *v* into sentence *s*, add a designated node to *b* with the substitution
        into *s* of a new constant not yet appearing on *b* for *v*, then tick *n*.
        """
        quantifier  = Quantifier.Existential
        designation = True
        branch_level = 1

        # NewConstantStoppingRule implementation

        def get_new_nodes_for_constant(self, c, node, branch):
            s = self.sentence(node)
            v = s.variable
            si = s.sentence
            r = si.substitute(c, v)
            return [
                # Keep designation neutral for UniversalUndesignated
                {'sentence': r, 'designated': self.designation},
            ]

    class ExistentialNegatedDesignated(DefaultNodeRule):
        """
        From an unticked designated negated existential node *n* on a branch *b*,
        quantifying over variable *v* into sentence *s*, add a designated node to *b*
        that universally quantifies over *v* into the negation of *s* (i.e. change
        :s:`~XxFx` to :s:`Lx~Fx`), then tick *n*.
        """
        negated     = True
        quantifier  = Quantifier.Existential
        designation = True
        branch_level = 1
        convert_to  = Quantifier.Universal

        def _get_node_targets(self, node, branch):
            s = self.sentence(node)
            v = s.variable
            si = s.sentence
            sq = self.convert_to(v, si.negate())
            return {
                'adds': [
                    [
                        {'sentence': sq, 'designated': self.designation},
                    ],
                ],
            }

    class ExistentialUndesignated(DefaultAllConstantsRule):
        """
        From an undesignated existential node *n* on a branch *b*, for any constant *c* on
        *b* such that the result *r* of substituting *c* for the variable bound by the
        sentence of *n* does not appear on *b*, then add an undesignated node with *r* to *b*.
        If there are no constants yet on *b*, then instantiate with a new constant. The node
        *n* is never ticked.
        """
        quantifier  = Quantifier.Existential
        designation = False
        branch_level = 1

        # AllConstantsStoppingRule implementation

        def get_new_nodes_for_constant(self, c, node, branch):
            s = self.sentence(node)
            v = s.variable
            si = s.sentence
            r = si.substitute(c, v)
            return [
                {'sentence': r, 'designated': self.designation},
            ]

    class ExistentialNegatedUndesignated(ExistentialNegatedDesignated):
        """
        From an unticked undesignated negated existential node *n* on a branch *b*,
        quantifying over variable *v* into sentence *s*, add an undesignated node to *b*
        that universally quantifies over *v* into the negation of *s* (e.g. change
        :s:`~XxFx` to :s:`Lx~Fx`), then tick *n*.
        """
        quantifier  = Quantifier.Existential
        designation = False
        convert_to  = Quantifier.Universal

    class UniversalDesignated(ExistentialUndesignated):
        """
        From a designated universal node *n* on a branch *b*, for any constant *c* on *b*
        such that the result *r* of substituting *c* for the variable bound by the sentence
        of *n* does not appear on *b*, then add a designated node with *r* to *b*. If there
        are no constants yet on *b*, then instantiate with a new constant. The node *n* is
        never ticked.
        """
        quantifier  = Quantifier.Universal
        designation = True

    class UniversalNegatedDesignated(ExistentialNegatedDesignated):
        """
        From an unticked designated negated universal node *n* on a branch *b*,
        quantifying over variable *v* into sentence *s*, add a designated node to *b*
        with the existential quantifier over *v* into the negation of *s* (e.g. change
        :s:`~LxFx` to :s:`Xx~Fx`), then tick *n*.
        """
        quantifier  = Quantifier.Universal
        designation = True
        convert_to  = Quantifier.Existential

    class UniversalUndesignated(ExistentialDesignated):
        """
        From an unticked undesignated universal node *n* on a branch *b* quantifying over *v*
        into sentence *s*, add an undesignated node to *b* with the result of substituting into
        *s* a constant new to *b* for *v*, then tick *n*.
        """
        quantifier  = Quantifier.Universal
        designation = False

    class UniversalNegatedUndesignated(ExistentialNegatedDesignated):
        """
        From an unticked undesignated negated universal node *n* on a branch *b*,
        quantifying over variable *v* into sentence *s*, add an undesignated node to *b*
        with the existential quantifier over *v* into the negation of *s* (e.g. change
        :s:`~LxFx` to :s:`Xx~Fx`), then tick *n*.
        """
        quantifier  = Quantifier.Universal
        designation = False
        convert_to  = Quantifier.Existential

    closure_rules = [
        DesignationClosure,
    ]

    rule_groups = [
        [
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
        ],
        [
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
        ],
        [
            ExistentialDesignated,
            ExistentialUndesignated,
        ],
        [
            UniversalDesignated,
            UniversalUndesignated,
        ],
    ]