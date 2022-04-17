# pytableaux, a multi-logic proof generator.
# Copyright (C) 2014-2022 Doug Owings.
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
from __future__ import annotations

name = 'K3'

class Meta:
    title       = 'Strong Kleene 3-valued logic'
    category    = 'Many-valued'
    description = 'Three-valued logic (T, F, N)'
    category_order = 20
    tags = (
        'many-valued',
        'gappy',
        'non-modal',
        'first-order',
    )

from pytableaux.logics import fde as FDE
from pytableaux.models import Mval
from pytableaux.proof.baserules import BaseClosureRule
from pytableaux.proof.common import Branch, Node, Target
from pytableaux.tools.hybrids import qsetf
from pytableaux.tools.sets import setf

class Model(FDE.Model):
    """A L{K3} model is like an {@FDE model} without the V{B} value."""

    class Value(Mval):
        'The admissible values for sentences.'
        F = 'False',   0.0
        N = 'Neither', 0.5
        T = 'True',    1.0

    #: The (singleton) set of designated values in model.
    #:
    #: :type: set
    designated_values = setf({Value.T})

    unassigned_value = Value.N

class TableauxSystem(FDE.TableauxSystem):
    """
    L{K3}'s Tableaux System inherits directly from the {@FDE system},
    employing designation markers, and building the trunk in the same way.
    """
    pass
        
class TabRules:
    """
    The rules for L{K3} comprise all the {@FDE rules}, plus an additional
    closure rule.
    """

    class GlutClosure(BaseClosureRule):
        """A branch closes when a sentence and its negation both appear as
        designated nodes on the branch.
        """

        def _branch_target_hook(self, node: Node, branch: Branch, /):
            nnode = self._find_closing_node(node, branch)
            if nnode is not None:
               return Target(
                   nodes = qsetf((node, nnode)),
                   branch = branch,
                )

        def node_will_close_branch(self, node: Node, branch: Branch, /) -> bool:
            return bool(self._find_closing_node(node, branch))

        def _find_closing_node(self, node: Node, branch: Branch, /):
            if node.get('designated'):
                s = self.sentence(node)
                if s is not None:
                    return branch.find(dict(
                        sentence = s.negative(),
                        designated = True,
                    ))

        @staticmethod
        def example_nodes():
            from pytableaux.lexicals import Atomic
            from pytableaux.logics.fde import sdnode
            a = Atomic.first()
            return sdnode(a, True), sdnode(~a, True)

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
