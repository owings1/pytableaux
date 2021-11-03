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
from utils import OrderedAttrsView, isint, isstr, rcurry, lcurry
from lexicals import Variable, Predicate, Predicated, Atomic, Quantified, \
    Operated, operarity

class AdzHelper(object):

    def __init__(self, rule):
        self.rule = rule
        self.Node = rule.Node

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
            nodes = [self.Node(node) for node in nodes]
            for rule in self.rule.tableau.closure_rules():
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

    # Event Listeners

    def after_node_add(self, node, branch):
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

    # Event Listeners

    def after_branch_add(self, branch):
        parent = branch.parent
        if parent != None and parent.id in self.flagged:
            self.flagged[branch.id] = self.flagged[parent.id]
        else:
            self.flagged[branch.id] = False

    def after_apply(self, target):
        if target.get('flag'):
            self.flagged[target['branch'].id] = True

class NodeFilterHelper(object):

    def __init__(self, rule):
        self.rule = rule
        self.__flist = []
        self.__fmap = {}
        self.__cache = {}
        self.__include_ticked = None
        self.__viewfilters = OrderedAttrsView(self.__fmap, self.__flist)
        for name, cls in getattr(rule, 'NodeFilters', tuple()):
            self.add_filter(name, cls)

    # API

    def add_filter(self, name, cls):
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
        if not self.include_ticked and branch.is_ticked(node):
            return False
        for func in self.__flist:
            if not func(node):
                return False
        return True

    # Subscript API

    def __getitem__(self, branch):
        return self.__cache[branch]

    def __setitem__(self, branch, value):
        if branch in self.__cache:
            raise KeyError('Branch {} already in cache'.format(branch.id))
        self.__cache[branch] = value

    def __delitem__(self, branch):
        del(self.__cache[branch])

    def __contains__(self, branch):
        return branch in self.__cache

    def __len__(self):
        return len(self.__cache)

    def __iter__(self):
        return iter(self.__cache)
    # Induced Rule Properties

    @property
    def include_ticked(self):
        if self.__include_ticked != None:
            return self.__include_ticked
        return getattr(self.rule, 'include_ticked', None)

    @include_ticked.setter
    def include_ticked(self, val):
        self.__include_ticked = val

    # Event Listeners

    def after_branch_add(self, branch):
        self[branch] = set()
        if branch.parent:
            self[branch].update(self[branch.parent])

    def after_branch_close(self, branch):
        del(self[branch])

    def after_node_add(self, node, branch):
        if self.filter(node, branch):
            self[branch].add(node)

    def after_node_tick(self, node, branch):
        if not self.include_ticked:
            self[branch].discard(node)

class Getters(object):

    def __new__(cls, *items):
        return cls.chain(*items)

    @staticmethod
    def chain(*items):
        chain = [cls(*args) for cls, *args in items]
        last = chain.pop()
        class chained(object):
            def __call__(self, obj, *args):
                for func in chain:
                    obj = func(obj)
                return last(obj, *args)
        return chained()

    class Getter(object):
        curry = rcurry
        def __new__(cls, *args):
            inst = object.__new__(cls)
            if args:
                return cls.curry(inst, args)
            return inst

    class Attr(Getter):
        def __call__(self, obj, name):
            return getattr(obj, name)

    class AttrSafe(Getter):
        def __call__(self, obj, name):
            return getattr(obj, name, None)

    class Key(Getter):
        def __call__(self, obj, key):
            return obj[key]

    class KeySafe(Getter):
        def __call__(self, obj, key):
            try:
                return obj[key]
            except KeyError:
                pass

    class It(Getter):
        curry = lcurry
        def __call__(self, obj, _ = None):
            return obj

    attr = Attr()
    attrsafe = AttrSafe()
    key = Key()
    keysafe = KeySafe()
    it = It()

class Filters(object):

    class Method(object):

        args = tuple()
        kw = {}

        get = Getters.attr

        def __init__(self, meth, *args, **kw):
            self.meth = meth
            if args:
                self.args = args
            self.kw.update(kw)

        def __call__(self, rhs):
            func = self.get(rhs, self.meth)
            return bool(func(*self.args, **self.kw))

    class Attr(object):

        attrs = tuple()

        lget = Getters.attrsafe
        rget = Getters.attr

        def __init__(self, lhs, **attrmap):
            self.lhs = lhs
            self.attrs = tuple(self.attrs + tuple(attrmap.items()))

        def __call__(self, rhs):
            for lattr, rattr in self.attrs:
                val = self.lget(self.lhs, lattr)
                if val != None and val != self.rget(rhs, rattr):
                    return False
            return True

    class Sentence(object):

        get = Getters.it

        @property
        def negated(self):
            if self.__negated != None:
                return self.__negated
            return Getters.attrsafe(self.lhs, 'negated')

        @negated.setter
        def negated(self, val):
            self.__negated = val

        @property
        def lhs(self):
            return self.__lhs

        @property
        def applies(self):
            return self.__applies
        def get_sentence(self, rhs):
            s = self.get(rhs)
            if s:
                if not self.negated:
                    return s
                if s.is_negated:
                    return s.operand
        def eg_sentence(self):
            if not self.applies:
                return
            a = Atomic(0, 0)
            if self.operator != None:
                params = []
                arity = operarity(self.operator)
                s = Operated(
                    self.operator,
                    
                )
                if arity > 0:
                    params.append(a)
                for i in range(arity - 1):
                    params.append(params[-1].next())
                s = Operated(self.operator, params)
            elif self.quantifier != None:
                sp = Predicated(Predicate(0, 0, 1), Variable(0, 0))
                s = Quantified(self.quantifier, sp)
            if self.negated:
                if s == None:
                    s = a
                s = s.negate()
            return s
        def __init__(self, lhs, negated = None):
            self.__negated = None
            self.__lhs = lhs
            self.__applies = any((lhs.operator, lhs.quantifier, lhs.predicate))
            if negated != None:
                self.negated = negated

        def __call__(self, rhs):
            if not self.applies:
                return True
            s = self.get_sentence(rhs)
            if not s:
                return False
            lhs = self.lhs
            if lhs.operator and lhs.operator != s.operator:
                return False
            if lhs.quantifier and lhs.quantifier != s.quantifier:
                return False
            if lhs.predicate:
                if not s.predicate or lhs.predicate not in s.predicate.refs:
                    return False
            return True
    Node = None

class NodeFilters(object):
    class Sentence(Filters.Sentence):
        get = Getters.KeySafe('sentence')

Filters.Node = NodeFilters

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
        for branch in tableau.branches():
            origin = branch.origin()
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
            for node in branch
        ])
        return max(1, branch.constants_count) * max(1, node_needed_constants) + 1

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
        for c in node.constants():
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

    def after_trunk_build(self, tableau):
        for branch in tableau.branches():
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
            for node in branch
        ])
        return branch.world_count + node_needed_worlds + 1

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

    def after_branch_add(self, branch):
        parent = branch.parent
        if parent != None and parent.id in self.unserial_worlds:
            self.unserial_worlds[branch.id] = set(self.unserial_worlds[parent.id])
        else:
            self.unserial_worlds[branch.id] = set()

    def after_node_add(self, node, branch):
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

    def after_branch_add(self, branch):
        parent = branch.parent
        if parent != None and parent.id in self.index:
            self.index[branch.id] = {
                w: set(self.index[parent.id][w])
                for w in self.index[parent.id]
            }
        else:
            self.index[branch.id] = {}

    def after_node_add(self, node, branch):
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

    def after_branch_add(self, branch):
        parent = branch.parent
        if parent != None and parent.id in self.predicated_nodes:
            self.predicated_nodes[branch.id] = set(self.predicated_nodes[parent.id])
        else:
            self.predicated_nodes[branch.id] = set()

    def after_node_add(self, node, branch):
        if node.has('sentence') and node.props['sentence'].is_predicated:
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

    def after_node_add(self, node, branch):
        if branch.id not in self.node_worlds_applied:
            self.node_worlds_applied[branch.id] = set()

    def after_apply(self, target):
        if target.get('flag'):
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

    def after_branch_add(self, branch):
        parent = branch.parent
        if parent != None and parent.id in self.counts:
            self.counts[branch.id] = dict(self.counts[parent.id])
        else:
            self.counts[branch.id] = {}

    def after_apply(self, target):
        if target.get('flag'):
            return
        branch = target['branch']
        sentence = target['sentence']
        if sentence not in self.counts[branch.id]:
            self.counts[branch.id][sentence] = 0
        self.counts[branch.id][sentence] += 1

class EllipsisExampleHelper(object):

    mynode = {'ellipsis': True}
    closenodes = []

    def __init__(self, rule):
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
        self.__addnode(target['branch'])

    def __addnode(self, branch):
        self.applied.add(branch)
        branch.add(self.mynode)