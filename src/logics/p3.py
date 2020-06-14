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
# pytableaux - Post 3-valued logic
name = 'P3'

class Meta(object):

    title    = 'Post 3-valued logic'
    category = 'Many-valued'

    description = 'Emil Post three-valued logic (T, F, and N) with mirror-image negation'

    tags = ['many-valued', 'gappy', 'non-modal', 'first-order']

    category_display_order = 7

import logic, helpers
from logic import negate, negative, operate
from . import fde, k3

class Model(k3.Model):
    """
    A P3 model is just like a `K3 model`_ with different tables for some of the connectives.

    .. _K3 model: k3.html#logics.k3.Model
    """

    def value_of_operated(self, sentence, **kw):
        """
        The value of a sentence with a truth-functional operator is determined by
        the values of its operands according to the following tables.

        Most notable is the behavior of negation. Disjunction is the same as in
        `K3`_, but conjunction is quite different, which is defined in terms of
        disjunction in the standard way (P{~(~A V ~B)}).

        //truth_tables//p3//

        .. _K3: k3.html
        """
        return super(Model, self).value_of_operated(sentence, **kw)

    def truth_function(self, operator, a, b=None):
        if operator == 'Negation':
            return self.back_cycle(a)
        if operator == 'Conjunction':
            return self.truth_function('Negation', *(self.truth_function('Negation', x) for x in (a, b)))
        return super().truth_function(operator, a, b)
        
    def back_cycle(self, value):
        i = self.truth_values_list.index(value)
        return self.truth_values_list[i - 1]

    def read_branch(self, branch):
        for node in branch.nodes:
            if node.has('sentence'):
                self._collect_node(node)
                sentence = node.props['sentence']
                is_literal = self.is_sentence_literal(sentence)
                is_opaque = self.is_sentence_opaque(sentence)
                if is_literal or is_opaque:
                    if sentence.operator == 'Negation':
                        sentence = sentence.negatum
                        if node.props['designated']:
                            value = 'F'
                        else:
                            if branch.has({'sentence': sentence, 'designated': False}):
                                value = 'N'
                            else:
                                value = 'T'
                    else:
                        if node.props['designated']:
                            value = 'T'
                        else:
                            if branch.has({'sentence': negate(sentence), 'designated': False}):
                                value = 'N'
                            else:
                                value = 'F'
                    if is_opaque:
                        self.set_opaque_value(sentence, value)
                    else:
                        self.set_literal_value(sentence, value)
        self.finish()

class TableauxSystem(fde.TableauxSystem):
    """
    P3's Tableaux System inherits directly from the `FDE system`_, employing
    designation markers, and building the trunk in the same way.

    .. _FDE system: fde.html#logics.fde.TableauxSystem
    """

    branchables = {
        'Negation': {
            True : {
                True  : 0,
                False : 1,
            },
        },
        'Assertion': {
            False : {
                True  : 0,
                False : 0,
            },
            True : {
                True  : 0,
                False : 0,
            },
        },
        'Conjunction': {
            False : {
                True  : 0,
                False : 3,
            },
            True  : {
                True  : 1,
                False : 2,
            },
        },
        'Disjunction': {
            False  : {
                True  : 1,
                False : 0,
            },
            True : {
                True  : 0,
                False : 1,
            },
        },
        # reduction
        'Material Conditional': {
            False  : {
                True  : 0,
                False : 0,
            },
            True : {
                True  : 0,
                False : 0,
            },
        },
        # reduction
        'Material Biconditional': {
            False  : {
                True  : 0,
                False : 0,
            },
            True : {
                True  : 0,
                False : 0,
            },
        },
        # reduction
        'Conditional': {
            False  : {
                True  : 0,
                False : 0,
            },
            True : {
                True  : 0,
                False : 0,
            },
        },
        # reduction
        'Biconditional': {
            False  : {
                True  : 0,
                False : 0,
            },
            True : {
                True  : 0,
                False : 0,
            },
        },
    }

class TableauxRules(object):
    """
    The Tableaux System for P3 contains the `FDE closure rule`_, and the
    `K3 closure rule`_. Some of the operator rules are the same as `FDE`_,
    most notably disjunction. However, many rules for P3 are different
    from `FDE`_, given the non-standard negation. Notably, an undesignated
    double-negation will branch.
    
    .. _FDE closure rule: fde.html#logics.fde.TableauxRules.Closure
    .. _K3 closure rule: k3.html#logics.k3.TableauxRules.Closure
    .. _FDE: fde.html
    """

    class DoubleNegationDesignated(logic.TableauxSystem.FilterNodeRule):
        """
        From an unticked, designated, double-negation node `n` on a branch `b`,
        add two undesignated nodes to `b`, one with the double-negatum, and one
        with the negatum. Then tick `n`.
        """
        negated     = True
        operator    = 'Negation'
        designation = True

        branch_level = 1
        ticking      = True

        def get_target_for_node(self, node, branch):
            s = self.sentence(node)
            si = s.operand
            return {
                'adds': [
                    [
                        {'sentence': negate(si), 'designated': False},
                        {'sentence':        si , 'designated': False},
                    ],
                ],
            }

        def apply_to_target(self, target):
            self.adz.apply_to_target(target)

        def score_candidate(self, target):
            return self.adz.closure_score(target)

    class DoubleNegationUndesignated(logic.TableauxSystem.FilterNodeRule):
        """
        From an unticked, undesignated, double-negation node `n` on a branch `b`,
        make two branches `b'` and `b''` from `b`. On `b'` add a designated
        node with the negatum, and on `b'` add a designated node with the
        double-negatum. Then tick `n`.
        """
        negated     = True
        operator    = 'Negation'
        designation = False

        branch_level = 2
        ticking      = True

        def get_target_for_node(self, node, branch):
            s = self.sentence(node)
            si = s.operand
            return {
                'adds': [
                    [
                        {'sentence': negate(si), 'designated': True},
                    ],
                    [
                        {'sentence':        si , 'designated': True},
                    ],
                ],
            }

        def apply_to_target(self, target):
            self.adz.apply_to_target(target)

        def score_candidate(self, target):
            return self.adz.closure_score(target)

    class AssertionDesignated(k3.TableauxRules.AssertionDesignated):
        """
        This rule is the same as the `FDE AssertionDesignated rule`_.

        .. _FDE AssertionDesignated rule: fde.html#logics.fde.TableauxRules.AssertionDesignated
        """
        pass

    class AssertionNegatedDesignated(k3.TableauxRules.AssertionNegatedDesignated):
        """
        This rule is the same as the `FDE AssertionNegatedDesignated rule`_.

        .. _FDE AssertionNegatedDesignated rule: fde.html#logics.fde.TableauxRules.AssertionNegatedDesignated
        """
        pass

    class AssertionUndesignated(k3.TableauxRules.AssertionUndesignated):
        """
        This rule is the same as the `FDE AssertionUndesignated rule`_.

        .. _FDE AssertionUndesignated rule: fde.html#logics.fde.TableauxRules.AssertionUndesignated
        """
        pass

    class AssertionNegatedUndesignated(k3.TableauxRules.AssertionNegatedUndesignated):
        """
        This rule is the same as the `FDE AssertionNegatedUndesignated rule`_.

        .. _FDE AssertionNegatedUndesignated rule: fde.html#logics.fde.TableauxRules.AssertionNegatedUndesignated
        """
        pass

    class ConjunctionDesignated(logic.TableauxSystem.FilterNodeRule):
        """
        From an unticked, designated conjunction node `n` on a branch `b`, add
        four undesignated nodes to `b`, one for each conjunct, and one for the
        negation of each conjunct. Then tick `n`.
        """

        operator    = 'Conjunction'
        designation = True

        branch_level = 1
        ticking      = True

        def get_target_for_node(self, node, branch):
            s = self.sentence(node)
            return {
                'adds': [
                    [
                        {'sentence': negate(s.lhs), 'designated': False},
                        {'sentence':        s.lhs , 'designated': False},
                        {'sentence': negate(s.rhs), 'designated': False},
                        {'sentence':        s.rhs , 'designated': False},
                    ],
                ],
            }

        def apply_to_target(self, target):
            self.adz.apply_to_target(target)

        def score_candidate(self, target):
            return self.adz.closure_score(target)

    class ConjunctionNegatedDesignated(logic.TableauxSystem.FilterNodeRule):
        """
        From an unticked, designated, negated conjunction node `n` on a branch
        `b`, make two branches `b'` and `b''` from `b`. On `b'` add a designated
        node with the first conjunct, and an undesignated node with the negation
        of the second conjunct. On `b''` add a designated node with the second
        conjunct, and an undesignated node with the negation of the frist conjunct.
        Then tick `n`.
        """

        negated     = True
        operator    = 'Conjunction'
        designation = True

        branch_level = 2
        ticking      = True

        def get_target_for_node(self, node, branch):
            s = self.sentence(node)
            return {
                'adds': [
                    [
                        {'sentence':        s.lhs , 'designated': True},
                        {'sentence': negate(s.rhs), 'designated': False},
                    ],
                    [
                        {'sentence':        s.rhs , 'designated': True},
                        {'sentence': negate(s.lhs), 'designated': False},
                    ],
                ],
            }

        def apply_to_target(self, target):
            self.adz.apply_to_target(target)

        def score_candidate(self, target):
            return self.adz.closure_score(target)

    class ConjunctionUndesignated(logic.TableauxSystem.FilterNodeRule):
        """
        From an unticked, undesignated conjunction node `n` on a branch `b`, make
        four branches `b'`, `b''`, `b'''`, and `b''''` from `b`. On `b'`, add a
        designated node with the negation of the first conjunct. On `b''`, add
        a designated node ith the first conjunct. On `b'''`, add a designated
        node with the negation of the second conjunct. On `b''''`, add a designated
        node with the second conjunct. Then tick `n`.
        """

        operator    = 'Conjunction'
        designation = False

        branch_level = 4
        ticking      = True

        def get_target_for_node(self, node, branch):
            s = self.sentence(node)
            return {
                'adds': [
                    [
                        {'sentence': negate(s.lhs), 'designated': True},
                    ],
                    [
                        {'sentence':        s.lhs , 'designated': True},
                    ],
                    [
                        {'sentence': negate(s.rhs), 'designated': True},
                    ],
                    [
                        {'sentence':        s.rhs , 'designated': True},
                    ],
                ],
            }

        def apply_to_target(self, target):
            self.adz.apply_to_target(target)

        def score_candidate(self, target):
            return self.adz.closure_score(target)

    class ConjunctionNegatedUndesignated(logic.TableauxSystem.FilterNodeRule):
        """
        From an unticked, undesignated, negated conjunction node `n` on a branch
        `b`, make three branches `b'`, `b''`, and `b'''` from `b`. On `b'`, add
        four undesignated nodes, one for each conjunct, and one for the negation
        of each conjunct. On `b''`, add a designated node with the negation of
        the first conjunct. On `b'''`, add a designated node with the negation
        of the second conjunct. Then tick `n`.
        """

        negated     = True
        operator    = 'Conjunction'
        designation = False

        branch_level = 3
        ticking      = True

        def get_target_for_node(self, node, branch):
            s = self.sentence(node)
            return {
                'adds': [
                    [
                        {'sentence': negate(s.lhs), 'designated': False},
                        {'sentence':        s.lhs , 'designated': False},
                        {'sentence': negate(s.rhs), 'designated': False},
                        {'sentence':        s.rhs , 'designated': False},
                    ],
                    [
                        {'sentence': negate(s.lhs), 'designated': True},
                    ],
                    [
                        {'sentence': negate(s.rhs), 'designated': True},
                    ],
                ],
            }

        def apply_to_target(self, target):
            self.adz.apply_to_target(target)

        def score_candidate(self, target):
            return self.adz.closure_score(target)

    class DisjunctionDesignated(k3.TableauxRules.DisjunctionDesignated):
        """
        This rule is the same as the `FDE DisjunctionDesignated rule`_.

        .. _FDE DisjunctionDesignated rule: fde.html#logics.fde.TableauxRules.DisjunctionDesignated
        """
        pass
            
    class DisjunctionNegatedDesignated(k3.TableauxRules.DisjunctionNegatedDesignated):
        """
        This rule is the same as the `FDE DisjunctionNegatedDesignated rule`_.

        .. _FDE DisjunctionNegatedDesignated rule: fde.html#logics.fde.TableauxRules.DisjunctionNegatedDesignated
        """
        pass

    class DisjunctionUndesignated(k3.TableauxRules.DisjunctionUndesignated):
        """
        This rule is the same as the `FDE DisjunctionUndesignated rule`_.

        .. _FDE DisjunctionUndesignated rule: fde.html#logics.fde.TableauxRules.DisjunctionUndesignated
        """
        pass

    class DisjunctionNegatedUndesignated(k3.TableauxRules.DisjunctionNegatedUndesignated):
        """
        This rule is the same as the `FDE DisjunctionNegatedUndesignated rule`_.

        .. _FDE DisjunctionNegatedUndesignated rule: fde.html#logics.fde.TableauxRules.DisjunctionNegatedUndesignated
        """
        pass

    class MaterialConditionalDesignated(logic.TableauxSystem.FilterNodeRule):
        """
        This rule reduces to a disjunction.
        """

        operator    = 'Material Conditional'
        designation = True

        branch_level = 1
        ticking      = True

        def get_target_for_node(self, node, branch):
            s = self.sentence(node)
            disj = operate('Disjunction', [negate(s.lhs), s.rhs])
            return {
                'adds': [
                    [
                        {'sentence': disj, 'designated': self.designation},
                    ],
                ],
            }

        def apply_to_target(self, target):
            self.adz.apply_to_target(target)

        def score_candidate(self, target):
            return self.adz.closure_score(target)
            
    class MaterialConditionalNegatedDesignated(logic.TableauxSystem.FilterNodeRule):
        """
        This rule reduces to a disjunction.
        """

        negated     = True
        operator    = 'Material Conditional'
        designation = True

        branch_level = 1
        ticking      = True

        def get_target_for_node(self, node, branch):
            s = self.sentence(node)
            disj = operate('Disjunction', [negate(s.lhs), s.rhs])
            return {
                'adds': [
                    [
                        {'sentence': negate(disj), 'designated': self.designation},
                    ],
                ],
            }

        def apply_to_target(self, target):
            self.adz.apply_to_target(target)

        def score_candidate(self, target):
            return self.adz.closure_score(target)

    class MaterialConditionalUndesignated(logic.TableauxSystem.FilterNodeRule):
        """
        This rule reduces to a disjunction.
        """

        operator    = 'Material Conditional'
        designation = False

        branch_level = 1
        ticking      = True

        def get_target_for_node(self, node, branch):
            s = self.sentence(node)
            disj = operate('Disjunction', [negate(s.lhs), s.rhs])
            return {
                'adds': [
                    [
                        {'sentence': disj, 'designated': self.designation},
                    ],
                ],
            }

        def apply_to_target(self, target):
            self.adz.apply_to_target(target)

        def score_candidate(self, target):
            return self.adz.closure_score(target)

    class MaterialConditionalNegatedUndesignated(logic.TableauxSystem.FilterNodeRule):
        """
        This rule reduces to a disjunction.
        """

        negated     = True
        operator    = 'Material Conditional'
        designation = False

        branch_level = 1
        ticking      = True

        def get_target_for_node(self, node, branch):
            s = self.sentence(node)
            disj = operate('Disjunction', [negate(s.lhs), s.rhs])
            return {
                'adds': [
                    [
                        {'sentence': negate(disj), 'designated': self.designation},
                    ],
                ],
            }

        def apply_to_target(self, target):
            self.adz.apply_to_target(target)

        def score_candidate(self, target):
            return self.adz.closure_score(target)

    class MaterialBiconditionalDesignated(logic.TableauxSystem.FilterNodeRule):
        """
        This rule reduces to a conjunction of material conditionals.
        """

        operator    = 'Material Biconditional'
        designation = True

        branch_level = 1
        ticking      = True

        def get_target_for_node(self, node, branch):
            s = self.sentence(node)
            cond1 = operate('Material Conditional', [s.lhs, s.rhs])
            cond2 = operate('Material Conditional', [s.rhs, s.lhs])
            conj = operate('Conjunction', [cond1, cond2])
            return {
                'adds': [
                    [
                        {'sentence': conj, 'designated': self.designation},
                    ],
                ],
            }

        def apply_to_target(self, target):
            self.adz.apply_to_target(target)

        def score_candidate(self, target):
            return self.adz.closure_score(target)

    class MaterialBiconditionalNegatedDesignated(logic.TableauxSystem.FilterNodeRule):
        """
        This rule reduces to a conjunction of material conditionals.
        """

        negated     = True
        operator    = 'Material Biconditional'
        designation = True

        branch_level = 1
        ticking      = True

        conjunct_op = 'Material Conditional'

        def get_target_for_node(self, node, branch):
            s = self.sentence(node)
            cond1 = operate(self.conjunct_op, [s.lhs, s.rhs])
            cond2 = operate(self.conjunct_op, [s.rhs, s.lhs])
            conj = operate('Conjunction', [cond1, cond2])
            return {
                'adds': [
                    [
                        {'sentence': negate(conj), 'designated': self.designation},
                    ],
                ],
            }

        def apply_to_target(self, target):
            self.adz.apply_to_target(target)

        def score_candidate(self, target):
            return self.adz.closure_score(target)

    class MaterialBiconditionalUndesignated(logic.TableauxSystem.FilterNodeRule):
        """
        This rule reduces to a conjunction of material conditionals.
        """

        operator    = 'Material Biconditional'
        designation = False

        branch_level = 1
        ticking      = True

        conjunct_op = 'Material Conditional'

        def get_target_for_node(self, node, branch):
            s = self.sentence(node)
            cond1 = operate(self.conjunct_op, [s.lhs, s.rhs])
            cond2 = operate(self.conjunct_op, [s.rhs, s.lhs])
            conj = operate('Conjunction', [cond1, cond2])
            return {
                'adds': [
                    [
                        {'sentence': conj, 'designated': self.designation},
                    ],
                ],
            }

        def apply_to_target(self, target):
            self.adz.apply_to_target(target)

        def score_candidate(self, target):
            return self.adz.closure_score(target)

    class MaterialBiconditionalNegatedUndesignated(logic.TableauxSystem.FilterNodeRule):
        """
        This rule reduces to a conjunction of material conditionals.
        """

        negated     = True
        operator    = 'Material Biconditional'
        designation = False

        branch_level = 1
        ticking      = True

        conjunct_op = 'Material Conditional'

        def get_target_for_node(self, node, branch):
            s = self.sentence(node)
            cond1 = operate(self.conjunct_op, [s.lhs, s.rhs])
            cond2 = operate(self.conjunct_op, [s.rhs, s.lhs])
            conj = operate('Conjunction', [cond1, cond2])
            return {
                'adds': [
                    [
                        {'sentence': negate(conj), 'designated': self.designation},
                    ],
                ],
            }

        def apply_to_target(self, target):
            self.adz.apply_to_target(target)

        def score_candidate(self, target):
            return self.adz.closure_score(target)

    class ConditionalDesignated(MaterialConditionalDesignated):
        """
        This is the same as the rule for the material conditional.
        """

        operator    = 'Conditional'

    class ConditionalNegatedDesignated(MaterialConditionalNegatedDesignated):
        """
        This is the same as the rule for the material conditional.
        """

        operator    = 'Conditional'

    class ConditionalUndesignated(MaterialConditionalUndesignated):
        """
        This is the same as the rule for the material conditional.
        """

        operator    = 'Conditional'

    class ConditionalNegatedUndesignated(MaterialConditionalNegatedUndesignated):
        """
        This is the same as the rule for the material conditional.
        """

        operator    = 'Conditional'

    class BiconditionalDesignated(MaterialBiconditionalDesignated):
        """
        This rule reduces to a conjunction of conditionals.
        """

        operator    = 'Biconditional'
        conjunct_op = 'Conditional'

    class BiconditionalNegatedDesignated(MaterialBiconditionalNegatedDesignated):
        """
        This rule reduces to a conjunction of conditionals.
        """

        operator    = 'Biconditional'
        conjunct_op = 'Conditional'

    class BiconditionalUndesignated(MaterialBiconditionalUndesignated):
        """
        This rule reduces to a conjunction of conditionals.
        """

        operator    = 'Biconditional'
        conjunct_op = 'Conditional'

    class BiconditionalNegatedUndesignated(MaterialBiconditionalNegatedUndesignated):
        """
        This rule reduces to a conjunction of conditionals.
        """

        operator    = 'Biconditional'
        conjunct_op = 'Conditional'

    class ExistentialDesignated(k3.TableauxRules.ExistentialDesignated):
        """
        This rule is the same as the `FDE ExistentialDesignated rule`_.

        .. _FDE ExistentialDesignated rule: fde.html#logics.fde.TableauxRules.ExistentialDesignated
        """
        pass

    class ExistentialNegatedDesignated(k3.TableauxRules.ExistentialNegatedDesignated):
        """
        This rule is the same as the `FDE ExistentialNegatedDesignated rule`_.

        .. _FDE ExistentialNegatedDesignated rule: fde.html#logics.fde.TableauxRules.ExistentialNegatedDesignated
        """
        pass

    class ExistentialUndesignated(k3.TableauxRules.ExistentialUndesignated):
        """
        This rule is the same as the `FDE ExistentialUndesignated rule`_.

        .. _FDE ExistentialUndesignated rule: fde.html#logics.fde.TableauxRules.ExistentialUndesignated
        """
        pass

    class ExistentialNegatedUndesignated(k3.TableauxRules.ExistentialNegatedUndesignated):
        """
        This rule is the same as the `FDE ExistentialNegatedUndesignated rule`_.

        .. _FDE ExistentialNegatedUndesignated rule: fde.html#logics.fde.TableauxRules.ExistentialNegatedUndesignated
        """
        pass

    class UniversalDesignated(k3.TableauxRules.UniversalDesignated):
        """
        This rule is the same as the `FDE UniversalDesignated rule`_.

        .. _FDE UniversalDesignated rule: fde.html#logics.fde.TableauxRules.UniversalDesignated
        """
        pass

    class UniversalNegatedDesignated(k3.TableauxRules.UniversalNegatedDesignated):
        """
        This rule is the same as the `FDE UniversalNegatedDesignated rule`_.

        .. _FDE UniversalNegatedDesignated rule: fde.html#logics.fde.TableauxRules.UniversalNegatedDesignated
        """
        pass

    class UniversalUndesignated(k3.TableauxRules.UniversalUndesignated):
        """
        This rule is the same as the `FDE UniversalUndesignated rule`_.

        .. _FDE UniversalUndesignated rule: fde.html#logics.fde.TableauxRules.UniversalUndesignated
        """
        pass

    class UniversalNegatedUndesignated(k3.TableauxRules.UniversalNegatedUndesignated):
        """
        This rule is the same as the `FDE UniversalNegatedUndesignated rule`_.

        .. _FDE UniversalNegatedUndesignated rule: fde.html#logics.fde.TableauxRules.UniversalNegatedUndesignated
        """
        pass

    closure_rules = list(k3.TableauxRules.closure_rules)

    rule_groups = [
        [
            # non-branching rules

            AssertionDesignated,
            AssertionUndesignated,
            AssertionNegatedDesignated,
            AssertionNegatedUndesignated,

            ConjunctionDesignated,

            DisjunctionUndesignated,
            DisjunctionNegatedDesignated,

            ExistentialNegatedDesignated,
            ExistentialNegatedUndesignated,
            UniversalNegatedDesignated,
            UniversalNegatedUndesignated,

            DoubleNegationDesignated,
            
            # reduction rules (thus, non-branching)
            MaterialConditionalDesignated,
            MaterialConditionalUndesignated,
            MaterialConditionalNegatedDesignated,
            MaterialConditionalNegatedUndesignated,
            ConditionalDesignated,
            ConditionalUndesignated,
            ConditionalNegatedDesignated,
            ConditionalNegatedUndesignated,
            MaterialBiconditionalDesignated,
            MaterialBiconditionalUndesignated,
            MaterialBiconditionalNegatedDesignated,
            MaterialBiconditionalNegatedUndesignated,
            BiconditionalDesignated,
            BiconditionalUndesignated,
            BiconditionalNegatedDesignated,
            BiconditionalNegatedUndesignated,
        ],
        [
            # two-branching rules
            DoubleNegationUndesignated,

            ConjunctionNegatedDesignated,

            DisjunctionDesignated,
            DisjunctionNegatedUndesignated,            
        ],
        [
            # three-branching rules
            ConjunctionNegatedUndesignated,
        ],
        [
            # four-branching rules
            ConjunctionUndesignated,
        ],
        [
            ExistentialDesignated,
            ExistentialUndesignated,
        ],
        [
            UniversalDesignated,
            UniversalUndesignated,
        ]
    ]