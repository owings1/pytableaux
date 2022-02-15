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
# pytableaux - Logic of Paradox
name = 'LP'

class Meta:
    title = 'Logic of Paradox'
    category = 'Many-valued'
    description = 'Three-valued logic (T, F, B)'
    tags = ('many-valued', 'glutty', 'non-modal', 'first-order')
    category_display_order = 100

from lexicals import Atomic
from proof.baserules import BaseClosureRule
from proof.common import Branch, Node, Target
# from proof.helpers import NodeTarget
from tools.hybrids import qsetf
from . import fde as FDE
from logics.fde import sdnode, group

class Model(FDE.Model):
    """
    An LP model is like an :ref:`FDE model <fde-model>` without the :m:`N` value,
    which yields an exhaustion restraint an predicate's extension/anti-extension.
    """
    #: The admissible values
    truth_values = FDE.Model.truth_values - {'N'}
    unassigned_value = 'F'
    nvals = {k: v for k,v in FDE.Model.nvals.items() if k != 'N'}
    cvals = {k: v for k,v in FDE.Model.cvals.items() if v != 'N'}

class TableauxSystem(FDE.TableauxSystem):
    """
    LP's Tableaux System inherits directly from the :ref:`FDE system <fde-system>`,
    employing designation markers, and building the trunk in the same way.
    """

class TabRules:
    """
    The Tableaux System for LP contains all the rules from :ref:`FDE <FDE>`, as
    well as an additional closure rule.
    """

    class GapClosure(BaseClosureRule):
        """
        A branch closes when a sentence and its negation both appear as undesignated nodes.
        This rule is **in addition to** the :m:`FDE` ``DesignationClosure`` rule.
        """

        def _branch_target_hook(self, node: Node, branch: Branch):
            nnode = self._find_closing_node(node, branch)
            if nnode:
                return Target(
                    nodes = qsetf((node, nnode)),
                    branch = branch,
                )

        def node_will_close_branch(self, node: Node, branch: Branch):
            return bool(self._find_closing_node(node, branch))

        @staticmethod
        def example_nodes():
            s = Atomic.first()
            return sdnode(s, False), sdnode(~s, False)

        # private util

        def _find_closing_node(self, node: Node, branch: Branch):
            if node.get('designated') is False:
                s = self.sentence(node)
                if s is not None:
                    return branch.find(dict(
                        sentence = s.negative(),
                        designated = False,
                    ))

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
        GapClosure,
        DesignationClosure,
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
