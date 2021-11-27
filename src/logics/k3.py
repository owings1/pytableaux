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
from proof.common import Branch, Node
from proof.rules import ClosureRule
from . import fde as FDE

class Model(FDE.Model):
    """
    A K3 model is like an :ref:`FDE model <fde-model>` without the :m:`B` value.
    """

    truth_values_list = ('F', 'N', 'T')
    #: The set of admissible values for sentences in a model.
    #:
    #: :type: set
    #: :value: {T, N, F}
    #: :meta hide-value:
    truth_values = frozenset(truth_values_list)

    #: The (singleton) set of designated values in model.
    #:
    #: :type: set
    #: :value: {T}
    #: :meta hide-value:
    designated_values = frozenset(('T',))

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

class TableauxSystem(FDE.TableauxSystem):
    """
    K3's Tableaux System inherits directly from the :ref:`FDE system <fde-system>`,
    employing designation markers, and building the trunk in the same way.
    """
    pass
        
class TabRules(object):
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

        def check_for_target(self, node: Node, branch: Branch):
            """
            Tracker implementation. See :class:`<proof.helpers.NodeTargetCheckHelper>`

            :meta private:
            """
            nnode = self.__find_closing_node(node, branch)
            if nnode:
               return {'nodes': {node, nnode}}

        # rule implementation

        def node_will_close_branch(self, node: Node, branch: Branch) -> bool:
            if self.__find_closing_node(node, branch):
                return True
            return False

        def applies_to_branch(self, branch: Branch) -> bool:
            return self.ntch.cached_target(branch)

        def example_nodes(self):
            a = Atomic.first()
            return (
                {'sentence': a         , 'designated': True},
                {'sentence': a.negate(), 'designated': True},
            )

        # private util

        def __find_closing_node(self, node: Node, branch: Branch):
            if node.has('sentence', 'designated') and node['designated']:
                return branch.find({
                    'sentence'   : node['sentence'].negative(),
                    'designated' : True,
                })

    class DesignationClosure(FDE.TabRules.DesignationClosure):
        pass

    class DoubleNegationDesignated(FDE.TabRules.DoubleNegationDesignated):
        pass

    class DoubleNegationUndesignated(FDE.TabRules.DoubleNegationUndesignated):
        pass

    class AssertionDesignated(FDE.TabRules.AssertionDesignated):
        pass

    class AssertionNegatedDesignated(FDE.TabRules.AssertionNegatedDesignated):
        pass

    class AssertionUndesignated(FDE.TabRules.AssertionUndesignated):
        pass

    class AssertionNegatedUndesignated(FDE.TabRules.AssertionNegatedUndesignated):
        pass

    class ConjunctionDesignated(FDE.TabRules.ConjunctionDesignated):
        pass

    class ConjunctionNegatedDesignated(FDE.TabRules.ConjunctionNegatedDesignated):
        pass

    class ConjunctionUndesignated(FDE.TabRules.ConjunctionUndesignated):
        pass

    class ConjunctionNegatedUndesignated(FDE.TabRules.ConjunctionNegatedUndesignated):
        pass

    class DisjunctionDesignated(FDE.TabRules.DisjunctionDesignated):
        pass

    class DisjunctionNegatedDesignated(FDE.TabRules.DisjunctionNegatedDesignated):
        pass

    class DisjunctionUndesignated(FDE.TabRules.DisjunctionUndesignated):
        pass

    class DisjunctionNegatedUndesignated(FDE.TabRules.DisjunctionNegatedUndesignated):
        pass

    class MaterialConditionalDesignated(FDE.TabRules.MaterialConditionalDesignated):
        pass

    class MaterialConditionalNegatedDesignated(FDE.TabRules.MaterialConditionalNegatedDesignated):
        pass

    class MaterialConditionalUndesignated(FDE.TabRules.MaterialConditionalUndesignated):
        pass

    class MaterialConditionalNegatedUndesignated(FDE.TabRules.MaterialConditionalNegatedUndesignated):
        pass

    class MaterialBiconditionalDesignated(FDE.TabRules.MaterialBiconditionalDesignated):
        pass

    class MaterialBiconditionalNegatedDesignated(FDE.TabRules.MaterialBiconditionalNegatedDesignated):
        pass

    class MaterialBiconditionalUndesignated(FDE.TabRules.MaterialBiconditionalUndesignated):
        pass

    class MaterialBiconditionalNegatedUndesignated(FDE.TabRules.MaterialBiconditionalNegatedUndesignated):
        pass

    class ConditionalDesignated(FDE.TabRules.ConditionalDesignated):
        pass

    class ConditionalNegatedDesignated(FDE.TabRules.ConditionalNegatedDesignated):
        pass

    class ConditionalUndesignated(FDE.TabRules.ConditionalUndesignated):
        pass

    class ConditionalNegatedUndesignated(FDE.TabRules.ConditionalNegatedUndesignated):
        pass
        
    class BiconditionalDesignated(FDE.TabRules.BiconditionalDesignated):
        pass

    class BiconditionalNegatedDesignated(FDE.TabRules.BiconditionalNegatedDesignated):
        pass

    class BiconditionalUndesignated(FDE.TabRules.BiconditionalUndesignated):
        pass

    class BiconditionalNegatedUndesignated(FDE.TabRules.BiconditionalNegatedUndesignated):
        pass

    class ExistentialDesignated(FDE.TabRules.ExistentialDesignated):
        pass

    class ExistentialNegatedDesignated(FDE.TabRules.ExistentialNegatedDesignated):
        pass

    class ExistentialUndesignated(FDE.TabRules.ExistentialUndesignated):
        pass

    class ExistentialNegatedUndesignated(FDE.TabRules.ExistentialNegatedUndesignated):
        pass

    class UniversalDesignated(FDE.TabRules.UniversalDesignated):
        pass

    class UniversalNegatedDesignated(FDE.TabRules.UniversalNegatedDesignated):
        pass

    class UniversalUndesignated(FDE.TabRules.UniversalUndesignated):
        pass

    class UniversalNegatedUndesignated(FDE.TabRules.UniversalNegatedUndesignated):
        pass

    closure_rules = (
        DesignationClosure,
        GlutClosure,
    )

    rule_groups = (
        (
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
        ),
        (
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
        ),
        (
            ExistentialDesignated,
            ExistentialUndesignated,
        ),
        (
            UniversalDesignated,
            UniversalUndesignated,
        ),
    )
TableauxRules = TabRules