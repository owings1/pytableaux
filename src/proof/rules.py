
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

class FilterNodeRule(PotentialNodeRule):
    """
    A ``FilterNodeRule`` filters potential nodes by matching the attribute
    conditions of the implementing class.

    The following attribute conditions can be defined. If a condition is set to
    ``None``, then it will be vacuously met.
    """

    #: The ticked status of the node, default is ``False``.
    #:
    #: :type: bool
    ticked = False

    #: Whether this rule applies to modal nodes, i.e. nodes that
    #: reference one or more worlds.
    #:
    #: :type: bool
    modal = None

    #: The main operator of the node's sentence, if any.
    #:
    #: :type: str
    operator = None

    #: Whether the sentence must be negated. if ``True``, then nodes
    #: whose sentence's main connective is Negation will be checked,
    #: and if the negatum has the main connective defined in the
    #: ``operator`` condition (above), then this condition will be met.
    #:
    #: :type: bool
    negated = None

    #: The quantifier of the sentence, e.g. 'Universal' or 'Existential'.
    #:
    #: :type: str
    quantifier = None

    #: The designation status of the node.
    #:
    #: :type: bool
    designation = None

    #: The predicate name.
    #:
    #: :type: str
    predicate = None

    # Implementation

    def is_potential_node(self, node, branch):
        return self.conditions_apply(node, branch)

    def get_target_for_node(self, node, branch):
        # Default is to return ``True``, which gets converted into a
        # target along the way.
        return self.conditions_apply(node, branch)

    def conditions_apply(self, node, branch):
        if self.ticked != None and self.ticked != branch.is_ticked(node):
            return False
        if self.modal != None and self.modal != node.is_modal:
            # modal = len(node.worlds) > 0
            # if self.modal != modal:
                return False
        sentence = operator = quantifier = predicate = None
        if node.has('sentence'):
            sentence = node['sentence']
            operator = sentence.operator
            quantifier = sentence.quantifier
            predicate = sentence.predicate
        if self.negated != None:
            negated = operator == 'Negation'
            if not sentence or negated != self.negated:
                return False
            if negated:
                sentence = sentence.operand
                operator = sentence.operator
                quantifier = sentence.quantifier
                predicate = sentence.predicate
        if self.operator != None:
            if self.operator != operator:
                return False
        elif self.quantifier != None:
            if self.quantifier != quantifier:
                return False
        if self.designation != None:
            if node.get('designated') != self.designation:
                return False
        if self.predicate != None:
            if predicate == None or self.predicate not in predicate.refs:
                return False
        return True

    # Override

    def sentence(self, node):
        s = None
        if 'sentence' in node:
            s = node['sentence']
            if self.negated:
                s = s.operand
        return s

    # Default

    def example_nodes(self, branch = None):
        props = {}
        if self.modal:
            props['world'] = 0
        if self.designation != None:
            props['designated'] = self.designation
        sentence = None
        a = Atomic.first()
        if self.operator != None:
            params = []
            arity = self.operator.arity
            if arity > 0:
                params.append(a)
            for i in range(arity - 1):
                params.append(params[-1].next())
            sentence = Operated(self.operator, params)
        elif self.quantifier != None:
            sentence = Quantified.first(quantifier = self.quantifier)
        if self.negated:
            if sentence == None:
                sentence = a
            sentence = sentence.negate()
        if sentence != None:
            props['sentence'] = sentence
        return (props,)

class AllConstantsStoppingRule(FilterNodeRule):

    Helpers = (
        *FilterNodeRule.Helpers,
        ('max_constants'     , MaxConstantsTracker),
        ('applied_constants' , AppliedNodeConstants),
        ('apqf'      , AppliedQuitFlag),
    )

    Timers = (
        *FilterNodeRule.Timers,
        'in_get_targets_for_nodes',
        'in_node_examime',
        'in_should_apply',
    )

    def get_new_nodes_for_constant(self, c, node, branch):
        """
        Create the new nodes for the given constant, node, and branch, according
        to the implementation.

        :param lexicals.Constant c:
        :param tableaux.Node node:
        :param tableaux.Branch branch:
        :return: The list of nodes.
        :meta abstract:
        """
        raise NotImplementedError()

    def get_targets_for_node(self, node, branch):
        """
        Implements ``PotentialNodeRule``.
        """
        with self.timers['in_should_apply']:
            should_apply = self.__should_apply(node, branch)

        if not should_apply:
            if self.__should_flag(branch, node.get('world')):
                return [self.__get_flag_target(branch)]
            return

        with self.timers['in_get_targets_for_nodes']:

            with self.timers['in_node_examime']:
                constants = self.applied_constants.get_unapplied(node, branch)

            targets = []

            if constants:
                is_new = False
            else:
                is_new = True
                constants = {branch.new_constant()}

            for c in constants:
                new_nodes = self.get_new_nodes_for_constant(c, node, branch)
                if is_new or not branch.has_all(new_nodes):
                    targets.append({
                        'constant' : c,
                        'adds'     : [new_nodes],
                    })

        return targets

    def __should_apply(self, node, branch):
        if self.max_constants.max_constants_exceeded(branch, node.get('world')):
            return False
        # Apply if there are no constants on the branch
        if not branch.constants_count:
            return True
        # Apply if we have tracked a constant that we haven't applied to.
        if self.applied_constants.get_unapplied(node, branch):
            return True

    def __should_flag(self, branch, world):
        # Slight difference with FDE here -- using world
        return (
            self.max_constants.max_constants_exceeded(branch, world) and
            not self.apqf.get(branch)
        )

    def __get_flag_target(self, branch):
        return {
            'flag': True,
            'adds': [
                [
                    self.max_constants.quit_flag(branch),
                ],
            ],
        }

