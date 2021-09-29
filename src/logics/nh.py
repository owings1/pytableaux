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

import logic, examples
from . import fde, lp, mh
from logic import negate, operate

class Model(lp.Model):

    def value_of_operated(self, sentence, **kw):
        """
        The value of a sentence with a truth-functional operator is determined by
        the values of its operands according to the following tables.

        //truth_tables//nh//
        """
        return super().value_of_operated(sentence, **kw)

    def is_sentence_opaque(self, sentence):
        if sentence.is_quantified():
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

    class DoubleNegationDesignated(lp.TableauxRules.DoubleNegationDesignated):
        """
        This rule is the same as the `FDE DoubleNegationDesignated rule`_.

        //ruledoc//fde//DoubleNegationDesignated//

        .. _FDE DoubleNegationDesignated rule: fde.html#logics.fde.TableauxRules.DoubleNegationDesignated
        """
        pass

    class DoubleNegationUndesignated(lp.TableauxRules.DoubleNegationUndesignated):
        """
        This rule is the same as the `FDE DoubleNegationUndesignated rule`_.

        //ruledoc//fde//DoubleNegationUndesignated//

        .. _FDE DoubleNegationUndesignated rule: fde.html#logics.fde.TableauxRules.DoubleNegationUndesignated
        """
        pass

    class AssertionDesignated(lp.TableauxRules.AssertionDesignated):
        """
        This rule is the same as the `FDE AssertionDesignated rule`_.

        //ruledoc//fde//AssertionDesignated//

        .. _FDE AssertionDesignated rule: fde.html#logics.fde.TableauxRules.AssertionDesignated
        """
        pass

    class AssertionNegatedDesignated(lp.TableauxRules.AssertionNegatedDesignated):
        """
        This rule is the same as the `FDE AssertionNegatedDesignated rule`_.

        //ruledoc//fde//AssertionNegatedDesignated//

        .. _FDE AssertionNegatedDesignated rule: fde.html#logics.fde.TableauxRules.AssertionNegatedDesignated
        """
        pass

    class AssertionUndesignated(lp.TableauxRules.AssertionUndesignated):
        """
        This rule is the same as the `FDE AssertionUndesignated rule`_.

        //ruledoc//fde//AssertionUndesignated//

        .. _FDE AssertionUndesignated rule: fde.html#logics.fde.TableauxRules.AssertionUndesignated
        """
        pass

    class AssertionNegatedUndesignated(lp.TableauxRules.AssertionNegatedUndesignated):
        """
        This rule is the same as the `FDE AssertionNegatedUndesignated rule`_.

        //ruledoc//fde//AssertionNegatedUndesignated//

        .. _FDE AssertionNegatedUndesignated rule: fde.html#logics.fde.TableauxRules.AssertionNegatedUndesignated
        """
        pass

    class ConjunctionDesignated(lp.TableauxRules.ConjunctionDesignated):
        """
        This rule is the same as the `FDE ConjunctionDesignated rule`_.

        //ruledoc//fde//ConjunctionDesignated//

        .. _FDE ConjunctionDesignated rule: fde.html#logics.fde.TableauxRules.ConjunctionDesignated
        """
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
                        {'sentence': negate(s.lhs), 'designated': True},
                        {'sentence': negate(s.rhs), 'designated': False},
                    ],
                    [
                        {'sentence':        s.rhs , 'designated': True},
                        {'sentence': negate(s.rhs), 'designated': True},
                        {'sentence': negate(s.lhs), 'designated': False},
                    ],
                ],
            }

    class ConjunctionUndesignated(lp.TableauxRules.ConjunctionUndesignated):
        """
        This rule is the same as the `FDE ConjunctionUndesignated rule`_.

        //ruledoc//fde//ConjunctionUndesignated//

        .. _FDE ConjunctionUndesignated rule: fde.html#logics.fde.TableauxRules.ConjunctionUndesignated
        """
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
                        {'sentence': negate(s.lhs), 'designated': False},
                        {'sentence': negate(s.rhs), 'designated': False},
                    ],
                    [
                        {'sentence':        s.lhs , 'designated': True},
                        {'sentence': negate(s.lhs), 'designated': True},
                        {'sentence':        s.rhs , 'designated': True},
                        {'sentence': negate(s.rhs), 'designated': True},
                    ],
                ],
            }

    class DisjunctionDesignated(lp.TableauxRules.DisjunctionDesignated):
        """
        This rule is the same as the `FDE DisjunctionDesignated rule`_.

        //ruledoc//fde//DisjunctionDesignated//

        .. _FDE DisjunctionDesignated rule: fde.html#logics.fde.TableauxRules.DisjunctionDesignated
        """
        pass

    class DisjunctionNegatedDesignated(lp.TableauxRules.DisjunctionNegatedDesignated):
        """
        This rule is the same as the `FDE DisjunctionNegatedDesignated rule`_.

        //ruledoc//fde//DisjunctionNegatedDesignated//

        .. _FDE DisjunctionNegatedDesignated rule: fde.html#logics.fde.TableauxRules.DisjunctionNegatedDesignated
        """
        pass

    class DisjunctionUndesignated(lp.TableauxRules.DisjunctionUndesignated):
        """
        This rule is the same as the `FDE DisjunctionUndesignated rule`_.

        //ruledoc//fde//DisjunctionUndesignated//

        .. _FDE DisjunctionUndesignated rule: fde.html#logics.fde.TableauxRules.DisjunctionUndesignated
        """
        pass

    class DisjunctionNegatedUndesignated(lp.TableauxRules.DisjunctionNegatedUndesignated):
        """
        This rule is the same as the `FDE DisjunctionNegatedUndesignated rule`_.

        //ruledoc//fde//DisjunctionNegatedUndesignated//

        .. _FDE DisjunctionNegatedUndesignated rule: fde.html#logics.fde.TableauxRules.DisjunctionNegatedUndesignated
        """
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
            disj = operate('Disjunction', [negate(s.lhs), s.rhs])
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
            disj = operate('Disjunction', [negate(s.lhs), s.rhs])
            return {
                'adds': [
                    [
                        {'sentence': negate(disj), 'designated': self.designation},
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
            cond1 = operate('Material Conditional', s.operands)
            cond2 = operate('Material Conditional', list(reversed(s.operands)))
            conj = operate('Conjunction', [cond1, cond2])
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
            cond1 = operate('Material Conditional', s.operands)
            cond2 = operate('Material Conditional', list(reversed(s.operands)))
            conj = operate('Conjunction', [cond1, cond2])
            return {
                'adds': [
                    [
                        {'sentence': negate(conj), 'designated': self.designation}
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
        """
        This rule is the same as the `MH ConditionalDesignated rule`_.

        //ruledoc//mh//ConditionalDesignated//

        .. _MH ConditionalDesignated rule: mh.html#logics.mh.TableauxRules.ConditionalDesignated
        """
        pass

    class ConditionalNegatedDesignated(mh.TableauxRules.ConditionalNegatedDesignated):
        """
        This rule is the same as the `MH ConditionalNegatedDesignated rule`_.

        //ruledoc//mh//ConditionalNegatedDesignated//

        .. _MH ConditionalNegatedDesignated rule: mh.html#logics.mh.TableauxRules.ConditionalNegatedDesignated
        """
        pass

    class ConditionalUndesignated(mh.TableauxRules.ConditionalUndesignated):
        """
        This rule is the same as the `MH ConditionalUndesignated rule`_.

        //ruledoc//mh//ConditionalUndesignated//

        .. _MH ConditionalUndesignated rule: mh.html#logics.mh.TableauxRules.ConditionalUndesignated
        """
        pass

    class ConditionalNegatedUndesignated(mh.TableauxRules.ConditionalNegatedUndesignated):
        """
        This rule is the same as the `MH ConditionalNegatedUndesignated rule`_.

        //ruledoc//mh//ConditionalNegatedUndesignated//

        .. _MH ConditionalNegatedUndesignated rule: mh.html#logics.mh.TableauxRules.ConditionalNegatedUndesignated
        """
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
            cond1 = operate('Conditional', s.operands)
            cond2 = operate('Conditional', list(reversed(s.operands)))
            conj = operate('Conjunction', [cond1, cond2])
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
            cond1 = operate('Conditional', s.operands)
            cond2 = operate('Conditional', list(reversed(s.operands)))
            conj = operate('Conjunction', [cond1, cond2])
            return {
                'adds': [
                    [
                        {'sentence': negate(conj), 'designated': self.designation}
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

    closure_rules = list(lp.TableauxRules.closure_rules)

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