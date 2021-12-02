
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
# pytableaux - tableaux rules module
from lexicals import Atomic, Quantified, Operated
from .common import Branch, Node, Target
from .tableaux import Rule
from .helpers import NodeTargetCheckHelper

class ClosureRule(Rule):
    """
    A closure rule has a fixed ``apply()`` method that marks the branch as
    closed. Sub-classes should implement the ``applies_to_branch()`` method.
    """

    Helpers = (NodeTargetCheckHelper,)
    ntch: NodeTargetCheckHelper

    opts = {'is_rank_optim': False}

    @property
    def is_closure(self):
        return True

    def _get_targets(self, branch: Branch):
        """
        :implements: Rule
        """
        target = self.applies_to_branch(branch)
        if target:
            return (Target.create(target, branch = branch),)

    def _apply(self, target: Target):
        """
        :implements: Rule
        """
        target.branch.close()

    def applies_to_branch(self, branch: Branch):
        """
        :meta abstract:
        """
        raise NotImplementedError()

    def nodes_will_close_branch(self, nodes, branch):
        """
        Used in AdzHelper for calculating a target's closure score. This default
        implementation delegates to the abstract ``node_will_close_branch()``.

        :param iterable(Node) nodes:
        :param tableaux.Branch branch:
        :rtype: bool
        """
        for node in nodes:
            if self.node_will_close_branch(node, branch):
                return True

    def node_will_close_branch(self, node, branch):
        raise NotImplementedError()

    # NodeTargetCheckHelper implementation

    def check_for_target(self, node, branch):
        raise NotImplementedError()
