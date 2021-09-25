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
# pytableaux - Bochvar 3 External logic
name = 'B3E'

class Meta(object):

    title    = 'Bochvar 3 External Logic'
    category = 'Many-valued'

    description = 'Three-valued logic (True, False, Neither) with assertion operator'

    tags = ['many-valued', 'gappy', 'non-modal', 'first-order']
    
    category_display_order = 5

import logic
from logic import assertion, operate, negate
from . import k3, k3w, fde

def gap(v):
    return min(v, 1 - v)

def crunch(v):
    return v - gap(v)

class Model(k3w.Model):
    """
    A B3E model is just like a `K3W model`_ with different tables for some of the connectives.

    .. _K3W model: k3w.html#logics.k3w.Model
    """

    def value_of_operated(self, sentence, **kw):
        """
        The value of a sentence with a truth-functional operator is determined by
        the values of its operands according to the following tables.

        Note that the conditional operator O{Conditional} is definable in terms of the
        assertion operator O{Assertion}, as P{~\\*A V \\*B}.

        //truth_tables//b3e//

        Bochvar also defined `external` versions of O{Conjunction} and O{Disjunction}
        using the assertion operator:

        * External conjunction: P{\\*A & \\*B}
        * External disjunction: P{\\*A V \\*B}

        These connectives always result in a classical value. For compatibility,
        we use the standard `internal` readings of O{Conjunction} and O{Disjunction},
        and use the `internal` reading for O{Conditional} and O{Biconditional}.
        """
        return super(Model, self).value_of_operated(sentence, **kw)

    def truth_function(self, operator, a, b=None):
        if operator == 'Assertion':
            return self.cvals[crunch(self.nvals[a])]
        elif operator == 'Conditional':
            return self.truth_function(
                'Disjunction',
                self.truth_function('Negation', self.truth_function('Assertion', a)),
                self.truth_function('Assertion', b)
            )
        elif operator == 'Biconditional':
            return fde.Model.truth_function(self, operator, a, b)
        return super(Model, self).truth_function(operator, a, b)

class TableauxSystem(fde.TableauxSystem):
    """
    B3E's Tableaux System inherits directly from the `FDE system`_, employing
    designation markers, and building the trunk in the same way.

    .. _FDE system: fde.html#logics.fde.TableauxSystem
    """

    # operator => negated => designated
    branchables = dict(k3w.TableauxSystem.branchables)
    branchables.update({
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
    })

class DefaultNodeRule(fde.DefaultNodeRule):
    pass

class TableauxRules(object):
    """
    The closure rules for B3E are the `FDE closure rule`_, and the `K3 closure rule`_.
    The operator rules are mostly a mix of `FDE`_ and `K3W`_ rules, but with different
    rules for the assertion, conditional and biconditional operators.

    .. _FDE closure rule: fde.html#logics.fde.TableauxRules.DesignationClosure
    .. _K3 closure rule: k3.html#logics.k3.TableauxRules.GlutClosure
    .. _FDE: fde.html
    .. _K3W: k3w.html
    """

    class DoubleNegationDesignated(k3w.TableauxRules.DoubleNegationDesignated):
        """
        This rule is the same as the `FDE DoubleNegationDesignated rule`_.

        //ruledoc//fde//DoubleNegationDesignated//

        .. _FDE DoubleNegationDesignated rule: fde.html#logics.fde.TableauxRules.DoubleNegationDesignated
        """
        pass

    class DoubleNegationUndesignated(k3w.TableauxRules.DoubleNegationUndesignated):
        """
        This rule is the same as the `FDE DoubleNegationUndesignated rule`_.

        //ruledoc//fde//DoubleNegationUndesignated//

        .. _FDE DoubleNegationUndesignated rule: fde.html#logics.fde.TableauxRules.DoubleNegationUndesignated
        """
        pass

    class AssertionDesignated(k3w.TableauxRules.AssertionDesignated):
        """
        This rule is the same as the `FDE AssertionDesignated rule`_.

        //ruledoc//fde//AssertionDesignated//

        .. _FDE AssertionDesignated rule: fde.html#logics.fde.TableauxRules.AssertionDesignated
        """
        pass

    class AssertionNegatedDesignated(DefaultNodeRule):
        """
        From an unticked, designated, negated assertion node *n* on a branch *b*,
        add an undesignated node to *b* with the assertion of *n*, then tick *n*.
        """

        negated     = True
        operator    = 'Assertion'
        designation = True

        branch_level = 1

        def get_target_for_node(self, node, branch):
            s = self.sentence(node)
            return {
                'adds': [
                    [
                        {'sentence': s.operand, 'designated': False},
                    ],
                ],
            }

    class AssertionUndesignated(AssertionNegatedDesignated):
        """
        From an unticked, undesignated assertion node *n* on a branch *b*, add
        an undesignated node to *b* with the assertion of *n*, then tick *n*.
        """

        negated     = False
        designation = False

    class AssertionNegatedUndesignated(AssertionNegatedDesignated):
        """
        From an unticked, undesignated, negated assertion node *n* on a branch *b*, add
        a designated node to *b* with the assertion of *n*, then tick *n*.
        """

        negated     = True
        designation = False

        def get_target_for_node(self, node, branch):
            s = self.sentence(node)
            return {
                'adds': [
                    [
                        {'sentence': s.operand, 'designated': True},
                    ],
                ],
            }

    class ConjunctionDesignated(k3w.TableauxRules.ConjunctionDesignated):
        """
        This rule is the same as the `FDE ConjunctionDesignated rule`_.

        //ruledoc//fde//ConjunctionDesignated//

        .. _FDE ConjunctionDesignated rule: fde.html#logics.fde.TableauxRules.ConjunctionDesignated
        """
        pass

    class ConjunctionNegatedDesignated(k3w.TableauxRules.ConjunctionNegatedDesignated):
        """
        This rule is the same as the `K3W ConjunctionNegatedDesignated rule`_.

        //ruledoc//k3w//ConjunctionNegatedDesignated//

        .. _K3W ConjunctionNegatedDesignated rule: k3w.html#logics.k3w.TableauxRules.ConjunctionNegatedDesignated
        """
        pass

    class ConjunctionUndesignated(k3w.TableauxRules.ConjunctionUndesignated):
        """
        This rule is the same as the `FDE ConjunctionUndesignated rule`_.

        //ruledoc//fde//ConjunctionUndesignated//

        .. _FDE ConjunctionUndesignated rule: fde.html#logics.fde.TableauxRules.ConjunctionUndesignated
        """
        pass

    class ConjunctionNegatedUndesignated(k3w.TableauxRules.ConjunctionNegatedUndesignated):
        """
        This rule is the same as the `K3W ConjunctionNegatedUndesignated rule`_.

        //ruledoc//k3w//ConjunctionNegatedUndesignated//

        .. _K3W ConjunctionNegatedUndesignated rule: k3w.html#logics.k3w.TableauxRules.ConjunctionNegatedUndesignated
        """
        pass

    class DisjunctionDesignated(k3w.TableauxRules.DisjunctionDesignated):
        """
        This rule is the same as the `K3W DisjunctionDesignated rule`_.

        //ruledoc//k3w//DisjunctionDesignated//

        .. _K3W DisjunctionDesignated rule: k3w.html#logics.k3w.TableauxRules.DisjunctionDesignated
        """
        pass

    class DisjunctionNegatedDesignated(k3w.TableauxRules.DisjunctionNegatedDesignated):
        """
        This rule is the same as the `FDE DisjunctionNegatedDesignated rule`_.

        //ruledoc//fde//DisjunctionNegatedDesignated//

        .. _FDE DisjunctionNegatedDesignated rule: fde.html#logics.fde.TableauxRules.DisjunctionNegatedDesignated
        """
        pass

    class DisjunctionUndesignated(k3w.TableauxRules.DisjunctionUndesignated):
        """
        This rule is the same as the `K3W DisjunctionUndesignated rule`_.

        //ruledoc//k3w//DisjunctionUndesignated//

        .. _K3W DisjunctionUndesignated rule: k3w.html#logics.k3w.TableauxRules.DisjunctionUndesignated
        """
        pass

    class DisjunctionNegatedUndesignated(k3w.TableauxRules.DisjunctionNegatedUndesignated):
        """
        This rule is the same as the `K3W DisjunctionNegatedUndesignated rule`_.

        //ruledoc//k3w//DisjunctionNegatedUndesignated//

        .. _K3W DisjunctionNegatedUndesignated rule: k3w.html#logics.k3w.TableauxRules.DisjunctionNegatedUndesignated
        """
        pass

    class MaterialConditionalDesignated(k3w.TableauxRules.MaterialConditionalDesignated):
        """
        This rule is the same as the `K3W MaterialConditionalDesignated rule`_.

        //ruledoc//k3w//MaterialConditionalDesignated//

        .. _K3W MaterialConditionalDesignated rule: k3w.html#logics.k3w.TableauxRules.MaterialConditionalDesignated
        """
        pass

    class MaterialConditionalNegatedDesignated(k3w.TableauxRules.MaterialConditionalNegatedDesignated):
        """
        This rule is the same as the `K3W MaterialConditionalNegatedDesignated rule`_.

        //ruledoc//k3w//MaterialConditionalNegatedDesignated//

        .. _K3W MaterialConditionalNegatedDesignated rule: k3w.html#logics.k3w.TableauxRules.MaterialConditionalNegatedDesignated
        """
        pass

    class MaterialConditionalUndesignated(k3w.TableauxRules.MaterialConditionalUndesignated):
        """
        This rule is the same as the `K3W MaterialConditionalUndesignated rule`_.

        //ruledoc//k3w//MaterialConditionalUndesignated//

        .. _K3W MaterialConditionalUndesignated rule: k3w.html#logics.k3w.TableauxRules.MaterialConditionalUndesignated
        """
        pass

    class MaterialConditionalNegatedUndesignated(k3w.TableauxRules.MaterialConditionalNegatedUndesignated):
        """
        This rule is the same as the `K3W MaterialConditionalNegatedUndesignated rule`_.

        //ruledoc//k3w//MaterialConditionalNegatedUndesignated//

        .. _K3W MaterialConditionalNegatedUndesignated rule: k3w.html#logics.k3w.TableauxRules.MaterialConditionalNegatedUndesignated
        """
        pass

    class MaterialBiconditionalDesignated(k3w.TableauxRules.MaterialBiconditionalDesignated):
        """
        This rule is the same as the `K3W MaterialBiconditionalDesignated rule`_.

        //ruledoc//k3w//MaterialBiconditionalDesignated//

        .. _K3W MaterialBiconditionalDesignated rule: k3w.html#logics.k3w.TableauxRules.MaterialBiconditionalDesignated
        """
        pass

    class MaterialBiconditionalNegatedDesignated(k3w.TableauxRules.MaterialBiconditionalNegatedDesignated):
        """
        This rule is the same as the `K3W MaterialBiconditionalNegatedDesignated rule`_.

        //ruledoc//k3w//MaterialBiconditionalNegatedDesignated//

        .. _K3W MaterialBiconditionalNegatedDesignated rule: k3w.html#logics.k3w.TableauxRules.MaterialBiconditionalNegatedDesignated
        """
        pass

    class MaterialBiconditionalUndesignated(k3w.TableauxRules.MaterialBiconditionalUndesignated):
        """
        This rule is the same as the `K3W MaterialBiconditionalUndesignated rule`_.

        //ruledoc//k3w//MaterialBiconditionalUndesignated//

        .. _K3W MaterialBiconditionalUndesignated rule: k3w.html#logics.k3w.TableauxRules.MaterialBiconditionalUndesignated
        """
        pass

    class MaterialBiconditionalNegatedUndesignated(k3w.TableauxRules.MaterialBiconditionalNegatedUndesignated):
        """
        This rule is the same as the `K3W MaterialBiconditionalNegatedUndesignated rule`_.

        //ruledoc//k3w//MaterialBiconditionalNegatedUndesignated//

        .. _K3W MaterialBiconditionalNegatedUndesignated rule: k3w.html#logics.k3w.TableauxRules.MaterialBiconditionalNegatedUndesignated
        """
        pass

    class ConditionalDesignated(DefaultNodeRule):
        """
        From an unticked, designated conditional node *n* on a branch *b*,
        add a designated node to *b* with a disjunction, where the
        first disjunction is the negation of the assertion of the antecedent,
        and the second disjunct is the assertion of the consequent. Then tick *n*.
        """
        
        operator    = 'Conditional'
        designation = True

        branch_level = 1

        def get_target_for_node(self, node, branch):
            s = self.sentence(node)
            sn = operate(
                'Disjunction',
                [negate(assertion(s.lhs)), assertion(s.rhs)]
            )
            # keep negated neutral for inheritance below
            if self.negated:
                sn = negate(sn)
            return {
                'adds': [
                    [
                        # keep designation neutral for inheritance below
                        {'sentence': sn, 'designated': self.designation},
                    ],
                ],
            }

    class ConditionalNegatedDesignated(DefaultNodeRule):
        """
        From an unticked, designated negated conditional node *n* on a branch *b*,
        add a designated node with the antecedent, and an undesigntated node
        with the consequent to *b*. Then tick *n*.
        """

        negated     = True
        operator    = 'Conditional'
        designation = True

        branch_level = 1

        def get_target_for_node(self, node, branch):
            s = self.sentence(node)
            return {
                'adds': [
                    [
                        {'sentence': s.lhs, 'designated': True},
                        {'sentence': s.rhs, 'designated': False},
                    ],
                ],
            }

    class ConditionalUndesignated(ConditionalNegatedDesignated):
        """
        From an unticked, undesignated conditional node *n* on a branch *b*,
        add a designated node with the antecedent, and an undesigntated node
        with the consequent to *b*. Then tick *n*.
        """

        negated     = False
        designation = False

    class ConditionalNegatedUndesignated(ConditionalDesignated):
        """
        From an unticked, undesignated, negated conditional node *n* on a branch *b*,
        add an undesignated node to *b* with a negated material conditional, where the
        operands are preceded by the Assertion operator, then tick *n*.
        """

        negated     = True
        designation = False

    class BiconditionalDesignated(DefaultNodeRule):
        """
        From an unticked, designated biconditional node *n* on a branch *b*, add two
        designated nodes to *b*, one with a disjunction, where the
        first disjunct is the negated asserted antecedent, and the second disjunct
        is the asserted consequent, and the other node is the same with the disjuncts
        inverted. Then tick *n*.
        """

        operator    = 'Biconditional'
        designation = True

        branch_level = 2

        def get_target_for_node(self, node, branch):
            s = self.sentence(node)
            d = self.designation
            sn1 = operate('Disjunction', [
                negate(assertion(s.lhs)),
                assertion(s.rhs)
            ])
            sn2 = operate('Disjunction', [
                negate(assertion(s.rhs)),
                assertion(s.lhs)
            ])
            # keep negated neutral for inheritance below
            if self.negated:
                sn1 = negate(sn1)
                sn2 = negate(sn2)
            return {
                'adds': [
                    [
                        # keep designation neutral for inheritance below
                        {'sentence': sn1, 'designated': d},
                        {'sentence': sn2, 'designated': d},
                    ],
                ],
            }

    class BiconditionalNegatedDesignated(BiconditionalDesignated):
        """
        From an unticked, designated, biconditional node *n* on a branch *b*, add two
        undesignated nodes to *b*, one with a negated disjunction, where the
        first disjunct is the negated asserted antecedent, and the second disjunct
        is the asserted consequent, and the other node is the same with the disjuncts
        inverted. Then tick *n*.
        """

        negated     = True
        designation = True

    class BiconditionalUndesignated(BiconditionalDesignated):
        """
        From an unticked, undesignated biconditional node *n* on a branch *b*, add two
        undesignated nodes to *b*, one with a disjunction, where the
        first disjunct is the negated asserted antecedent, and the second disjunct
        is the asserted consequent, and the other node is the same with the disjuncts
        inverted. Then tick *n*.
        """

        negated     = False
        designation = False

    class BiconditionalNegatedUndesignated(BiconditionalUndesignated):
        """
        From an unticked, designated, biconditional node *n* on a branch *b*, add two
        undesignated nodes to *b*, one with a negated disjunction, where the
        first disjunct is the negated asserted antecedent, and the second disjunct
        is the asserted consequent, and the other node is the same with the disjuncts
        inverted. Then tick *n*.
        """

        negated     = True
        designation = False

    class ExistentialDesignated(k3w.TableauxRules.ExistentialDesignated):
        """
        This rule is the same as the `FDE ExistentialDesignated rule`_.

        //ruledoc//fde//ExistentialDesignated//

        .. _FDE ExistentialDesignated rule: fde.html#logics.fde.TableauxRules.ExistentialDesignated
        """
        pass

    class ExistentialNegatedDesignated(k3w.TableauxRules.ExistentialNegatedDesignated):
        """
        This rule is the same as the `FDE ExistentialNegatedDesignated rule`_.

        //ruledoc//fde//ExistentialNegatedDesignated//

        .. _FDE ExistentialNegatedDesignated rule: fde.html#logics.fde.TableauxRules.ExistentialNegatedDesignated
        """
        pass

    class ExistentialUndesignated(k3w.TableauxRules.ExistentialUndesignated):
        """
        This rule is the same as the `FDE ExistentialUndesignated rule`_.

        //ruledoc//fde//ExistentialUndesignated//

        .. _FDE ExistentialUndesignated rule: fde.html#logics.fde.TableauxRules.ExistentialUndesignated
        """
        pass

    class ExistentialNegatedUndesignated(k3w.TableauxRules.ExistentialNegatedUndesignated):
        """
        This rule is the same as the `FDE ExistentialNegatedUndesignated rule`_.

        //ruledoc//fde//ExistentialNegatedUndesignated//

        .. _FDE ExistentialNegatedUndesignated rule: fde.html#logics.fde.TableauxRules.ExistentialNegatedUndesignated
        """
        pass

    class UniversalDesignated(k3w.TableauxRules.UniversalDesignated):
        """
        This rule is the same as the `FDE UniversalDesignated rule`_.

        //ruledoc//fde//UniversalDesignated//

        .. _FDE UniversalDesignated rule: fde.html#logics.fde.TableauxRules.UniversalDesignated
        """
        pass

    class UniversalNegatedDesignated(k3w.TableauxRules.UniversalNegatedDesignated):
        """
        This rule is the same as the `FDE UniversalNegatedDesignated rule`_.

        //ruledoc//fde//UniversalNegatedDesignated//

        .. _FDE UniversalNegatedDesignated rule: fde.html#logics.fde.TableauxRules.UniversalNegatedDesignated
        """
        pass

    class UniversalUndesignated(k3w.TableauxRules.UniversalUndesignated):
        """
        This rule is the same as the `FDE UniversalUndesignated rule`_.

        //ruledoc//fde//UniversalUndesignated//

        .. _FDE UniversalUndesignated rule: fde.html#logics.fde.TableauxRules.UniversalUndesignated
        """
        pass

    class UniversalNegatedUndesignated(k3w.TableauxRules.UniversalNegatedUndesignated):
        """
        This rule is the same as the `FDE UniversalNegatedUndesignated rule`_.

        //ruledoc//fde//UniversalNegatedUndesignated//

        .. _FDE UniversalNegatedUndesignated rule: fde.html#logics.fde.TableauxRules.UniversalNegatedUndesignated
        """
        pass

    closure_rules = list(k3.TableauxRules.closure_rules)

    rule_groups = [
        [
            AssertionDesignated,
            AssertionUndesignated,
            AssertionNegatedDesignated,
            AssertionNegatedUndesignated,
            ConjunctionDesignated, 
            DisjunctionNegatedDesignated,
            ConditionalNegatedDesignated,
            ConditionalUndesignated,
            ExistentialNegatedDesignated,
            ExistentialNegatedUndesignated,
            UniversalNegatedDesignated,
            UniversalNegatedUndesignated,
            DoubleNegationDesignated,
            DoubleNegationUndesignated,
            # reduction rules (thus, non-branching)
            MaterialConditionalDesignated,
            MaterialConditionalUndesignated,
            MaterialConditionalNegatedDesignated,
            MaterialConditionalNegatedUndesignated,
            ConditionalDesignated,
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
            ConjunctionUndesignated,
        ],
        [
            # three-branching rules
            DisjunctionDesignated,
            DisjunctionUndesignated,
            ConjunctionNegatedDesignated,
            ConjunctionNegatedUndesignated,
            # (formerly) four-branching rules
            DisjunctionNegatedUndesignated,
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