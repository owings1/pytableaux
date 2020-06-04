# pytableaux, a multi-logic proof generator.
# Copyright (C) 2014-2020 Doug Owings.
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
title = 'First Degree Entailment'
description = 'Four-valued logic (True, False, Neither, Both)'
tags_list = ['many-valued', 'gappy', 'glutty', 'non-modal', 'first-order']
tags = set(tags_list)
category = 'Many-valued'
category_display_order = 1

import logic, examples
from logic import negate, negative, quantify, atomic, NotImplementedError

Identity = logic.get_system_predicate('Identity')
Existence = logic.get_system_predicate('Existence')

class Model(logic.Model):
    """
    FDE Model.
    """

    #: The admissable values
    truth_values = set(['F', 'N', 'B', 'T'])

    #: The designated values
    designated_values = set(['B', 'T'])

    #: An assignment of each atomic sentence to a value.
    atomics = {}

    #: An assignment of each opaque (un-interpreted) sentence to a value.
    opaques = {}

    #: A map of predicates to their extension.
    extensions = {}

    #: A map of predicates to their anti-extension.
    anti_extensions = {}

    truth_values_list = ['F', 'N', 'B', 'T']
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

        super(Model, self).__init__()

        self.extensions = {}
        self.anti_extensions = {}
        self.atomics = {}
        self.opaques = {}

        self.all_atomics = set()
        self.constants = set()
        self.predicates = set([
            #Identity,
            #Existence,
        ])

    def value_of_operated(self, sentence, **kw):
        """
        The value of a sentence with a truth-functional operator is determined by
        the values of its operands according to the following tables.

        //truth_tables//fde//
        """
        return super(Model, self).value_of_operated(sentence, **kw)

    def value_of_predicated(self, sentence, **kw):
        """
        A sentence with predicate `P` with parameters `<p,...>` has the value:

        * **T** iff `<p,...>` is in the extension of `P` and not in the anti-extension of `P`.
        * **F** iff `<p,...>` is in the anti-extension of `P` and not in the extension of `P`.
        * **B** iff `<p,...>` is in both the extension and anti-extension of `P`.
        * **N** iff `<p,...>` is neither in the extension nor anti-extension of `P`.

        Note, for FDE, there is no exclusivity or exhaustion constraint on a predicate's
        extension/anti-extension. This means that `<p,...>` could be in neither the extension
        nor the anti-extension of a predicate, or it could be in both the extension and the
        anti-extension.
        """
        params = tuple(sentence.parameters)
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
        the values from least to greatest is: **F**, **N**, **B**, **T**.
        """
        values = {self.value_of(sentence.substitute(c, sentence.variable), **kw) for c in self.constants}
        return self.cvals[max({self.nvals[value] for value in values})]

    def value_of_universal(self, sentence, **kw):
        """
        The value of an universal sentence is the minimum value of the sentences that
        result from replacing each constant for the quantified variable. The ordering of
        the values from least to greatest is: **F**, **N**, **B**, **T**.
        """
        values = {self.value_of(sentence.substitute(c, sentence.variable), **kw) for c in self.constants}
        return self.cvals[min({self.nvals[value] for value in values})]

    def is_sentence_opaque(self, sentence):
        """
        A sentence is opaque if its operator is Necessity or Possibility, or if it is
        a negated sentence whose negatum has the operator Necessity or Possibility.
        """
        if sentence.operator in self.modal_operators:
            return True
        return super(Model, self).is_sentence_opaque(sentence)

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
                    for sentence in sorted(list(self.atomics.keys()))
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
                    for sentence in sorted(list(self.opaques.keys()))
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
        for node in branch.nodes:
            if node.has('sentence'):
                self.predicates.update(node.predicates())
                self.all_atomics.update(node.atomics())
                sentence = node.props['sentence']
                is_literal = self.is_sentence_literal(sentence)
                is_opaque = self.is_sentence_opaque(sentence)
                if is_literal or is_opaque:
                    d = node.props['designated']
                    if sentence.is_operated() and sentence.operator == 'Negation':
                        # the negative of s is the negatum of s
                        nnode = branch.find({'sentence': sentence.operand})
                    else:
                        # the negative of s is the negation of s
                        nnode = branch.find({'sentence': negate(sentence)})
                    if nnode != None:
                        # both s and its negative are on the branch
                        nd = nnode.props['designated']
                        if d and not nd:
                            # only s is designated
                            value = 'T'
                        elif not d and nd:
                            # only the negative of s is designated
                            value = 'F'
                        elif d and nd:
                            # both sentences are designated
                            value = 'B'
                        else:
                            # both sentences are undesignated
                            value = 'N'
                    else:
                        # the negative of s is not on the branch
                        if d:
                            # any designated value will work
                            value = 'T'
                        else:
                            # any undesignated value will work
                            value = 'F'
                    if is_opaque:
                        self.set_opaque_value(sentence, value)
                    else:
                        self.set_literal_value(sentence, value)
        self.finish()

    def finish(self):
        # TODO: consider augmenting the logic with identity and existence predicate
        #       restrictions. in that case, new tableaux rules need to be written.
        for s in self.all_atomics:
            if s not in self.atomics:
                self.set_literal_value(s, self.unassigned_value)
        pass

    def is_sentence_literal(self, sentence):
        if sentence.operator == 'Negation' and self.is_sentence_opaque(sentence.operand):
            return True
        return sentence.is_literal()

    def set_literal_value(self, sentence, value):
        if self.is_sentence_opaque(sentence):
            self.set_opaque_value(sentence, value)
        elif sentence.is_operated() and sentence.operator == 'Negation':
            self.set_literal_value(sentence.operand, self.truth_function('Negation', value))
        elif sentence.is_atomic():
            self.set_atomic_value(sentence, value)
        elif sentence.is_predicated():
            self.set_predicated_value(sentence, value)
        else:
            raise NotImplementedError(NotImplemented)

    def set_opaque_value(self, sentence, value):
        if sentence in self.opaques and self.opaques[sentence] != value:
            raise Model.ModelValueError('Inconsistent value {0} for sentence {1}'.format(str(value), str(sentence)))
        self.opaques[sentence] = value
        
    def set_atomic_value(self, sentence, value):
        if sentence in self.atomics and self.atomics[sentence] != value:
            raise Model.ModelValueError('Inconsistent value {0} for sentence {1}'.format(str(value), str(sentence)))
        self.atomics[sentence] = value

    def set_predicated_value(self, sentence, value):
        predicate = sentence.predicate
        params = tuple(sentence.parameters)
        for param in params:
            if param.is_constant():
                self.constants.add(param)
        extension = self.get_extension(predicate)
        anti_extension = self.get_anti_extension(predicate)
        if 'N' in self.truth_values and value == 'N':
            if params in extension:
                raise Model.ModelValueError('Cannot set value {0} for tuple {1} already in extension'.format(str(value), str(params)))
            if params in anti_extension:
                raise Model.ModelValueError('Cannot set value {0} for tuple {1} already in anti-extension'.format(str(value), str(params)))
        elif value == 'T':
            if params in anti_extension:
                raise Model.ModelValueError('Cannot set value {0} for tuple {1} already in anti-extension'.format(str(value), str(params)))
            extension.add(params)
        elif value == 'F':
            if params in extension:
                raise Model.ModelValueError('Cannot set value {0} for tuple {1} already in extension'.format(str(value), str(params)))
            anti_extension.add(params)
        elif 'B' in self.truth_values and value == 'B':
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
        if q == 'Existential':
            return self.value_of_existential(sentence, **kw)
        elif q == 'Universal':
            return self.value_of_universal(sentence, **kw)
        return super(Model, self).value_of_quantified(sentence, **kw)

    def truth_function(self, operator, a, b=None):

        # Define as generically as possible for reuse.
        if operator == 'Assertion':
            return a
        if operator == 'Negation':
            if a == 'F' or a == 'T':
                return self.cvals[1 - self.nvals[a]]
            return a
        elif operator == 'Conjunction':
            return self.cvals[min(self.nvals[a], self.nvals[b])]
        elif operator == 'Disjunction':
            return self.cvals[max(self.nvals[a], self.nvals[b])]
        elif operator == 'Material Conditional':
            return self.truth_function('Disjunction', self.truth_function('Negation', a), b)
        elif operator == 'Material Biconditional':
            return self.truth_function(
                'Conjunction',
                self.truth_function('Material Conditional', a, b),
                self.truth_function('Material Conditional', b, a)
            )
        elif operator == 'Conditional':
            return self.truth_function('Material Conditional', a, b)
        elif operator == 'Biconditional':
            return self.truth_function(
                'Conjunction',
                self.truth_function('Conditional', a, b),
                self.truth_function('Conditional', b, a)
            )
        else:
            raise NotImplementedError(NotImplemented)

class TableauxSystem(logic.TableauxSystem):
    """
    Nodes for FDE have a boolean *designation* property, and a branch is closed iff
    the same sentence appears on both a designated and undesignated node. This allows
    for both a sentence and its negation to appear as designated (xor undesignated)
    on an open branch.
    """

    @staticmethod
    def build_trunk(tableau, argument):
        """
        To build the trunk for an argument, add a designated node for each premise, and
        an undesignated node for the conclusion.
        """
        branch = tableau.branch()
        for premise in argument.premises:
            branch.add({'sentence': premise, 'designated': True, 'world': None})
        branch.add({'sentence' : argument.conclusion, 'designated': False, 'world': None})

class TableauxRules(object):
    """
    In general, rules for connectives consist of four rules per connective:
    a designated rule, an undesignated rule, a negated designated rule, and a negated
    undesignated rule. The special case of negation has a total of two rules which apply
    to double negation only, one designated rule, and one undesignated rule.
    """

    class DesignationClosure(logic.TableauxSystem.ClosureRule):
        """
        A branch closes when a sentence appears on a node marked *designated*,
        and the same sentence appears on a node marked *undesignated*.
        """

        def applies_to_branch(self, branch):
            for node in branch.find_all({'designated': True}):
                n = branch.find({'sentence': self.sentence(node), 'designated': False})
                if n != None:
                    return {'nodes': set([node, n]), 'type': 'Nodes'}
            return False

        def example(self):
            a = atomic(0, 0)
            self.branch().update([
                {'sentence': a, 'designated': True },
                {'sentence': a, 'designated': False},
            ])

    class DoubleNegationDesignated(logic.TableauxSystem.ConditionalNodeRule):
        """
        From an unticked designated negated negation node *n* on a branch *b*, add a designated
        node to *b* with the double-negatum of *n*, then tick *n*.
        """

        negated     = True
        operator    = 'Negation'
        designation = True

        def apply_to_node(self, node, branch):
            s = self.sentence(node)
            d = self.designation
            branch.add({'sentence': s.operand, 'designated': d}).tick(node)

    class DoubleNegationUndesignated(DoubleNegationDesignated):
        """
        From an unticked undesignated negated negation node *n* on a branch *b*, add an
        undesignated node to *b* with the double-negatum of *n*, then tick *n*.
        """

        designation = False

    class AssertionDesignated(logic.TableauxSystem.ConditionalNodeRule):
        """
        From an unticked, designated, assertion node *n* on a branch *b*, add a designated
        node to *b* with the operand of *b*, then tick *n*.
        """

        operator = 'Assertion'
        designation = True

        def apply_to_node(self, node, branch):
            s = self.sentence(node)
            d = self.designation
            branch.add({'sentence': s.operand, 'designated': d}).tick(node)

    class AssertionUndesignated(AssertionDesignated):
        """
        From an unticked, undesignated, assertion node *n* on a branch *b*, add an undesignated
        node to *b* with the operand of *n*, then tick *n*.
        """

        designation = False

    class AssertionNegatedDesignated(logic.TableauxSystem.ConditionalNodeRule):
        """
        From an unticked, designated, negated assertion node *n* on branch *b*, add a designated
        node to *b* with the negation of the assertion's operand to *b*, then tick *n*.
        """

        operator = 'Assertion'
        negated = True
        designation = True

        def apply_to_node(self, node, branch):
            s = self.sentence(node)
            d = self.designation
            branch.add({'sentence': negate(s.operand), 'designated': d}).tick(node)

    class AssertionNegatedUndesignated(AssertionNegatedDesignated):
        """
        From an unticked, undesignated, negated assertion node *n* on branch *b*, add an undesignated
        node to *b* with the negation of the assertion's operand to *b*, then tick *n*.
        """

        designation = False

    class ConjunctionDesignated(logic.TableauxSystem.ConditionalNodeRule):
        """
        From an unticked designated conjunction node *n* on a branch *b*, for each conjunct
        *c*, add a designated node with *c* to *b*, then tick *n*.
        """

        operator    = 'Conjunction'
        designation = True

        def apply_to_node(self, node, branch):
            s = self.sentence(node)
            d = self.designation
            for conjunct in s.operands:
                branch.add({'sentence': conjunct, 'designated': d})
            branch.tick(node)

    class ConjunctionNegatedDesignated(logic.TableauxSystem.ConditionalNodeRule):
        """
        From an unticked designated negated conjunction node *n* on a branch *b*, for each conjunct
        *c*, make a new branch *b'* from *b* and add a designated node with the negation of *c* to *b'*,
        then tick *n*.
        """

        negated     = True
        operator    = 'Conjunction'
        designation = True

        def apply_to_node(self, node, branch):
            s = self.sentence(node)
            d = self.designation
            b1 = branch
            b2 = self.branch(branch)
            b1.add({'sentence': negate(s.lhs), 'designated': d}).tick(node)
            b2.add({'sentence': negate(s.rhs), 'designated': d}).tick(node)

        def score_target_map(self, target):
            branch = target['branch']
            s = self.sentence(target['node'])
            d = self.designation
            return {
                'b1': branch.has({'sentence': negative(s.lhs), 'designated': not d}),
                'b2': branch.has({'sentence': negative(s.rhs), 'designated': not d}),
            }

    class ConjunctionUndesignated(logic.TableauxSystem.ConditionalNodeRule):
        """
        From an unticked undesignated conjunction node *n* on a branch *b*, for each conjunct
        *c*, make a new branch *b'* from *b* and add an undesignated node with *c* to *b'*,
        then tick *n*.
        """

        operator    = 'Conjunction'
        designation = False

        def apply_to_node(self, node, branch):
            s = self.sentence(node)
            d = self.designation
            b1 = branch
            b2 = self.branch(branch)
            b1.add({'sentence': s.lhs, 'designated': d}).tick(node)
            b2.add({'sentence': s.rhs, 'designated': d}).tick(node)

        def score_target_map(self, target):
            branch = target['branch']
            s = self.sentence(target['node'])
            d = self.designation
            return {
                'b1': branch.has({'sentence': s.lhs, 'designated': not d}),
                'b2': branch.has({'sentence': s.rhs, 'designated': not d}),
            }

    class ConjunctionNegatedUndesignated(logic.TableauxSystem.ConditionalNodeRule):
        """
        From an unticked undesignated negated conjunction node *n* on a branch *b*, for each conjunct
        *c*, add an undesignated node with the negation of *c* to *b*, then tick *n*.
        """

        negated     = True
        operator    = 'Conjunction'
        designation = False

        def apply_to_node(self, node, branch):
            s = self.sentence(node)
            d = self.designation
            for conjunct in s.operands:
                branch.add({'sentence' : negate(conjunct), 'designated': d})
            branch.tick(node)

    class DisjunctionDesignated(ConjunctionUndesignated):
        """
        From an unticked designated disjunction node *n* on a branch *b*, for each disjunt
        *d*, make a new branch *b'* from *b* and add a designated node with *d* to *b'*,
        then tick *n*.
        """

        operator    = 'Disjunction'
        designation = True

    class DisjunctionNegatedDesignated(ConjunctionNegatedUndesignated):
        """
        From an unticked designated negated disjunction node *n* on a branch *b*, for each disjunct
        *d*, add a designated node with the negation of *d* to *b*, then tick *n*.
        """

        operator    = 'Disjunction'
        designation = True

    class DisjunctionUndesignated(ConjunctionDesignated):
        """
        From an unticked undesignated disjunction node *n* on a branch *b*, for each disjunct
        *d*, add an undesignated node with *d* to *b*, then tick *n*.
        """

        operator    = 'Disjunction'
        designation = False

    class DisjunctionNegatedUndesignated(ConjunctionNegatedDesignated):
        """
        From an unticked undesignated negated disjunction node *n* on a branch *b*, for each disjunct
        *d*, make a new branch *b'* from *b* and add an undesignated node with the negation of *d* to
        *b'*, then tick *n*.
        """

        operator    = 'Disjunction'
        designation = False

    class MaterialConditionalDesignated(logic.TableauxSystem.ConditionalNodeRule):
        """
        From an unticked designated material conditional node *n* on a branch *b*, make
        two new branches *b'* and *b''* from *b*, add a designated node with the negation
        of the antecedent to *b'*, add a designated node with the consequent to *b''*,
        then tick *n*.
        """

        operator    = 'Material Conditional'
        designation = True

        def apply_to_node(self, node, branch):
            s = self.sentence(node)
            d = self.designation
            b1 = branch
            b2 = self.branch(branch)
            b1.add({'sentence': negate(s.lhs), 'designated': d}).tick(node)
            b2.add({'sentence':        s.rhs , 'designated': d}).tick(node)

        def score_target_map(self, target):
            branch = target['branch']
            s = self.sentence(target['node'])
            d = self.designation
            return {
                'b1': branch.has({'sentence': negative(s.lhs), 'designated': not d}),
                'b2': branch.has({'sentence':          s.rhs , 'designated': not d}),
            }

    class MaterialConditionalNegatedDesignated(logic.TableauxSystem.ConditionalNodeRule):
        """
        From an unticked designated negated material conditional node *n* on a branch *b*, add
        a designated node with the antecedent, and a designated node with the negation of the
        consequent to *b*, then tick *n*.
        """

        negated     = True
        operator    = 'Material Conditional'
        designation = True

        def apply_to_node(self, node, branch):
            s = self.sentence(node)
            d = self.designation
            branch.update([
                {'sentence':        s.lhs , 'designated': d},
                {'sentence': negate(s.rhs), 'designated': d},
            ]).tick(node)

    class MaterialConditionalUndesignated(logic.TableauxSystem.ConditionalNodeRule):
        """
        From an unticked undesignated material conditional node *n* on a branch *b*, add
        an undesignated node with the negation of the antecedent and an undesignated node
        with the consequent to *b*, then tick *n*.
        """

        operator    = 'Material Conditional'
        designation = False

        def apply_to_node(self, node, branch):
            s = self.sentence(node)
            d = self.designation
            branch.update([
                {'sentence': negate(s.lhs), 'designated': d},
                {'sentence':        s.rhs , 'designated': d},
            ]).tick(node)

    class MaterialConditionalNegatedUndesignated(logic.TableauxSystem.ConditionalNodeRule):
        """
        From an unticked undesignated negated material conditional node *n* on a branch *b*, make
        two new branches *b'* and *b''* from *b*, add an undesignated node with the antecedent to
        *b'*, and add an undesignated node with the negation of the consequent to *b''*, then
        tick *n*.
        """

        negated     = True
        operator    = 'Material Conditional'
        designation = False

        def apply_to_node(self, node, branch):
            s = self.sentence(node)
            d = self.designation
            b1 = branch
            b2 = self.branch(branch)
            b1.add({'sentence':        s.lhs , 'designated': d}).tick(node)
            b2.add({'sentence': negate(s.rhs), 'designated': d}).tick(node)

        def score_target_map(self, target):
            branch = target['branch']
            s = self.sentence(target['node'])
            d = self.designation
            return {
                'b1': branch.has({'sentence':          s.lhs , 'designated': not d}),
                'b2': branch.has({'sentence': negative(s.rhs), 'designated': not d}),
            }

    class MaterialBiconditionalDesignated(logic.TableauxSystem.ConditionalNodeRule):
        """
        From an unticked designated material biconditional node *n* on a branch *b*, make
        two new branches *b'* and *b''* from *b*, add a designated node with the negation
        of the antecedent and a designated node with the negation of the consequent to *b'*,
        and add a designated node with the antecedent and a designated node with the
        consequent to *b''*, then tick *n*.
        """

        operator    = 'Material Biconditional'
        designation = True

        def apply_to_node(self, node, branch):
            s = self.sentence(node)
            d = self.designation
            b1 = branch
            b2 = self.branch(branch)
            b1.update([
                {'sentence': negate(s.lhs), 'designated': d},
                {'sentence': negate(s.rhs), 'designated': d},
            ]).tick(node)
            b2.update([
                {'sentence': s.rhs, 'designated': d},
                {'sentence': s.lhs, 'designated': d},
            ]).tick(node)

        def score_target_map(self, target):
            branch = target['branch']
            s = self.sentence(target['node'])
            d = self.designation
            return {
                'b1': branch.has_any([
                    {'sentence': negative(s.lhs), 'designated': not d},
                    {'sentence': negative(s.rhs), 'designated': not d},
                ]),
                'b2': branch.has_any([
                    {'sentence': s.rhs, 'designated': not d},
                    {'sentence': s.lhs, 'designated': not d},
                ]),
            }

    class MaterialBiconditionalNegatedDesignated(logic.TableauxSystem.ConditionalNodeRule):
        """
        From an unticked designated negated material biconditional node *n* on a branch *b*, make
        two branches *b'* and *b''* from *b*, add a designated node with the antecedent and a
        designated node with the negation of the consequent to *b'*, and add a designated node
        with the negation of the antecedent and a designated node with the consequent to *b''*,
        then tick *n*.
        """

        negated     = True
        operator    = 'Material Biconditional'
        designation = True

        def apply_to_node(self, node, branch):
            s = self.sentence(node)
            d = self.designation
            b1 = branch
            b2 = self.branch(branch)
            b1.update([
                {'sentence':        s.lhs , 'designated': d},
                {'sentence': negate(s.rhs), 'designated': d},
            ]).tick(node)
            b2.update([
                {'sentence': negate(s.lhs), 'designated': d},
                {'sentence':        s.rhs , 'designated': d},
            ]).tick(node)

        def score_target_map(self, target):
            branch = target['branch']
            s = self.sentence(target['node'])
            d = self.designation
            return {
                'b1': branch.has_any([
                    {'sentence':          s.lhs , 'designated': not d},
                    {'sentence': negative(s.rhs), 'designated': not d},
                ]),
                'b2': branch.has_any([
                    {'sentence': negative(s.lhs), 'designated': not d},
                    {'sentence':          s.rhs , 'designated': not d},
                ]),
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

        operator = 'Conditional'

    class ConditionalNegatedDesignated(MaterialConditionalNegatedDesignated):
        """
        This rule functions the same as the corresponding material conditional rule.

        From an unticked designated negated conditional node *n* on a branch *b*, add a
        designated node with the antecedent, and a designated node with the negation of
        the consequent to *b*, then tick *n*.
        """

        operator = 'Conditional'

    class ConditionalUndesignated(MaterialConditionalUndesignated):
        """
        This rule functions the same as the corresponding material conditional rule.

        From an unticked undesignated conditional node *n* on a branch *b*, add an
        undesignated node with the negation of the antecedent and an undesignated node
        with the consequent to *b*, then tick *n*.
        """

        operator = 'Conditional'

    class ConditionalNegatedUndesignated(MaterialConditionalNegatedUndesignated):
        """
        This rule functions the same as the corresponding material conditional rule.

        From an unticked undesignated negated conditional node *n* on a branch *b*, make two
        new branches *b'* and *b''* from *b*, add an undesignated node with the antecedent to
        *b'*, and add an undesignated node with the negation of the consequent to *b''*, then
        tick *n*.
        """

        operator = 'Conditional'

    class BiconditionalDesignated(MaterialBiconditionalDesignated):
        """
        This rule functions the same as the corresponding material biconditional rule.

        From an unticked designated biconditional node *n* on a branch *b*, make two new
        branches *b'* and *b''* from *b*, add a designated node with the negation of the
        antecedent and a designated node with the negation of the consequent to *b'*,
        and add a designated node with the antecedent and a designated node with the
        consequent to *b''*, then tick *n*.
        """

        operator = 'Biconditional'

    class BiconditionalNegatedDesignated(MaterialBiconditionalNegatedDesignated):
        """
        This rule functions the same as the corresponding material biconditional rule.

        From an unticked designated negated biconditional node *n* on a branch *b*, make two
        branches *b'* and *b''* from *b*, add a designated node with the antecedent and a
        designated node with the negation of the consequent to *b'*, and add a designated node
        with the negation of the antecedent and a designated node with the consequent to *b''*,
        then tick *n*.
        """

        operator = 'Biconditional'

    class BiconditionalUndesignated(MaterialBiconditionalUndesignated):
        """
        This rule functions the same as the corresponding material biconditional rule.

        From an unticked undesignated material biconditional node *n* on a branch *b*, make
        two new branches *b'* and *b''* from *b*, add an undesignated node with the negation
        of the antecedent and an undesignated node with the consequent to *b'*, and add an
        undesignated node with the antecedent and an undesignated node with the negation of
        the consequent to *b''*, then tick *n*.
        """

        operator = 'Biconditional'

    class BiconditionalNegatedUndesignated(MaterialBiconditionalNegatedUndesignated):
        """
        This rule functions the same as the corresponding material biconditional rule.

        From an undesignated negated biconditional node *n* on a branch *b*, make two
        branches *b'* and *b''* from *b*, add an undesignated node with the negation of the
        antecendent and an undesignated node with the negation of the consequent to *b'*,
        and add an undesignated node with the antecedent and an undesignated node with the
        consequent to *b''*, then tick *n*.
        """

        operator = 'Biconditional'

    class ExistentialDesignated(logic.TableauxSystem.ConditionalNodeRule):
        """
        From an unticked designated existential node *n* on a branch *b* quantifying over
        variable *v* into sentence *s*, add a designated node to *b* with the substitution
        into *s* of a new constant not yet appearing on *b* for *v*, then tick *n*.
        """

        quantifier  = 'Existential'
        designation = True

        def apply_to_node(self, node, branch):
            s = self.sentence(node)
            d = self.designation
            v = s.variable
            c = branch.new_constant()
            r = s.substitute(c, v)
            branch.add({'sentence': r, 'designated': d}).tick(node)

    class ExistentialNegatedDesignated(logic.TableauxSystem.ConditionalNodeRule):
        """
        From an unticked designated negated existential node *n* on a branch *b*,
        quantifying over variable *v* into sentence *s*, add a designated node to *b*
        that universally quantifies over *v* into the negation of *s* (i.e. change
        'not exists x: A' to 'for all x: not A'), then tick *n*.
        """

        negated     = True
        quantifier  = 'Existential'
        convert_to  = 'Universal'
        designation = True

        def apply_to_node(self, node, branch):
            s = self.sentence(node)
            d = self.designation
            v = s.variable
            si = s.sentence
            sq = quantify(self.convert_to, v, negate(si))
            branch.add({'sentence': sq, 'designated': d}).tick(node)

    class ExistentialUndesignated(logic.TableauxSystem.SelectiveTrackingBranchRule):
        """
        From an undesignated existential node *n* on a branch *b*, for any constant *c* on
        *b* such that the result *r* of substituting *c* for the variable bound by the
        sentence of *n* does not appear on *b*, then add an undesignated node with *r* to *b*.
        If there are no constants yet on *b*, then instantiate with a new constant. The node
        *n* is never ticked.
        """

        quantifier  = 'Existential'
        designation = False

        def get_candidate_targets_for_branch(self, branch):
            cands = list()
            d = self.designation
            q = self.quantifier
            constants = branch.constants()
            for n in branch.find_all({'_quantifier': q, 'designated': d}):
                # keep quantifier and designation neutral for inheritance below
                s = self.sentence(n)
                v = s.variable
                if len(constants):
                    for c in constants:
                        r = s.substitute(c, v)
                        if not branch.has({'sentence': r, 'designated': d}):
                            cands.append({'branch': branch, 'sentence': r, 'node': n})
                else:
                    c = branch.new_constant()
                    r = s.substitute(c, v)
                    cands.append({'branch': branch, 'sentence': r, 'node': n})
            return cands
            
        def apply_to_target(self, target):
            # keep designation neutral for inheritance below
            target['branch'].add({'sentence': target['sentence'], 'designated': self.designation})

        def example(self):
            # keep quantifier and designation neutral for inheritance below
            s = examples.quantified(self.quantifier)
            self.branch().add({'sentence': s, 'designated': self.designation})

    class ExistentialNegatedUndesignated(ExistentialNegatedDesignated):
        """
        From an unticked undesignated negated existential node *n* on a branch *b*,
        quantifying over variable *v* into sentence *s*, add an undesignated node to *b*
        that universally quantifies over *v* into the negation of *s* (i.e. change 'not
        exists x: A' to 'for all x: not A'), then tick *n*.
        """

        quantifier  = 'Existential'
        convert_to  = 'Universal'
        designation = False

    class UniversalDesignated(ExistentialUndesignated):
        """
        From a designated universal node *n* on a branch *b*, for any constant *c* on *b*
        such that the result *r* of substituting *c* for the variable bound by the sentence
        of *n* does not appear on *b*, then add a designated node with *r* to *b*. If there
        are no constants yet on *b*, then instantiate with a new constant. The node *n* is
        never ticked.
        """

        quantifier  = 'Universal'
        designation = True

    class UniversalNegatedDesignated(ExistentialNegatedDesignated):
        """
        From an unticked designated negated universal node *n* on a branch *b*,
        quantifying over variable *v* into sentence *s*, add a designated node to *b*
        with the existential quantifier over *v* into the negation of *s* (i.e. change
        'not all x: A' to 'exists x: not A'), then tick *n*.
        """

        quantifier  = 'Universal'
        convert_to  = 'Existential'
        designation = True

    class UniversalUndesignated(ExistentialDesignated):
        """
        From an unticked undesignated universal node *n* on a branch *b* quantifying over *v*
        into sentence *s*, add an undesignated node to *b* with the result of substituting into
        *s* a constant new to *b* for *v*, then tick *n*.
        """

        quantifier  = 'Universal'
        designation = False

    class UniversalNegatedUndesignated(ExistentialNegatedDesignated):
        """
        From an unticked undesignated negated universal node *n* on a branch *b*,
        quantifying over variable *v* into sentence *s*, add an undesignated node to *b*
        with the existential quantifier over *v* into the negation of *s* (i.e. change
        'not all x: A' to 'exists x: not A'), then tick *n*.
        """

        quantifier  = 'Universal'
        convert_to  = 'Existential'
        designation = False

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
            ExistentialDesignated,
            ExistentialNegatedDesignated,
            ExistentialUndesignated,
            ExistentialNegatedUndesignated,
            UniversalDesignated,
            UniversalNegatedDesignated,
            UniversalUndesignated,
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
    ]