# -*- coding: utf-8 -*-
# pytableaux, a multi-logic proof generator.
# Copyright (C) 2014-2023 Doug Owings.
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
from __future__ import annotations as annotations

from ..models import BaseModel, ValueLP
from ..proof import Branch, Node, Target, sdnode
from ..proof.rules import BaseClosureRule
from ..tools import qsetf, group
from . import fde as FDE

name = 'LP'

class Meta(FDE.Meta):
    title = 'Logic of Paradox'
    description = 'Three-valued logic (T, F, B)'
    category_order = 100
    tags = (
        'many-valued',
        'glutty',
        'non-modal',
        'first-order')

class Model(FDE.Model, BaseModel[ValueLP]):
    Value = ValueLP
    designated_values = frozenset({Value.B, Value.T})
    unassigned_value = Value.F

class TableauxSystem(FDE.TableauxSystem):
    pass

@TableauxSystem.initialize
class TabRules(FDE.TabRules):

    class GapClosure(BaseClosureRule):
        """
        A branch closes when a sentence and its negation both appear as undesignated nodes.
        """

        def _branch_target_hook(self, node: Node, branch: Branch, /):
            nnode = self._find_closing_node(node, branch)
            if nnode is not None:
                return Target(
                    nodes = qsetf((node, nnode)),
                    branch = branch)

        def node_will_close_branch(self, node: Node, branch: Branch, /) -> bool:
            return bool(self._find_closing_node(node, branch))

        def _find_closing_node(self, node: Node, branch: Branch, /):
            if node.get('designated') is False:
                s = self.sentence(node)
                if s is not None:
                    return branch.find(sdnode(s.negative(), False))

        @staticmethod
        def example_nodes():
            from ..lang import Atomic
            s = Atomic.first()
            return sdnode(s, False), sdnode(~s, False)

    closure_rules = group(GapClosure) + FDE.TabRules.closure_rules
