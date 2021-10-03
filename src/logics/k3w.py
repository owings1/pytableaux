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
# pytableaux - Weak Kleene Logic
name = 'K3W'

class Meta(object):

    title    = 'Weak Kleene 3-valued logic'
    category = 'Many-valued'

    description = 'Three-valued logic with values T, F, and N'

    tags = ['many-valued', 'gappy', 'non-modal', 'first-order']

    category_display_order = 30

from lexicals import operarity, Operated
from . import fde, k3

class Model(k3.Model):
    """
    A K3W model is just like a `K3 model`_ with different tables for some of the connectives.

    .. _K3 model: k3.html#logics.k3.Model
    """

    def value_of_operated(self, sentence, **kw):
        """
        The value of a sentence with a truth-functional operator is determined by
        the values of its operands according to the following tables.

        Note that, for the binary connectives, if either operand has the value **N**,
        then the whole sentence has the value **N**. To (re-)quote a Chinese proverb,
        "a single jot of rat's dung spoils the soup."

        //truth_tables//k3w//
        """
        return super().value_of_operated(sentence, **kw)

    def truth_function(self, operator, a, b=None):
        if operarity(operator) == 2 and (a == 'N' or b == 'N'):
            return 'N'
        return super().truth_function(operator, a, b)

class TableauxSystem(fde.TableauxSystem):
    """
    K3W's Tableaux System inherits directly from the `FDE system`_, employing
    designation markers, and building the trunk in the same way.

    .. _FDE system: fde.html#logics.fde.TableauxSystem
    """
    branchables = {
        'Negation': {
            True : {
                True  : 0,
                False : 0,
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
                False : 1,
            },
            True  : {
                True  : 2,
                False : 2,
            },
        },
        'Disjunction': {
            False  : {
                True  : 2,
                False : 2,
            },
            True : {
                True  : 0,
                False : 2,
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

class DefaultNodeRule(fde.DefaultNodeRule):
    pass

class TableauxRules(object):
    """
    The Tableaux System for K3W contains the `FDE closure rule`_, and the
    `K3 closure rule`_. Several of the operator rules are the same as :ref:`FDE`.
    However, many rules for K3W are different from :ref:`FDE`, given
    the behavior of the *N* value.
    
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

    class ConjunctionNegatedDesignated(DefaultNodeRule):
        """
        From an unticked, designated, negated conjunction node *n* on a branch *b*, make
        three new branches *b'*, *b''*, and *b'''* from *b*. On *b'* add a designated
        node with the first conjunct, and a designated node with the negation of the
        second conjunct. On *b''* add a designated node with the negation of the first
        conjunct, and a designated node with the second conjunct. On *b'''* add
        designated nodes with the negation of each conjunct. Then tick *n*.
        """
        negated     = True
        operator    = 'Conjunction'
        designation = True
        branch_level = 3

        def get_target_for_node(self, node, branch):
            s = self.sentence(node)
            return {
                'adds': [
                    [
                        {'sentence': s.lhs         , 'designated': True},
                        {'sentence': s.rhs.negate(), 'designated': True},
                    ],
                    [
                        {'sentence': s.lhs.negate(), 'designated': True},
                        {'sentence': s.rhs         , 'designated': True},
                    ],
                    [
                        {'sentence': s.lhs.negate(), 'designated': True},
                        {'sentence': s.rhs.negate(), 'designated': True},
                    ],
                ],
            }

        # If you try this 2-branching version, don't forget to
        # reorder the rules!
        #
        #def apply_to_node(self, node, branch):
        #    s = self.sentence(node)
        #    d = self.designation
        #    b1 = branch
        #    b2 = self.tableau.branch(branch)
        #    disj1 = operate('Disjunction', [s.rhs, negate(s.rhs)])
        #    disj2 = operate('Disjunction', [s.lhs, negate(s.lhs)])
        #    b1.update([
        #        {'sentence': negate(s.lhs), 'designated': True},
        #        {'sentence':        disj1 , 'designated': True},
        #    ]).tick(node)
        #    b2.update([
        #        {'sentence': negate(s.rhs), 'designated': True},
        #        {'sentence':        disj2 , 'designated': True},
        #    ]).tick(node)


    class ConjunctionUndesignated(fde.TableauxRules.ConjunctionUndesignated):
        pass

    class ConjunctionNegatedUndesignated(DefaultNodeRule):
        """
        From an unticked, undesignated, negated conjunction node *n* on a branch *b*, make
        three new branches *b'*, *b''*, and *b'''* from *b*. On *b'* add undesignated nodes
        for the first conjunct and its negation. On *b''* add undesignated nodes for the
        second conjunct and its negation. On *b'''* add a designated node for each conjunct.
        Then tick *n*. 
        """
        negated     = True
        operator    = 'Conjunction'
        designation = False
        branch_level = 3

        def get_target_for_node(self, node, branch):
            s = self.sentence(node)
            return {
                'adds': [
                    [
                        {'sentence': s.lhs         , 'designated': False},
                        {'sentence': s.lhs.negate(), 'designated': False},
                    ],
                    [
                        {'sentence': s.rhs         , 'designated': False},
                        {'sentence': s.rhs.negate(), 'designated': False},
                    ],
                    [
                        {'sentence':        s.lhs , 'designated': True},
                        {'sentence':        s.rhs , 'designated': True},
                    ],
                ],
            }

    class DisjunctionDesignated(DefaultNodeRule):
        """
        From an unticked, designated, disjunction node *n* on a branch *b*, make
        three new branches *b'*, *b''*, and *b'''* from *b*. On *b'* add a designated
        node with the first disjunct, and a designated node with the negation of the
        second disjunct. On *b''* add a designated node with the negation of the first
        disjunct, and a designated node with the second disjunct. On *b'''* add a
        designated node with each disjunct. Then tick *n*.
        """
        operator    = 'Disjunction'
        designation = True
        branch_level = 3

        def get_target_for_node(self, node, branch):
            s = self.sentence(node)
            return {
                'adds': [
                    [
                        {'sentence': s.lhs         , 'designated': True},
                        {'sentence': s.rhs.negate(), 'designated': True},
                    ],
                    [
                        {'sentence': s.lhs.negate(), 'designated': True},
                        {'sentence': s.rhs         , 'designated': True},
                    ],
                    [
                        {'sentence':        s.lhs, 'designated': True},
                        {'sentence':        s.rhs, 'designated': True},
                    ],
                ],
            }
            
    class DisjunctionNegatedDesignated(fde.TableauxRules.DisjunctionNegatedDesignated):
        pass

    class DisjunctionUndesignated(DefaultNodeRule):
        """
        From an unticked, undesignated disjunction node *n* on a branch *b*, make three
        new branches *b'*, *b''*, and *b'''* from b. On *b'* add undesignated nodes for
        the first disjunct and its negation. On *b''* add undesignated nodes for the
        second disjunct and its negation. On *b'''* add designated nodes for the negation
        of each disjunct. Then tick *n*.
        """
        operator    = 'Disjunction'
        designation = False
        branch_level = 3

        def get_target_for_node(self, node, branch):
            s = self.sentence(node)
            return {
                'adds': [
                    [
                        {'sentence': s.lhs         , 'designated': False},
                        {'sentence': s.lhs.negate(), 'designated': False},
                    ],
                    [
                        {'sentence': s.rhs         , 'designated': False},
                        {'sentence': s.rhs.negate(), 'designated': False},
                    ],
                    [
                        {'sentence': s.lhs.negate(), 'designated': True},
                        {'sentence': s.rhs.negate(), 'designated': True},
                    ],
                ],
            }

    class DisjunctionNegatedUndesignated(DefaultNodeRule):
        """
        Either the disjunction is designated, or at least one of the disjuncts
        has the value **N**. So, from an unticked, undesignated, negated
        disjunction node *n* on a branch *b*, make three branches *b'*, *b''*,
        and *b'''* from *b*. On *b'* add a designated node with the disjunction.
        On *b''* add two undesignated nodes with the first disjunct and its
        negation, respectively. On *b'''* add undesignated nodes with the second
        disjunct and its negation, respectively. Then tick *n*.
        """
        negated     = True
        operator    = 'Disjunction'
        designation = False
        branch_level = 3

        def get_target_for_node(self, node, branch):
            s = self.sentence(node)
            return {
                'adds': [
                    [
                        {'sentence': s, 'designated': True},
                    ],
                    [
                        {'sentence': s.lhs         , 'designated': False},
                        {'sentence': s.lhs.negate(), 'designated': False},
                    ],
                    [
                        {'sentence': s.rhs         , 'designated': False},
                        {'sentence': s.rhs.negate(), 'designated': False},
                    ],
                ],
            }

    class MaterialConditionalDesignated(DefaultNodeRule):
        """
        This rule reduces to a disjunction.
        """
        operator    = 'Material Conditional'
        designation = True
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
        negated     = True
        operator    = 'Material Conditional'
        designation = True
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
        operator    = 'Material Biconditional'
        designation = True
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
        negated     = True
        operator    = 'Material Biconditional'
        designation = True
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

    class ConditionalDesignated(MaterialConditionalDesignated):
        """
        Same as for the material conditional designated.
        """
        operator = 'Conditional'

    class ConditionalNegatedDesignated(MaterialConditionalNegatedDesignated):
        """
        Same as for the negated material conditional designated.
        """
        operator = 'Conditional'

    class ConditionalUndesignated(MaterialConditionalUndesignated):
        """
        Same as for the material conditional undesignated.
        """
        operator = 'Conditional'

    class ConditionalNegatedUndesignated(MaterialConditionalNegatedUndesignated):
        """
        Same as for the negated material conditional undesignated.
        """
        operator = 'Conditional'

    class BiconditionalDesignated(MaterialBiconditionalDesignated):
        """
        Same as for the material biconditional designated.
        """
        operator = 'Biconditional'

    class BiconditionalNegatedDesignated(MaterialBiconditionalNegatedDesignated):
        """
        Same as for the negated material biconditional designated.
        """
        operator = 'Biconditional'

    class BiconditionalUndesignated(MaterialBiconditionalUndesignated):
        """
        Same as for the material biconditional undesignated.
        """
        operator = 'Biconditional'

    class BiconditionalNegatedUndesignated(MaterialBiconditionalNegatedUndesignated):
        """
        Same as for the negated material biconditional undesignated.
        """
        operator = 'Biconditional'

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
            ConjunctionUndesignated,
        ],
        [
            # three-branching rules
            DisjunctionDesignated,
            DisjunctionUndesignated,
            ConjunctionNegatedDesignated,
            ConjunctionNegatedUndesignated,
            # five-branching rules (formerly)
            DisjunctionNegatedUndesignated,
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