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

from ..lang import Atomic
from ..models import ValueLP
from ..proof import rules, sdwnode
from ..tools import group
from . import LogicType
from . import fde as FDE


class Meta(FDE.Meta):
    name = 'LP'
    title = 'Logic of Paradox'
    values = ValueLP
    designated_values = frozenset({values.B, values.T})
    unassigned_value = values.F
    description = 'Three-valued logic (T, F, B)'
    category_order = 100
    extension_of = ('FDE')

class Model(FDE.Model): pass

class System(FDE.System): pass

class Rules(LogicType.Rules):

    class GapClosure(rules.FindClosingNodeRule):
        """
        A branch closes when a sentence and its negation both appear as undesignated nodes.
        """

        def _find_closing_node(self, node, branch, /):
            if node['designated'] is False:
                return branch.find(sdwnode(-self.sentence(node), False, node.get('world')))

        def example_nodes(self):
            s = Atomic.first()
            w = 0 if self.modal else None
            yield sdwnode(s, False, w)
            yield sdwnode(~s, False, w)

    closure = group(GapClosure) + FDE.Rules.closure
    groups = FDE.Rules.groups
