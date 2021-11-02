
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
from inspect import isclass
from lexicals import Atomic, Operated, operarity
from utils import EventEmitter, StopWatch, istableau, safeprop, typecheck
from .helpers import AdzHelper, NodeTargetCheckHelper, NodeAppliedConstants, \
    MaxConstantsTracker, QuitFlagHelper
from events import Events

class Rule(EventEmitter):
    """
    Base class for a tableau rule.
    """

    Helpers = tuple()#(('adz', AdzHelper),)
    Timers = tuple()

    branch_level = 1

    default_opts = {
        'is_rank_optim' : True
    }

    def __init__(self, tableau, **opts):
        if not istableau(tableau):
            raise TypeError(
                '`tableau` must be a Tableau, got {}'.format(tableau.__class__)
            )
        super().__init__()

        self.search_timer = StopWatch()
        self.apply_timer = StopWatch()
        self.timers = {}

        self.opts = dict(__class__.default_opts)
        self.opts.update(self.default_opts)
        self.opts.update(opts)

        self.__apply_count = 0
        self.__helpers = []
        self.__tableau = tableau

        self.register_event(
            Events.AFTER_APPLY,
            Events.BEFORE_APPLY,
        )
        for name, helper in self.Helpers:
            self.add_helper(helper, name)
        self.add_timer(*self.Timers)

    @property
    def apply_count(self):
        """
        The number of times the rule has applied.

        :type: int
        """
        return self.__apply_count

    @property
    def is_closure(self):
        """
        Whether this is an instance of :class:`~ClosureRule`.

        :type: bool
        """
        return isinstance(self, ClosureRule)

    @property
    def name(self):
        """
        The rule name, default it the class name.

        :type: str
        """
        return self.__class__.__name__

    @property
    def tableau(self):
        """
        Reference to the tableau instance.

        :type: tableaux.Tableau
        """
        return self.__tableau

    @property
    def Node(self):
        """
        Reference to the :class:`~tableaux.Node` class.

        :type: class
        """
        return self.tableau.Node

    def get_target(self, branch):
        """
        :meta public final:
        """
        # Concrete classes should not override this, but should implement
        # ``_get_targets()`` instead.
        targets = self._get_targets(branch)
        if targets:
            self.__extend_targets(targets)
            return self.__select_best_target(targets)

    def apply(self, target):
        """
        :meta public final:
        """
        # Concrete classes should not override this, but should implement
        # ``_apply()`` instead.
        with self.apply_timer:
            self.emit(Events.BEFORE_APPLY, target)
            self._apply(target)
            self.__apply_count += 1
            self.emit(Events.AFTER_APPLY, target)

    def branch(self, parent = None):
        """
        Create a new branch on the tableau. Convenience for ``self.tableau.branch()``.

        :param tableaux.Branch parent: The parent branch, if any.
        :return: The new branch.
        :rtype: tableaux.Branch
        :meta public final:
        """
        return self.tableau.branch(parent)

    def add_timer(self, *names):
        """
        Add a timer.

        :meta public:
        """
        for name in names:
            if name in self.timers:
                raise KeyError("Timer '{}' already exists".format(name))
            self.timers[name] = StopWatch()

    def add_helper(self, helper, attr = None):
        """
        Add a helper.

        :meta public:
        """
        if isclass(helper):
            helper = helper(self)
        if attr != None:
            safeprop(self, attr, helper)
        for event, meth in (
            (Events.AFTER_APPLY  , 'after_apply'),
            (Events.BEFORE_APPLY , 'before_apply'),
        ):
            if hasattr(helper, meth):
                self.add_listener(event, getattr(helper, meth))
        for event, meth in (
            (Events.AFTER_BRANCH_ADD   , 'after_branch_add'),
            (Events.AFTER_BRANCH_CLOSE , 'after_branch_close'),
            (Events.AFTER_NODE_ADD     , 'after_node_add'),
            (Events.AFTER_NODE_TICK    , 'after_node_tick'),
            (Events.AFTER_TRUNK_BUILD  , 'after_trunk_build'),
            (Events.BEFORE_TRUNK_BUILD , 'before_trunk_build'),
        ):
            if hasattr(helper, meth):
                self.tableau.add_listener(event, getattr(helper, meth))
        self.__helpers.append(helper)
        return helper

    # Abstract methods
    def example_nodes(self):
        """
        :meta abstract:
        """
        raise NotImplementedError()

    def _get_targets(self, branch):
        """
        :meta protected abstract:
        """
        # Intermediate classes such as ``ClosureRule``, ``PotentialNodeRule``,
        # (and its child ``FilterNodeRule``) implement this and ``select_best_target()``,
        # and define finer-grained methods for concrete classes to implement.
        raise NotImplementedError()

    def _apply(self, target):
        """
        Apply the rule to the target. Implementations should modify the tableau directly,
        with no return value.

        :meta abstract:
        """
        raise NotImplementedError()

    # Default implementation

    def sentence(self, node):
        """
        Get the sentence for the node, or ``None``.

        :param tableaux.Node node:
        :rtype: lexicals.Sentence
        """
        return node.get('sentence')

    # Scoring

    def group_score(self, target):
        # Called in tableau
        return self.score_candidate(target) / max(1, self.branch_level)

    # Candidate score implementation options ``is_rank_optim``

    def score_candidate(self, target):
        return sum(self.score_candidate_list(target))

    def score_candidate_list(self, target):
        return self.score_candidate_map(target).values()

    def score_candidate_map(self, target):
        # Will sum to 0 by default
        return {}

    # Other

    def __repr__(self):
        return self.name

    # Private Util

    def __extend_targets(self, targets):
        """
        Augment the targets with the following keys:
        
        - `rule`
        - `is_rank_optim`
        - `candidate_score`
        - `total_candidates`
        - `min_candidate_score`
        - `max_candidate_score`

        :param iterable(dict) targets: The list of targets.
        :param tableaux.Branch branch: The branch.
        :return: ``None``
        """
        if self.opts['is_rank_optim']:
            scores = [self.score_candidate(target) for target in targets]
        else:
            scores = [0]
        max_score = max(scores)
        min_score = min(scores)
        for i, target in enumerate(targets):
            target.update({
                'rule'            : self,
                'total_candidates': len(targets),
            })
            if self.opts['is_rank_optim']:
                target.update({
                    'is_rank_optim'       : True,
                    'candidate_score'     : scores[i],
                    'min_candidate_score' : min_score,
                    'max_candidate_score' : max_score,
                })
            else:
                target.update({
                    'is_rank_optim'       : False,
                    'candidate_score'     : None,
                    'min_candidate_score' : None,
                    'max_candidate_score' : None,
                })

    def __select_best_target(self, targets):
        """
        Selects the best target. Assumes targets have been extended.
        """
        for target in targets:
            if not self.opts['is_rank_optim']:
                return target
            if target['candidate_score'] == target['max_candidate_score']:
                return target

class Target(object):

    __comps = {'type'}
    __attrs = {'branch', 'node', 'rule'}
    __oppos = {}

    __opkeys = {
        # 'node': {'nodes'},
        # 'nodes': {'node'},
    }

    @staticmethod
    def create(obj, **data):
        if isinstance(obj, __class__):
            target = obj
            target.update(data)
        else:
            target = __class__(data)
            if isinstance(obj, dict):
                target.update(obj)
        return target

    def __init__(self, data):
        self.__keys = set(self.__comps)
        self.__data = {}
        self.__oppos = {}
        self.update(data)
        self['branch']
        # self['rule']

    def update(self, obj):
        for k in obj:
            self[k] = obj[k]

    def get(self, key, default = None):
        try:
            return self[key]
        except KeyError:
            return default

    def __getitem__(self, item):
        if item in self.__comps:
            return getattr(self, item)
        return self.__data[item]

    def __setitem__(self, item, val):
        if item in self.__oppos:
            oppos = self.__oppos[item]
            raise KeyError("Cannot set '{}' when '{}' is set".format(item, oppos))
        if item in self.__keys:
            if item in self.__comps:
                raise KeyError("Computed property '{}'".format(item))
            if self.__data[item] == val:
                return
            raise KeyError("Cannot replace '{}'".format(item))
        self.__data[item] = val
        self.__keys.add(item)
        if item in self.__opkeys:
            for key in self.__opkeys[item]:
                self.__oppos[key] = item

    def __contains__(self, item):
        return item in self.__keys

    @property
    def type(self):
        if 'nodes' in self.__data:
            return 'Nodes'
        if 'node' in self.__data:
            return 'Node'
        return 'Branch'

    def __getattr__(self, item):
        if item in self.__attrs:
            return getattr(self.__data, item)
        raise AttributeError("'{}'".format(item))

class ClosureRule(Rule):
    """
    A closure rule has a fixed ``apply()`` method that marks the branch as
    closed. Sub-classes should implement the ``applies_to_branch()`` method.
    """

    Helpers = (
        *Rule.Helpers,
        ('tracker', NodeTargetCheckHelper),
    )

    default_opts = {
        'is_rank_optim' : False
    }

    def _get_targets(self, branch):
        """
        :implements: Rule
        """
        target = self.applies_to_branch(branch)
        if target:
            return [Target.create(target, branch = branch)]

    def _apply(self, target):
        """
        :implements: Rule
        """
        target['branch'].close()

    def applies_to_branch(self, branch):
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
        self.tableau.add_listeners({
            Events.AFTER_BRANCH_ADD   : self.__after_branch_add,
            Events.AFTER_BRANCH_CLOSE : self.__after_branch_close,
            Events.AFTER_NODE_ADD     : self.__after_node_add,
            Events.AFTER_NODE_TICK    : self.__after_node_tick,
        })
        self.add_listener(Events.AFTER_APPLY, self.__after_apply)

    # Implementation

    def _get_targets(self, branch):
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

    def score_candidate(self, target):
        score = super().score_candidate(target)
        if score == 0:
            complexity = self.tableau.branching_complexity(target['node'])
            score = -1 * complexity
        return score

    def _apply(self, target):
        # Default implementation, to provide a more convenient
        # method signature.
        self.apply_to_node_target(target['node'], target['branch'], target)

    def get_targets_for_node(self, node, branch):
        # Default implementation, delegates to ``get_target_for_node``
        target = self.get_target_for_node(node, branch)
        if target:
            return [target]

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
            # modal = len(node.worlds()) > 0
            # if self.modal != modal:
                return False
        sentence = operator = quantifier = predicate = None
        if node.has('sentence'):
            sentence = node.props['sentence']
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
            if node.props.get('designated') != self.designation:
                return False
        if self.predicate != None:
            if predicate == None or self.predicate not in predicate.refs:
                return False
        return True

    # Override

    def sentence(self, node):
        s = None
        if 'sentence' in node.props:
            s = node.props['sentence']
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
        a = Atomic(0, 0)
        if self.operator != None:
            params = []
            arity = operarity(self.operator)
            if arity > 0:
                params.append(a)
            for i in range(arity - 1):
                params.append(params[-1].next())
            sentence = Operated(self.operator, params)
        elif self.quantifier != None:
            import examples
            sentence = examples.quantified(self.quantifier)
        if self.negated:
            if sentence == None:
                sentence = a
            sentence = sentence.negate()
        if sentence != None:
            props['sentence'] = sentence
        return (props,)

class NewConstantStoppingRule(FilterNodeRule):
    """
    Intermediate class for a one-constant instantiating rule. This class uses
    the ``MaxConstantsTracker``, and adds a quit flag to the branch once the
    max number of constants is exceeded.
 
    This class implements ``get_target_for_node()`` from ``FilterNodeRule``,
    replacing it with the abstract method: ``get_new_nodes_for_constant()``.
    """

    Helpers = (
        *FilterNodeRule.Helpers,
        ('max_constants', MaxConstantsTracker),
        ('quit_flagger' , QuitFlagHelper),
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

    def add_to_adds(self, node, branch):
        """
        Optionally extend the target `adds` with additional branches.
        """
        pass

    def get_target_for_node(self, node, branch):
        """
        Implements ``PotentialNodeRule``.
        """
        if not self.__should_apply(branch, node.props['world']):
            if not self.quit_flagger.has_flagged(branch):
                return self.__get_flag_target(branch)
            return

        c = branch.new_constant()

        target = {
            'adds': [
                self.get_new_nodes_for_constant(c, node, branch)
            ],
        }

        # TODO:
        # Most implementations do not branch, so ``get_new_nodes_for_constant``
        # expects just a list of nodes, not branches. However, K3WQ and P3 are
        # apparently exceptions, so this workaround is introduced.
        more_adds = self.add_to_adds(node, branch)
        if more_adds:
            target['adds'].extend(more_adds)

        return target

    def __should_apply(self, branch, world):
        return not self.max_constants.max_constants_exceeded(branch, world)

    def __get_flag_target(self, branch):
        return {
            'flag': True,
            'adds': [
                [
                    self.max_constants.quit_flag(branch),
                ]
            ],
        }

class AllConstantsStoppingRule(FilterNodeRule):

    Helpers = (
        *FilterNodeRule.Helpers,
        ('max_constants'     , MaxConstantsTracker),
        ('applied_constants' , NodeAppliedConstants),
        ('quit_flagger'      , QuitFlagHelper),
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
            if self.__should_flag(branch, node.props['world']):
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
        if self.max_constants.max_constants_exceeded(branch, node.props['world']):
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
            not self.quit_flagger.has_flagged(branch)
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

Rule.Target = Target