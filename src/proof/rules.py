
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
from lexicals import AtomicSentence, OperatedSentence, operarity
from utils import StopWatch
from .helpers import AdzHelper, NodeTargetCheckHelper, NodeAppliedConstants, \
    MaxConstantsTracker, QuitFlagHelper
from events import Events

class Rule(object):
    """
    Base class for a tableau rule.
    """

    branch_level = 1

    default_opts = {
        'is_rank_optim' : True
    }

    # For helper
    ticking = None

    # TODO: We may be able to remove this `ticked` property, since it looks
    #  like the only time this class uses it is if "not branch.parent", which
    #  seems like the only typical (read actual) case would be on trunk build.
    #  Furthermore, I believe it is just a (vacuous) optimization, instead
    #  of always using None for the filter in _after_branch_add. But tests
    #  will have to be performed.

    # For compatibility in ``_after_branch_add()``
    ticked = None

    def __init__(self, tableau, **opts):
        if not _check_is_tableau(tableau):
            raise TypeError('Must instantiate rule with a tableau instance.')
        #: Reference to the tableau for which the rule is instantiated.
        self.tableau = tableau
        self.search_timer = StopWatch()
        self.apply_timer = StopWatch()
        self.timers = {}
        self.helpers = []
        self.name = self.__class__.__name__
        self.apply_count = 0
        self.opts = dict(self.default_opts)
        self.opts.update(opts)
        self.add_helper('adz', AdzHelper(self))
        self.setup()
        self.tableau.add_listener(Events.AFTER_BRANCH_ADD, self.__after_branch_add)
        self.tableau.add_listener(Events.AFTER_BRANCH_CLOSE, self.__after_branch_close)
        self.tableau.add_listener(Events.AFTER_NODE_ADD, self.__after_node_add)
        self.tableau.add_listener(Events.AFTER_NODE_TICK, self.__after_node_tick)
        self.tableau.add_listener(Events.AFTER_TRUNK_BUILD, self.__after_trunk_build)
        self.tableau.add_listener(Events.BEFORE_TRUNK_BUILD, self.__before_trunk_build)

    # External API

    def apply(self, target):
        # Concrete classes should not override this, but should implement
        # ``apply_to_target()`` instead.
        with self.apply_timer:
            self.apply_to_target(target)
            self.apply_count += 1
            self.__after_apply(target)

    def get_target(self, branch):
        # Concrete classes should not override this, but should implement
        # ``get_candidate_targets()`` instead.
        cands = self.get_candidate_targets(branch)
        if cands:
            self.__extend_branch_targets(cands, branch)
            return self.__select_best_target(cands, branch)

    def __extend_branch_targets(self, targets, branch):
        # Augment the targets with the following keys:
        #
        #  - branch
        #  - is_rank_optim
        #  - candidate_score
        #  - total_candidates
        #  - min_candidate_score
        #  - max_candidate_score

        for target in targets:
            if 'branch' not in target:
                target['branch'] = branch

        if self.opts['is_rank_optim']:
            scores = [self.score_candidate(target) for target in targets]
        else:
            scores = [0]
        max_score = max(scores)
        min_score = min(scores)
        for i in range(len(targets)):
            target = targets[i]
            if self.opts['is_rank_optim']:
                target.update({
                    'is_rank_optim'       : True,
                    'candidate_score'     : scores[i],
                    'total_candidates'    : len(targets),
                    'min_candidate_score' : min_score,
                    'max_candidate_score' : max_score,
                })
            else:
                target.update({
                    'is_rank_optim'       : False,
                    'candidate_score'     : None,
                    'total_candidates'    : len(targets),
                    'min_candidate_score' : None,
                    'max_candidate_score' : None,
                })

    def __select_best_target(self, targets, branch):
        # Selects the best target. Assumes targets have been extended.
        for target in targets:
            if not self.opts['is_rank_optim']:
                return target
            if target['candidate_score'] == target['max_candidate_score']:
                return target

    # Abstract methods

    def get_candidate_targets(self, branch):
        # Intermediate classes such as ``ClosureRule``, ``PotentialNodeRule``,
        # (and its child ``FilterNodeRule``) implement this and ``select_best_target()``,
        # and define finer-grained methods for concrete classes to implement.
        raise NotImplementedError()

    def apply_to_target(self, target):
        # Apply the rule to the target. Implementations should
        # modify the tableau directly, with no return value.
        raise NotImplementedError()

    # Implementation options for ``example()``

    def example(self):
        # Add example branches/nodes sufficient for ``applies()`` to return true.
        # Implementations should modify the tableau directly, with no return
        # value. Used for building examples/documentation.
        branch = self.branch()
        branch.update(self.example_nodes(branch))

    def example_nodes(self, branch):
        return [self.example_node(branch)]

    def example_node(self, branch):
        raise NotImplementedError()

    # Default implementation

    def group_score(self, target):
        # Called in tableau
        return self.score_candidate(target) / max(1, self.branch_level)

    def sentence(self, node):
        # Overriden in FilterNodeRule
        if 'sentence' in node.props:
            return node.props['sentence']

    # Candidate score implementation options ``is_rank_optim``

    def score_candidate(self, target):
        return sum(self.score_candidate_list(target))

    def score_candidate_list(self, target):
        return self.score_candidate_map(target).values()

    def score_candidate_map(self, target):
        # Will sum to 0 by default
        return {}

    # Implementable callbacks -- always call ``super()``, or use a helper.

    def register_branch(self, branch, parent):
        pass

    def register_node(self, node, branch):
        pass

    def before_trunk_build(self, argument):
        pass

    def after_trunk_build(self, branches):
        pass

    def after_node_tick(self, node, branch):
        pass

    def after_branch_close(self, branch):
        pass

    def after_apply(self, target):
        pass

    # Util methods

    def setup(self):
        # Convenience instead of overriding ``__init__``. Should
        # only be used by concrete classes. called in constructor.
        pass

    def branch(self, parent=None):
        # Convenience for ``self.tableau.branch()``.
        return self.tableau.branch(parent)

    #: TODO: move tableau implementation to here directly.
    def branching_complexity(self, node):
        return self.tableau.branching_complexity(node)

    def safeprop(self, name, value=None):
        if hasattr(self, name):
            raise KeyError('Property {0} already exists'.format(str(name)))
        self.__dict__[name] = value

    def add_timer(self, *names):
        for name in names:
            if name in self.timers:
                raise KeyError('Timer {0} already exists'.format(str(name)))
            self.timers[name] = StopWatch()

    def add_helper(self, name, helper):
        self.safeprop(name, helper)
        self.helpers.append(helper)
        return helper

    def add_helpers(self, helpers):
        for name in helpers:
            self.add_helper(name, helpers[name])
        return self

    # Callbacks

    def __before_trunk_build(self, argument):
        self.before_trunk_build(argument)
        for helper in self.helpers:
            if hasattr(helper, 'before_trunk_build'):
                helper.before_trunk_build(argument)

    def __after_trunk_build(self, branches):
        self.after_trunk_build(branches)
        for helper in self.helpers:
            if hasattr(helper, 'after_trunk_build'):
                helper.after_trunk_build(branches)

    def __after_branch_add(self, branch):
        if not branch.parent:
            # For corner case of a register_branch callback adding a node, make
            # sure we don't call register_node twice, so prefetch the nodes.
            nodes = branch.get_nodes(ticked = self.ticked)
        else:
            nodes = None
        self.register_branch(branch, branch.parent)
        for helper in self.helpers:
            if hasattr(helper, 'register_branch'):
                helper.register_branch(branch, branch.parent)
        if not branch.parent:
            for node in nodes:
                self.register_node(node, branch)
                for helper in self.helpers:
                    if hasattr(helper, 'register_node'):
                        helper.register_node(node, branch)

    def __after_branch_close(self, branch):
        self.after_branch_close(branch)
        for helper in self.helpers:
            if hasattr(helper, 'after_branch_close'):
                helper.after_branch_close(branch)

    def __after_node_add(self, node, branch):
        self.register_node(node, branch)
        for helper in self.helpers:
            if hasattr(helper, 'register_node'):
                helper.register_node(node, branch)

    def __after_node_tick(self, node, branch):
        self.after_node_tick(node, branch)
        for helper in self.helpers:
            if hasattr(helper, 'after_node_tick'):
                helper.after_node_tick(node, branch)

    def __after_apply(self, target):
        self.after_apply(target)
        for helper in self.helpers:
            if hasattr(helper, 'after_apply'):
                helper.after_apply(target)

    def __repr__(self):
        return self.name

class ClosureRule(Rule):
    """
    A closure rule has a fixed ``apply()`` method that marks the branch as
    closed. Sub-classes should implement the ``applies_to_branch()`` method.
    """

    default_opts = {
        'is_rank_optim' : False
    }

    def __init__(self, *args, **opts):
        super().__init__(*args, **opts)
        self.add_helper('tracker', NodeTargetCheckHelper(self))

    def get_candidate_targets(self, branch):
        target = self.applies_to_branch(branch)
        if target:
            if target == True:
                target = {'branch': branch}
            if 'branch' not in target:
                target['branch'] = branch
            if 'type' not in target:
                target['type'] = 'Branch'
            return [target]

    def apply_to_target(self, target):
        target['branch'].close()

    def applies_to_branch(self, branch):
        raise NotImplementedError()

    def nodes_will_close_branch(self, nodes, branch):
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
    ``PotentialNodeRule`` base class. Caches potential nodes as they appear,
    and tracks the number of applications to each node. Provides default
    implementation of some methods, and delegates to finer-grained abstract
    methods.
    """

    # Override
    ticked = False

    def __init__(self, *args, **opts):
        super().__init__(*args, **opts)
        self.safeprop('potential_nodes', {})
        self.safeprop('node_applications', {})

    # Implementation

    def get_candidate_targets(self, branch):
        # Implementations should be careful with overriding this method.
        # Be sure you at least call ``_extend_node_target()``.
        cands = list()
        if branch.id in self.potential_nodes:
            for node in set(self.potential_nodes[branch.id]):
                targets = self.get_targets_for_node(node, branch)
                if targets:
                    for target in targets:
                        target = self._extend_node_target(target, node, branch)
                        cands.append(target)
                else:
                    if not self.is_potential_node(node, branch):
                        self.potential_nodes[branch.id].discard(node)
        return cands

    def _extend_node_target(self, target, node, branch):
        if target == True:
            target = {'node' : node}
        if 'node' not in target:
            target['node'] = node
        if 'type' not in target:
            target['type'] = 'Node'
        if 'branch' not in target:
            target['branch'] = branch
        return target

    # Caching

    def register_branch(self, branch, parent):
        # Likely to be extended in concrete class - call super and pay attention
        super().register_branch(branch, parent)
        if parent != None and parent.id in self.potential_nodes:
            self.potential_nodes[branch.id] = set(self.potential_nodes[parent.id])
            self.node_applications[branch.id] = dict(self.node_applications[parent.id])
        else:
            self.potential_nodes[branch.id] = set()
            self.node_applications[branch.id] = dict()

    def register_node(self, node, branch):
        # Likely to be extended in concrete class - call super and pay attention
        super().register_node(node, branch)
        if self.is_potential_node(node, branch):
            self.potential_nodes[branch.id].add(node)
            self.node_applications[branch.id][node.id] = 0

    def after_apply(self, target):
        super().after_apply(target)
        self.node_applications[target['branch'].id][target['node'].id] += 1

    def after_branch_close(self, branch):
        super().after_branch_close(branch)
        del(self.potential_nodes[branch.id])
        del(self.node_applications[branch.id])

    def after_node_tick(self, node, branch):
        super().after_node_tick(node, branch)
        if self.ticked == False and branch.id in self.potential_nodes:
            self.potential_nodes[branch.id].discard(node)

    # Util

    def min_application_count(self, branch_id):
        if branch_id in self.node_applications:
            if not len(self.node_applications[branch_id]):
                return 0
            return min({
                self.node_application_count(node_id, branch_id)
                for node_id in self.node_applications[branch_id]
            })
        return 0

    def node_application_count(self, node_id, branch_id):
        if branch_id in self.node_applications:
            if node_id in self.node_applications[branch_id]:
                return self.node_applications[branch_id][node_id]
        return 0

    # Default

    def score_candidate(self, target):
        score = super().score_candidate(target)
        if score == 0:
            complexity = self.branching_complexity(target['node'])
            score = -1 * complexity
        return score

    # Abstract

    def is_potential_node(self, node, branch):
        raise NotImplementedError()

    # Delegating abstract

    def get_targets_for_node(self, node, branch):
        # Default implementation, delegates to ``get_target_for_node``
        target = self.get_target_for_node(node, branch)
        if target:
            return [target]

    def get_target_for_node(self, node, branch):
        raise NotImplementedError()

    def apply_to_target(self, target):
        # Default implementation, to provide a more convenient
        # method signature.
        self.apply_to_node_target(target['node'], target['branch'], target)

    def apply_to_node_target(self, node, branch, target):
        # Default implementation, to provide a more convenient
        # method signature.
        self.apply_to_node(node, branch)

    def apply_to_node(self, node, branch):
        # Simpler signature to implement, mostly for legacy purposes.
        # New code should implement ``apply_to_node_target()`` instead,
        # which provides more flexibility.
        raise NotImplementedError()

class FilterNodeRule(PotentialNodeRule):
    """
    A ``FilterNodeRule`` filters potential nodes by matching
    the attribute conditions of the implementing class.

    The following attribute conditions can be defined. If a condition is
    set to ``None``, then it will be vacuously met.
    """

    #: The ticked status of the node, default is ``False``.
    ticked      = False

    #: Whether this rule applies to modal nodes, i.e. nodes that
    #: reference one or more worlds.
    modal       = None

    #: The main operator of the node's sentence, if any.
    operator    = None

    #: Whether the sentence must be negated. if ``True``, then nodes
    #: whose sentence's main connective is Negation will be checked,
    #: and if the negatum has the main connective defined in the
    #: ``operator`` condition (above), then this condition will be met.
    negated     = None

    #: The quantifier of the sentence, e.g. 'Universal' or 'Existential'.
    quantifier  = None

    #: The designation status (``True``/``False``) of the node.
    designation = None

    #: The predicate name
    predicate   = None

    # Implementation

    def is_potential_node(self, node, branch):
        return self.conditions_apply(node, branch)

    def get_target_for_node(self, node, branch):
        # Default is to return ``True``, which gets converted into a
        # target along the way.
        return self.conditions_apply(node, branch)

    def conditions_apply(self, node, branch):
        if self.ticked != None and self.ticked != (node in branch.ticked_nodes):
            return False
        if self.modal != None:
            modal = len(node.worlds()) > 0
            if self.modal != modal:
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
            if 'designated' not in node.props or node.props['designated'] != self.designation:
                return False
        if self.predicate != None:
            if predicate == None or self.predicate != predicate.name:
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

    def example_node(self, branch):
        props = {}
        if self.modal:
            props['world'] = 0
        if self.designation != None:
            props['designated'] = self.designation
        sentence = None
        a = AtomicSentence(0, 0)
        if self.operator != None:
            params = []
            arity = operarity(self.operator)
            if arity > 0:
                params.append(a)
            for i in range(arity - 1):
                params.append(params[-1].next())
            sentence = OperatedSentence(self.operator, params)
        elif self.quantifier != None:
            import examples
            sentence = examples.quantified(self.quantifier)
        if self.negated:
            if sentence == None:
                sentence = a
            sentence = OperatedSentence('Negation', [sentence])
        if sentence != None:
            props['sentence'] = sentence
        return props

class NewConstantStoppingRule(FilterNodeRule):
    """
    Default rule implementation for a one-constant instantiating rule. The rule
    will check the ``MaxConstantsTracker``. If the max constants have been
    exceeded for the branch and world, emits a quit flag using the ``QuitFlagHelper``.
    Concrete classes must implement ``get_new_nodes_for_constant()``.

    This rule inherits from ``FilterNodeRule`` and implements the
    ``get_target_for_node()`` method.
    """

    # To be implemented

    def get_new_nodes_for_constant(self, c, node, branch):
        raise NotImplementedError()

    # node rule implementation

    def __init__(self, *args, **opts):
        super().__init__(*args, **opts)
        self.add_helpers({
            'max_constants' : MaxConstantsTracker(self),
            'quit_flagger'  : QuitFlagHelper(self),
        })

    def get_target_for_node(self, node, branch):

        if not self._should_apply(branch, node.props['world']):
            if not self.quit_flagger.has_flagged(branch):
                return self._get_flag_target(branch)
            return

        c = branch.new_constant()

        target = {
            'adds': [
                self.get_new_nodes_for_constant(c, node, branch)
            ],
        }

        more_adds = self.add_to_adds(node, branch)
        if more_adds:
            target['adds'].extend(more_adds)

        return target

    def add_to_adds(self, node, branch):
        pass

    # private util

    def _should_apply(self, branch, world):
        return not self.max_constants.max_constants_exceeded(branch, world)

    def _get_flag_target(self, branch):
        return {
            'flag': True,
            'adds': [
                [
                    self.max_constants.quit_flag(branch),
                ]
            ],
        }

class AllConstantsStoppingRule(FilterNodeRule):

    # To be implemented

    def get_new_nodes_for_constant(self, c, node, branch):
        raise NotImplementedError()

    def __init__(self, *args, **opts):
        super().__init__(*args, **opts)
        self.add_timer(
            'in_get_targets_for_nodes',
            'in_node_examime'         ,
            'in_should_apply'         ,
        )
        self.add_helpers({
            'max_constants'     : MaxConstantsTracker(self),
            'applied_constants' : NodeAppliedConstants(self),
            'quit_flagger'      : QuitFlagHelper(self),
        })

    # rule implementation

    def get_targets_for_node(self, node, branch):

        with self.timers['in_should_apply']:
            should_apply = self._should_apply(node, branch)

        if not should_apply:
            if self._should_flag(branch, node.props['world']):
                return [self._get_flag_target(branch)]
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

    # private util

    def _should_apply(self, node, branch):
        if self.max_constants.max_constants_exceeded(branch, node.props['world']):
            return False
        # Apply if there are no constants on the branch
        if not branch.constants():
            return True
        # Apply if we have tracked a constant that we haven't applied to.
        if self.applied_constants.get_unapplied(node, branch):
            return True

    def _should_flag(self, branch, world):
        # Slight difference with FDE here -- using world
        return (
            self.max_constants.max_constants_exceeded(branch, world) and
            not self.quit_flagger.has_flagged(branch)
        )

    def _get_flag_target(self, branch):
        return {
            'flag': True,
            'adds': [
                [
                    self.max_constants.quit_flag(branch),
                ],
            ],
        }

def _check_is_tableau(obj):
    # Just enough for what we call.
    return (
        callable(getattr(obj, 'branch', None)) and
        #: TODO: move the Tableau impl to Rule class, then we don't need this check
        callable(getattr(obj, 'branching_complexity', None)) and
        isinstance(getattr(obj, 'history', None), list)
    )