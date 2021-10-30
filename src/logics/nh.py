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

from lexicals import Operated
from . import fde, lp, mh

class Model(lp.Model):

    def value_of_operated(self, sentence, **kw):
        """
        The value of a sentence with a truth-functional operator is determined by
        the values of its operands according to the following tables.

        //truth_tables//nh//
        """
        return super().value_of_operated(sentence, **kw)

    def is_sentence_opaque(self, sentence):
        if sentence.is_quantified:
            return True
        return super().is_sentence_opaque(sentence)

    def truth_function(self, operator, a, b = None):
        if operator == 'Conjunction':
            if a == 'B' and b == 'B':
                return 'T'
        elif operator == 'Conditional':
            if a != 'F' and b == 'F':
                return 'F'
            return 'T'
        return super().truth_function(operator, a, b)

class TableauxSystem(fde.TableauxSystem):
    """
    NH's Tableaux System inherits directly from the `FDE system`_, employing
    designation markers, and building the trunk in the same way.

    .. _FDE system: fde.html#logics.fde.TableauxSystem
    """
    # operator => negated => designated
    branchables = {
        'Negation': {
            True  : {True: 0, False: 0},
        },
        'Assertion': {
            False : {True: 0, False: 0},
            True  : {True: 0, False: 0},
        },
        'Conjunction': {
            False : {True: 0, False: 1},
            True  : {True: 3, False: 1},
        },
        'Disjunction': {
            False : {True: 1, False: 0},
            True  : {True: 0, False: 1},
        },
        # for now, reduce to negated disjunction
        'Material Conditional': {
            False : {True: 0, False: 0},
            True  : {True: 0, False: 0},
        },
        # for now, reduce to conjunction
        'Material Biconditional': {
            False : {True: 0, False: 0},
            True  : {True: 0, False: 0},
        },
        'Conditional': {
            False : {True: 1, False: 0},
            True  : {True: 0, False: 1},
        },
        # for now, reduce to conjunction
        'Biconditional': {
            False : {True: 0, False: 0},
            True  : {True: 0, False: 0},
        },
    }

class DefaultNodeRule(fde.DefaultNodeRule):
    pass

class TableauxRules(object):
    """
    The closure rules for NH are the `FDE closure rule`_, and the `LP closure rule`_.
    ...
    
    .. _FDE closure rule: fde.html#logics.fde.TableauxRules.DesignationClosure
    .. _LP closure rule: lp.html#logics.lp.TableauxRules.GapClosure
    """

    class GapClosure(lp.TableauxRules.GapClosure):
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

    class ConjunctionNegatedDesignated(DefaultNodeRule):
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
        operator     = 'Conjunction'
        designation  = True
        branch_level = 4

        def get_target_for_node(self, node, branch):
            s = self.sentence(node)
            return {
                'adds': [
                    [
                        {'sentence':        s.lhs , 'designated': False},
                    ],
                    [
                        {'sentence':        s.lhs , 'designated': False},
                    ],
                    [
                        {'sentence':        s.lhs , 'designated': True},
                        {'sentence': s.lhs.negate(), 'designated': True},
                        {'sentence': s.rhs.negate(), 'designated': False},
                    ],
                    [
                        {'sentence':        s.rhs , 'designated': True},
                        {'sentence': s.rhs.negate(), 'designated': True},
                        {'sentence': s.lhs.negate(), 'designated': False},
                    ],
                ],
            }

    class ConjunctionUndesignated(fde.TableauxRules.ConjunctionUndesignated):
        pass

    class ConjunctionNegatedUndesignated(DefaultNodeRule):
        """
        From an unticked, negated, undesignated conjunction node *n* on a branch *b*,
        make two branches *b'* and *b''* from *b*. On *b'*, add two undesignated nodes,
        one for the negation of each conjunct. On *b''*, add four designated nodes, one
        for each of the conjuncts and its negation. Then tick *n*.
        """
        negated      = True
        operator     = 'Conjunction'
        designation  = False
        branch_level = 2

        def get_target_for_node(self, node, branch):
            s = self.sentence(node)
            return {
                'adds': [
                    [
                        {'sentence': s.lhs.negate(), 'designated': False},
                        {'sentence': s.rhs.negate(), 'designated': False},
                    ],
                    [
                        {'sentence':        s.lhs , 'designated': True},
                        {'sentence': s.lhs.negate(), 'designated': True},
                        {'sentence':        s.rhs , 'designated': True},
                        {'sentence': s.rhs.negate(), 'designated': True},
                    ],
                ],
            }

    class DisjunctionDesignated(fde.TableauxRules.DisjunctionDesignated):
        pass

    class DisjunctionNegatedDesignated(fde.TableauxRules.DisjunctionNegatedDesignated):
        pass

    class DisjunctionUndesignated(fde.TableauxRules.DisjunctionUndesignated):
        pass

    class DisjunctionNegatedUndesignated(fde.TableauxRules.DisjunctionNegatedUndesignated):
        pass

    class MaterialConditionalDesignated(DefaultNodeRule):
        """
        This rule reduces to a disjunction.
        """
        operator     = 'Material Conditional'
        designation  = True
        branch_level = 1

        def get_target_for_node(self, node, branch):
            s = self.sentence(node)
            disj = Operated('Disjunction', [s.lhs.negate(), s.rhs])
            return {
                'adds': [
                    [
                        {'sentence': disj, 'designated': self.designation},
                    ],
                ],
            }

    class MaterialConditionalNegatedDesignated(DefaultNodeRule):
        """
        This rule reduces to a negated disjunction.
        """
        negated      = True
        operator     = 'Material Conditional'
        designation  = True
        branch_level = 1

        def get_target_for_node(self, node, branch):
            s = self.sentence(node)
            disj = Operated('Disjunction', [s.lhs.negate(), s.rhs])
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

    class MaterialBiconditionalDesignated(DefaultNodeRule):
        """
        This rule reduces to a conjunction of material conditionals.
        """
        operator     = 'Material Biconditional'
        designation  = True
        branch_level = 1

        def get_target_for_node(self, node, branch):
            s = self.sentence(node)
            cond1 = Operated('Material Conditional', s.operands)
            cond2 = Operated('Material Conditional', list(reversed(s.operands)))
            conj = Operated('Conjunction', [cond1, cond2])
            return {
                'adds': [
                    [
                        {'sentence': conj, 'designated': self.designation}
                    ],
                ],
            }

    class MaterialBiconditionalNegatedDesignated(DefaultNodeRule):
        """
        This rule reduces to a negated conjunction of material conditionals.
        """
        negated      = True
        operator     = 'Material Biconditional'
        designation  = True
        branch_level = 1

        def get_target_for_node(self, node, branch):
            s = self.sentence(node)
            cond1 = Operated('Material Conditional', s.operands)
            cond2 = Operated('Material Conditional', list(reversed(s.operands)))
            conj = Operated('Conjunction', [cond1, cond2])
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

    class ConditionalDesignated(mh.TableauxRules.ConditionalDesignated):
        pass

    class ConditionalNegatedDesignated(mh.TableauxRules.ConditionalNegatedDesignated):
        pass

    class ConditionalUndesignated(mh.TableauxRules.ConditionalUndesignated):
        pass

    class ConditionalNegatedUndesignated(mh.TableauxRules.ConditionalNegatedUndesignated):
        pass

    class BiconditionalDesignated(DefaultNodeRule):
        """
        This rule reduces to a conjunction of conditionals.
        """
        operator    = 'Biconditional'
        designation = True
        branch_level = 1

        def get_target_for_node(self, node, branch):
            s = self.sentence(node)
            cond1 = Operated('Conditional', s.operands)
            cond2 = Operated('Conditional', list(reversed(s.operands)))
            conj = Operated('Conjunction', [cond1, cond2])
            return {
                'adds': [
                    [
                        {'sentence': conj, 'designated': self.designation}
                    ],
                ],
            }

    class BiconditionalNegatedDesignated(DefaultNodeRule):
        """
        This rule reduces to a negated conjunction of conditionals.
        """
        negated     = True
        operator    = 'Biconditional'
        designation = True
        branch_level = 1

        def get_target_for_node(self, node, branch):
            s = self.sentence(node)
            cond1 = Operated('Conditional', s.operands)
            cond2 = Operated('Conditional', list(reversed(s.operands)))
            conj = Operated('Conjunction', [cond1, cond2])
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

    closure_rules = [
        GapClosure,
        DesignationClosure,
    ]

    rule_groups = [
        # Non-branching rules.
        [
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
        ],
        # 1-branching rules.
        [
            ConjunctionUndesignated,
            ConjunctionNegatedUndesignated,
            DisjunctionDesignated,
            DisjunctionNegatedUndesignated,
            ConditionalDesignated,
            ConditionalNegatedUndesignated,
        ],
        # 3-branching rules.
        [
            ConjunctionNegatedDesignated,
        ],
    ]