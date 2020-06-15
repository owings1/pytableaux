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
# pytableaux - Strong Kleene Logic
name = 'K3'

class Meta(object):

    title    = 'Strong Kleene 3-valued logic'
    category = 'Many-valued'

    description = 'Three-valued logic (T, F, N)'

    tags = ['many-valued', 'gappy', 'non-modal', 'first-order']
    
    category_display_order = 2

import logic, helpers
from logic import negate, negative
from . import fde

class Model(fde.Model):
    """
    A K3 model is like an `FDE model`_ without the **B** value, which yields an
    exclusivity restraint an predicate's extension/anti-extension.

    .. _FDE model: fde.html#logics.fde.Model
    """

    #: The admissible values
    truth_values = set(['F', 'N', 'T'])

    #: The designated value
    designated_values = set(['T'])

    truth_values_list = ['F', 'N', 'T']
    unassigned_value = 'N'

    #tmp
    nvals = {
        'F': 0   ,
        'N': 0.5 ,
        'T': 1   ,
    }
    cvals = {
        0   : 'F',
        0.5 : 'N',
        1   : 'T',
    }

    def value_of_operated(self, sentence, **kw):
        """
        The value of a sentence with a truth-functional operator is determined by
        the values of its operands according to the following tables.

        //truth_tables//k3//
        """
        return super(Model, self).value_of_operated(sentence, **kw)

class TableauxSystem(fde.TableauxSystem):
    """
    K3's Tableaux System inherits directly from the `FDE system`_, employing
    designation markers, and building the trunk in the same way.

    .. _FDE system: fde.html#logics.fde.TableauxSystem
    """
    pass
        
class TableauxRules(object):
    """
    The Tableaux System for K3 contains all the rules from `FDE`_, as well as an additional
    closure rule.
    """
    
    class GlutClosure(logic.TableauxSystem.ClosureRule):
        """
        A branch closes when a sentence and its negation both appear as designated nodes.
        This rule is **in addition to** the `FDE closure rule`_.

        .. _FDE closure Rule: fde.html#logics.fde.TableauxRules.Closure
        """

        # tracker implementation

        def check_for_target(self, node, branch):
            nnode = self._find_closing_node(node, branch)
            if nnode:
               return {'nodes': set([node, nnode]), 'type': 'Nodes'}

        # rule implementation

        def node_will_close_branch(self, node, branch):
            if self._find_closing_node(node, branch):
                return True
            return False

        def applies_to_branch(self, branch):
            return self.tracker.cached_target(branch)

        def example_nodes(self, branch):
            a = logic.atomic(0, 0)
            return [
                {'sentence':        a , 'designated': True},
                {'sentence': negate(a), 'designated': True},
            ]

        # private util

        def _find_closing_node(self, node, branch):
            if node.has('sentence', 'designated') and node.props['designated']:
                return branch.find({
                    'sentence'   : negative(node.props['sentence']),
                    'designated' : True,
                })

    class DoubleNegationDesignated(fde.TableauxRules.DoubleNegationDesignated):
        """
        This rule is the same as the `FDE DoubleNegationDesignated rule`_.

        .. _FDE DoubleNegationDesignated rule: fde.html#logics.fde.TableauxRules.DoubleNegationDesignated
        """
        pass

    class DoubleNegationUndesignated(fde.TableauxRules.DoubleNegationUndesignated):
        """
        This rule is the same as the `FDE DoubleNegationUndesignated rule`_.

        .. _FDE DoubleNegationUndesignated rule: fde.html#logics.fde.TableauxRules.DoubleNegationUndesignated
        """
        pass

    class AssertionDesignated(fde.TableauxRules.AssertionDesignated):
        """
        This rule is the same as the `FDE AssertionDesignated rule`_.

        .. _FDE AssertionDesignated rule: fde.html#logics.fde.TableauxRules.AssertionDesignated
        """
        pass

    class AssertionNegatedDesignated(fde.TableauxRules.AssertionNegatedDesignated):
        """
        This rule is the same as the `FDE AssertionNegatedDesignated rule`_.

        .. _FDE AssertionNegatedDesignated rule: fde.html#logics.fde.TableauxRules.AssertionNegatedDesignated
        """
        pass

    class AssertionUndesignated(fde.TableauxRules.AssertionUndesignated):
        """
        This rule is the same as the `FDE AssertionUndesignated rule`_.

        .. _FDE AssertionUndesignated rule: fde.html#logics.fde.TableauxRules.AssertionUndesignated
        """
        pass

    class AssertionNegatedUndesignated(fde.TableauxRules.AssertionNegatedUndesignated):
        """
        This rule is the same as the `FDE AssertionNegatedUndesignated rule`_.

        .. _FDE AssertionNegatedUndesignated rule: fde.html#logics.fde.TableauxRules.AssertionNegatedUndesignated
        """
        pass

    class ConjunctionDesignated(fde.TableauxRules.ConjunctionDesignated):
        """
        This rule is the same as the `FDE ConjunctionDesignated rule`_.

        .. _FDE ConjunctionDesignated rule: fde.html#logics.fde.TableauxRules.ConjunctionDesignated
        """
        pass

    class ConjunctionNegatedDesignated(fde.TableauxRules.ConjunctionNegatedDesignated):
        """
        This rule is the same as the `FDE ConjunctionNegatedDesignated rule`_.

        .. _FDE ConjunctionNegatedDesignated rule: fde.html#logics.fde.TableauxRules.ConjunctionNegatedDesignated
        """

        def score_candidate_map(self, target):
            scores = super(TableauxRules.ConjunctionNegatedDesignated, self).score_candidate_map(target)
            if self.designation:
                # only apply to implementations for designated rules
                branch = target['branch']
                s = self.sentence(target['node'])
                scores.update({
                    'b1': scores['b1'] or branch.has({'sentence': s.lhs, 'designated': True}),
                    'b2': scores['b2'] or branch.has({'sentence': s.rhs, 'designated': True}),
                })
            return scores

    class ConjunctionUndesignated(fde.TableauxRules.ConjunctionUndesignated):
        """
        This rule is the same as the `FDE ConjunctionUndesignated rule`_.

        .. _FDE ConjunctionUndesignated rule: fde.html#logics.fde.TableauxRules.ConjunctionUndesignated
        """

        def score_candidate_map(self, target):
            scores = super(TableauxRules.ConjunctionUndesignated, self).score_candidate_map(target)
            if self.designation:
                # only apply to implementations for designated rules
                branch = target['branch']
                s = self.sentence(target['node'])
                scores.update({
                    'b1': scores['b1'] or branch.has({'sentence': negative(s.lhs), 'designated': True}),
                    'b2': scores['b2'] or branch.has({'sentence': negative(s.rhs), 'designated': True}),
                })
            return scores

    class ConjunctionNegatedUndesignated(fde.TableauxRules.ConjunctionNegatedUndesignated):
        """
        This rule is the same as the `FDE ConjunctionNegatedUndesignated rule`_.

        .. _FDE ConjunctionNegatedUndesignated rule: fde.html#logics.fde.TableauxRules.ConjunctionNegatedUndesignated
        """
        pass

    class DisjunctionDesignated(ConjunctionUndesignated):
        """
        This rule is the same as the `FDE DisjunctionDesignated rule`_.

        .. _FDE DisjunctionDesignated rule: fde.html#logics.fde.TableauxRules.DisjunctionDesignated
        """

        operator    = 'Disjunction'
        designation = True

    class DisjunctionNegatedDesignated(ConjunctionNegatedUndesignated):
        """
        This rule is the same as the `FDE DisjunctionNegatedDesignated rule`_.

        .. _FDE DisjunctionNegatedDesignated rule: fde.html#logics.fde.TableauxRules.DisjunctionNegatedDesignated
        """

        operator    = 'Disjunction'
        designation = True

    class DisjunctionUndesignated(ConjunctionDesignated):
        """
        This rule is the same as the `FDE DisjunctionUndesignated rule`_.

        .. _FDE DisjunctionUndesignated rule: fde.html#logics.fde.TableauxRules.DisjunctionUndesignated
        """

        operator    = 'Disjunction'
        designation = False

    class DisjunctionNegatedUndesignated(ConjunctionNegatedDesignated):
        """
        This rule is the same as the `FDE DisjunctionNegatedUndesignated rule`_.

        .. _FDE DisjunctionNegatedUndesignated rule: fde.html#logics.fde.TableauxRules.DisjunctionNegatedUndesignated
        """

        operator    = 'Disjunction'
        designation = False

    class MaterialConditionalDesignated(fde.TableauxRules.MaterialConditionalDesignated):
        """
        This rule is the same as the `FDE MaterialConditionalDesignated rule`_.

        .. _FDE MaterialConditionalDesignated rule: fde.html#logics.fde.TableauxRules.MaterialConditionalDesignated
        """

        def score_candidate_map(self, target):
            scores = super(TableauxRules.MaterialConditionalDesignated, self).score_candidate_map(target)
            if self.designation:
                # only apply to implementations for designated rules
                branch = target['branch']
                s = self.sentence(target['node'])
                scores.update({
                    'b1': scores['b1'] or branch.has({'sentence':          s.lhs , 'designated': True}),
                    'b2': scores['b2'] or branch.has({'sentence': negative(s.rhs), 'designated': True}),
                })
            return scores

    class MaterialConditionalNegatedDesignated(fde.TableauxRules.MaterialConditionalNegatedDesignated):
        """
        This rule is the same as the `FDE MaterialConditionalNegatedDesignated rule`_.

        .. _FDE MaterialConditionalNegatedDesignated rule: fde.html#logics.fde.TableauxRules.MaterialConditionalNegatedDesignated
        """
        pass

    class MaterialConditionalUndesignated(fde.TableauxRules.MaterialConditionalUndesignated):
        """
        This rule is the same as the `FDE MaterialConditionalUndesignated rule`_.

        .. _FDE MaterialConditionalUndesignated rule: fde.html#logics.fde.TableauxRules.MaterialConditionalUndesignated
        """
        pass

    class MaterialConditionalNegatedUndesignated(fde.TableauxRules.MaterialConditionalNegatedUndesignated):
        """
        This rule is the same as the `FDE MaterialConditionalNegatedUndesignated rule`_.

        .. _FDE MaterialConditionalNegatedUndesignated rule: fde.html#logics.fde.TableauxRules.MaterialConditionalNegatedUndesignated
        """
        pass

    class MaterialBiconditionalDesignated(fde.TableauxRules.MaterialBiconditionalDesignated):
        """
        This rule is the same as the `FDE MaterialBiconditionalDesignated rule`_.

        .. _FDE MaterialBiconditionalDesignated rule: fde.html#logics.fde.TableauxRules.MaterialBiconditionalDesignated
        """

        def score_candidate_map(self, target):
            scores = super(TableauxRules.MaterialBiconditionalDesignated, self).score_candidate_map(target)
            if self.designation:
                # only apply to implementations for designated rules
                branch = target['branch']
                s = self.sentence(target['node'])
                scores.update({
                    'b1': scores['b1'] or branch.has_any([
                        {'sentence': s.lhs, 'designated': True},
                        {'sentence': s.rhs, 'designated': True},
                    ]),
                    'b2': scores['b2'] or branch.has_any([
                        {'sentence': negative(s.lhs), 'designated': True},
                        {'sentence': negative(s.rhs), 'designated': True},
                    ]),
                })
            return scores

    class MaterialBiconditionalNegatedDesignated(fde.TableauxRules.MaterialBiconditionalNegatedDesignated):
        """
        This rule is the same as the `FDE MaterialBiconditionalNegatedDesignated rule`_.

        .. _FDE MaterialBiconditionalNegatedDesignated rule: fde.html#logics.fde.TableauxRules.MaterialBiconditionalNegatedDesignated
        """

        def score_candidate_map(self, target):
            scores = super(TableauxRules.MaterialBiconditionalNegatedDesignated, self).score_candidate_map(target)
            if self.designation:
                # only apply to implementations for designated rules
                branch = target['branch']
                s = self.sentence(target['node'])
                scores.update({
                    'b1': scores['b1'] or branch.has_any([
                        {'sentence': negative(s.lhs), 'designated': True},
                        {'sentence':          s.rhs , 'designated': True},
                    ]),
                    'b2': scores['b2'] or branch.has_any([
                        {'sentence':          s.lhs , 'designated': True},
                        {'sentence': negative(s.rhs), 'designated': True},
                    ]),
                })
            return scores

    class MaterialBiconditionalUndesignated(MaterialBiconditionalNegatedDesignated):
        """
        This rule is the same as the `FDE MaterialBiconditionalUndesignated rule`_.

        .. _FDE MaterialBiconditionalUndesignated rule: fde.html#logics.fde.TableauxRules.MaterialBiconditionalUndesignated
        """

        negated     = False
        designation = False

    class MaterialBiconditionalNegatedUndesignated(MaterialBiconditionalDesignated):
        """
        This rule is the same as the `FDE MaterialBiconditionalNegatedUndesignated rule`_.

        .. _FDE MaterialBiconditionalNegatedUndesignated rule: fde.html#logics.fde.TableauxRules.MaterialBiconditionalNegatedUndesignated
        """

        negated     = True
        designation = False

    class ConditionalDesignated(MaterialConditionalDesignated):
        """
        This rule is the same as the `FDE ConditionalDesignated rule`_.

        .. _FDE ConditionalDesignated rule: fde.html#logics.fde.TableauxRules.ConditionalDesignated
        """

        operator = 'Conditional'

    class ConditionalNegatedDesignated(MaterialConditionalNegatedDesignated):
        """
        This rule is the same as the `FDE ConditionalNegatedDesignated rule`_.

        .. _FDE ConditionalNegatedDesignated rule: fde.html#logics.fde.TableauxRules.ConditionalNegatedDesignated
        """

        operator = 'Conditional'

    class ConditionalUndesignated(MaterialConditionalUndesignated):
        """
        This rule is the same as the `FDE ConditionalUndesignated rule`_.

        .. _FDE ConditionalUndesignated rule: fde.html#logics.fde.TableauxRules.ConditionalUndesignated
        """

        operator = 'Conditional'

    class ConditionalNegatedUndesignated(MaterialConditionalNegatedUndesignated):
        """
        This rule is the same as the `FDE ConditionalNegatedUndesignated rule`_.

        .. _FDE ConditionalNegatedUndesignated rule: fde.html#logics.fde.TableauxRules.ConditionalNegatedUndesignated
        """

        operator = 'Conditional'
        
    class BiconditionalDesignated(MaterialBiconditionalDesignated):
        """
        This rule is the same as the `FDE BiconditionalDesignated rule`_.

        .. _FDE BiconditionalDesignated rule: fde.html#logics.fde.TableauxRules.BiconditionalDesignated
        """

        operator = 'Biconditional'

    class BiconditionalNegatedDesignated(MaterialBiconditionalNegatedDesignated):
        """
        This rule is the same as the `FDE BiconditionalNegatedDesignated rule`_.

        .. _FDE BiconditionalNegatedDesignated rule: fde.html#logics.fde.TableauxRules.BiconditionalNegatedDesignated
        """

        operator = 'Biconditional'

    class BiconditionalUndesignated(MaterialBiconditionalUndesignated):
        """
        This rule is the same as the `FDE BiconditionalUndesignated rule`_.

        .. _FDE BiconditionalUndesignated rule: fde.html#logics.fde.TableauxRules.BiconditionalUndesignated
        """

        operator = 'Biconditional'

    class BiconditionalNegatedUndesignated(MaterialBiconditionalNegatedUndesignated):
        """
        This rule is the same as the `FDE BiconditionalNegatedUndesignated rule`_.

        .. _FDE BiconditionalNegatedUndesignated rule: fde.html#logics.fde.TableauxRules.BiconditionalNegatedUndesignated
        """

        operator = 'Biconditional'

    class ExistentialDesignated(fde.TableauxRules.ExistentialDesignated):
        """
        This rule is the same as the `FDE ExistentialDesignated rule`_.

        .. _FDE ExistentialDesignated rule: fde.html#logics.fde.TableauxRules.ExistentialDesignated
        """
        pass

    class ExistentialNegatedDesignated(fde.TableauxRules.ExistentialNegatedDesignated):
        """
        This rule is the same as the `FDE ExistentialNegatedDesignated rule`_.

        .. _FDE ExistentialNegatedDesignated rule: fde.html#logics.fde.TableauxRules.ExistentialNegatedDesignated
        """
        pass

    class ExistentialUndesignated(fde.TableauxRules.ExistentialUndesignated):
        """
        This rule is the same as the `FDE ExistentialUndesignated rule`_.

        .. _FDE ExistentialUndesignated rule: fde.html#logics.fde.TableauxRules.ExistentialUndesignated
        """
        pass

    class ExistentialNegatedUndesignated(fde.TableauxRules.ExistentialNegatedUndesignated):
        """
        This rule is the same as the `FDE ExistentialNegatedUndesignated rule`_.

        .. _FDE ExistentialNegatedUndesignated rule: fde.html#logics.fde.TableauxRules.ExistentialNegatedUndesignated
        """
        pass

    class UniversalDesignated(fde.TableauxRules.UniversalDesignated):
        """
        This rule is the same as the `FDE UniversalDesignated rule`_.

        .. _FDE UniversalDesignated rule: fde.html#logics.fde.TableauxRules.UniversalDesignated
        """
        pass

    class UniversalNegatedDesignated(fde.TableauxRules.UniversalNegatedDesignated):
        """
        This rule is the same as the `FDE UniversalNegatedDesignated rule`_.

        .. _FDE UniversalNegatedDesignated rule: fde.html#logics.fde.TableauxRules.UniversalNegatedDesignated
        """
        pass

    class UniversalUndesignated(fde.TableauxRules.UniversalUndesignated):
        """
        This rule is the same as the `FDE UniversalUndesignated rule`_.

        .. _FDE UniversalUndesignated rule: fde.html#logics.fde.TableauxRules.UniversalUndesignated
        """
        pass

    class UniversalNegatedUndesignated(fde.TableauxRules.UniversalNegatedUndesignated):
        """
        This rule is the same as the `FDE UniversalNegatedUndesignated rule`_.

        .. _FDE UniversalNegatedUndesignated rule: fde.html#logics.fde.TableauxRules.UniversalNegatedUndesignated
        """
        pass

    closure_rules = list(fde.TableauxRules.closure_rules) + [
        GlutClosure,
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
            ConditionalUndesignated, 
            ConditionalNegatedDesignated,
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
            ConditionalNegatedUndesignated,
            BiconditionalDesignated,
            BiconditionalNegatedDesignated,
            BiconditionalUndesignated,
            BiconditionalNegatedUndesignated,
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