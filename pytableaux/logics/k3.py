# -*- coding: utf-8 -*-
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

import pytableaux.logics.fde as FDE
from pytableaux.models import BaseModel, ValueK3
from pytableaux.proof.common import Branch, Node, Target
from pytableaux.proof.rules import BaseClosureRule
from pytableaux.proof import sdnode
from pytableaux.tools.hybrids import qsetf
from pytableaux.tools.sets import setf

name = 'K3'

class Meta(FDE.Meta):
    title       = 'Strong Kleene Logic'
    category    = 'Many-valued'
    description = 'Three-valued logic (T, F, N)'
    category_order = 20
    tags = (
        'many-valued',
        'gappy',
        'non-modal',
        'first-order',
    )

class Model(FDE.Model, BaseModel[ValueK3]):
    """A L{K3} model is like an {@FDE model} without the V{B} value."""

    Value = ValueK3

    designated_values = setf({Value.T})
    "The (singleton) set of designated values."

    unassigned_value = Value.N

class TableauxSystem(FDE.TableauxSystem):
    """
    L{K3}'s Tableaux System inherits directly from the {@FDE system},
    employing designation markers, and building the trunk in the same way.
    """
    pass
        
@TableauxSystem.initialize
class TabRules(FDE.TabRules):
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
                    return branch.find(sdnode(s.negative(), True))

        @staticmethod
        def example_nodes():
            from pytableaux.lang.lex import Atomic
            a = Atomic.first()
            return sdnode(a, True), sdnode(~a, True)

    closure_rules = (
        FDE.TabRules.DesignationClosure,
        GlutClosure,
    )