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
# pytableaux - R-mingle 3 logic
name = 'RM3'

class Meta(object):
    title = 'R-mingle 3'
    description = 'Three-valued logic (True, False, Both) with a primitive Conditional operator'
    tags = ['many-valued', 'glutty', 'non-modal', 'first-order']
    category = 'Many-valued'
    category_display_order = 8

import logic
from logic import negate, negative, operate
from . import fde, lp, l3

class Model(lp.Model):
    """
    An RM3 model is just like an `LP model`_ with different tables for the conditional
    and bi-conditional operators.

    .. _LP model: lp.html#logics.lp.Model
    """

    def value_of_operated(self, sentence, **kw):
        """
        The value of a sentence with a truth-functional operator is determined by
        the values of its operands according to the following tables.

        //truth_tables//rm3//
        """
        return super(Model, self).value_of_operated(sentence, **kw)

    def truth_function(self, operator, a, b=None):
        if operator == 'Conditional' and self.nvals[a] > self.nvals[b]:
            return 'F'
        return super(Model, self).truth_function(operator, a, b)

class TableauxSystem(fde.TableauxSystem):
    """
    RM3's Tableaux System inherits directly from the `FDE system`_, employing
    designation markers, and building the trunk in the same way.

    .. _FDE system: fde.html#logics.fde.TableauxSystem
    """
    branchables = dict(fde.TableauxSystem.branchables)
    branchables.update({
        'Conditional': {
            False  : {
                True  : 2,
                False : 1,
            },
            True : {
                True  : 0,
                False : 1,
            },
        },
        'Biconditional': {
            False  : {
                True  : 2,
                False : 1,
            },
            True : {
                True  : 1,
                False : 1,
            },
        },
    })

class TableauxRules(object):
    """
    The closure rules for RM3 are the `FDE closure rule`_, and the `LP closure rule`_.
    Most of the operator rules are the same as `FDE`_, except for the conditional
    rules. The biconditional rules are borrowed from `L3_`, since they are
    simplification rules.

    .. _FDE closure rule: fde.html#logics.fde.TableauxRules.Closure
    .. _LP closure rule: lp.html#logics.lp.TableauxRules.Closure
    """

    class DoubleNegationDesignated(lp.TableauxRules.DoubleNegationDesignated):
        """
        This rule is the same as the `FDE DoubleNegationDesignated rule`_.

        .. _FDE DoubleNegationDesignated rule: fde.html#logics.fde.TableauxRules.DoubleNegationDesignated
        """
        pass

    class DoubleNegationUndesignated(lp.TableauxRules.DoubleNegationUndesignated):
        """
        This rule is the same as the `FDE DoubleNegationUndesignated rule`_.

        .. _FDE DoubleNegationUndesignated rule: fde.html#logics.fde.TableauxRules.DoubleNegationUndesignated
        """
        pass

    class AssertionDesignated(lp.TableauxRules.AssertionDesignated):
        """
        This rule is the same as the `FDE AssertionDesignated rule`_.

        .. _FDE AssertionDesignated rule: fde.html#logics.fde.TableauxRules.AssertionDesignated
        """
        pass

    class AssertionNegatedDesignated(lp.TableauxRules.AssertionNegatedDesignated):
        """
        This rule is the same as the `FDE AssertionNegatedDesignated rule`_.

        .. _FDE AssertionNegatedDesignated rule: fde.html#logics.fde.TableauxRules.AssertionNegatedDesignated
        """
        pass

    class AssertionUndesignated(lp.TableauxRules.AssertionUndesignated):
        """
        This rule is the same as the `FDE AssertionUndesignated rule`_.

        .. _FDE AssertionUndesignated rule: fde.html#logics.fde.TableauxRules.AssertionUndesignated
        """
        pass

    class AssertionNegatedUndesignated(lp.TableauxRules.AssertionNegatedUndesignated):
        """
        This rule is the same as the `FDE AssertionNegatedUndesignated rule`_.

        .. _FDE AssertionNegatedUndesignated rule: fde.html#logics.fde.TableauxRules.AssertionNegatedUndesignated
        """
        pass

    class ConjunctionDesignated(lp.TableauxRules.ConjunctionDesignated):
        """
        This rule is the same as the `FDE ConjunctionDesignated rule`_.

        .. _FDE ConjunctionDesignated rule: fde.html#logics.fde.TableauxRules.ConjunctionDesignated
        """
        pass

    class ConjunctionNegatedDesignated(lp.TableauxRules.ConjunctionNegatedDesignated):
        """
        This rule is the same as the `FDE ConjunctionNegatedDesignated rule`_.

        .. _FDE ConjunctionNegatedDesignated rule: fde.html#logics.fde.TableauxRules.ConjunctionNegatedDesignated
        """
        pass

    class ConjunctionUndesignated(lp.TableauxRules.ConjunctionUndesignated):
        """
        This rule is the same as the `FDE ConjunctionUndesignated rule`_.

        .. _FDE ConjunctionUndesignated rule: fde.html#logics.fde.TableauxRules.ConjunctionUndesignated
        """
        pass

    class ConjunctionNegatedUndesignated(lp.TableauxRules.ConjunctionNegatedUndesignated):
        """
        This rule is the same as the `FDE ConjunctionNegatedUndesignated rule`_.

        .. _FDE ConjunctionNegatedUndesignated rule: fde.html#logics.fde.TableauxRules.ConjunctionNegatedUndesignated
        """
        pass

    class DisjunctionDesignated(lp.TableauxRules.DisjunctionDesignated):
        """
        This rule is the same as the `FDE DisjunctionDesignated rule`_.

        .. _FDE DisjunctionDesignated rule: fde.html#logics.fde.TableauxRules.DisjunctionDesignated
        """
        pass

    class DisjunctionNegatedDesignated(lp.TableauxRules.DisjunctionNegatedDesignated):
        """
        This rule is the same as the `FDE DisjunctionNegatedDesignated rule`_.

        .. _FDE DisjunctionNegatedDesignated rule: fde.html#logics.fde.TableauxRules.DisjunctionNegatedDesignated
        """
        pass

    class DisjunctionUndesignated(lp.TableauxRules.DisjunctionUndesignated):
        """
        This rule is the same as the `FDE DisjunctionUndesignated rule`_.

        .. _FDE DisjunctionUndesignated rule: fde.html#logics.fde.TableauxRules.DisjunctionUndesignated
        """
        pass

    class DisjunctionNegatedUndesignated(lp.TableauxRules.DisjunctionNegatedUndesignated):
        """
        This rule is the same as the `FDE DisjunctionNegatedUndesignated rule`_.

        .. _FDE DisjunctionNegatedUndesignated rule: fde.html#logics.fde.TableauxRules.DisjunctionNegatedUndesignated
        """
        pass

    class MaterialConditionalDesignated(lp.TableauxRules.MaterialConditionalDesignated):
        """
        This rule is the same as the `FDE MaterialConditionalDesignated rule`_.

        .. _FDE MaterialConditionalDesignated rule: fde.html#logics.fde.TableauxRules.MaterialConditionalDesignated
        """
        pass

    class MaterialConditionalNegatedDesignated(lp.TableauxRules.MaterialConditionalNegatedDesignated):
        """
        This rule is the same as the `FDE MaterialConditionalNegatedDesignated rule`_.

        .. _FDE MaterialConditionalNegatedDesignated rule: fde.html#logics.fde.TableauxRules.MaterialConditionalNegatedDesignated
        """
        pass

    class MaterialConditionalNegatedUndesignated(lp.TableauxRules.MaterialConditionalNegatedUndesignated):
        """
        This rule is the same as the `FDE MaterialConditionalNegatedUndesignated rule`_.

        .. _FDE MaterialConditionalNegatedUndesignated rule: fde.html#logics.fde.TableauxRules.MaterialConditionalNegatedUndesignated
        """
        pass

    class MaterialConditionalUndesignated(lp.TableauxRules.MaterialConditionalUndesignated):
        """
        This rule is the same as the `FDE MaterialConditionalUndesignated rule`_.

        .. _FDE MaterialConditionalUndesignated rule: fde.html#logics.fde.TableauxRules.MaterialConditionalUndesignated
        """
        pass

    class MaterialBiconditionalDesignated(lp.TableauxRules.MaterialBiconditionalDesignated):
        """
        This rule is the same as the `FDE MaterialBiconditionalDesignated rule`_.

        .. _FDE MaterialBiconditionalDesignated rule: fde.html#logics.fde.TableauxRules.MaterialBiconditionalDesignated
        """
        pass

    class MaterialBiconditionalNegatedDesignated(lp.TableauxRules.MaterialBiconditionalNegatedDesignated):
        """
        This rule is the same as the `FDE MaterialBiconditionalNegatedDesignated rule`_.

        .. _FDE MaterialBiconditionalNegatedDesignated rule: fde.html#logics.fde.TableauxRules.MaterialBiconditionalNegatedDesignated
        """
        pass

    class MaterialBiconditionalUndesignated(lp.TableauxRules.MaterialBiconditionalUndesignated):
        """
        This rule is the same as the `FDE MaterialBiconditionalUndesignated rule`_.

        .. _FDE MaterialBiconditionalUndesignated rule: fde.html#logics.fde.TableauxRules.MaterialBiconditionalUndesignated
        """
        pass

    class MaterialBiconditionalNegatedUndesignated(lp.TableauxRules.MaterialBiconditionalNegatedUndesignated):
        """
        This rule is the same as the `FDE MaterialBiconditionalNegatedUndesignated rule`_.

        .. _FDE MaterialBiconditionalNegatedUndesignated rule: fde.html#logics.fde.TableauxRules.MaterialBiconditionalNegatedUndesignated
        """
        pass

    class ConditionalDesignated(logic.TableauxSystem.FilterNodeRule):
        """
        From an unticked, designated conditional node *n* on a branch *b*, make
        three branches *b'*, *b''*, and *b'''* from *b*. On *b'* add an undesignated
        node with the antecedent. On *b''* add an undesignated node with the
        negation of the consequent. On *b'''* add four designated nodes, with
        the antecedent, its negation, the consequent, and its negation,
        respectively. Then tick *n*.
        """

        operator    = 'Conditional'
        designation = True

        branch_level = 3

        def apply_to_node(self, node, branch):
            lhs, rhs = self.sentence(node).operands
            b1 = branch
            b2 = self.branch(branch)
            b3 = self.branch(branch)
            b1.update([
                {'sentence':        lhs , 'designated': False},
            ]).tick(node)
            b2.update([
                {'sentence': negate(rhs), 'designated': False},
            ]).tick(node)
            b3.update([
                {'sentence':        lhs , 'designated': True},
                {'sentence': negate(lhs), 'designated': True},
                {'sentence':        rhs , 'designated': True},
                {'sentence': negate(rhs), 'designated': True},
            ]).tick(node)

        def score_candidate_map(self, target):
            branch = target['branch']
            lhs, rhs = self.sentence(target['node']).operands
            return {
                'b1': branch.has_any([
                    # FDE closure
                    {'sentence':          lhs , 'designated': True},
                    # LP closure
                    {'sentence': negative(lhs), 'designated': False},
                ]),
                'b2': branch.has_any([
                    # FDE closure
                    {'sentence': negative(rhs), 'designated': True},
                    # LP closure
                    {'sentence':          rhs , 'designated': False},
                ]),
                'b3': branch.has_any([
                    # FDE closure
                    {'sentence':          lhs , 'designated': False},
                    {'sentence': negative(lhs), 'designated': False},
                    {'sentence':          rhs , 'designated': False},
                    {'sentence': negative(rhs), 'designated': False},
                    # LP closure - n/a
                ]),
            }

    class ConditionalNegatedDesignated(lp.TableauxRules.ConditionalNegatedDesignated):
        """
        This rule is the same as the `FDE ConditionalNegatedDesignated rule`_.

        .. _FDE ConditionalNegatedDesignated rule: fde.html#logics.fde.TableauxRules.ConditionalNegatedDesignated
        """
        pass

    class ConditionalUndesignated(logic.TableauxSystem.FilterNodeRule):
        """
        From an unticked, undesignated, conditional node *n* on a branch *b*, make
        two branches *b'* and *b''* from *b*. On *b'*, add a designated node
        with the antecedent, and an undesignated node with with consequent.
        On *b''*, add an undesignated node with the negation of the antecedent,
        and a designated node with the negation of the consequent. Then tick *n*.
        """

        operator    = 'Conditional'
        designation = False

        branch_level = 2

        def apply_to_node(self, node, branch):
            lhs, rhs = self.sentence(node).operands
            b1 = branch
            b2 = self.branch(branch)
            b1.update([
                {'sentence': lhs, 'designated': True},
                {'sentence': rhs, 'designated': False},
            ]).tick(node)
            b2.update([
                {'sentence': negate(lhs), 'designated': False},
                {'sentence': negate(rhs), 'designated': True},
            ]).tick(node)

        def score_candidate_map(self, target):
            branch = target['branch']
            lhs, rhs = self.sentence(target['node']).operands
            return {
                'b1': branch.has_any([
                    # FDE closure
                    {'sentence': lhs, 'designated': False},
                    {'sentence': rhs, 'designated': True},
                    # LP closure
                    {'sentence': negative(rhs), 'designated': False},
                ]),
                'b2': branch.has_any([
                    # FDE closure
                    {'sentence': negative(lhs), 'designated': True},
                    {'sentence': negative(rhs), 'designated': False},
                    # LP closure
                    {'sentence': lhs, 'designated': False},
                ])
            }

    class ConditionalNegatedUndesignated(lp.TableauxRules.ConditionalNegatedUndesignated):
        """
        This rule is the same as the `FDE ConditionalNegatedDesignated rule`_.

        .. _FDE ConditionalNegatedUndesignated rule: fde.html#logics.fde.TableauxRules.ConditionalNegatedUndesignated
        """
        pass

    class BiconditionalDesignated(logic.TableauxSystem.FilterNodeRule):
        """
        From an unticked designated biconditional node *n* on a branch *b*, make
        three branches *b'*, *b''*, and *b'''* from *b*. On *b'* add undesignated
        nodes for each of the two operands. On *b''*, add undesignated nodes fo
        the negation of each operand. On *b'''*, add four designated nodes, one
        with each operand, and one for the negation of each operand. Then tick *n*.
        """

        operator    = 'Biconditional'
        designation = True

        branch_level = 3

        def apply_to_node(self, node, branch):
            lhs, rhs = self.sentence(node).operands
            b1 = branch
            b2 = self.branch(branch)
            b3 = self.branch(branch)
            b1.update([
                {'sentence': lhs, 'designated': False},
                {'sentence': rhs, 'designated': False},
            ]).tick(node)
            b2.update([
                {'sentence': negate(lhs), 'designated': False},
                {'sentence': negate(rhs), 'designated': False},
            ]).tick(node)
            b3.update([
                {'sentence':        lhs , 'designated': True},
                {'sentence': negate(lhs), 'designated': True},
                {'sentence':        rhs , 'designated': True},
                {'sentence': negate(rhs), 'designated': True},
            ]).tick(node)

        def score_candidate_map(self, target):
            branch = target['branch']
            lhs, rhs = self.sentence(target['node']).operands
            return {
                'b1': branch.has_any([
                    # FDE closure
                    {'sentence': lhs, 'designated': True},
                    {'sentence': rhs, 'designated': True},
                    # LP closure
                    {'sentence': negative(lhs), 'designated': False},
                    {'sentence': negative(rhs), 'designated': False},
                ]),
                'b2': branch.has_any([
                    # FDE closure
                    {'sentence': negative(lhs), 'designated': True},
                    {'sentence': negative(rhs), 'designated': True},
                    # LP closure
                    {'sentence': lhs, 'designated': False},
                    {'sentence': rhs, 'designated': False},
                ]),
                'b3': branch.has_any([
                    # FDE closure
                    {'sentence':          lhs , 'designated': False},
                    {'sentence': negative(lhs), 'designated': False},
                    {'sentence':          rhs , 'designated': False},
                    {'sentence': negative(rhs), 'designated': False},
                    # LP closure - n/a
                ]),
            }

    class BiconditionalNegatedDesignated(lp.TableauxRules.BiconditionalNegatedDesignated):
        """
        This rule is the same as the `FDE BiconditionalNegatedDesignated rule`_.

        .. _FDE BiconditionalNegatedDesignated rule: fde.html#logics.fde.TableauxRules.BiconditionalNegatedDesignated
        """
        pass

    class BiconditionalUndesignated(logic.TableauxSystem.FilterNodeRule):
        """
        From an unticked undesignated biconditional node *n* on a branch *b*, add a
        conjunction undesignated node to *b*, with first conjunct being a conditional
        with the same operands as *n*, and the second conjunct being a conditional
        with the reversed operands of *n*, then tick *n*.
        """

        operator    = 'Biconditional'
        designation = False

        branch_level = 2

        def apply_to_node(self, node, branch):
            lhs, rhs = self.sentence(node).operands
            s_cond1 = operate('Conditional', [lhs, rhs])
            s_cond2 = operate('Conditional', [rhs, lhs])
            b1 = branch
            b2 = self.branch(branch)
            b1.update([
                {'sentence': s_cond1, 'designated': False},
            ]).tick(node)
            b2.update([
                {'sentence': s_cond2, 'designated': False},
            ]).tick(node)

        def score_candidate_map(self, target):
            branch = target['branch']
            lhs, rhs = self.sentence(target['node']).operands
            s_cond1 = operate('Conditional', [lhs, rhs])
            s_cond2 = operate('Conditional', [rhs, lhs])
            return {
                'b1': branch.has_any([
                    # FDE closure
                    {'sentence':          s_cond1 , 'designated': True},
                    # LP closure
                    {'sentence': negative(s_cond1), 'designated': False},
                ]),
                'b2': branch.has_any([
                    # FDE closure
                    {'sentence':          s_cond2 , 'designated': True},
                    # LP closure
                    {'sentence': negative(s_cond2), 'designated': False},
                ]),
            }

    class BiconditionalNegatedUndesignated(logic.TableauxSystem.FilterNodeRule):
        """
        From an unticked undesignated negated biconditional node *n* on a branch *b*,
        make two branches *b'* and *b''* from *b*. On *b'* add an undesignated node
        for each operand. On *b''* add an undesignated nodes for the negation of
        each operand. Then tick *n*.
        """

        negated     = True
        operator    = 'Biconditional'
        designation = False

        branch_level = 2

        def apply_to_node(self, node, branch):
            lhs, rhs = self.sentence(node).operands
            b1 = branch
            b2 = self.branch(branch)
            b1.update([
                {'sentence': lhs, 'designated': False},
                {'sentence': rhs, 'designated': False},
            ]).tick(node)
            b2.update([
                {'sentence': negate(lhs), 'designated': False},
                {'sentence': negate(rhs), 'designated': False},
            ]).tick(node)

        def score_candidate_map(self, target):
            branch = target['branch']
            lhs, rhs = self.sentence(target['node']).operands
            return {
                'b1': branch.has_any([
                    # FDE closure
                    {'sentence': lhs, 'designated': True},
                    {'sentence': rhs, 'designated': True},
                    # LP closure
                    {'sentence': negative(lhs), 'designated': False},
                    {'sentence': negative(rhs), 'designated': False},
                ]),
                'b2': branch.has_any([
                    # FDE closure
                    {'sentence': negative(lhs), 'designated': True},
                    {'sentence': negative(rhs), 'designated': True},
                    # LP closure
                    {'sentence': lhs, 'designated': False},
                    {'sentence': rhs, 'designated': False},
                ]),
            }

    class ExistentialDesignated(lp.TableauxRules.ExistentialDesignated):
        """
        This rule is the same as the `FDE ExistentialDesignated rule`_.

        .. _FDE ExistentialDesignated rule: fde.html#logics.fde.TableauxRules.ExistentialDesignated
        """
        pass

    class ExistentialNegatedDesignated(lp.TableauxRules.ExistentialNegatedDesignated):
        """
        This rule is the same as the `FDE ExistentialNegatedDesignated rule`_.

        .. _FDE ExistentialNegatedDesignated rule: fde.html#logics.fde.TableauxRules.ExistentialNegatedDesignated
        """
        pass

    class ExistentialUndesignated(lp.TableauxRules.ExistentialUndesignated):
        """
        This rule is the same as the `FDE ExistentialUndesignated rule`_.

        .. _FDE ExistentialUndesignated rule: fde.html#logics.fde.TableauxRules.ExistentialUndesignated
        """
        pass

    class ExistentialNegatedUndesignated(lp.TableauxRules.ExistentialNegatedUndesignated):
        """
        This rule is the same as the `FDE ExistentialNegatedUndesignated rule`_.

        .. _FDE ExistentialNegatedUndesignated rule: fde.html#logics.fde.TableauxRules.ExistentialNegatedUndesignated
        """
        pass

    class UniversalDesignated(lp.TableauxRules.UniversalDesignated):
        """
        This rule is the same as the `FDE UniversalDesignated rule`_.

        .. _FDE UniversalDesignated rule: fde.html#logics.fde.TableauxRules.UniversalDesignated
        """
        pass

    class UniversalNegatedDesignated(lp.TableauxRules.UniversalNegatedDesignated):
        """
        This rule is the same as the `FDE UniversalNegatedDesignated rule`_.

        .. _FDE UniversalNegatedDesignated rule: fde.html#logics.fde.TableauxRules.UniversalNegatedDesignated
        """
        pass

    class UniversalUndesignated(lp.TableauxRules.UniversalUndesignated):
        """
        This rule is the same as the `FDE UniversalUndesignated rule`_.

        .. _FDE UniversalUndesignated rule: fde.html#logics.fde.TableauxRules.UniversalUndesignated
        """
        pass

    class UniversalNegatedUndesignated(lp.TableauxRules.UniversalNegatedUndesignated):
        """
        This rule is the same as the `FDE UniversalNegatedUndesignated rule`_.

        .. _FDE UniversalNegatedUndesignated rule: fde.html#logics.fde.TableauxRules.UniversalNegatedUndesignated
        """
        pass

    closure_rules = list(lp.TableauxRules.closure_rules)

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
            ConditionalNegatedDesignated,
            ConditionalUndesignated,
            ExistentialNegatedDesignated,
            ExistentialNegatedUndesignated,
            UniversalNegatedDesignated,
            UniversalNegatedUndesignated,
            DoubleNegationDesignated,
            DoubleNegationUndesignated,
        ],
        [
            # 2 branching rules
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
            ConditionalNegatedUndesignated,
            BiconditionalNegatedDesignated,
            BiconditionalUndesignated,
            BiconditionalNegatedUndesignated,
        ],
        [
            # 3 branching rules
            ConditionalDesignated,
            BiconditionalDesignated,
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