# -*- coding: utf-8 -*-
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
# pytableaux - Lukasiewicz 3-valued Logic
name = 'L3'
title = u'Łukasiewicz 3-valued Logic'
description = 'Three-valued logic (True, False, Neither) with a primitive Conditional operator'
tags_list = ['many-valued', 'gappy', 'non-modal', 'first-order']
tags = set(tags_list)
category = 'Many-valued'
category_display_order = 6

from . import fde, k3
import logic
from logic import operate, negate, negative

class Model(k3.Model):
    """
    An L3 model is just like a `K3 model`_ with different tables for the conditional
    and bi-conditional operators.

    .. _K3 model: k3.html#logics.k3.Model
    """

    def value_of_operated(self, sentence, **kw):
        """
        The value of a sentence with a truth-functional operator is determined by
        the values of its operands according to the following tables.

        //truth_tables//l3//
        """
        return super(Model, self).value_of_operated(sentence, **kw)

    def truth_function(self, operator, a, b=None):
        if operator == 'Conditional' or operator == 'Biconditional':
            if a == 'N' and a == b:
                return 'T'
        return super(Model, self).truth_function(operator, a, b)

class TableauxSystem(fde.TableauxSystem):
    """
    Ł3's Tableaux System inherits directly from the `FDE system`_, employing
    designation markers, and building the trunk in the same way.

    .. _FDE system: fde.html#logics.fde.TableauxSystem
    """
    branchables = dict(fde.TableauxSystem.branchables)
    branchables.update({
        'Conditional': {
            False  : {
                True  : 1,
                False : 1,
            },
            True : {
                True  : 0,
                False : 1,
            },
        },
        'Biconditional': {
            False  : {
                True  : 1,
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
    The closure rules for Ł3 are the `FDE closure rule`_, and the `K3 closure rule`_.
    The operator rules for Ł3 are mostly the rules for `FDE`_, with the exception
    of the rules for the conditional and biconditional operators.

    .. _FDE closure rule: fde.html#logics.fde.TableauxRules.Closure
    .. _K3 closure rule: k3.html#logics.k3.TableauxRules.Closure
    .. _FDE: fde.html
    """

    class DoubleNegationDesignated(k3.TableauxRules.DoubleNegationDesignated):
        """
        This rule is the same as the `FDE DoubleNegationDesignated rule`_.

        .. _FDE DoubleNegationDesignated rule: fde.html#logics.fde.TableauxRules.DoubleNegationDesignated
        """
        pass

    class DoubleNegationUndesignated(k3.TableauxRules.DoubleNegationUndesignated):
        """
        This rule is the same as the `FDE DoubleNegationUndesignated rule`_.

        .. _FDE DoubleNegationUndesignated rule: fde.html#logics.fde.TableauxRules.DoubleNegationUndesignated
        """
        pass

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

    class ConjunctionDesignated(k3.TableauxRules.ConjunctionDesignated):
        """
        This rule is the same as the `FDE ConjunctionDesignated rule`_.

        .. _FDE ConjunctionDesignated rule: fde.html#logics.fde.TableauxRules.ConjunctionDesignated
        """
        pass

    class ConjunctionNegatedDesignated(k3.TableauxRules.ConjunctionNegatedDesignated):
        """
        This rule is the same as the `FDE ConjunctionNegatedDesignated rule`_.

        .. _FDE ConjunctionNegatedDesignated rule: fde.html#logics.fde.TableauxRules.ConjunctionNegatedDesignated
        """
        pass

    class ConjunctionUndesignated(k3.TableauxRules.ConjunctionUndesignated):
        """
        This rule is the same as the `FDE ConjunctionUndesignated rule`_.

        .. _FDE ConjunctionUndesignated rule: fde.html#logics.fde.TableauxRules.ConjunctionUndesignated
        """
        pass

    class ConjunctionNegatedUndesignated(k3.TableauxRules.ConjunctionNegatedUndesignated):
        """
        This rule is the same as the `FDE ConjunctionNegatedUndesignated rule`_.

        .. _FDE ConjunctionNegatedUndesignated rule: fde.html#logics.fde.TableauxRules.ConjunctionNegatedUndesignated
        """
        pass

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

    class MaterialConditionalDesignated(k3.TableauxRules.MaterialConditionalDesignated):
        """
        This rule is the same as the `FDE MaterialConditionalDesignated rule`_.

        .. _FDE MaterialConditionalDesignated rule: fde.html#logics.fde.TableauxRules.MaterialConditionalDesignated
        """
        pass

    class MaterialConditionalNegatedDesignated(k3.TableauxRules.MaterialConditionalNegatedDesignated):
        """
        This rule is the same as the `FDE MaterialConditionalNegatedDesignated rule`_.

        .. _FDE MaterialConditionalNegatedDesignated rule: fde.html#logics.fde.TableauxRules.MaterialConditionalNegatedDesignated
        """
        pass

    class MaterialConditionalNegatedUndesignated(k3.TableauxRules.MaterialConditionalNegatedUndesignated):
        """
        This rule is the same as the `FDE MaterialConditionalNegatedUndesignated rule`_.

        .. _FDE MaterialConditionalNegatedUndesignated rule: fde.html#logics.fde.TableauxRules.MaterialConditionalNegatedUndesignated
        """
        pass

    class MaterialConditionalUndesignated(k3.TableauxRules.MaterialConditionalUndesignated):
        """
        This rule is the same as the `FDE MaterialConditionalUndesignated rule`_.

        .. _FDE MaterialConditionalUndesignated rule: fde.html#logics.fde.TableauxRules.MaterialConditionalUndesignated
        """
        pass

    class MaterialBiconditionalDesignated(k3.TableauxRules.MaterialBiconditionalDesignated):
        """
        This rule is the same as the `FDE MaterialBiconditionalDesignated rule`_.

        .. _FDE MaterialBiconditionalDesignated rule: fde.html#logics.fde.TableauxRules.MaterialBiconditionalDesignated
        """
        pass

    class MaterialBiconditionalNegatedDesignated(k3.TableauxRules.MaterialBiconditionalNegatedDesignated):
        """
        This rule is the same as the `FDE MaterialBiconditionalNegatedDesignated rule`_.

        .. _FDE MaterialBiconditionalNegatedDesignated rule: fde.html#logics.fde.TableauxRules.MaterialBiconditionalNegatedDesignated
        """
        pass

    class MaterialBiconditionalUndesignated(k3.TableauxRules.MaterialBiconditionalUndesignated):
        """
        This rule is the same as the `FDE MaterialBiconditionalUndesignated rule`_.

        .. _FDE MaterialBiconditionalUndesignated rule: fde.html#logics.fde.TableauxRules.MaterialBiconditionalUndesignated
        """
        pass

    class MaterialBiconditionalNegatedUndesignated(k3.TableauxRules.MaterialBiconditionalNegatedUndesignated):
        """
        This rule is the same as the `FDE MaterialBiconditionalNegatedUndesignated rule`_.

        .. _FDE MaterialBiconditionalNegatedUndesignated rule: fde.html#logics.fde.TableauxRules.MaterialBiconditionalNegatedUndesignated
        """
        pass

    class ConditionalDesignated(logic.TableauxSystem.FilterNodeRule):
        """
        From an unticked designated conditional node *n* on a branch *b*, make two
        new branches *b'* and *b''* from *b*. To *b'* add a designated disjunction
        node with the negation of the antecedent as the first disjunct, and the
        consequent as the second disjunct. On *b''* add four undesignated nodes:
        a node with the antecedent, a node with the negation of the antecedent,
        a node with the consequent, and a node with the negation of the consequent.
        Then tick *n*.
        """

        operator    = 'Conditional'
        designation = True

        branch_level = 2

        def apply_to_node(self, node, branch):
            s = self.sentence(node)
            s_disj = operate('Disjunction', [negate(s.lhs), s.rhs])
            b1 = branch
            b2 = self.branch(branch)
            b1.add(
                { 'sentence' : s_disj, 'designated' : True }
            ).tick(node)
            b2.update([
                {'sentence':        s.lhs,  'designated': False},
                {'sentence': negate(s.lhs), 'designated': False},
                {'sentence':        s.rhs,  'designated': False},
                {'sentence': negate(s.rhs), 'designated': False},
            ]).tick(node)

        def score_candidate_map(self, target):
            branch = target['branch']
            s = self.sentence(target['node'])
            s_disj = operate('Disjunction', [negative(s.lhs), s.rhs])
            return {
                'b1': branch.has_any([
                    # FDE closure
                    {'sentence':          s_disj , 'designated': False},
                    # K3 closure
                    {'sentence': negative(s_disj), 'designated': True},
                ]),
                'b2': branch.has_any([
                    # FDE closure
                    {'sentence' :          s.lhs , 'designated' : True},
                    {'sentence' : negative(s.lhs), 'designated' : True},
                    {'sentence' :          s.rhs , 'designated' : True},
                    {'sentence' : negative(s.rhs), 'designated' : True},
                    # K3 closure - n/a
                ]),
            }

    class ConditionalNegatedDesignated(k3.TableauxRules.ConditionalNegatedDesignated):
        """
        This rule is the same as the `FDE ConditionalNegatedDesignated rule`_.

        .. _FDE ConditionalNegatedDesignated rule: fde.html#logics.fde.TableauxRules.ConditionalNegatedDesignated
        """
        pass

    class ConditionalUndesignated(logic.TableauxSystem.FilterNodeRule):
        """
        From an unticked undesignated conditional node *n* on a branch *b*,
        make two new branches *b'* and *b''* from *b*. On *b'* add a designated node
        with the antecedent and an undesignated node with the consequent. On *b''*,
        add undesignated nodes for the antecedent and its negation, and a designated
        with the negation of the consequent. Then tick *n*.   
        """

        operator    = 'Conditional'
        designation = False

        branch_level = 2

        def apply_to_node(self, node, branch):
            s = self.sentence(node)
            b1 = branch
            b2 = self.branch(branch)
            b1.update([
                {'sentence': s.lhs, 'designated': True},
                {'sentence': s.rhs, 'designated': False},
            ]).tick(node)
            b2.update([
                {'sentence':        s.lhs , 'designated': False},
                {'sentence': negate(s.lhs), 'designated': False},
                {'sentence': negate(s.rhs), 'designated': True},
            ]).tick(node)

        def score_candidate_map(self, target):
            branch = target['branch']
            s = self.sentence(target['node'])
            return {
                'b1': branch.has_any([
                    # FDE closure
                    {'sentence': s.lhs, 'designated': False},
                    {'sentence': s.rhs, 'designated': True},
                    # K3 closure
                    {'sentence': negative(s.lhs), 'designated': True},
                ]),
                'b2': branch.has_any([
                    # FDE closure
                    {'sentence':          s.lhs , 'designated': True},
                    {'sentence': negative(s.lhs), 'designated': True},
                    {'sentence': negative(s.rhs), 'designated': False},
                    # K3 closure
                    {'sentence': s.rhs, 'designated': True},
                ]),
            }

    class ConditionalNegatedUndesignated(k3.TableauxRules.ConditionalNegatedUndesignated):
        """
        This rule is the same as the `FDE ConditionalNegatedUndesignated rule`_.

        .. _FDE ConditionalNegatedUndesignated rule: fde.html#logics.fde.TableauxRules.ConditionalNegatedUndesignated
        """
        pass
        
    class BiconditionalDesignated(logic.TableauxSystem.FilterNodeRule):
        """
        From an unticked designated biconditional node *n* on a branch *b*, add
        two branches *b'* and *b''* to *b*. On *b'* add a designated material
        biconditional node with the same operands. On *b''* add four undesignated
        nodes, with the antecedent, the negation of the antecedent, the consequent,
        and the negation of the consequent, respectively. Then tick *n*.
        """

        operator    = 'Biconditional'
        designation = True

        branch_level = 2

        def apply_to_node(self, node, branch):
            s = self.sentence(node)
            s_mbicond = operate('Material Biconditional', s.operands)
            b1 = branch
            b2 = self.branch(branch)
            b1.update([
                {'sentence': s_mbicond, 'designated': True},
            ]).tick(node)
            b2.update([
                {'sentence':        s.lhs,  'designated': False},
                {'sentence': negate(s.lhs), 'designated': False},
                {'sentence':        s.rhs,  'designated': False},
                {'sentence': negate(s.rhs), 'designated': False},
            ]).tick(node)

        def score_candidate_map(self, target):
            branch = target['branch']
            s = self.sentence(target['node'])
            s_mbicond = operate('Material Biconditional', s.operands)
            return {
                'b1': branch.has_any([
                    # FDE closure
                    {'sentence': s_mbicond, 'designated': False},
                    # K3 closure
                    {'sentence': negative(s_mbicond), 'designated': True},
                ]),
                'b2': branch.has_any([
                    # FDE closure
                    {'sentence':          s.lhs,  'designated': True},
                    {'sentence': negative(s.lhs), 'designated': True},
                    {'sentence':          s.rhs,  'designated': True},
                    {'sentence': negative(s.rhs), 'designated': True},
                    # K3 closure - n/a
                ]),
            }

    class BiconditionalNegatedDesignated(k3.TableauxRules.BiconditionalNegatedDesignated):
        """
        This rule is the same as the `FDE BiconditionalNegatedDesignated rule`_.

        .. _FDE BiconditionalNegatedDesignated rule: fde.html#logics.fde.TableauxRules.BiconditionalNegatedDesignated
        """
        pass

    class BiconditionalUndesignated(logic.TableauxSystem.FilterNodeRule):
        """
        From an unticked undesignated biconditional node *n* on a branch *b*, make
        two branches *b'* and *b''* from *b*. On *b'* add an undesignated conditional
        node with the same operands. On *b''* add an undesignated conditional node
        with the reversed operands. Then tick *n*.
        """

        operator    = 'Biconditional'
        designation = False

        branch_level = 2

        def apply_to_node(self, node, branch):
            s = self.sentence(node)
            b1, b2 = branch, self.branch(branch)
            s_cond1 = operate('Conditional', [s.lhs, s.rhs])
            s_cond2 = operate('Conditional', [s.rhs, s.lhs])
            b1.update([
                {'sentence': s_cond1, 'designated': False},
            ]).tick(node)
            b2.update([
                {'sentence': s_cond2, 'designated': False},
            ]).tick(node)

        def score_candidate_map(self, target):
            branch = target['branch']
            s = self.sentence(target['node'])
            s_cond1 = operate('Conditional', [s.lhs, s.rhs])
            s_cond2 = operate('Conditional', [s.rhs, s.lhs])
            return {
                'b1': branch.has_any([
                    # FDE closure
                    {'sentence': s_cond1, 'designated': True},
                    # K3 closure - n/a
                ]),
                'b2': branch.has_any([
                    # FDE closure
                    {'sentence': s_cond2, 'designated': True},
                    # K3 closure - n/a
                ])
            }

    class BiconditionalNegatedUndesignated(k3.TableauxRules.BiconditionalNegatedUndesignated):
        """
        From an unticked designated biconditional node *n* on a branch *b*, add
        two branches *b'* and *b''* to *b*. On *b'* add an undesignated negated material
        biconditional node with the same operands. On *b''* add four undesignated
        nodes, with the antecedent, the negation of the antecedent, the consequent,
        and the negation of the consequent, respectively. Then tick *n*.
        """

        negated     = True
        operator    = 'Biconditional'
        designation = False

        branch_level = 2

        def apply_to_node(self, node, branch):
            s = self.sentence(node)
            s_mbicond = operate('Material Biconditional', s.operands)
            b1 = branch
            b2 = self.branch(branch)
            b1.update([
                {'sentence': negate(s_mbicond), 'designated': False},
            ]).tick(node)
            b2.update([
                {'sentence':        s.lhs,  'designated': False},
                {'sentence': negate(s.lhs), 'designated': False},
                {'sentence':        s.rhs,  'designated': False},
                {'sentence': negate(s.rhs), 'designated': False},
            ]).tick(node)

        def score_candidate_map(self, target):
            branch = target['branch']
            s = self.sentence(target['node'])
            s_mbicond = operate('Material Biconditional', s.operands)
            return {
                'b1': branch.has_any([
                    # FDE closure
                    {'sentence': negative(s_mbicond), 'designated': True},
                    # K3 closure - n/a
                ]),
                'b2': branch.has_any([
                    # FDE closure
                    {'sentence':          s.lhs,  'designated': True},
                    {'sentence': negative(s.lhs), 'designated': True},
                    {'sentence':          s.rhs,  'designated': True},
                    {'sentence': negative(s.rhs), 'designated': True},
                    # K3 closure - n/a
                ]),
            }

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
            DisjunctionNegatedDesignated,
            DisjunctionUndesignated,
            DisjunctionNegatedUndesignated,
            MaterialConditionalNegatedDesignated,
            MaterialConditionalUndesignated,
            ConditionalNegatedDesignated,
            BiconditionalNegatedDesignated,
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
            ConditionalUndesignated,
            ConditionalNegatedUndesignated,
            BiconditionalDesignated,
            BiconditionalNegatedUndesignated,
            BiconditionalUndesignated,
        ],
    ]