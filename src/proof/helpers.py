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
from copy import copy
from models import BaseModel
from utils import OrderedAttrsView, LinkOrderSet, EmptySet, kwrepr, isstr
from .common import Target
from itertools import chain
from events import Events

def clshelpers(**kw):
    """
    Class decorator to add to Helpers attribute through mro.
    Attribute name is ``Helpers``.
    """
    def addhelpers(cls):
        attr = 'Helpers'
        value = _dedupvalue(_collectattr(cls, attr, **kw))
        setattr(cls, attr, tuple(value))
        return cls
    return addhelpers

class AdzHelper(object):

    def adztarget(getadds):
        def adz_transform(self, *args, **kw):
            res = getadds(self, *args, **kw)
            if not res: return res
            if isinstance(res, dict):
                res = (res,)
            if not isinstance(res, (tuple, list)):
                raise TypeError('expecting tuple/list, %s' % res)
            return {'adds': res}
        return adz_transform

    def __init__(self, rule, *args, **kw):
        self.rule = rule
        self.Node = rule.Node
        self.tableau = rule.tableau

    def apply_to_target(self, target):
        branch = target.branch
        adds = target.get('adds', 0)
        for i in range(len(adds)):
            if i == 0:
                continue
            b = self.rule.branch(branch)
            b.extend(target['adds'][i])
            if self.rule.ticking:
                b.tick(target['node'])
        branch.extend(target['adds'][0])
        if self.rule.ticking:
            branch.tick(target['node'])

    def closure_score(self, target):
        close_count = 0
        for nodes in target['adds']:
            nodes = [self.Node(node) for node in nodes]
            for rule in self.tableau.rules.closure:
                if rule.nodes_will_close_branch(nodes, target.branch):
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

    def __init__(self, rule, *args, **kw):
        self.rule = rule
        self.targets = {}

    def cached_target(self, branch):
        """
        Return the cached target for the branch, if any.
        """
        if branch in self.targets:
            return self.targets[branch]

    # Event Listeners

    def after_node_add(self, node, branch):
        target = self.rule.check_for_target(node, branch)
        if target:
            self.targets[branch] = target

class QuitFlagHelper(object):
    """
    Track the application of a flag node by the rule for each branch. A branch
    is considered flagged when the target has a non-empty ``flag`` property.
    """

    def __init__(self, rule, *args, **kw):
        self.rule = rule
        self.flagged = {}

    def has_flagged(self, branch):
        """
        Whether the branch has been flagged.
        """
        if branch in self.flagged:
            return self.flagged[branch]
        return False

    # Event Listeners

    def after_branch_add(self, branch):
        parent = branch.parent
        if parent:
            self.flagged[branch] = self.flagged[parent]
        else:
            self.flagged[branch] = False

    def after_apply(self, target):
        if target.get('flag'):
            self.flagged[target.branch] = True

class BranchCache(object):

    _valuetype = bool
    def __init__(self, *args, **kw):
        pass

    def __getitem__(self, branch):
        return self.__cache[branch]

    def __setitem__(self, branch, value):
        if branch in self.__cache:
            raise KeyError('Branch %s already in cache' % branch.id)
        self.__linkset.add(branch)
        self.__cache[branch] = value

    def __delitem__(self, branch):
        del(self.__cache[branch])
        del(self.__linkset[branch])

    def __contains__(self, branch):
        return branch in self.__cache

    def __len__(self):
        return len(self.__cache)

    def __iter__(self):
        return iter(self.__linkset)

    def __reversed__(self):
        return reversed(self.__linkset)

    def __new__(cls, rule, *args):
        inst = super().__new__(cls)
        inst.__linkset = LinkOrderSet()
        inst.__cache = {}
        inst.rule = rule
        inst.tab = rule.tableau
        inst.tab.on(Events.AFTER_BRANCH_ADD,   inst.__BranchCache_after_branch_add)
        inst.tab.on(Events.AFTER_BRANCH_CLOSE, inst.__BranchCache_after_branch_close)
        return inst

    def __BranchCache_after_branch_close(self, branch):
        del(self[branch])

    def __BranchCache_after_branch_add(self, branch):
        if branch.parent:
            self[branch] = copy(self[branch.parent])
        else:
            self[branch] = self._valuetype()

    # Other
    def _reprdict(self):
        return {'branches': len(self)}

    def __repr__(self):
        return '<%s>:' % self.__class__.__name__ + kwrepr(
            **self._reprdict()
        )

class BranchNodeCache(BranchCache):
    _valuetype = set
    
    # Induced Rule Properties

    __ignore_ticked = None

    @property
    def ignore_ticked(self):
        if self.__ignore_ticked != None:
            return self.__ignore_ticked
        return getattr(self.rule, 'ignore_ticked', None)

    @ignore_ticked.setter
    def ignore_ticked(self, val):
        self.__ignore_ticked = val

    def __new__(cls, rule, *args):
        inst = super().__new__(cls, rule)
        inst.tab.on(Events.AFTER_NODE_ADD,  inst._BranchNodeCache_after_node_add)
        inst.tab.on(Events.AFTER_NODE_TICK, inst._BranchNodeCache_after_node_tick)
        return inst

    # Event Listeners

    def _BranchNodeCache_after_node_add(self, node, branch):
        res = self(node, branch)
        if res != None:
            self[branch].add(res)

    def _BranchNodeCache_after_node_tick(self, node, branch):
        if self.ignore_ticked:
            self[branch].discard(node)

    def __call__(self, *args, **kw):
        pass

class PredicatedNodesTracker(BranchNodeCache):
    """
    Track all predicated nodes on the branch.
    """
    def __call__(self, node, *a, **kw):
        if node.has('sentence') and node['sentence'].is_predicated:
            return node

class FilterHelper(BranchNodeCache):
    """
    Set configurable and chainable filters in ``NodeFilters``
    class attribute.
    """

    clsattr = 'NodeFilters'

    # Decorators

    @classmethod
    def clsfilters(cls, **kw):
        """
        Class decorator to add to ``NodeFilters`` attribute
        through mro.
        """
        def addfilters(rulecls):
            attr = cls.clsattr
            value = _dedupvalue(_collectattr(rulecls, attr, **kw))
            setattr(rulecls, attr, tuple(value))
            return rulecls
        return addfilters

    @classmethod
    def node_targets(cls, _get_targets):
        """
        Method decorator to only iterate through nodes matching the
        configured FilterHelper filters.
        """
        def get_targets_filtered(self, branch):
            helper = self.helpers[cls]
            resgen = (
                (_get_targets(self, node, branch), branch, node)
                for node in helper[branch]
            )
            filt = (x for x in resgen if bool(x[0]))
            create = (
                Target.create(res, branch=branch, node=node, rule=self)
                for res, branch, node in filt
            )
            return tuple(create)
        return get_targets_filtered

    def add_filter(self, name, cls):
        """
        Instantiate a filter class from the NodeFilters config.
        """
        if name in self.__fmap:
            raise KeyError('{} exists'.format(name))
        if not isstr(name):
            raise TypeError('name not a string')
        filt = cls(self.rule)
        self.__fmap[name] = filt
        self.__flist.append(filt)

    @property
    def filters(self):
        return self.__viewfilters

    def filter(self, node, branch):
        self.callcount += 1
        if not self.ignore_ticked and branch.is_ticked(node):
            return False
        for func in self.__flist:
            if not func(node):
                return False
        return True

    def example_node(self):
        node = {}
        for filt in self.filters:
            if callable(getattr(filt, 'example_node', None)):
                n = filt.example_node()
                if n:
                    node.update(n)
            elif callable(getattr(filt, 'example', None)):
                ret = filt.example()
                if isinstance(ret, dict):
                    node.update(ret)
        return node

    def __call__(self, node, branch):
        if self.filter(node, branch):
            return node

    def __init__(self, rule, attr = None, *args, **kw):
        super().__init__(rule, *args, **kw)
        self.rule = rule
        self.callcount = 0
        self.__flist = []
        self.__fmap = {}
        self.__viewfilters = OrderedAttrsView(self.__fmap, self.__flist)
        clsval = getattr(rule, self.__class__.clsattr, tuple())
        for name, cls in clsval:
            self.add_filter(name, cls)

    def _reprdict(self):
        return super()._reprdict() | {
            'filters': '(%s) %s' % (len(self.filters), self.filters),
        }

class MaxConstantsTracker(object):
    """
    Project the maximum number of constants per world required for a branch
    by examining the branches after the trunk is built.
    """

    def __init__(self, rule, *args, **kw):
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
        origin = branch.origin
        if origin.id in self.branch_max_constants:
            return self.branch_max_constants[origin.id]
        return 1

    def get_branch_constants_at_world(self, branch, world):
        """
        Get the cached set of constants at a world for the branch.

        :param tableaux.Branch branch:
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

        :param tableaux.Branch branch:
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

        :param tableaux.Branch branch:
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

        :param tableaux.Branch branch:
        :rtype: dict
        """
        info = '{0}:MaxConstants({1})'.format(self.rule.name, str(self.get_max_constants(branch)))
        return {'is_flag': True, 'flag': 'quit', 'info': info}

    # Helper implementation

    def after_trunk_build(self, tableau):
        for branch in tableau:
            origin = branch.origin
            # In most cases, we will have only one origin branch.
            if origin.id in self.branch_max_constants:
                return
            self.branch_max_constants[origin.id] = self._compute_max_constants(branch)

    def after_branch_add(self, branch):
        parent = branch.parent
        if parent != None and parent.id in self.world_constants:
            self.world_constants[branch.id] = {
                world : set(self.world_constants[parent.id][world])
                for world in self.world_constants[parent.id]
            }
        else:
            self.world_constants[branch.id] = {}

    def after_node_add(self, node, branch):
        if node.has('sentence'):
            consts = node['sentence'].constants
            world = node.get('world')
            if world == None:
                world = 0
            if world not in self.world_constants[branch.id]:
                self.world_constants[branch.id][world] = set()
            self.world_constants[branch.id][world].update(consts)

    # Private util

    def _compute_max_constants(self, branch):
        """
        Project the maximum number of constants for a branch (origin) as
        the number of constants already on the branch (min 1) * the number of
        quantifiers (min 1) + 1.
        """
        node_needed_constants = sum([
            self._compute_needed_constants_for_node(node, branch)
            for node in branch
        ])
        return max(1, branch.constants_count) * max(1, node_needed_constants) + 1

    def _compute_needed_constants_for_node(self, node, branch):
        if node.has('sentence'):
            return len(node['sentence'].quantifiers)
        return 0

class NodeAppliedConstants(object):
    """
    Track the applied and unapplied constants per branch for each potential node.
    The rule's target should have `branch`, `node` and `constant` properties.

    Only nodes that are applicable according to the rule's ``is_potential_node()``
    method are tracked.
    """

    def __init__(self, rule, *args, **kw):
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

    def after_branch_add(self, branch):
        parent = branch.parent
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

    def after_node_add(self, node, branch):
        if self.__should_track_node(node, branch):
            if node.id not in self.node_states[branch.id]:
                # By tracking per node, we are tracking per world, a fortiori.
                self.node_states[branch.id][node.id] = {
                    'applied'   : set(),
                    'unapplied' : set(self.consts[branch.id]),
                }
        consts = node['sentence'].constants if node.has('sentence') else EmptySet
        for c in consts:
            if c not in self.consts[branch.id]:
                for node_id in self.node_states[branch.id]:
                    self.node_states[branch.id][node_id]['unapplied'].add(c)
                self.consts[branch.id].add(c)

    def after_apply(self, target):
        if target.get('flag'):
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

    def __init__(self, rule, *args, **kw):
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
        origin = branch.origin
        if origin.id in self.branch_max_worlds:
            return self.branch_max_worlds[origin.id]

    def max_worlds_reached(self, branch):
        """
        Whether we have already reached or exceeded the max number of worlds
        projected for the branch (origin).
        """
        max_worlds = self.get_max_worlds(branch)
        return max_worlds != None and branch.world_count >= max_worlds

    def max_worlds_exceeded(self, branch):
        """
        Whether we have exceeded the max number of worlds projected for the
        branch (origin).
        """
        max_worlds = self.get_max_worlds(branch)
        return max_worlds != None and branch.world_count > max_worlds

    def modal_complexity(self, sentence):
        """
        Compute and cache the modal complexity of a sentence by counting its
        modal operators.
        """
        if sentence not in self.modal_complexities:
            self.modal_complexities[sentence] = len([
                o for o in sentence.operators if o in self.modal_operators
            ])
        return self.modal_complexities[sentence]

    def quit_flag(self, branch):
        """
        Generate a quit flag node for the branch.
        """
        info = '{0}:MaxWorlds({1})'.format(self.rule.name, str(self.get_max_worlds(branch)))
        return {'is_flag': True, 'flag': 'quit', 'info': info}

    # Helper implementation

    def after_trunk_build(self, tableau):
        for branch in tableau:
            origin = branch.origin
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
            for node in branch
        ])
        return branch.world_count + node_needed_worlds + 1

    def __compute_needed_worlds_for_node(self, node, branch):
        # we only care about unticked nodes, since ticked nodes will have
        # already created any worlds.
        if not branch.is_ticked(node) and node.has('sentence'):
            return self.modal_complexity(node['sentence'])
        return 0

class UnserialWorldsTracker(object):
    """
    Track the unserial worlds on the branch.
    """

    def __init__(self, rule, *args, **kw):
        self.rule = rule
        self.track = {}

    def get_unserial_worlds(self, branch):
        """
        Get the set of unserial worlds on the branch.
        """
        return self.track[branch]

    # helper implementation

    def after_branch_add(self, branch):
        parent = branch.parent
        self.track[branch] = set()
        if parent:
            self.track[branch].update(self.track[parent])

    def after_node_add(self, node, branch):
        for w in node.worlds:
            if branch.has({'world1': w}):
                self.track[branch].discard(w)
            else:
                self.track[branch].add(w)

class VisibleWorldsIndex(object):
    """
    Index the visible worlds for each world on the branch.
    """

    def __init__(self, rule, *args, **kw):
        self.rule = rule
        self.index = {}

    def get_visibles(self, branch, world):
        """
        Get all the worlds on the branch that are visible to the given world.
        """
        if world in self.index[branch]:
            return self.index[branch][world]
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

    def after_branch_add(self, branch):
        self.index[branch] = {}
        if branch.parent:
            self.index[branch].update({
                w: set(self.index[branch.parent][w])
                for w in self.index[branch.parent]
            })

    def after_node_add(self, node, branch):
        if node.has('world1', 'world2'):
            w1 = node['world1']
            w2 = node['world2']
            if w1 not in self.index[branch]:
                self.index[branch][w1] = set()
            self.index[branch][w1].add(w2)

class AppliedNodesWorldsTracker(object):
    """
    Track the nodes applied to by the rule for each world on the branch. The
    rule's target must have `branch`, `node`, and `world` keys.
    """

    def __init__(self, rule, *args, **kw):
        self.rule = rule
        self.track = {}

    def is_applied(self, node, world, branch):
        """
        Whether the rule has applied to the node for the world and branch.
        """
        return (node.id, world) in self.track[branch]

    # helper implementation

    def after_node_add(self, node, branch):
        if branch not in self.track:
            self.track[branch] = set()

    def after_apply(self, target):
        if target.get('flag'):
            return
        pair = (target.node.id, target['world'])
        self.track[target.branch].add(pair)

class AppliedSentenceCounter(object):
    """
    Count the times the rule has applied for a sentence per branch. This tracks
    the `sentence` property of the rule's target. The target should also include
    the `branch` key.
    """

    def __init__(self, rule, *args, **kw):
        self.rule = rule
        self.counts = {}

    def get_count(self, sentence, branch):
        """
        Return the count for the given sentence and branch.
        """
        if sentence not in self.counts[branch]:
            return 0
        return self.counts[branch][sentence]

    # helper implementation

    def after_branch_add(self, branch):
        self.counts[branch] = {}
        if branch.parent:
            self.counts[branch].update(self.counts[branch.parent])

    def after_apply(self, target):
        if target.get('flag'):
            return
        branch = target.branch
        sentence = target['sentence']
        if sentence not in self.counts[branch]:
            self.counts[branch][sentence] = 0
        self.counts[branch][sentence] += 1

class EllipsisExampleHelper(object):

    mynode = {'ellipsis': True}
    closenodes = []

    def __init__(self, rule, *args, **kw):
        self.rule = rule
        self.applied = set()
        if rule.is_closure:
            self.closenodes = list(
                n if isinstance(n, dict) else n.props
                for n in reversed(rule.example_nodes())
            )
        self.istrunk = False

    def before_trunk_build(self, *_):
        self.istrunk = True

    def after_trunk_build(self, *_):
        self.istrunk = False

    def after_branch_add(self, branch):
        if self.applied:
            return
        if len(self.closenodes) == 1:
            self.__addnode(branch)        

    def after_node_add(self, node, branch):
        if self.applied:
            return
        if node.has_props(self.mynode) or node.is_closure:
            return
        if self.istrunk:
            self.__addnode(branch)
        elif self.closenodes and node.has_props(self.closenodes[-1]):
            self.closenodes.pop()
            if len(self.closenodes) == 1:
                self.__addnode(branch)

    def before_apply(self, target):
        if self.applied:
            return
        if self.rule.is_closure:
            return
        self.__addnode(target.branch)

    def __addnode(self, branch):
        self.applied.add(branch)
        branch.add(self.mynode)

def _collectattr(cls, attr, **adds):
    return filter (bool, chain(
        * (
            c.__dict__.get(attr, tuple())
            for c in reversed(cls.mro())
        ),
        (
            (name, value)
            for name, value in adds.items()
        )
    ))

def _dedupvalue(value):
    track = {}
    dedup = []
    for k, v in value:
        if k not in track:
            track[k] = v
            dedup.append((k, v))
        elif track[k] != v:
            raise ValueError('Conflict %s / %s / %s' % (k, v, track[k]))
    return dedup