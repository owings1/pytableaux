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
# pytableaux - Paracomplete Hybrid 3-valued Logic
name = 'MH'

class Meta(object):
    title    = 'Paracomplete Hybrid Logic'
    category = 'Many-valued'
    description = ' '.join((
        'Three-valued logic (True, False, Neither) with non-standard disjunction,',
        'and a classical-like conditional',
    ))
    tags = ['many-valued', 'gappy', 'non-modal', 'first-order']
    category_display_order = 70

from lexicals import Operated
from . import fde, k3

class Model(k3.Model):

    def value_of_operated(self, sentence, **kw):
        """
        The value of a sentence with a truth-functional operator is determined by
        the values of its operands according to the following tables.

        //truth_tables//mh//
        """
        return super().value_of_operated(sentence, **kw)

    def is_sentence_opaque(self, sentence):
        if sentence.is_quantified:
            return True
        return super().is_sentence_opaque(sentence)

    def truth_function(self, operator, a, b = None):
        if operator == 'Disjunction':
            if a == 'N' and b == 'N':
                return 'F'
        elif operator == 'Conditional':
            if a == 'T' and b != 'T':
                return 'F'
            return 'T'
        return super().truth_function(operator, a, b)

class TableauxSystem(fde.TableauxSystem):
    """
    MH's Tableaux System inherits directly from the `FDE system`_, employing
    designation markers, and building the trunk in the same way.

    .. _FDE system: fde.html#logics.fde.TableauxSystem
    """
    # operator => negated => designated
    branchables = {
        'Negation': {
            True  : {True: 0, False: 0}
        },
        'Assertion': {
            False : {True: 0, False: 0},
            True  : {True: 0, False: 0},
        },
        'Conjunction': {
            False : {True: 0, False: 1},
            True  : {True: 1, False: 0},
        },
        'Disjunction': {
            False : {True: 1, False: 0},
            True  : {True: 1, False: 3},
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
    The closure rules for MH are the `FDE closure rule`_, and the `K3 closure rule`_.
    ...
    
    .. _FDE closure rule: fde.html#logics.fde.TableauxRules.DesignationClosure
    .. _K3 closure rule: k3.html#logics.k3.TableauxRules.GlutClosure
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

    class DisjunctionNegatedDesignated(DefaultNodeRule):
        """
        From an unticked, negated, designated disjunction node *n* on a branch *b*,
        make two branches *b'* and *b''* from *b*. On *b'* add four undesignated
        nodes, one for each disjunct and its negation. On *b''* add two designated
        nodes, one for the negation of each disjunct. Then tick *n*.
        """
        negated      = True
        operator     = 'Disjunction'
        designation  = True
        branch_level = 2

        def _get_node_targets(self, node, branch):
            s = self.sentence(node)
            return {
                'adds': [
                    [
                        {'sentence': s.lhs         , 'designated': False},
                        {'sentence': s.lhs.negate(), 'designated': False},
                        {'sentence': s.rhs         , 'designated': False},
                        {'sentence': s.rhs.negate(), 'designated': False},
                    ],
                    [
                        {'sentence': s.lhs.negate(), 'designated': True},
                        {'sentence': s.rhs.negate(), 'designated': True},
                    ],
                ],
            }

    class DisjunctionUndesignated(fde.TableauxRules.DisjunctionUndesignated):
        pass

    class DisjunctionNegatedUndesignated(DefaultNodeRule):
        """
        From an unticked, negated, undesignated disjunction node *n* on a branch
        *b*, make four branches from *b*: *b'*, *b''*, *b'''*, and *b''''*. On *b'*,
        add a designated node with the first disjunct, and on *b''*, add a designated
        node with the second disjunct.

        On *b'''* add three nodes:

        - An undesignated node with the first disjunct.
        - An undesignated node with the negation of the first disjunct.
        - A designated node with the negation of the second disjunct.

        On *b''''* add three nodes:

        - An undesignated node with the second disjunct.
        - An undesignated node with the negation of the second disjunct.
        - A designated node with the negation of the first disjunct.

        Then tick *n*.
        """
        negated      = True
        operator     = 'Disjunction'
        designation  = False
        branch_level = 4

        def _get_node_targets(self, node, branch):
            s = self.sentence(node)
            return {
                'adds': [
                    [
                        {'sentence': s.lhs         , 'designated': True},
                    ],
                    [
                        {'sentence': s.rhs         , 'designated': True},
                    ],
                    [
                        {'sentence': s.lhs         , 'designated': False},
                        {'sentence': s.lhs.negate(), 'designated': False},
                        {'sentence': s.rhs.negate(), 'designated': True},
                    ],
                    [
                        {'sentence': s.rhs         , 'designated': False},
                        {'sentence': s.rhs.negate(), 'designated': False},
                        {'sentence': s.lhs.negate(), 'designated': True},
                    ],
                ],
            }

    class MaterialConditionalDesignated(DefaultNodeRule):
        """
        This rule reduces to a disjunction.
        """
        operator     = 'Material Conditional'
        designation  = True
        branch_level = 1

        def _get_node_targets(self, node, branch):
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

        def _get_node_targets(self, node, branch):
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

        def _get_node_targets(self, node, branch):
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

        def _get_node_targets(self, node, branch):
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

    class ConditionalDesignated(DefaultNodeRule):
        """
        From an unticked, designated conditional node *n* on a branch *b*, make
        two branches *b'* and *b''* from *b*. On *b'* add an undesignated node
        with the antecedent, and on *b''* add a designated node with the consequent.
        Then tick *n*.
        """
        operator     = 'Conditional'
        designation  = True
        branch_level = 2

        def _get_node_targets(self, node, branch):
            s = self.sentence(node)
            return {
                'adds': [
                    [
                        {'sentence': s.lhs, 'designated': False},
                    ],
                    [
                        {'sentence': s.rhs, 'designated': True},
                    ],
                ],
            }

    class ConditionalNegatedDesignated(DefaultNodeRule):
        """
        From an unticked, negated, desigated conditional node *n* on a branch *b*,
        add two nodes to *b*:

        - A designated node with the antecedent.
        - An undesignated node with the consequent.

        Then tick *n*.
        """
        negated      = True
        operator     = 'Conditional'
        designation  = True
        branch_level = 1

        def _get_node_targets(self, node, branch):
            s = self.sentence(node)
            return {
                'adds': [
                    [
                        {'sentence': s.lhs, 'designated': True},
                        {'sentence': s.rhs, 'designated': False},
                    ]
                ]
            }

    class ConditionalUndesignated(ConditionalNegatedDesignated):
        """
        From an unticked, undesignated conditional node *n* on a branch *b*, add
        two nodes to *b*:

        - A designated node with the antecedent.
        - An undesignated node with the consequent.

        Then tick *n*.

        Note that the nodes added are the same as for the above
        *ConditionalNegatedDesignated* rule.
        """
        negated     = False
        designation = False

    class ConditionalNegatedUndesignated(ConditionalDesignated):
        """
        From an unticked, negated, undesignated conditional node *n* on a branch *b*,
        make two branches *b'* and *b''* from *b*. On *b'* add an undesignated node
        with the antecedent, and on *b''* add a designated node with the consequent.
        Then tick *n*.

        Note that the result is the same as for the above *ConditionalDesignated* rule.
        """
        negated     = True
        designation = False

    class BiconditionalDesignated(DefaultNodeRule):
        """
        This rule reduces to a conjunction of conditionals.
        """
        operator     = 'Biconditional'
        designation  = True
        branch_level = 1

        def _get_node_targets(self, node, branch):
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
        negated      = True
        operator     = 'Biconditional'
        designation  = True
        branch_level = 1

        def _get_node_targets(self, node, branch):
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
        GlutClosure,
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
            ConjunctionNegatedUndesignated,
            DisjunctionUndesignated,
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
            ConjunctionNegatedDesignated,
            DisjunctionDesignated,
            DisjunctionNegatedDesignated,
            ConditionalDesignated,
            ConditionalNegatedUndesignated,
        ],
        # 3-branching rules.
        [
            DisjunctionNegatedUndesignated,
        ],
    ]