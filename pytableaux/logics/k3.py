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
from __future__ import annotations

from ..lang import Atomic
from ..models import BaseModel, ValueK3
from ..proof import Branch, Node, Target, sdnode
from ..proof.rules import BaseClosureRule
from . import fde as FDE


class Meta(FDE.Meta):
    name = 'K3'
    title = 'Strong Kleene Logic'
    values = ValueK3
    designated_values = frozenset({values.T})
    unassigned_value = values.N
    description = 'Three-valued logic (T, F, N)'
    category_order = 20
    tags = (
        'many-valued',
        'gappy',
        'non-modal',
        'first-order')

class Model(FDE.Model, BaseModel[ValueK3]):
    Value = Meta.values
    designated_values = Meta.designated_values
    "The (singleton) set of designated values."
    unassigned_value = Meta.unassigned_value

class TableauxSystem(FDE.TableauxSystem):
    pass

@TableauxSystem.initialize
class TabRules(FDE.TabRules):

    class GlutClosure(BaseClosureRule):
        """A branch closes when a sentence and its negation both appear as
        designated nodes on the branch.
        """
    
        def _branch_target_hook(self, node: Node, branch: Branch, /):
            nnode = self._find_closing_node(node, branch)
            if nnode is not None:
               return Target(
                   nodes = (node, nnode),
                   branch = branch)

        def node_will_close_branch(self, node: Node, branch: Branch, /) -> bool:
            return bool(self._find_closing_node(node, branch))

        def _find_closing_node(self, node: Node, branch: Branch, /):
            if node[Node.Key.designated]:
                return branch.find(sdnode(self.sentence(node).negative(), True))

        @staticmethod
        def example_nodes():
            a = Atomic.first()
            yield sdnode(a, True)
            yield sdnode(~a, True)

    closure_rules = (GlutClosure,) + FDE.TabRules.closure_rules
