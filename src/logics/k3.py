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

from lexicals import Atomic
from proof.rules import ClosureRule
from . import fde

class Model(fde.Model):
    """
    A K3 model is like an :ref:`FDE model <fde-model>` without the :m:`B` value.
    """

    #: The set of admissible values for sentences in a model.
    #:
    #: :type: set
    #: :value: {T, N, F}
    #: :meta hide-value:
    truth_values = set(['F', 'N', 'T'])

    #: The (singleton) set of designated values in model.
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
    K3's Tableaux System inherits directly from the :ref:`FDE system <fde-system>`,
    employing designation markers, and building the trunk in the same way.
    """
    pass
        
class TableauxRules(object):
    """
    The Tableaux System for K3 contains all the rules from :ref:`FDE <fde-rules>`, as well
    as an additional closure rule.
    """

    class GlutClosure(ClosureRule):
        """
        A branch closes when a sentence and its negation both appear as designated nodes.
        This rule is **in addition to** the :class:`FDE DesignationClosure rule
        <DesignationClosure>`
        """

        # tracker implementation

        def check_for_target(self, node, branch):
            """
            Tracker implementation. See :class:`<rules.helpers.NodeTargetCheckHelper>`

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
            a = Atomic(0, 0)
            return [
                {'sentence': a         , 'designated': True},
                {'sentence': a.negate(), 'designated': True},
            ]

        # private util

        def __find_closing_node(self, node, branch):
            if node.has('sentence', 'designated') and node.props['designated']:
                return branch.find({
                    'sentence'   : node.props['sentence'].negative(),
                    'designated' : True,
                })

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

    class ConditionalDesignated(fde.TableauxRules.ConditionalDesignated):
        pass

    class ConditionalNegatedDesignated(fde.TableauxRules.ConditionalNegatedDesignated):
        pass

    class ConditionalUndesignated(fde.TableauxRules.ConditionalUndesignated):
        pass

    class ConditionalNegatedUndesignated(fde.TableauxRules.ConditionalNegatedUndesignated):
        pass
        
    class BiconditionalDesignated(fde.TableauxRules.BiconditionalDesignated):
        pass

    class BiconditionalNegatedDesignated(fde.TableauxRules.BiconditionalNegatedDesignated):
        pass

    class BiconditionalUndesignated(fde.TableauxRules.BiconditionalUndesignated):
        pass

    class BiconditionalNegatedUndesignated(fde.TableauxRules.BiconditionalNegatedUndesignated):
        pass

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