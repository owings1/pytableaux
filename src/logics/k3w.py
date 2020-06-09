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
# pytableaux - Weak Kleene Logic
name = 'K3W'

class Meta(object):
    title = 'Weak Kleene 3-valued logic'
    description = 'Three-valued logic with values T, F, and N'
    tags = ['many-valued', 'gappy', 'non-modal', 'first-order']
    category = 'Many-valued'
    category_display_order = 3

import logic
from logic import negate, negative, operate
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
        return super(Model, self).value_of_operated(sentence, **kw)

    def truth_function(self, operator, a, b=None):
        if logic.arity(operator) == 2 and (a == 'N' or b == 'N'):
            return 'N'
        return super(Model, self).truth_function(operator, a, b)

class TableauxSystem(fde.TableauxSystem):
    """
    K3W's Tableaux System inherits directly from the `FDE system`_, employing
    designation markers, and building the trunk in the same way.

    .. _FDE system: fde.html#logics.fde.TableauxSystem
    """
    branchables = {
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
        
class TableauxRules(object):
    """
    The Tableaux System for K3W contains the `FDE closure rule`_, and the
    `K3 closure rule`_. Several of the operator rules are the same as `FDE`_.
    However, many rules for K3W are different from `FDE`_, given
    the behavior of the *N* value.
    
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

    class ConjunctionNegatedDesignated(logic.TableauxSystem.FilterNodeRule):
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

        def apply_to_node(self, node, branch):
            s = self.sentence(node)
            b1 = branch
            b2 = self.branch(branch)
            b3 = self.branch(branch)
            b1.update([
                {'sentence':        s.lhs , 'designated': True},
                {'sentence': negate(s.rhs), 'designated': True},
            ]).tick(node)
            b2.update([
                {'sentence': negate(s.lhs), 'designated': True},
                {'sentence':        s.rhs , 'designated': True},
            ]).tick(node)
            b3.update([
                {'sentence': negate(s.lhs), 'designated': True},
                {'sentence': negate(s.rhs), 'designated': True},
            ]).tick(node)

        def score_candidate_map(self, target):
            branch = target['branch']
            s = self.sentence(target['node'])
            return {
                'b1': branch.has_any([
                    # FDE closure
                    {'sentence':          s.lhs , 'designated': False},
                    {'sentence': negative(s.rhs), 'designated': False},
                    # K3 closure
                    {'sentence': negative(s.lhs), 'designated': True},
                    {'sentence':          s.rhs , 'designated': True},
                ]),
                'b2': branch.has_any([
                    # FDE closure
                    {'sentence': negative(s.lhs), 'designated': False},
                    {'sentence':          s.rhs , 'designated': False},
                    # K3 closure
                    {'sentence':          s.lhs , 'designated': True},
                    {'sentence': negative(s.rhs), 'designated': True},
                ]),
                'b3': branch.has_any([
                    # FDE closure
                    {'sentence': negative(s.lhs), 'designated': False},
                    {'sentence': negative(s.rhs), 'designated': False},
                    # K3 closure
                    {'sentence': s.lhs, 'designated': True},
                    {'sentence': s.rhs, 'designated': True},
                ]),
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


    class ConjunctionUndesignated(k3.TableauxRules.ConjunctionUndesignated):
        """
        This rule is the same as the `FDE ConjunctionUndesignated rule`_.

        .. _FDE ConjunctionUndesignated rule: fde.html#logics.fde.TableauxRules.ConjunctionUndesignated
        """
        pass

    class ConjunctionNegatedUndesignated(logic.TableauxSystem.FilterNodeRule):
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

        def apply_to_node(self, node, branch):
            s = self.sentence(node)
            b1 = branch
            b2 = self.branch(branch)
            b3 = self.branch(branch)
            b1.update([
                {'sentence':        s.lhs , 'designated': False},
                {'sentence': negate(s.lhs), 'designated': False},
            ]).tick(node)
            b2.update([
                {'sentence':        s.rhs , 'designated': False},
                {'sentence': negate(s.rhs), 'designated': False},
            ]).tick(node)
            b3.update([
                {'sentence':        s.lhs , 'designated': True},
                {'sentence':        s.rhs , 'designated': True},
            ]).tick(node)

        def score_candidate_map(self, target):
            branch = target['branch']
            s = self.sentence(target['node'])
            return {
                'b1': branch.has_any([
                    # FDE closure
                    {'sentence':          s.lhs , 'designated': True},
                    {'sentence': negative(s.lhs), 'designated': True},
                    # K3 closure - n/a
                ]),
                'b2': branch.has_any([
                    # FDE closure
                    {'sentence':          s.rhs , 'designated': True},
                    {'sentence': negative(s.rhs), 'designated': True},
                    # K3 closure - n/a
                ]),
                'b3': branch.has_any([
                    # FDE closure
                    {'sentence': s.lhs, 'designated': False},
                    {'sentence': s.rhs, 'designated': False},
                    # K3 closure
                    {'sentence': negative(s.lhs), 'designated': True},
                    {'sentence': negative(s.rhs), 'designated': True},
                ]),
            }

    class DisjunctionDesignated(logic.TableauxSystem.FilterNodeRule):
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

        def apply_to_node(self, node, branch):
            s = self.sentence(node)
            b1 = branch
            b2 = self.branch(branch)
            b3 = self.branch(branch)
            b1.update([
                {'sentence':        s.lhs , 'designated': True},
                {'sentence': negate(s.rhs), 'designated': True},
            ]).tick(node)
            b2.update([
                {'sentence': negate(s.lhs), 'designated': True},
                {'sentence':        s.rhs , 'designated': True},
            ]).tick(node)
            b3.update([
                {'sentence': s.lhs, 'designated': True},
                {'sentence': s.rhs, 'designated': True},
            ]).tick(node)

        def score_candidate_map(self, target):
            branch = target['branch']
            s = self.sentence(target['node'])
            return {
                'b1': branch.has_any([
                    # FDE closure
                    {'sentence':          s.lhs , 'designated': False},
                    {'sentence': negative(s.rhs), 'designated': False},
                    # K3 closure
                    {'sentence': negative(s.lhs), 'designated': True},
                    {'sentence':          s.rhs , 'designated': True},
                ]),
                'b2': branch.has_any([
                    # FDE closure
                    {'sentence': negative(s.lhs), 'designated': False},
                    {'sentence':          s.rhs , 'designated': False},
                    # K3 closure
                    {'sentence':          s.lhs , 'designated': True},
                    {'sentence': negative(s.rhs), 'designated': True},
                ]),
                'b3': branch.has_any([
                    # FDE closure
                    {'sentence': s.lhs, 'designated': False},
                    {'sentence': s.rhs, 'designated': False},
                    # K3 closure
                    {'sentence': negative(s.lhs), 'designated': True},
                    {'sentence': negative(s.rhs), 'designated': True},
                ]),
            }
            
    class DisjunctionNegatedDesignated(k3.TableauxRules.DisjunctionNegatedDesignated):
        """
        This rule is the same as the `FDE DisjunctionNegatedDesignated rule`_.

        .. _FDE DisjunctionNegatedDesignated rule: fde.html#logics.fde.TableauxRules.DisjunctionNegatedDesignated
        """
        pass

    class DisjunctionUndesignated(logic.TableauxSystem.FilterNodeRule):
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

        def apply_to_node(self, node, branch):
            s = self.sentence(node)
            d = self.designation
            b1 = branch
            b2 = self.branch(branch)
            b3 = self.branch(branch)
            b1.update([
                {'sentence':        s.lhs , 'designated': False},
                {'sentence': negate(s.lhs), 'designated': False},
            ]).tick(node)
            b2.update([
                {'sentence':        s.rhs , 'designated': False},
                {'sentence': negate(s.rhs), 'designated': False},
            ]).tick(node)
            b3.update([
                {'sentence': negate(s.lhs), 'designated': True},
                {'sentence': negate(s.rhs), 'designated': True},
            ]).tick(node)

        def score_candidate_map(self, target):
            branch = target['branch']
            s = self.sentence(target['node'])
            d = self.designation
            return {
                'b1': branch.has_any([
                    # FDE closure
                    {'sentence':          s.lhs , 'designated': True},
                    {'sentence': negative(s.lhs), 'designated': True},
                    # K3 closure - n/a
                ]),
                'b2': branch.has_any([
                    # FDE closure
                    {'sentence':          s.rhs , 'designated': True},
                    {'sentence': negative(s.rhs), 'designated': True},
                    # K3 closure - n/a
                ]),
                'b3': branch.has_any([
                    # FDE closure
                    {'sentence': negative(s.lhs), 'designated': False},
                    {'sentence': negative(s.rhs), 'designated': False},
                    # K3 closure
                    {'sentence': s.lhs, 'designated': True},
                    {'sentence': s.rhs, 'designated': True},
                ]),
            }

    class DisjunctionNegatedUndesignated(logic.TableauxSystem.FilterNodeRule):
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

        def apply_to_node(self, node, branch):
            s = self.sentence(node)
            b1 = branch
            b2 = self.branch(branch)
            b3 = self.branch(branch)
            b1.add({'sentence': s, 'designated': True}).tick(node)
            b2.update([
                {'sentence':        s.lhs , 'designated': False},
                {'sentence': negate(s.lhs), 'designated': False},
            ]).tick(node)
            b3.update([
                {'sentence':        s.rhs , 'designated': False},
                {'sentence': negate(s.rhs), 'designated': False},
            ]).tick(node)

        def score_candidate_map(self, target):
            branch = target['branch']
            s = self.sentence(target['node'])
            return {
                'b1': branch.has_any([
                    # FDE closure
                    {'sentence': s, 'designated': False},
                    # K3 closure
                    {'sentence': negative(s), 'designated': True},
                ]),
                    'b2': branch.has_any([
                    # FDE closure
                    {'sentence':          s.lhs , 'designated': True},
                    {'sentence': negative(s.lhs), 'designated': True},
                    # K3 closure - no known impl
                ]),
                'b3': branch.has_any([
                    # FDE closure
                    {'sentence':          s.rhs , 'designated': True},
                    {'sentence': negative(s.rhs), 'designated': True},
                    # K3 closure - no known impl
                ]),
            }

    class MaterialConditionalDesignated(k3.TableauxRules.MaterialConditionalDesignated):
        """
        This rule reduces to a disjunction.
        """

        def apply_to_node(self, node, branch):
            s = self.sentence(node)
            d = self.designation
            sd = operate('Disjunction', [negate(s.lhs), s.rhs])
            branch.add({'sentence': sd, 'designated': d}).tick(node)

    class MaterialConditionalNegatedDesignated(k3.TableauxRules.MaterialConditionalNegatedDesignated):
        """
        This rule reduces to a negated disjunction.
        """

        def apply_to_node(self, node, branch):
            s = self.sentence(node)
            d = self.designation
            sd = operate('Disjunction', [negate(s.lhs), s.rhs])
            branch.add({'sentence': negate(sd), 'designated': d}).tick(node)

    class MaterialConditionalUndesignated(MaterialConditionalDesignated):
        """
        This rule reduces to a disjunction.
        """

        designation = False

    class MaterialConditionalNegatedUndesignated(MaterialConditionalNegatedDesignated):
        """
        This rule reduces to a negated disjunction.
        """

        designation = False

    class MaterialBiconditionalDesignated(k3.TableauxRules.MaterialBiconditionalDesignated):
        """
        This rule reduces to a conjunction of material conditionals.
        """

        def apply_to_node(self, node, branch):
            s = self.sentence(node)
            d = self.designation
            branch.add({
                'sentence' : operate('Conjunction', [
                    operate('Material Conditional', s.operands),
                    operate('Material Conditional', list(reversed(s.operands)))
                ]),
                'designated' : d
            }).tick(node)

    class MaterialBiconditionalNegatedDesignated(k3.TableauxRules.MaterialBiconditionalNegatedDesignated):
        """
        This rule reduces to a negated conjunction of material conditionals.
        """

        def apply_to_node(self, node, branch):
            s = self.sentence(node)
            d = self.designation
            branch.add({
                'sentence' : negate(
                    operate('Conjunction', [
                        operate('Material Conditional', s.operands),
                        operate('Material Conditional', list(reversed(s.operands)))
                    ])
                ),
                'designated' : d
            }).tick(node)

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