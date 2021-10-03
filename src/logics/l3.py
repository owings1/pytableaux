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
# pytableaux - Lukasiewicz 3-valued Logic
name = 'L3'

class Meta(object):

    title    = u'Łukasiewicz 3-valued Logic'
    category = 'Many-valued'

    description = 'Three-valued logic (True, False, Neither) with a primitive Conditional operator'

    tags = ['many-valued', 'gappy', 'non-modal', 'first-order']

    category_display_order = 80

from lexicals import Operated
from . import fde, k3

class Model(k3.Model):
    """
    An Ł3 model is just like a `K3 model`_ with different tables for the conditional
    and bi-conditional operators.

    .. _K3 model: k3.html#logics.k3.Model
    """

    def value_of_operated(self, sentence, **kw):
        """
        The value of a sentence with a truth-functional operator is determined by
        the values of its operands according to the following tables.

        //truth_tables//l3//
        """
        return super().value_of_operated(sentence, **kw)

    def truth_function(self, operator, a, b=None):
        if operator == 'Conditional':
            if a == 'N' and b == 'N':
                return 'T'
        return super().truth_function(operator, a, b)

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

class DefaultNodeRule(fde.DefaultNodeRule):
    pass

class TableauxRules(object):
    """
    The closure rules for Ł3 are the `FDE closure rule`_, and the `K3 closure rule`_.
    The operator rules for Ł3 are mostly the rules for :ref:`FDE <FDE>`, with the exception
    of the rules for the conditional and biconditional operators.

    .. _FDE closure rule: fde.html#logics.fde.TableauxRules.DesignationClosure
    .. _K3 closure rule: k3.html#logics.k3.TableauxRules.GlutClosure
    .. _FDE: fde.html
    """

    class GlutClosure(k3.TableauxRules.GlutClosure):
        pass

    class DesignationClosure(fde.TableauxRules.DesignationClosure):
        pass

    class DoubleNegationDesignated(fde.TableauxRules.DoubleNegationDesignated):
        pass

    class DoubleNegationUndesignated(fde.TableauxRules.DoubleNegationUndesignated):
        pass

    class AssertionDesignated(fde.TableauxRules.AssertionDesignated):
        pass

    class AssertionNegatedDesignated(fde.TableauxRules.AssertionNegatedDesignated):
        pass

    class AssertionUndesignated(fde.TableauxRules.AssertionUndesignated):
        pass

    class AssertionNegatedUndesignated(fde.TableauxRules.AssertionNegatedUndesignated):
        pass

    class ConjunctionDesignated(fde.TableauxRules.ConjunctionDesignated):
        pass

    class ConjunctionNegatedDesignated(fde.TableauxRules.ConjunctionNegatedDesignated):
        pass

    class ConjunctionUndesignated(fde.TableauxRules.ConjunctionUndesignated):
        pass

    class ConjunctionNegatedUndesignated(fde.TableauxRules.ConjunctionNegatedUndesignated):
        pass

    class DisjunctionDesignated(fde.TableauxRules.DisjunctionDesignated):
        pass

    class DisjunctionNegatedDesignated(fde.TableauxRules.DisjunctionNegatedDesignated):
        pass

    class DisjunctionUndesignated(fde.TableauxRules.DisjunctionUndesignated):
        pass

    class DisjunctionNegatedUndesignated(fde.TableauxRules.DisjunctionNegatedUndesignated):
        pass

    class MaterialConditionalDesignated(fde.TableauxRules.MaterialConditionalDesignated):
        pass

    class MaterialConditionalNegatedDesignated(fde.TableauxRules.MaterialConditionalNegatedDesignated):
        pass

    class MaterialConditionalUndesignated(fde.TableauxRules.MaterialConditionalUndesignated):
        pass

    class MaterialConditionalNegatedUndesignated(fde.TableauxRules.MaterialConditionalNegatedUndesignated):
        pass

    class MaterialBiconditionalDesignated(fde.TableauxRules.MaterialBiconditionalDesignated):
        pass

    class MaterialBiconditionalNegatedDesignated(fde.TableauxRules.MaterialBiconditionalNegatedDesignated):
        pass

    class MaterialBiconditionalUndesignated(fde.TableauxRules.MaterialBiconditionalUndesignated):
        pass

    class MaterialBiconditionalNegatedUndesignated(fde.TableauxRules.MaterialBiconditionalNegatedUndesignated):
        pass

    class ConditionalDesignated(DefaultNodeRule):
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

        def get_target_for_node(self, node, branch):
            s = self.sentence(node)
            disj = Operated('Disjunction', [s.lhs.negate(), s.rhs])
            return {
                'adds': [
                    [
                        {'sentence': disj, 'designated': True},
                    ],
                    [
                        {'sentence': s.lhs         , 'designated': False},
                        {'sentence': s.lhs.negate(), 'designated': False},
                        {'sentence': s.rhs         , 'designated': False},
                        {'sentence': s.rhs.negate(), 'designated': False},
                    ],
                ],
            }

    class ConditionalNegatedDesignated(fde.TableauxRules.ConditionalNegatedDesignated):
        pass

    class ConditionalUndesignated(DefaultNodeRule):
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

        def get_target_for_node(self, node, branch):
            s = self.sentence(node)
            return {
                'adds': [
                    [
                        {'sentence': s.lhs, 'designated': True},
                        {'sentence': s.rhs, 'designated': False},
                    ],
                    [
                        {'sentence': s.lhs         , 'designated': False},
                        {'sentence': s.lhs.negate(), 'designated': False},
                        {'sentence': s.rhs.negate(), 'designated': True},
                    ],
                ],
            }

    class ConditionalNegatedUndesignated(fde.TableauxRules.ConditionalNegatedUndesignated):
        pass
        
    class BiconditionalDesignated(DefaultNodeRule):
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

        def get_target_for_node(self, node, branch):
            s = self.sentence(node)
            bicond = Operated('Material Biconditional', s.operands)
            return {
                'adds': [
                    [
                        {'sentence': bicond, 'designated': True},
                    ],
                    [
                        {'sentence': s.lhs         , 'designated': False},
                        {'sentence': s.lhs.negate(), 'designated': False},
                        {'sentence': s.rhs         , 'designated': False},
                        {'sentence': s.rhs.negate(), 'designated': False},
                    ],
                ],
            }

    class BiconditionalNegatedDesignated(fde.TableauxRules.BiconditionalNegatedDesignated):
        pass

    class BiconditionalUndesignated(DefaultNodeRule):
        """
        From an unticked undesignated biconditional node *n* on a branch *b*, make
        two branches *b'* and *b''* from *b*. On *b'* add an undesignated conditional
        node with the same operands. On *b''* add an undesignated conditional node
        with the reversed operands. Then tick *n*.
        """
        operator    = 'Biconditional'
        designation = False
        branch_level = 2

        def get_target_for_node(self, node, branch):
            s = self.sentence(node)
            cond1 = Operated('Conditional', [s.lhs, s.rhs])
            cond2 = Operated('Conditional', [s.rhs, s.lhs])
            return {
                'adds': [
                    [
                        {'sentence': cond1, 'designated': False},
                    ],
                    [
                        {'sentence': cond2, 'designated': False},
                    ],
                ],
            }

    class BiconditionalNegatedUndesignated(DefaultNodeRule):
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

        def get_target_for_node(self, node, branch):
            s = self.sentence(node)
            bicond = Operated('Material Biconditional', s.operands)
            return {
                'adds': [
                    [
                        {'sentence': bicond.negate(), 'designated': False},
                    ],
                    [
                        {'sentence': s.lhs         , 'designated': False},
                        {'sentence': s.lhs.negate(), 'designated': False},
                        {'sentence': s.rhs         , 'designated': False},
                        {'sentence': s.rhs.negate(), 'designated': False},
                    ],
                ],
            }

    class ExistentialDesignated(fde.TableauxRules.ExistentialDesignated):
        pass

    class ExistentialNegatedDesignated(fde.TableauxRules.ExistentialNegatedDesignated):
        pass

    class ExistentialUndesignated(fde.TableauxRules.ExistentialUndesignated):
        pass

    class ExistentialNegatedUndesignated(fde.TableauxRules.ExistentialNegatedUndesignated):
        pass

    class UniversalDesignated(fde.TableauxRules.UniversalDesignated):
        pass

    class UniversalNegatedDesignated(fde.TableauxRules.UniversalNegatedDesignated):
        pass

    class UniversalUndesignated(fde.TableauxRules.UniversalUndesignated):
        pass

    class UniversalNegatedUndesignated(fde.TableauxRules.UniversalNegatedUndesignated):
        pass

    closure_rules = [
        GlutClosure,
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
            ConditionalNegatedDesignated,
            BiconditionalNegatedDesignated,
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
            ConditionalUndesignated,
            ConditionalNegatedUndesignated,
            BiconditionalDesignated,
            BiconditionalNegatedUndesignated,
            BiconditionalUndesignated,
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