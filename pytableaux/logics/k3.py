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

from typing import TYPE_CHECKING

from ..lang import Atomic
from ..models import ValueK3
from ..proof import rules, sdwnode
from . import LogicType
from . import fde as FDE


class Meta(FDE.Meta):
    name = 'K3'
    title = 'Strong Kleene Logic'
    values: type[ValueK3] = ValueK3
    designated_values = 'T'
    description = 'Three-valued logic (T, F, N)'
    category_order = 2
    extension_of = ('FDE')

class Model(LogicType.Model[Meta.values]):
    if TYPE_CHECKING:
        class TruthFunction(LogicType.Model.TruthFunction[Meta.values]): pass

class System(FDE.System): pass

class Rules(FDE.Rules):

    class GlutClosure(rules.FindClosingNodeRule):
        """A branch closes when a sentence and its negation both appear as
        designated nodes on the branch.
        """

        def _find_closing_node(self, node, branch, /):
            if node['designated']:
                return branch.find(sdwnode(-node['sentence'], True, node.get('world')))

        def example_nodes(self):
            a = Atomic.first()
            w = 0 if self.modal else None
            yield sdwnode(a, True, w)
            yield sdwnode(~a, True, w)

    closure = (GlutClosure, *FDE.Rules.closure)
