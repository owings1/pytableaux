
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
from .helpers import AdzHelper, NodeTargetCheckHelper, AppliedNodeConstants, \
    MaxConstantsTracker, AppliedQuitFlag
from events import Events
from itertools import chain
from past.builtins import basestring
from typing import Generator, NamedTuple, final

class ClosureRule(Rule):
    """
    A closure rule has a fixed ``apply()`` method that marks the branch as
    closed. Sub-classes should implement the ``applies_to_branch()`` method.
    """

    Helpers = (NodeTargetCheckHelper,)

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

class PotentialNodeRule(Rule):
    """
    ``PotentialNodeRule`` intermediate class. Caches potential nodes as they appear,
    and tracks the number of applications to each node. Provides default
    implementation of some methods, and delegates to finer-grained abstract
    methods.
    """
    Helpers = (
        *Rule.Helpers,
        ('adz', AdzHelper),
    )
    ticked = False
    # For AdzHelper.
    ticking = None

    def __init__(self, *args, **opts):
        super().__init__(*args, **opts)
        self.__potential_nodes = dict()
        self.__node_applications = dict()
        self.tableau.on({
            Events.AFTER_BRANCH_ADD   : self.__after_branch_add,
            Events.AFTER_BRANCH_CLOSE : self.__after_branch_close,
            Events.AFTER_NODE_ADD     : self.__after_node_add,
            Events.AFTER_NODE_TICK    : self.__after_node_tick,
        })
        self.on(Events.AFTER_APPLY, self.__after_apply)

    # Implementation

    def _get_targets(self, branch: Branch):
        """
        :implements: Rule
        """
        # Implementations should be careful with overriding this method.
        cands = list()
        if branch.id in self.__potential_nodes:
            # Must copy to avoid concurrent modification.
            for node in set(self.__potential_nodes[branch.id]):
                targets = self.get_targets_for_node(node, branch)
                if targets:
                    cands.extend(
                        Target.create(target, branch = branch, node = node)
                        for target in targets
                    )
                else:
                    if not self.is_potential_node(node, branch):
                        self.__potential_nodes[branch.id].discard(node)
        return cands

    # Util

    def min_application_count(self, branch_id):
        if branch_id in self.__node_applications:
            if not len(self.__node_applications[branch_id]):
                return 0
            return min({
                self.node_application_count(node_id, branch_id)
                for node_id in self.__node_applications[branch_id]
            })
        return 0

    def node_application_count(self, node_id, branch_id):
        if branch_id in self.__node_applications:
            if node_id in self.__node_applications[branch_id]:
                return self.__node_applications[branch_id][node_id]
        return 0

    # Default

    def score_candidate(self, target: Target):
        score = super().score_candidate(target)
        if score == 0:
            complexity = self.tableau.branching_complexity(target['node'])
            score = -1 * complexity
        return score

    def _apply(self, target: Target):
        # Default implementation, to provide a more convenient
        # method signature.
        self.apply_to_node_target(target['node'], target['branch'], target)

    def get_targets_for_node(self, node, branch):
        # Default implementation, delegates to ``get_target_for_node``
        target = self.get_target_for_node(node, branch)
        if target:
            return [Target.create(target, branch = branch, node = node)]

    # Abstract

    def apply_to_node_target(self, node, branch, target):
        raise NotImplementedError()

    def get_target_for_node(self, node, branch):
        raise NotImplementedError()

    def is_potential_node(self, node, branch):
        raise NotImplementedError()

    # Events

    def __after_apply(self, target):
        self.__node_applications[target['branch'].id][target['node'].id] += 1

    def __after_branch_add(self, branch):
        parent = branch.parent
        if parent != None and parent.id in self.__potential_nodes:
            self.__potential_nodes[branch.id] = set(self.__potential_nodes[parent.id])
            self.__node_applications[branch.id] = dict(self.__node_applications[parent.id])
        else:
            self.__potential_nodes[branch.id] = set()
            self.__node_applications[branch.id] = dict()

    def __after_branch_close(self, branch):
        del(self.__potential_nodes[branch.id])
        del(self.__node_applications[branch.id])

    def __after_node_tick(self, node, branch):
        if self.ticked == False and branch.id in self.__potential_nodes:
            self.__potential_nodes[branch.id].discard(node)

    def __after_node_add(self, node, branch):
        if self.is_potential_node(node, branch):
            self.__potential_nodes[branch.id].add(node)
            self.__node_applications[branch.id][node.id] = 0
