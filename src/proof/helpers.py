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
# pytableaux - rule helpers module
from models import BaseModel

class AdzHelper(object):

    def __init__(self, rule):
        self.rule = rule

    def apply_to_target(self, target):
        branch = target['branch']
        for i in range(len(target['adds'])):
            if i == 0:
                continue
            b = self.rule.branch(branch)
            b.update(target['adds'][i])
            if self.rule.ticking:
                b.tick(target['node'])
        branch.update(target['adds'][0])
        if self.rule.ticking:
            branch.tick(target['node'])

    def closure_score(self, target):
        close_count = 0
        for nodes in target['adds']:
            nodes = [target['branch'].create_node(node) for node in nodes]
            for rule in self.rule.tableau.closure_rules:
                if rule.nodes_will_close_branch(nodes, target['branch']):
                    close_count += 1
                    break
        return float(close_count / min(1, len(target['adds'])))

class NodeTargetCheckHelper(object):
    """
    Calls the rule's ``check_for_target(node, branch)`` when a node is added to
    a branch. If a target is returned, it is cached relative to the branch. The
    rule can then call ``cached_target(branch)``  on the helper to retrieve the
    target. This is used primarily in closure rules for performance.

    NB: The rule must implement ``check_for_target(self, node, branch)``.
    """

    def __init__(self, rule):
        self.rule = rule
        self.targets = {}

    def cached_target(self, branch):
        """
        Return the cached target for the branch, if any.
        """
        if branch.id in self.targets:
            return self.targets[branch.id]

    # Helper Implementation

    def register_node(self, node, branch):
        target = self.rule.check_for_target(node, branch)
        if target:
            self.targets[branch.id] = target

class QuitFlagHelper(object):
    """
    Track the application of a flag node by the rule for each branch. A branch
    is considered flagged when the target has a non-empty ``flag`` property.
    """

    def __init__(self, rule):
        self.rule = rule
        self.flagged = {}

    def has_flagged(self, branch):
        """
        Whether the branch has been flagged.
        """
        if branch.id in self.flagged:
            return self.flagged[branch.id]
        return False

    # Helper implementation

    def register_branch(self, branch, parent):
        if parent != None and parent.id in self.flagged:
            self.flagged[branch.id] = self.flagged[parent.id]
        else:
            self.flagged[branch.id] = False

    def after_apply(self, target):
        if 'flag' in target and target['flag']:
            self.flagged[target['branch'].id] = True

class MaxConstantsTracker(object):
    """
    Project the maximum number of constants per world required for a branch
    by examining the branches after the trunk is built.
    """

    def __init__(self, rule):
        self.rule = rule
        #: Track the maximum number of constants that should be on the branch
        #: (per world) so we can halt on infinite branches. Map from ``branch.id```
        #: to ``int```.
        #: :type: dict({int: int})
        self.branch_max_constants = {}
        #: Track the constants at each world.
        #: :type: dict{int: set(Constant)}
        self.world_constants = {}

    def get_max_constants(self, branch):
        """
        Get the projected max number of constants (per world) for the branch.
        """
        origin = branch.origin()
        if origin.id in self.branch_max_constants:
            return self.branch_max_constants[origin.id]
        return 1

    def get_branch_constants_at_world(self, branch, world):
        """
        Get the cached set of constants at a world for the branch.

        :param Branch branch:
        :param int world:
        :rtype: bool
        """
        if world not in self.world_constants[branch.id]:
            self.world_constants[branch.id][world] = set()
        return self.world_constants[branch.id][world]

    def max_constants_reached(self, branch, world=0):
        """
        Whether we have already reached or exceeded the max number of constants
        projected for the branch (origin) at the given world.

        :param Branch branch:
        :param int world:
        :rtype: bool
        """
        if world == None:
            world = 0
        max_constants = self.get_max_constants(branch)
        world_constants = self.get_branch_constants_at_world(branch, world)
        return max_constants != None and len(world_constants) >= max_constants

    def max_constants_exceeded(self, branch, world=0):
        """
        Whether we have exceeded the max number of constants projected for
        the branch (origin) at the given world.

        :param Branch branch:
        :param int world:
        :rtype: bool
        """
        if world == None:
            world = 0
        max_constants = self.get_max_constants(branch)
        world_constants = self.get_branch_constants_at_world(branch, world)
        if max_constants != None and len(world_constants) > max_constants:
            return True

    def quit_flag(self, branch):
        """
        Generate a quit flag node for the branch. Return value is a ``dict`` with the
        following keys:

        - *is_flag*: ``True``
        - *flag*: ``'quit'``
        - *info*: ``'RuleName:MaxConstants({n})'`` where *RuleName* is ``rule.name``,
            and ``n`` is the computed max allowed constants for the branch.

        :param Branch branch:
        :rtype: dict
        """
        info = '{0}:MaxConstants({1})'.format(self.rule.name, str(self.get_max_constants(branch)))
        return {'is_flag': True, 'flag': 'quit', 'info': info}

    # Helper implementation

    def after_trunk_build(self, branches):
        for branch in branches:
            origin = branch.origin()
            # In most cases, we will have only one origin branch.
            if origin.id in self.branch_max_constants:
                return
            self.branch_max_constants[origin.id] = self._compute_max_constants(branch)

    def register_branch(self, branch, parent):
        if parent != None and parent.id in self.world_constants:
            self.world_constants[branch.id] = {
                world : set(self.world_constants[parent.id][world])
                for world in self.world_constants[parent.id]
            }
        else:
            self.world_constants[branch.id] = {}

    def register_node(self, node, branch):
        if node.has('sentence'):
            world = node.props['world']
            if world == None:
                world = 0
            if world not in self.world_constants[branch.id]:
                self.world_constants[branch.id][world] = set()
            self.world_constants[branch.id][world].update(node.constants())

    # Private util

    def _compute_max_constants(self, branch):
        """
        Project the maximum number of constants for a branch (origin) as
        the number of constants already on the branch (min 1) * the number of
        quantifiers (min 1) + 1.
        """
        node_needed_constants = sum([
            self._compute_needed_constants_for_node(node, branch)
            for node in branch.get_nodes()
        ])
        return max(1, len(branch.constants())) * max(1, node_needed_constants) + 1

    def _compute_needed_constants_for_node(self, node, branch):
        if node.has('sentence'):
            return len(node.props['sentence'].quantifiers())
        return 0

class NodeAppliedConstants(object):
    """
    Track the applied and unapplied constants per branch for each potential node.
    The rule's target should have `branch`, `node` and `constant` properties.

    Only nodes that are applicable according to the rule's ``is_potential_node()``
    method are tracked.
    """

    def __init__(self, rule):
        self.rule = rule
        self.node_states = {}
        self.consts = {}

    def get_applied(self, node, branch):
        """
        Return the set of constants that have been applied to the node for the
        branch.
        """
        return self.node_states[branch.id][node.id]['applied']

    def get_unapplied(self, node, branch):
        """
        Return the set of constants that have not been applied to the node for
        the branch.
        """
        return self.node_states[branch.id][node.id]['unapplied']

    # helper implementation

    def register_branch(self, branch, parent):
        if parent != None and parent.id in self.node_states:
            self.consts[branch.id] = set(self.consts[parent.id])
            self.node_states[branch.id] = {
                node_id : {
                    k : set(self.node_states[parent.id][node_id][k])
                    for k in self.node_states[parent.id][node_id]
                }
                for node_id in self.node_states[parent.id]
            }
        else:
            self.node_states[branch.id] = dict()
            self.consts[branch.id] = set()

    def register_node(self, node, branch):
        if self.__should_track_node(node, branch):
            if node.id not in self.node_states[branch.id]:
                # By tracking per node, we are tracking per world, a fortiori.
                self.node_states[branch.id][node.id] = {
                    'applied'   : set(),
                    'unapplied' : set(self.consts[branch.id]),
                }
        for c in node.constants():
            if c not in self.consts[branch.id]:
                for node_id in self.node_states[branch.id]:
                    self.node_states[branch.id][node_id]['unapplied'].add(c)
                self.consts[branch.id].add(c)

    def after_apply(self, target):
        if 'flag' in target and target['flag']:
            return
        idx = self.node_states[target['branch'].id][target['node'].id]
        c = target['constant']
        idx['applied'].add(c)
        idx['unapplied'].discard(c)

    # private util

    def __should_track_node(self, node, branch):
        return self.rule.is_potential_node(node, branch)

class MaxWorldsTracker(object):
    """
    Project the maximum number of worlds required for a branch by examining the
    branches after the trunk is built.
    """

    modal_operators = set(BaseModel.modal_operators)

    def __init__(self, rule):
        self.rule = rule
        # Track the maximum number of worlds that should be on the branch
        # so we can halt on infinite branches.
        self.branch_max_worlds = {}
        # Cache the modal complexities
        self.modal_complexities = {}

    def get_max_worlds(self, branch):
        """
        Get the maximum worlds projected for the branch.
        """
        origin = branch.origin()
        if origin.id in self.branch_max_worlds:
            return self.branch_max_worlds[origin.id]

    def max_worlds_reached(self, branch):
        """
        Whether we have already reached or exceeded the max number of worlds
        projected for the branch (origin).
        """
        max_worlds = self.get_max_worlds(branch)
        return max_worlds != None and len(branch.worlds()) >= max_worlds

    def max_worlds_exceeded(self, branch):
        """
        Whether we have exceeded the max number of worlds projected for the
        branch (origin).
        """
        max_worlds = self.get_max_worlds(branch)
        return max_worlds != None and len(branch.worlds()) > max_worlds

    def modal_complexity(self, sentence):
        """
        Compute and cache the modal complexity of a sentence by counting its
        modal operators.
        """
        if sentence not in self.modal_complexities:
            self.modal_complexities[sentence] = len([
                o for o in sentence.operators() if o in self.modal_operators
            ])
        return self.modal_complexities[sentence]

    def quit_flag(self, branch):
        """
        Generate a quit flag node for the branch.
        """
        info = '{0}:MaxWorlds({1})'.format(self.rule.name, str(self.get_max_worlds(branch)))
        return {'is_flag': True, 'flag': 'quit', 'info': info}

    # Helper implementation

    def after_trunk_build(self, branches):
        for branch in branches:
            origin = branch.origin()
            # In most cases, we will have only one origin branch.
            if origin.id in self.branch_max_worlds:
                return
            self.branch_max_worlds[origin.id] = self.__compute_max_worlds(branch)

    # Private util

    def __compute_max_worlds(self, branch):
        # Project the maximum number of worlds for a branch (origin) as
        # the number of worlds already on the branch + the number of modal
        # operators + 1.
        node_needed_worlds = sum([
            self.__compute_needed_worlds_for_node(node, branch)
            for node in branch.get_nodes()
        ])
        return len(branch.worlds()) + node_needed_worlds + 1

    def __compute_needed_worlds_for_node(self, node, branch):
        # we only care about unticked nodes, since ticked nodes will have
        # already created any worlds.
        if not branch.is_ticked(node) and node.has('sentence'):
            return self.modal_complexity(node.props['sentence'])
        return 0

class UnserialWorldsTracker(object):
    """
    Track the unserial worlds on the branch.
    """

    def __init__(self, rule):
        self.rule = rule
        self.unserial_worlds = {}

    def get_unserial_worlds(self, branch):
        """
        Get the set of unserial worlds on the branch.
        """
        return self.unserial_worlds[branch.id]

    # helper implementation

    def register_branch(self, branch, parent):
        if parent != None and parent.id in self.unserial_worlds:
            self.unserial_worlds[branch.id] = set(self.unserial_worlds[parent.id])
        else:
            self.unserial_worlds[branch.id] = set()

    def register_node(self, node, branch):
        for w in node.worlds():
            if branch.has({'world1': w}):
                self.unserial_worlds[branch.id].discard(w)
            else:
                self.unserial_worlds[branch.id].add(w)

class VisibleWorldsIndex(object):
    """
    Index the visible worlds for each world on the branch.
    """

    def __init__(self, rule):
        self.rule = rule
        self.index = {}

    def get_visibles(self, branch, world):
        """
        Get all the worlds on the branch that are visible to the given world.
        """
        if world in self.index[branch.id]:
            return self.index[branch.id][world]
        return set()

    def get_intransitives(self, branch, w1, w2):
        """
        Get all the worlds on the branch that are visible to w2, but are not
        visible to w1.
        """
        # TODO: can we make this more efficient? for each world pair,
        #       track the intransitives?
        return self.get_visibles(branch, w2).difference(self.get_visibles(branch, w1))

    # helper implementation

    def register_branch(self, branch, parent):
        if parent != None and parent.id in self.index:
            self.index[branch.id] = {
                w: set(self.index[parent.id][w])
                for w in self.index[parent.id]
            }
        else:
            self.index[branch.id] = {}

    def register_node(self, node, branch):
        if node.has('world1', 'world2'):
            w1 = node.props['world1']
            w2 = node.props['world2']
            if w1 not in self.index[branch.id]:
                self.index[branch.id][w1] = set()
            self.index[branch.id][w1].add(w2)

class PredicatedNodesTracker(object):
    """
    Track all predicated nodes on the branch.
    """

    def __init__(self, rule):
        self.rule = rule
        self.predicated_nodes = {}

    def get_predicated(self, branch):
        """
        Return all predicated nodes on the branch.
        """
        return self.predicated_nodes[branch.id]

    # helper implementation

    def register_branch(self, branch, parent):
        if parent != None and parent.id in self.predicated_nodes:
            self.predicated_nodes[branch.id] = set(self.predicated_nodes[parent.id])
        else:
            self.predicated_nodes[branch.id] = set()

    def register_node(self, node, branch):
        if node.has('sentence') and node.props['sentence'].is_predicated():
            self.predicated_nodes[branch.id].add(node)

class AppliedNodesWorldsTracker(object):
    """
    Track the nodes applied to by the rule for each world on the branch. The
    rule's target must have `branch`, `node`, and `world` keys.
    """

    def __init__(self, rule):
        self.rule = rule
        self.node_worlds_applied = {}

    def is_applied(self, node, world, branch):
        """
        Whether the rule has applied to the node for the world and branch.
        """
        return (node.id, world) in self.node_worlds_applied[branch.id]

    # helper implementation

    def register_node(self, node, branch):
        if branch.id not in self.node_worlds_applied:
            self.node_worlds_applied[branch.id] = set()

    def after_apply(self, target):
        if 'flag' in target and target['flag']:
            return
        pair = (target['node'].id, target['world'])
        self.node_worlds_applied[target['branch'].id].add(pair)

class AppliedSentenceCounter(object):
    """
    Count the times the rule has applied for a sentence per branch. This tracks
    the `sentence` property of the rule's target. The target should also include
    the `branch` key.
    """

    def __init__(self, rule):
        self.rule = rule
        self.counts = {}

    def get_count(self, sentence, branch):
        """
        Return the count for the given sentence and branch.
        """
        if sentence not in self.counts[branch.id]:
            return 0
        return self.counts[branch.id][sentence]

    # helper implementation

    def register_branch(self, branch, parent):
        if parent != None and parent.id in self.counts:
            self.counts[branch.id] = dict(self.counts[parent.id])
        else:
            self.counts[branch.id] = {}

    def after_apply(self, target):
        if 'flag' in target and target['flag']:
            return
        branch = target['branch']
        sentence = target['sentence']
        if sentence not in self.counts[branch.id]:
            self.counts[branch.id][sentence] = 0
        self.counts[branch.id][sentence] += 1