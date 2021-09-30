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
# pytableaux - Strong Kleene Logic
name = 'K3'

class Meta(object):

    title    = 'Strong Kleene 3-valued logic'
    category = 'Many-valued'

    description = 'Three-valued logic (T, F, N)'

    tags = ['many-valued', 'gappy', 'non-modal', 'first-order']
    
    category_display_order = 20

import logic
from logic import negate, negative
from . import fde

class Model(fde.Model):
    """
    A K3 model is like an :class:`FDE model <logics.fde.Model>` without the **B** value.
    """

    #: The set of admissible values for sentences in a model.
    #:
    #: :type: set
    #: :value: {T, N, F}
    #: :meta hide-value:
    truth_values = set(['F', 'N', 'T'])

    #: There (singleton) set of designated values in model.
    #:
    #: :type: set
    #: :value: {T}
    #: :meta hide-value:
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

class TableauxSystem(fde.TableauxSystem):
    """
    K3's Tableaux System inherits directly from the `FDE system`_, employing
    designation markers, and building the trunk in the same way.

    .. _FDE system: fde.html#logics.fde.TableauxSystem
    """
    pass
        
class TableauxRules(object):
    """
    The Tableaux System for K3 contains all the rules from {@FDE}, as well as an additional
    closure rule.
    """

    class GlutClosure(logic.TableauxSystem.ClosureRule):
        """
        A branch closes when a sentence and its negation both appear as designated nodes.
        This rule is **in addition to** the :class:`FDE DesignationClosure rule
        <logics.fde.TableauxRules.DesignationClosure>`
        """

        # tracker implementation

        def check_for_target(self, node, branch):
            """
            Tracker implementation. See :class:`<logic.TableauxSystem.NodeTargetCheckHelper>`

            :meta private:
            """
            nnode = self.__find_closing_node(node, branch)
            if nnode:
               return {'nodes': set([node, nnode]), 'type': 'Nodes'}

        # rule implementation

        def node_will_close_branch(self, node, branch):
            if self.__find_closing_node(node, branch):
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

        def __find_closing_node(self, node, branch):
            if node.has('sentence', 'designated') and node.props['designated']:
                return branch.find({
                    'sentence'   : negative(node.props['sentence']),
                    'designated' : True,
                })

    class DesignationClosure(fde.TableauxRules.DesignationClosure):
        pass

    class DoubleNegationDesignated(fde.TableauxRules.DoubleNegationDesignated):
        """
        *This rule is the same as* :class:`FDE DoubleNegationDesignated
        <logics.fde.TableauxRules.DoubleNegationDesignated>`

        //ruledoc//fde//DoubleNegationDesignated//
        """
        pass

    class DoubleNegationUndesignated(fde.TableauxRules.DoubleNegationUndesignated):
        """
        *This rule is the same as* :class:`FDE DoubleNegationUndesignated
        <logics.fde.TableauxRules.DoubleNegationUndesignated>`

        //ruledoc//fde//DoubleNegationUndesignated//
        """
        pass

    class AssertionDesignated(fde.TableauxRules.AssertionDesignated):
        """
        *This rule is the same as* :class:`FDE AssertionDesignated
        <logics.fde.TableauxRules.AssertionDesignated>`

        //ruledoc//fde//AssertionDesignated//
        """
        pass

    class AssertionNegatedDesignated(fde.TableauxRules.AssertionNegatedDesignated):
        """
        *This rule is the same as* :class:`FDE AssertionNegatedDesignated
        <logics.fde.TableauxRules.AssertionNegatedDesignated>`

        //ruledoc//fde//AssertionNegatedDesignated//
        """
        pass

    class AssertionUndesignated(fde.TableauxRules.AssertionUndesignated):
        """
        *This rule is the same as* :class:`FDE AssertionUndesignated
        <logics.fde.TableauxRules.AssertionUndesignated>`

        //ruledoc//fde//AssertionUndesignated//
        """
        pass

    class AssertionNegatedUndesignated(fde.TableauxRules.AssertionNegatedUndesignated):
        """
        *This rule is the same as* :class:`FDE AssertionNegatedUndesignated
        <logics.fde.TableauxRules.AssertionNegatedUndesignated>`

        //ruledoc//fde//AssertionNegatedUndesignated//
        """
        pass

    class ConjunctionDesignated(fde.TableauxRules.ConjunctionDesignated):
        """
        *This rule is the same as* :class:`FDE ConjunctionDesignated
        <logics.fde.TableauxRules.ConjunctionDesignated>`

        //ruledoc//fde//ConjunctionDesignated//
        """
        pass

    class ConjunctionNegatedDesignated(fde.TableauxRules.ConjunctionNegatedDesignated):
        """
        *This rule is the same as* :class:`FDE ConjunctionNegatedDesignated
        <logics.fde.TableauxRules.ConjunctionNegatedDesignated>`

        //ruledoc//fde//ConjunctionNegatedDesignated//
        """
        pass

    class ConjunctionUndesignated(fde.TableauxRules.ConjunctionUndesignated):
        """
        *This rule is the same as* :class:`FDE ConjunctionUndesignated
        <logics.fde.TableauxRules.ConjunctionUndesignated>`

        //ruledoc//fde//ConjunctionUndesignated//
        """
        pass

    class ConjunctionNegatedUndesignated(fde.TableauxRules.ConjunctionNegatedUndesignated):
        """
        *This rule is the same as* :class:`FDE ConjunctionNegatedUndesignated
        <logics.fde.TableauxRules.ConjunctionNegatedUndesignated>`

        //ruledoc//fde//ConjunctionNegatedUndesignated//
        """
        pass

    class DisjunctionDesignated(fde.TableauxRules.DisjunctionDesignated):
        """
        *This rule is the same as* :class:`FDE DisjunctionDesignated
        <logics.fde.TableauxRules.DisjunctionDesignated>`

        //ruledoc//fde//DisjunctionDesignated//
        """
        pass

    class DisjunctionNegatedDesignated(fde.TableauxRules.DisjunctionNegatedDesignated):
        """
        *This rule is the same as* :class:`FDE DisjunctionNegatedDesignated
        <logics.fde.TableauxRules.DisjunctionNegatedDesignated>`

        //ruledoc//fde//DisjunctionNegatedDesignated//
        """
        pass

    class DisjunctionUndesignated(fde.TableauxRules.DisjunctionUndesignated):
        """
        *This rule is the same as* :class:`FDE DisjunctionUndesignated
        <logics.fde.TableauxRules.DisjunctionUndesignated>`

        //ruledoc//fde//DisjunctionUndesignated//
        """
        pass

    class DisjunctionNegatedUndesignated(fde.TableauxRules.DisjunctionNegatedUndesignated):
        """
        *This rule is the same as* :class:`FDE DisjunctionNegatedUndesignated
        <logics.fde.TableauxRules.DisjunctionNegatedUndesignated>`

        //ruledoc//fde//DisjunctionNegatedUndesignated//
        """
        pass

    class MaterialConditionalDesignated(fde.TableauxRules.MaterialConditionalDesignated):
        """
        *This rule is the same as* :class:`FDE MaterialConditionalDesignated
        <logics.fde.TableauxRules.MaterialConditionalDesignated>`

        //ruledoc//fde//MaterialConditionalDesignated//
        """
        pass

    class MaterialConditionalNegatedDesignated(fde.TableauxRules.MaterialConditionalNegatedDesignated):
        """
        *This rule is the same as* :class:`FDE MaterialConditionalNegatedDesignated
        <logics.fde.TableauxRules.MaterialConditionalNegatedDesignated>`

        //ruledoc//fde//MaterialConditionalNegatedDesignated//
        """
        pass

    class MaterialConditionalUndesignated(fde.TableauxRules.MaterialConditionalUndesignated):
        """
        *This rule is the same as* :class:`FDE MaterialConditionalUndesignated
        <logics.fde.TableauxRules.MaterialConditionalUndesignated>`

        //ruledoc//fde//MaterialConditionalUndesignated//
        """
        pass

    class MaterialConditionalNegatedUndesignated(fde.TableauxRules.MaterialConditionalNegatedUndesignated):
        """
        *This rule is the same as* :class:`FDE MaterialConditionalNegatedUndesignated
        <logics.fde.TableauxRules.MaterialConditionalNegatedUndesignated>`

        //ruledoc//fde//MaterialConditionalNegatedUndesignated//
        """
        pass

    class MaterialBiconditionalDesignated(fde.TableauxRules.MaterialBiconditionalDesignated):
        """
        *This rule is the same as* :class:`FDE MaterialBiconditionalDesignated
        <logics.fde.TableauxRules.MaterialBiconditionalDesignated>`

        //ruledoc//fde//MaterialBiconditionalDesignated//
        """
        pass

    class MaterialBiconditionalNegatedDesignated(fde.TableauxRules.MaterialBiconditionalNegatedDesignated):
        """
        *This rule is the same as* :class:`FDE MaterialBiconditionalNegatedDesignated
        <logics.fde.TableauxRules.MaterialBiconditionalNegatedDesignated>`

        //ruledoc//fde//MaterialBiconditionalNegatedDesignated//
        """
        pass

    class MaterialBiconditionalUndesignated(fde.TableauxRules.MaterialBiconditionalUndesignated):
        """
        *This rule is the same as* :class:`FDE MaterialBiconditionalUndesignated
        <logics.fde.TableauxRules.MaterialBiconditionalUndesignated>`

        //ruledoc//fde//MaterialBiconditionalUndesignated//
        """
        pass

    class MaterialBiconditionalNegatedUndesignated(fde.TableauxRules.MaterialBiconditionalNegatedUndesignated):
        """
        *This rule is the same as* :class:`FDE MaterialBiconditionalNegatedUndesignated
        <logics.fde.TableauxRules.MaterialBiconditionalNegatedUndesignated>`

        //ruledoc//fde//MaterialBiconditionalNegatedUndesignated//
        """
        pass

    class ConditionalDesignated(fde.TableauxRules.ConditionalDesignated):
        """
        *This rule is the same as* :class:`FDE ConditionalDesignated
        <logics.fde.TableauxRules.ConditionalDesignated>`

        //ruledoc//fde//ConditionalDesignated//
        """
        pass

    class ConditionalNegatedDesignated(fde.TableauxRules.ConditionalNegatedDesignated):
        """
        *This rule is the same as* :class:`FDE ConditionalNegatedDesignated
        <logics.fde.TableauxRules.ConditionalNegatedDesignated>`

        //ruledoc//fde//ConditionalNegatedDesignated//
        """
        pass

    class ConditionalUndesignated(fde.TableauxRules.ConditionalUndesignated):
        """
        *This rule is the same as* :class:`FDE ConditionalUndesignated
        <logics.fde.TableauxRules.ConditionalUndesignated>`

        //ruledoc//fde//ConditionalUndesignated//
        """
        pass

    class ConditionalNegatedUndesignated(fde.TableauxRules.ConditionalNegatedUndesignated):
        """
        *This rule is the same as* :class:`FDE ConditionalNegatedUndesignated
        <logics.fde.TableauxRules.ConditionalNegatedUndesignated>`

        //ruledoc//fde//ConditionalNegatedUndesignated//
        """
        pass
        
    class BiconditionalDesignated(fde.TableauxRules.BiconditionalDesignated):
        """
        *This rule is the same as* :class:`FDE BiconditionalDesignated
        <logics.fde.TableauxRules.BiconditionalDesignated>`

        //ruledoc//fde//BiconditionalDesignated//
        """
        pass

    class BiconditionalNegatedDesignated(fde.TableauxRules.BiconditionalNegatedDesignated):
        """
        *This rule is the same as* :class:`FDE BiconditionalNegatedDesignated
        <logics.fde.TableauxRules.BiconditionalNegatedDesignated>`

        //ruledoc//fde//BiconditionalNegatedDesignated//
        """
        pass

    class BiconditionalUndesignated(fde.TableauxRules.BiconditionalUndesignated):
        """
        *This rule is the same as* :class:`FDE BiconditionalUndesignated
        <logics.fde.TableauxRules.BiconditionalUndesignated>`

        //ruledoc//fde//BiconditionalUndesignated//
        """
        pass

    class BiconditionalNegatedUndesignated(fde.TableauxRules.BiconditionalNegatedUndesignated):
        """
        *This rule is the same as* :class:`FDE BiconditionalNegatedUndesignated
        <logics.fde.TableauxRules.BiconditionalNegatedUndesignated>`

        //ruledoc//fde//BiconditionalNegatedUndesignated//
        """
        pass

    class ExistentialDesignated(fde.TableauxRules.ExistentialDesignated):
        """
        *This rule is the same as* :class:`FDE ExistentialDesignated
        <logics.fde.TableauxRules.ExistentialDesignated>`

        //ruledoc//fde//ExistentialDesignated//
        """
        pass

    class ExistentialNegatedDesignated(fde.TableauxRules.ExistentialNegatedDesignated):
        """
        *This rule is the same as* :class:`FDE ExistentialNegatedDesignated
        <logics.fde.TableauxRules.ExistentialNegatedDesignated>`

        //ruledoc//fde//ExistentialNegatedDesignated//
        """
        pass

    class ExistentialUndesignated(fde.TableauxRules.ExistentialUndesignated):
        """
        *This rule is the same as* :class:`FDE ExistentialUndesignated
        <logics.fde.TableauxRules.ExistentialUndesignated>`

        //ruledoc//fde//ExistentialUndesignated//
        """
        pass

    class ExistentialNegatedUndesignated(fde.TableauxRules.ExistentialNegatedUndesignated):
        """
        *This rule is the same as* :class:`FDE ExistentialNegatedUndesignated
        <logics.fde.TableauxRules.ExistentialNegatedUndesignated>`

        //ruledoc//fde//ExistentialNegatedUndesignated//
        """
        pass

    class UniversalDesignated(fde.TableauxRules.UniversalDesignated):
        """
        *This rule is the same as* :class:`FDE UniversalDesignated
        <logics.fde.TableauxRules.UniversalDesignated>`

        //ruledoc//fde//UniversalDesignated//
        """
        pass

    class UniversalNegatedDesignated(fde.TableauxRules.UniversalNegatedDesignated):
        """
        *This rule is the same as* :class:`FDE UniversalNegatedDesignated
        <logics.fde.TableauxRules.UniversalNegatedDesignated>`

        //ruledoc//fde//UniversalNegatedDesignated//
        """
        pass

    class UniversalUndesignated(fde.TableauxRules.UniversalUndesignated):
        """
        *This rule is the same as* :class:`FDE UniversalUndesignated
        <logics.fde.TableauxRules.UniversalUndesignated>`

        //ruledoc//fde//UniversalUndesignated//
        """
        pass

    class UniversalNegatedUndesignated(fde.TableauxRules.UniversalNegatedUndesignated):
        """
        *This rule is the same as* :class:`FDE UniversalNegatedUndesignated
        <logics.fde.TableauxRules.UniversalNegatedUndesignated>`

        //ruledoc//fde//UniversalNegatedUndesignated//
        """
        pass

    closure_rules = [
        DesignationClosure,
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