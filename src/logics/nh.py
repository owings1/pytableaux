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
# pytableaux - Paraconsistent Hybrid 3-valued Logic
name = 'NH'

class Meta(object):
    title    = 'Paraconsistent Hybrid Logic'
    category = 'Many-valued'
    description = ' '.join((
        'Three-valued logic (True, False, Both) with non-standard conjunction,',
        'and a classical-like conditional',
    ))
    tags = ['many-valued', 'glutty', 'non-modal', 'first-order']
    category_display_order = 110

from lexicals import Operator as Oper, Sentence, Quantified, Operated
from proof.common import Branch, Node
from . import fde as FDE, lp as LP, mh as MH

class Model(LP.Model):

    def is_sentence_opaque(self, s: Sentence):
        return isinstance(s, Quantified) or super().is_sentence_opaque(s)

    def truth_function(self, oper: Oper, a, b = None):
        if oper == Oper.Conjunction:
            if a == 'B' and b == 'B':
                return 'T'
        elif oper == Oper.Conditional:
            if a != 'F' and b == 'F':
                return 'F'
            return 'T'
        return super().truth_function(oper, a, b)

class TableauxSystem(FDE.TableauxSystem):
    """
    NH's Tableaux System inherits directly from the `FDE system`_, employing
    designation markers, and building the trunk in the same way.

    .. _FDE system: fde.html#logics.fde.TableauxSystem
    """
    # operator => negated => designated
    branchables = {
        Oper.Negation: {
            True  : {True: 0, False: 0},
        },
        Oper.Assertion: {
            False : {True: 0, False: 0},
            True  : {True: 0, False: 0},
        },
        Oper.Conjunction: {
            False : {True: 0, False: 1},
            True  : {True: 3, False: 1},
        },
        Oper.Disjunction: {
            False : {True: 1, False: 0},
            True  : {True: 0, False: 1},
        },
        # for now, reduce to negated disjunction
        Oper.MaterialConditional: {
            False : {True: 0, False: 0},
            True  : {True: 0, False: 0},
        },
        # for now, reduce to conjunction
        Oper.MaterialBiconditional: {
            False : {True: 0, False: 0},
            True  : {True: 0, False: 0},
        },
        Oper.Conditional: {
            False : {True: 1, False: 0},
            True  : {True: 0, False: 1},
        },
        # for now, reduce to conjunction
        Oper.Biconditional: {
            False : {True: 0, False: 0},
            True  : {True: 0, False: 0},
        },
    }

class TabRules:

    class GapClosure         (LP.TabRules.GapClosure): pass
    class DesignationClosure (FDE.TabRules.DesignationClosure): pass

    class DoubleNegationDesignated   (FDE.TabRules.DoubleNegationDesignated): pass
    class DoubleNegationUndesignated (FDE.TabRules.DoubleNegationUndesignated): pass

    class AssertionDesignated          (FDE.TabRules.AssertionDesignated): pass
    class AssertionNegatedDesignated   (FDE.TabRules.AssertionNegatedDesignated): pass
    class AssertionUndesignated        (FDE.TabRules.AssertionUndesignated): pass
    class AssertionNegatedUndesignated (FDE.TabRules.AssertionNegatedUndesignated): pass

    class ConjunctionDesignated(FDE.TabRules.ConjunctionDesignated):
        pass

    class ConjunctionNegatedDesignated(FDE.OperatorNodeRule):
        """
        From an unticked, negated, designated conjunction node *n* on a branch *b*,
        make four new branches from *b*: *b'*, *b''*, *b'''*, *b''''*. On *b'*, add
        an undesignated node with the first conjunct. On *b''*, add an undesignated
        node with the second conjunct.

        On *b'''*, add three nodes:

        - A designated node with the first conjunct.
        - A designated node with the negation of the first conjunct.
        - An undesignated node with the negation of the second conjunct.

        On *b''''*, add three nodes:

        - A designated node with the second conjunct.
        - A designated node with the negation of the second conjunct.
        - An undesignated node with the negation of the first conjunct.

        Then, tick *n*.
        """
        negated      = True
        operator     = Oper.Conjunction
        designation  = True
        branch_level = 4

        def _get_node_targets(self, node: Node, _: Branch):
            lhs, rhs = self.sentence(node)
            return {
                'adds': [
                    [
                        {'sentence': lhs, 'designated': False},
                    ],
                    [
                        {'sentence': lhs, 'designated': False},
                    ],
                    [
                        {'sentence': lhs         ,  'designated': True},
                        {'sentence': lhs.negate(), 'designated': True},
                        {'sentence': rhs.negate(), 'designated': False},
                    ],
                    [
                        {'sentence': rhs         , 'designated': True},
                        {'sentence': rhs.negate(), 'designated': True},
                        {'sentence': lhs.negate(), 'designated': False},
                    ],
                ],
            }

    class ConjunctionUndesignated(FDE.TabRules.ConjunctionUndesignated):
        pass

    class ConjunctionNegatedUndesignated(FDE.OperatorNodeRule):
        """
        From an unticked, negated, undesignated conjunction node *n* on a branch *b*,
        make two branches *b'* and *b''* from *b*. On *b'*, add two undesignated nodes,
        one for the negation of each conjunct. On *b''*, add four designated nodes, one
        for each of the conjuncts and its negation. Then tick *n*.
        """
        negated      = True
        operator     = Oper.Conjunction
        designation  = False
        branch_level = 2

        def _get_node_targets(self, node: Node, _: Branch):
            lhs, rhs = self.sentence(node)
            return {
                'adds': [
                    [
                        {'sentence': lhs.negate(), 'designated': False},
                        {'sentence': rhs.negate(), 'designated': False},
                    ],
                    [
                        {'sentence': lhs         , 'designated': True},
                        {'sentence': lhs.negate(), 'designated': True},
                        {'sentence': rhs         , 'designated': True},
                        {'sentence': rhs.negate(), 'designated': True},
                    ],
                ],
            }

    class DisjunctionDesignated(FDE.TabRules.DisjunctionDesignated):
        pass

    class DisjunctionNegatedDesignated(FDE.TabRules.DisjunctionNegatedDesignated):
        pass

    class DisjunctionUndesignated(FDE.TabRules.DisjunctionUndesignated):
        pass

    class DisjunctionNegatedUndesignated(FDE.TabRules.DisjunctionNegatedUndesignated):
        pass

    class MaterialConditionalDesignated(FDE.OperatorNodeRule):
        """
        This rule reduces to a disjunction.
        """
        operator     = Oper.MaterialConditional
        designation  = True
        branch_level = 1

        def _get_node_targets(self, node: Node, _: Branch):
            lhs, rhs = self.sentence(node)
            disj = lhs.negate().disjoin(rhs)
            return {
                'adds': [
                    [
                        {'sentence': disj, 'designated': self.designation},
                    ],
                ],
            }

    class MaterialConditionalNegatedDesignated(FDE.OperatorNodeRule):
        """
        This rule reduces to a negated disjunction.
        """
        negated      = True
        operator     = Oper.MaterialConditional
        designation  = True
        branch_level = 1

        def _get_node_targets(self, node: Node, _: Branch):
            lhs, rhs = self.sentence(node)
            disj = lhs.negate().disjoin(rhs)
            return {
                'adds': [
                    [
                        {'sentence': disj.negate(), 'designated': self.designation},
                    ],
                ],
            }

    class MaterialConditionalUndesignated(MaterialConditionalDesignated):
        """
        This rule reduces to a disjunction.
        """
        negated     = False
        designation = False

    class MaterialConditionalNegatedUndesignated(MaterialConditionalNegatedDesignated):
        """
        This rule reduces to a negated disjunction.
        """
        negated     = True
        designation = False

    class MaterialBiconditionalDesignated(FDE.OperatorNodeRule):
        """
        This rule reduces to a conjunction of material conditionals.
        """
        operator     = Oper.MaterialBiconditional
        designation  = True
        branch_level = 1

        def _get_node_targets(self, node: Node, _: Branch):
            lhs, rhs = self.sentence(node)
            cond1 = Oper.MaterialConditional((lhs, rhs))
            cond2 = Oper.MaterialConditional((rhs, lhs))
            conj = cond1.conjoin(cond2)
            return {
                'adds': [
                    [
                        {'sentence': conj, 'designated': self.designation}
                    ],
                ],
            }

    class MaterialBiconditionalNegatedDesignated(FDE.OperatorNodeRule):
        """
        This rule reduces to a negated conjunction of material conditionals.
        """
        negated      = True
        operator     = Oper.MaterialBiconditional
        designation  = True
        branch_level = 1

        def _get_node_targets(self, node: Node, _: Branch):
            lhs, rhs = self.sentence(node)
            cond1 = Oper.MaterialConditional((lhs, rhs))
            cond2 = Oper.MaterialConditional((rhs, lhs))
            conj = cond1.conjoin(cond2)
            return {
                'adds': [
                    [
                        {'sentence': conj.negate(), 'designated': self.designation}
                    ],
                ],
            }

    class MaterialBiconditionalUndesignated(MaterialBiconditionalDesignated):
        """
        This rule reduces to a conjunction of material conditionals.
        """
        designation = False

    class MaterialBiconditionalNegatedUndesignated(MaterialBiconditionalNegatedDesignated):
        """
        This rule reduces to a negated conjunction of material conditionals.
        """
        designation = False

    class ConditionalDesignated(MH.TabRules.ConditionalDesignated):
        pass

    class ConditionalNegatedDesignated(MH.TabRules.ConditionalNegatedDesignated):
        pass

    class ConditionalUndesignated(MH.TabRules.ConditionalUndesignated):
        pass

    class ConditionalNegatedUndesignated(MH.TabRules.ConditionalNegatedUndesignated):
        pass

    class BiconditionalDesignated(FDE.OperatorNodeRule):
        """
        This rule reduces to a conjunction of conditionals.
        """
        operator    = Oper.Biconditional
        designation = True
        branch_level = 1

        def _get_node_targets(self, node: Node, _: Branch):
            lhs, rhs = self.sentence(node)
            cond1 = Oper.Conditional((lhs, rhs))
            cond2 = Oper.Conditional((rhs, lhs))
            conj = cond1.conjoin(cond2)
            return {
                'adds': [
                    [
                        {'sentence': conj, 'designated': self.designation}
                    ],
                ],
            }

    class BiconditionalNegatedDesignated(FDE.OperatorNodeRule):
        """
        This rule reduces to a negated conjunction of conditionals.
        """
        negated     = True
        operator    = Oper.Biconditional
        designation = True
        branch_level = 1

        def _get_node_targets(self, node: Node, _: Branch):
            lhs, rhs = self.sentence(node)
            cond1 = Oper.Conditional((lhs, rhs))
            cond2 = Oper.Conditional((rhs, lhs))
            conj = cond1.conjoin(cond2)
            return {
                'adds': [
                    [
                        {'sentence': conj.negate(), 'designated': self.designation}
                    ],
                ],
            }

    class BiconditionalUndesignated(BiconditionalDesignated):
        """
        This rule reduces to a conjunction of conditionals.
        """
        designation = False

    class BiconditionalNegatedUndesignated(BiconditionalNegatedDesignated):
        """
        This rule reduces to a negated conjunction of conditionals.
        """
        designation = False

    closure_rules = (
        GapClosure,
        DesignationClosure,
    )

    rule_groups = (
        # Non-branching rules.
        (
            AssertionDesignated,
            AssertionUndesignated,
            AssertionNegatedDesignated,
            AssertionNegatedUndesignated,
            ConjunctionDesignated,
            DisjunctionUndesignated,
            DisjunctionNegatedDesignated,
            MaterialConditionalDesignated,
            MaterialConditionalNegatedDesignated,
            MaterialConditionalUndesignated,
            MaterialConditionalNegatedUndesignated,
            MaterialBiconditionalDesignated,
            MaterialBiconditionalNegatedDesignated,
            MaterialBiconditionalUndesignated,
            MaterialBiconditionalNegatedUndesignated,
            ConditionalUndesignated,
            ConditionalNegatedDesignated,
            BiconditionalDesignated,
            BiconditionalNegatedDesignated,
            BiconditionalUndesignated,
            BiconditionalNegatedUndesignated,
            DoubleNegationDesignated,
            DoubleNegationUndesignated,
        ),
        # 1-branching rules.
        (
            ConjunctionUndesignated,
            ConjunctionNegatedUndesignated,
            DisjunctionDesignated,
            DisjunctionNegatedUndesignated,
            ConditionalDesignated,
            ConditionalNegatedUndesignated,
        ),
        # 3-branching rules.
        (
            ConjunctionNegatedDesignated,
        ),
    )
TableauxRules = TabRules