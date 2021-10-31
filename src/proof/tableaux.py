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
# pytableaux - tableaux module
from lexicals import Argument, Constant
from utils import EventEmitter, StopWatch, get_logic, isrule
from errors import IllegalStateError, NotFoundError, TimeoutError
from events import Events
from inspect import isclass

class TableauxSystem(object):

    @classmethod
    def build_trunk(cls, tableau, argument):
        raise NotImplementedError()

    @classmethod
    def branching_complexity(cls, node):
        return 0

    @classmethod
    def add_rules(cls, tableau, opts):
        TabRules = tableau.logic.TableauxRules
        for Rule in TabRules.closure_rules:
            tableau.add_closure_rule(Rule)
        for Rules in TabRules.rule_groups:
            tableau.add_rule_group(Rules)

class Tableau(EventEmitter):
    """
    A tableau proof.
    """

    default_opts = {
        'is_group_optim'  : True,
        'is_build_models' : False,
        'build_timeout'   : None,
        'max_steps'       : None,
    }

    def __init__(self, logic, argument = None, **opts):

        super().__init__()

        #: The history of rule applications. Each application is a ``dict``
        #: with the following keys:
        #:
        #: - `rule` - The :class:`~proof.rules.Rule` instance that was applied.
        #:
        #: - `target` - A ``dict`` containing information about the elements to
        #:    which the rule was applied, as well as any auxilliary information
        #:    that may be tracked for various rules and optimizations. There is
        #:    no hard constraint on what keys are in a target, but all current
        #:    implementations at least provide a `branch` key.
        #:
        #: - `duration_ms` - The duration in milliseconds of the application,
        #:    or ``0`` if no step timer was associated.
        #:
        #: :type: list
        self.history = list()

        #: A tree structure of the tableau. This is generated after the tableau
        #: is finished. If the `build_timeout` was exceeded, the tree is `not`
        #: built.
        #:
        #: :type: dict
        self.tree = None

        # Rules
        self.__all_rules = list()
        self.__closure_rules = list()
        self.__rule_groups = list()

        # Post-build properties
        self.models = None
        self.stats = None

        # Timers
        self.__build_timer = StopWatch()
        self.__models_timer = StopWatch()
        self.__tree_timer = StopWatch()
        self.__tunk_build_timer = StopWatch()

        # Options
        self.opts = dict(self.default_opts)
        self.opts.update(opts)

        self.__branch_list = list()
        self.__open_branchset = set()
        self.__branch_dict = dict()
        self.__finished = False
        self.__premature = True
        self.__timed_out = False
        self.__trunk_built = False

        # Cache for the nodes' branching complexities
        self.__branching_complexities = dict()

        self.register_event(
            Events.AFTER_BRANCH_ADD,
            Events.AFTER_BRANCH_CLOSE,
            Events.AFTER_NODE_ADD,
            Events.AFTER_NODE_TICK,
            Events.AFTER_TRUNK_BUILD,
            Events.BEFORE_TRUNK_BUILD,
        )
        self.__branch_listeners = {
            Events.AFTER_BRANCH_CLOSE : self.__after_branch_close,
            Events.AFTER_NODE_ADD     : self.__after_node_add,
            Events.AFTER_NODE_TICK    : self.__after_node_tick,
        }

        self.__logic = self.__argument = None
        if logic != None:
            self.logic = logic
        if argument != None:
            self.argument = argument

    @property
    def id(self):
        """
        The unique object ID of the tableau.

        :type: int
        """
        return id(self)

    @property
    def logic(self):
        """
        The logic of the tableau.

        :type: module
        """
        return self.__logic

    @logic.setter
    def logic(self, logic):
        """
        Setter for ``logic`` property. Assumes building has not started.
        """
        self.__check_not_started()
        self.__logic = get_logic(logic)
        self.clear_rules()
        self.System.add_rules(self, self.opts)

    @property
    def System(self):
        """
        Convenience property for ``self.logic.TableauxSystem``. If the ``logic``
        property is ``None``, the value will be ``None``.

        :type: TableauxSystem
        """
        if self.logic == None:
            return None
        return self.logic.TableauxSystem

    @property
    def argument(self):
        """
        The argument of the tableau.

        :type: lexicals.Argument
        """
        return self.__argument

    @argument.setter
    def argument(self, argument):
        """
        Setter for ``argument`` property. If the tableau has a logic set, then
        ``build_trunk()`` is automatically called.
        """
        if not isinstance(argument, Argument):
            raise TypeError(
                "Value for 'argument' must be a {0} instance".format(Argument)
            )
        self.__check_trunk_not_built()
        self.__argument = argument
        if self.logic != None:
            self.build_trunk()
        return self

    @property
    def finished(self):
        """
        Whether the tableau is finished. A tableau is `finished` iff `any` of the
        following conditions apply:

        i. The tableau is `completed`.
        ii. The `max_steps` option is met or exceeded.
        iii. The `build_timeout` option is exceeded.
        iv. The ``finish()`` method is manually invoked.

        :type: bool
        """
        return self.__finished

    @property
    def completed(self):
        """
        Whether the tableau is completed. A tableau is `completed` iff all rules
        that can be applied have been applied.

        :type: bool
        """
        return self.finished and not self.__premature

    @property
    def premature(self):
        """
        Whether the tableau is finished prematurely. A tableau is `premature` iff
        it is `finished` but not `completed`.

        :type: bool
        """
        return self.finished and self.__premature

    @property
    def valid(self):
        """
        Whether the tableau's argument is valid (proved). A tableau with an
        argument is `valid` iff it is `completed` and it has no open branches.
        If the tableau is not completed, or it has no argument, the value will
        be ``None``.

        :type: bool
        """
        if not self.completed or self.argument == None:
            return None
        return self.open_branch_count == 0

    @property
    def invalid(self):
        """
        Whether the tableau's argument is invalid (disproved). A tableau with
        an argument is `invalid` iff it is `completed` and it has at least one
        open branch. If the tableau is not completed, or it has no argument,
        the value will be ``None``.

        :type: bool
        """
        if not self.completed or self.argument == None:
            return None
        return self.open_branch_count > 0

    @property
    def trunk_built(self):
        """
        Whether the trunk has been built.

        :type: bool
        """
        return self.__trunk_built

    @property
    def current_step(self):
        """
        The current step number. This is the number of rule applications, plus ``1``
        if the trunk is built.

        :type: int
        """
        return len(self.history) + int(self.trunk_built)

    @property
    def branch_count(self):
        """
        The current number of branches.

        :type: int
        """
        return len(self.__branch_list)

    @property
    def open_branch_count(self):
        """
        The current number of open branches.

        :type: int
        """
        return len(self.__open_branchset)

    def build(self, **opts):
        """
        Build the tableau.

        :return: self
        :rtype: Tableau
        """
        self.opts.update(opts)
        with self.__build_timer:
            while not self.finished:
                self.__check_timeout()
                self.step()
        self.finish()
        return self

    def step(self):
        """
        Find, execute, and return the next rule application. If no rule can
        be applied, the ``finish()`` method is called, and ``None`` is returned.
        If the tableau is already finished when this method is called, return
        ``False``.

        .. Internally, this calls the ``__next_step()`` method to select the
        .. next step, and, if non-empty, applies the rule and appends the entry
        .. to the history.

        :return: The history entry, or ``None`` if just finished, or ``False``
          if previously finished.
        :raises errors.IllegalStateError: if the trunk is not built.
        """
        if self.finished:
            return False
        self.__check_trunk_built()
        step = entry = None
        with StopWatch() as timer:
            if not self.__is_max_steps_exceeded():
                step = self.__next_step()
                if not step:
                    self.__premature = False
            if step:
                rule, target = step
                rule.apply(target)
                entry = StepEntry(*step, timer.elapsed())
                self.history.append(entry)
            else:
                self.finish()
        return entry

    def branches(self):
        """
        Returns an iterator for all branches, in the order they were added to
        the tableau.

        :rtype: list_iterator(Branch)
        """
        return iter(self.__branch_list)

    def open_branches(self):
        """
        Returns an iterator for the set of open branches.

        :rtype: set_iterator(Branch)
        """
        return iter(self.__open_branchset)

    def get_branch(self, branch_id):
        """
        Get a branch by its id.

        :param int id: The branch id.
        :return: The branch.
        :rtype: Branch
        :raises KeyError: if the branch is not found.
        """
        return self.__branch_dict[branch_id]

    def get_branch_at(self, index):
        """
        Get a branch by its index.

        :param int index: The branch index.
        :return: The branch.
        :rtype: Branch
        :raises IndexError: if the index does not exist.
        """
        return self.__branch_list[index]

    def branch(self, parent = None):
        """
        Create a new branch on the tableau, as a copy of ``parent``, if given.
        This calls the ``after_branch_add()`` callback on all the rules of the
        tableau.

        :param Branch parent: The parent branch, if any.
        :return: The new branch.
        :rtype: Branch
        """
        if parent == None:
            branch = Branch()
        else:
            branch = parent.copy()
            branch.parent = parent
        self.add_branch(branch)
        return branch

    def add_branch(self, branch):
        """
        Add a new branch to the tableau. Returns self.

        :param Branch branch: The branch to add.
        :return: self
        :rtype: Tableau
        """
        if branch.id in self.__branch_dict:
            raise ValueError(
                'Branch {0} already on tableau'.format(branch.id)
            )
        branch.index = len(self.__branch_list)
        self.__branch_list.append(branch)
        if not branch.closed:
            self.__open_branchset.add(branch)
        self.__branch_dict[branch.id] = branch
        self.__after_branch_add(branch)
        return self

    def get_rule(self, ref):
        """
        Get a rule instance by name, class, or instance reference. Returns first
        matching occurrence.

        :param any ref: Rule name, class, or instance reference.
        :return: The rule instance.
        :rtype: rules.Rule
        :raises errors.NotFoundError: if the rule is not found.
        """
        for rule in self.__all_rules:
            if (
                rule.__class__ == ref or
                rule.name == ref or
                rule.__class__.__name__ == ref or
                rule.__class__ == ref.__class__
            ):
                return rule
        raise NotFoundError('Rule not found for ref: {0}'.format(ref))

    def get_rule_at(self, i, n):
        return self.__rule_groups[i][n]

    def get_rule_group(self, i):
        return tuple(self.__rule_groups[i])

    def rule_groups(self):
        return (iter(group) for group in self.__rule_groups)

    def add_closure_rule(self, rule):
        """
        Add a closure rule.

        :param class rule: Rule class reference. The rule should be a subclass
          of :class:`~rules.ClosureRule`
        :return: self
        :rtype: Tableau
        """
        self.__check_not_started()
        rule = self.__create_rule(rule)
        self.__closure_rules.append(rule)
        self.__all_rules.append(rule)
        return self

    def closure_rules(self):
        """
        Returns an iterator for the list of closure rule instances.

        :rtype: list_iterator(rules.ClosureRule)
        """
        return iter(self.__closure_rules)

    def add_rule_group(self, rules):
        """
        Add a rule group.

        :param list(class) rules: List of rule class references. Each rule
          
        :return: self
        :rtype: Tableau
        """
        self.__check_not_started()
        group = list(self.__create_rule(rule) for rule in rules)
        self.__rule_groups.append(group)
        self.__all_rules.extend(group)
        return self

    def clear_rules(self):
        """
        Clear the rules. Assumes building has not started. Returns self.

        :rtype: Tableau
        """
        self.__check_not_started()
        self.__closure_rules.clear()
        self.__rule_groups.clear()
        self.__all_rules.clear()
        return self

    def build_trunk(self):
        """
        Build the trunk of the tableau. Delegates to the ``build_trunk()`` method
        of ``TableauxSystem``. This is called automatically when the
        tableau has non-empty ``argument`` and ``logic`` properties. Returns self.

        :return: self
        :rtype: Tableau
        :raises errors.IllegalStateError: if the trunk is already built.
        """
        self.__check_trunk_not_built()
        with self.__tunk_build_timer:
            self.emit(Events.BEFORE_TRUNK_BUILD, self)
            self.System.build_trunk(self, self.argument)
            self.__trunk_built = True
            self.emit(Events.AFTER_TRUNK_BUILD, self)
        return self

    def finish(self):
        """
        Mark the tableau as finished, and perform post-build tasks, including
        populating the ``tree``, ``stats``, and ``models`` properties.
        
        When using the ``build()`` or ``step()`` methods, there is never a need
        to call this method, since it is handled internally. However, this
        method *is* safe to call multiple times. If the tableau is already
        finished, it will be a no-op.

        :return: self
        :rtype: Tableau
        """
        if self.finished:
            return self

        self.__finished = True

        if self.invalid and self.opts.get('is_build_models'):
            with self.__models_timer:
                self.__build_models()

        if not self.__timed_out:
            # In case of a timeout, we do `not` build the tree in order to best
            # respect the timeout. In case of `max_steps` excess, however, we
            # `do` build the tree.
            with self.__tree_timer:
                self.tree = make_tree_structure(list(self.branches()))

        self.stats = self.__compute_stats()

        return self

    def branching_complexity(self, node):
        """
        Caching method for the logic's ``TableauxSystem.branching_complexity()``
        method. If the tableau has no logic, then ``0`` is returned.

        :param Node node: The node to evaluate.
        :return: The branching complexity.
        :rtype: int
        """
        # TODO: Consider potential optimization using hash equivalence for nodes,
        #       to avoid redundant calculations. Perhaps the TableauxSystem should
        #       provide a special branch-complexity node hashing function.
        if node.id not in self.__branching_complexities:
            if self.System == None:
                return 0
            self.__branching_complexities[node.id] = \
                self.System.branching_complexity(node)
        return self.__branching_complexities[node.id]

    def __repr__(self):
        info = dict()
        info.update({
            prop: getattr(self, prop)
            for prop in ('id', 'branch_count', 'current_step', 'finished')
        })
        info.update({
            key: value
            for key, value in {
                prop: getattr(self, prop)
                for prop in ('premature', 'valid', 'invalid', 'argument')
            }.items()
            if value
        })
        return info.__repr__()

    ## :===============================:
    ## :       Private Methods         :
    ## :===============================:

    # :-----------:
    # : Callbacks :
    # :-----------:

    def __after_branch_add(self, branch):
        if not branch.parent:
            # For corner case of an AFTER_BRANCH_ADD callback adding a node, make
            # sure we don't emit AFTER_NODE_ADD twice, so prefetch the nodes.
            nodes = branch.get_nodes()
        else:
            nodes = None

        self.emit(Events.AFTER_BRANCH_ADD, branch)

        if not branch.parent:
            for node in nodes:
                self.__after_node_add(node, branch)

        branch.add_listeners(self.__branch_listeners)

    def __after_branch_close(self, branch):
        branch.closed_step = self.current_step
        self.__open_branchset.remove(branch)
        self.emit(Events.AFTER_BRANCH_CLOSE, branch)

    def __after_node_add(self, node, branch):
        node.step = self.current_step
        self.emit(Events.AFTER_NODE_ADD, node, branch)

    def __after_node_tick(self, node, branch):
        if node.ticked_step == None or self.current_step > node.ticked_step:
            node.ticked_step = self.current_step
        self.emit(Events.AFTER_NODE_TICK, node, branch)

    # :-----------:
    # : Util      :
    # :-----------:

    def __next_step(self):
        """
        Choose the next rule step to perform. Returns the (rule, target)
        pair, or ``None``if no rule can be applied.

        This iterates over the open branches and calls ``__get_branch_application()``.
        """
        for branch in self.open_branches():
            res = self.__get_branch_application(branch)
            if res:
                return res

    def __get_branch_application(self, branch):
        """
        Find and return the next available rule application for the given open
        branch. This first checks the closure rules, then iterates over the
        rule groups. The first non-empty result is returned.
        """
        res = self.__get_group_application(branch, self.__closure_rules)
        if res:
            return res
        for rules in self.__rule_groups:
            res = self.__get_group_application(branch, rules)
            if res:
                return res

    def __get_group_application(self, branch, rules):
        """
        Find and return the next available rule application for the given open
        branch and rule group. The ``rules`` parameter is a list of rules, and
        is assumed to be either the closure rules, or one of the rule groups of
        the tableau. This calls the ``rule.get_target(branch)`` on the rules.

        If the `is_group_optim` option is `disabled`, then the first non-empty
        target returned by a rule is selected. The target is updated with the
        the following:

        - `group_score`         : None
        - `total_group_targets` : 1
        - `min_group_score`     : None
        - `is_group_optim`      : False

        If the `is_group_optim` option is `enabled`, then all non-empty targets
        collected and passed to ``__select_optim_group_application()`` to
        compute the scores and select the winner.

        :return: A (rule, target) pair, or ``None``.
        """
        results = []
        for rule in rules:
            with rule.search_timer:
                target = rule.get_target(branch)
            if target:
                if not self.opts.get('is_group_optim'):
                    target.update({
                        'group_score'         : None,
                        'total_group_targets' : 1,
                        'min_group_score'     : None,
                        'is_group_optim'      : False,
                    })
                    return (rule, target)
                results.append((rule, target))
        if results:
            return self.__select_optim_group_application(results)

    def __select_optim_group_application(self, results):
        """
        Choose the highest scoring element from given results. The ``results``
        parameter is assumed to be a non-empty list/tuple of (rule, target) pairs.

        This calls ``rule.group_score(target)`` on each element to compute the
        score. In case of a tie, the earliest element wins.

        Before the selected result is returned, the ``target`` dict is updated
        with the following:
        
        - `group_score`        : int
        - `total_group_targets`: int
        - `min_group_score`    : int
        - `is_group_optim`     : True

        :param list results: A list/tuple of (Rule, dict) pairs.
        :return: The highest scoring element.
        :rtype: tuple(rules.Rule, dict)
        """
        group_scores = [rule.group_score(target) for rule, target in results]
        max_group_score = max(group_scores)
        min_group_score = min(group_scores)
        for i in range(len(results)):
            if group_scores[i] == max_group_score:
                rule, target = results[i]
                target.update({
                    'group_score'         : max_group_score,
                    'total_group_targets' : len(results),
                    'min_group_score'     : min_group_score,
                    'is_group_optim'      : True,
                })
                return (rule, target)

    def __compute_stats(self):
        """
        Compute the stats property after the tableau is finished.
        """
        num_open = self.open_branch_count
        distinct_nodes = self.tree['distinct_nodes'] if self.tree else None
        return {
            'id'                : self.id,
            'result'            : self.__result_word(),
            'branches'          : self.branch_count,
            'open_branches'     : num_open,
            'closed_branches'   : self.branch_count - num_open,
            'rules_applied'     : len(self.history),
            'distinct_nodes'    : distinct_nodes,
            'rules_duration_ms' : sum(
                application['duration_ms']
                for application in self.history
            ),
            'build_duration_ms' : self.__build_timer.elapsed(),
            'trunk_duration_ms' : self.__tunk_build_timer.elapsed(),
            'tree_duration_ms'  : self.__tree_timer.elapsed(),
            'models_duration_ms': self.__models_timer.elapsed(),
            'rules_time_ms'     : sum(
                sum((rule.search_timer.elapsed(), rule.apply_timer.elapsed()))
                for rule in self.__all_rules
            ),
            'rules' : [
                self.__compute_rule_stats(rule)
                for rule in self.__all_rules
            ],
        }

    def __compute_rule_stats(self, rule):
        """
        Compute the stats for a rule after the tableau is finished.
        """
        return {
            'name'            : rule.name,
            'queries'         : rule.search_timer.times_started(),
            'search_time_ms'  : rule.search_timer.elapsed(),
            'search_time_avg' : rule.search_timer.elapsed_avg(),
            'apply_count'     : rule.apply_count,
            'apply_time_ms'   : rule.apply_timer.elapsed(),
            'apply_time_avg'  : rule.apply_timer.elapsed_avg(),
            'timers'          : {
                name : {
                    'duration_ms'   : timer.elapsed(),
                    'duration_avg'  : timer.elapsed_avg(),
                    'times_started' : timer.times_started(),
                }
                for name, timer in rule.timers.items()
            },
        }

    def __check_timeout(self):
        timeout = self.opts.get('build_timeout')
        if timeout == None or timeout < 0:
            return
        if self.__build_timer.elapsed() > timeout:
            self.__build_timer.stop()
            self.__timed_out = True
            self.finish()
            raise TimeoutError('Timeout of {0}ms exceeded.'.format(timeout))

    def __is_max_steps_exceeded(self):
        max_steps = self.opts.get('max_steps')
        return max_steps != None and len(self.history) >= max_steps

    def __check_trunk_built(self):
        if self.argument != None and not self.trunk_built:
            raise IllegalStateError("Trunk is not built.")

    def __check_trunk_not_built(self):
        if self.trunk_built:
            raise IllegalStateError("Trunk is already built.")

    def __check_not_started(self):
        if self.current_step > 0:
            raise IllegalStateError("Tableau is already started.")

    def __create_rule(self, rule):
        if isclass(rule):
            rule = rule(self, **self.opts)
        if not isrule(rule):
            raise TypeError('Invalid rule class: {0}'.format(rule.__class__))
        if rule.tableau is not self:
            raise ValueError('Rule {0} not assigned to this tableau.'.format(rule))
        return rule
        
    def __result_word(self):
        if self.valid:
            return 'Valid'
        if self.invalid:
            return 'Invalid'
        if self.completed:
            return 'Completed'
        return 'Unfinished'

    def __build_models(self):
        """
        Build models for the open branches.
        """
        if self.logic == None:
            return
        self.models = set()
        for branch in self.__open_branchset:
            self.__check_timeout()
            model = self.logic.Model()
            model.read_branch(branch)
            if self.argument != None:
                model.is_countermodel = model.is_countermodel_to(self.argument)
            branch.model = model
            self.models.add(model)

class Branch(EventEmitter):
    """
    Represents a tableau branch.
    """

    def __init__(self):
        super().__init__()
        # Make sure properties are copied if needed in copy()
        self.id = id(self)
        self.closed = False
        self.ticked_nodes = set()
        self.nodes = []
        self.consts = set()
        self.ws = set()
        self.preds = set()
        self.atms = set()
        self.leaf = None
        self.closed_step = None
        self.index = None
        self.model = None
        self.parent = None
        self.node_index = {
            'sentence'   : {},
            'designated' : {},
            'world'      : {},
            'world1'     : {},
            'world2'     : {},
            'w1Rw2'      : {},
        }
        self.register_event(
            Events.AFTER_BRANCH_CLOSE,
            Events.AFTER_NODE_ADD,
            Events.AFTER_NODE_TICK,
        )

    def has(self, props, ticked = None):
        """
        Check whether there is a node on the branch that matches the given properties,
        optionally filtered by ticked status.
        """
        return self.find(props, ticked=ticked) != None

    def has_access(self, *worlds):
        """
        Check whether a tuple of the given worlds is on the branch.

        This is a performant way to check typical "access" nodes on the
        branch with `world1` and `world2` properties. For more advanced
        searches, use the ``has()`` method.
        """
        return str(list(worlds)) in self.node_index['w1Rw2']

    def has_any(self, props_list, ticked = None):
        """
        Check a list of property dictionaries against the ``has()`` method. Return ``True``
        when the first match is found.
        """
        for props in props_list:
            if self.has(props, ticked=ticked):
                return True
        return False

    def has_all(self, props_list, ticked = None):
        """
        Check a list of property dictionaries against the ``has()`` method. Return ``False``
        when the first non-match is found.
        """
        for props in props_list:
            if not self.has(props, ticked=ticked):
                return False
        return True

    def find(self, props, ticked = None):
        """
        Find the first node on the branch that matches the given properties, optionally
        filtered by ticked status. Returns ``None`` if not found.
        """
        results = self.search_nodes(props, ticked=ticked, limit=1)
        if len(results):
            return results[0]
        return None

    def find_all(self, props, ticked = None):
        """
        Find all the nodes on the branch that match the given properties, optionally
        filtered by ticked status. Returns a list.
        """
        return self.search_nodes(props, ticked=ticked)

    def search_nodes(self, props, ticked = None, limit = None):
        """
        Find all the nodes on the branch that match the given properties, optionally
        filtered by ticked status, up to the limit, if given. Returns a list.
        """
        results = []
        best_haystack = self._select_index(props, ticked)
        if not best_haystack:
            return results
        for node in best_haystack:
            if limit != None and len(results) >= limit:
                break
            if ticked != None and self.is_ticked(node) != ticked:
                continue
            if node.has_props(props):
                results.append(node)
        return results

    def add(self, node):
        """
        Add a node (Node object or dict of props). Returns self.
        """
        node = self.create_node(node)
        consts = node.constants()
        self.nodes.append(node)
        self.consts.update(consts)
        self.ws.update(node.worlds())
        self.preds.update(node.predicates())
        self.atms.update(node.atomics())
        node.parent = self.leaf
        self.leaf = node

        # Add to index *before* after_node_add callback
        self.__add_to_index(node, consts)
        self.emit(Events.AFTER_NODE_ADD, node, self)

        return self

    def update(self, nodes):
        """
        Add multiple nodes. Returns self.
        """
        for node in nodes:
            self.add(node)
        return self

    def tick(self, node):
        """
        Tick a node for the branch. Returns self.
        """
        if node not in self.ticked_nodes:
            self.ticked_nodes.add(node)
            node.ticked = True
            self.emit(Events.AFTER_NODE_TICK, node, self)
        return self

    def close(self):
        """
        Close the branch. Returns self.
        """
        self.closed = True
        self.add({'is_flag': True, 'flag': 'closure'})
        self.emit(Events.AFTER_BRANCH_CLOSE, self)
        return self

    def get_nodes(self, ticked = None):
        """
        Return the nodes, optionally filtered by ticked status.
        """
        if ticked == None:
            return self.nodes
        return [node for node in self.nodes if ticked == self.is_ticked(node)]

    def is_ticked(self, node):
        """
        Whether the node is ticked relative to the branch.
        """
        return node in self.ticked_nodes

    def copy(self):
        """
        Return a copy of the branch. Event listeners are *not* copied.
        """
        branch = self.__class__()
        branch.nodes = list(self.nodes)
        branch.ticked_nodes = set(self.ticked_nodes)
        branch.consts = set(self.consts)
        branch.ws = set(self.ws)
        branch.atms = set(self.atms)
        branch.preds = set(self.preds)
        branch.leaf = self.leaf
        branch.node_index = {
            prop : {
                key : set(self.node_index[prop][key])
                for key in self.node_index[prop]
            }
            for prop in self.node_index
        }
        return branch

    def worlds(self):
        """
        Return the set of worlds that appear on the branch.
        """
        return self.ws

    def new_world(self):
        """
        Return a new world that does not appear on the branch.
        """
        worlds = self.worlds()
        if not len(worlds):
            return 0
        return max(worlds) + 1

    def predicates(self):
        """
        Return the set of predicates that appear on the branch.
        """
        return self.preds

    def atomics(self):
        """
        Return the set of atomics that appear on the branch.
        """
        return self.atms

    def constants(self):
        """
        Return the set of constants that appear on the branch.
        """
        return self.consts

    def new_constant(self):
        """
        Return a new constant that does not appear on the branch.
        """
        if not self.consts:
            return Constant(0, 0)
        maxidx = Constant.MAXI
        coordset = set(c.coords for c in self.consts)
        index, sub = 0, 0
        while (index, sub) in coordset:
            index += 1
            if index > maxidx:
                index, sub = 0, sub + 1
        return Constant(index, sub)

    def constants_or_new(self):
        """
        Return a tuple ``(constants, is_new)``, where ``constants`` is either the
        branch constants, or, if no constants are on the branch, a singleton
        containing a new constant, and ``is_new`` indicates whether it is
        a new constant.
        """
        if self.constants():
            return (self.constants(), False)
        return ({self.new_constant()}, True)

    def origin(self):
        """
        Traverse up through the ``parent`` property.
        """
        origin = self
        while origin.parent != None:
            origin = origin.parent
        return origin

    def create_node(self, props):
        """
        Create a new node. Does not add it to the branch. If ``props`` is a
        node instance, return it. Otherwise create a new node from the props
        and return it.
        """
        if isinstance(props, Node):
            return props
        return Node(props=props)

    def __add_to_index(self, node, consts):
        for prop in self.node_index:
            key = None
            if prop == 'w1Rw2':
                if 'world1' in node.props and 'world2' in node.props:
                    key = str([node.props['world1'], node.props['world2']])
            elif prop in node.props:
                key = str(node.props[prop])
            if key:
                if key not in self.node_index[prop]:
                    self.node_index[prop][key] = set()
                self.node_index[prop][key].add(node)

    def _select_index(self, props, ticked):
        # TODO: Mangle with __, but we are using this in a test.
        best_index = None
        for prop in self.node_index:
            key = None
            if prop == 'w1Rw2':
                if 'world1' in props and 'world2' in props:
                    key = str([props['world1'], props['world2']])
            elif prop in props:
                key = str(props[prop])
            if key != None:
                if key not in self.node_index[prop]:
                    return False
                index = self.node_index[prop][key]
                if best_index == None or len(index) < len(best_index):
                    best_index = index
                # we could do no better
                if len(best_index) == 1:
                    break
        if not best_index:
            if ticked:
                best_index = self.ticked_nodes
            else:
                best_index = self.nodes
        return best_index

    def __repr__(self):
        return {
            'id'     : self.id,
            'nodes'  : len(self.nodes),
            'leaf'   : self.leaf.id if self.leaf else None,
            'closed' : self.closed,
        }.__repr__()

class Node(object):
    """
    A tableau node.
    """

    def __init__(self, props = {}):
        #: A dictionary of properties for the node.
        self.props = {
            'world'      : None,
            'designated' : None,
        }
        self.props.update(props)
        self.ticked = False
        self.parent = None
        self.step = None
        self.ticked_step = None
        self.id = id(self)

    @property
    def is_closure(self):
        return self.props.get('flag') == 'closure'

    def has(self, *names):
        """
        Whether the node has a non-``None`` property of all the given names.
        """
        for name in names:
            if self.props.get(name) == None:
                return False
        return True

    def has_any(self, *names):
        """
        Whether the node has a non-``None`` property of any of the given names.
        """
        for name in names:
            if self.props.get(name) != None:
                return True
        return False

    def has_props(self, props):
        """
        Whether the node properties match all those give in ``props`` (dict).
        """
        for prop in props:
            if prop not in self.props or not props[prop] == self.props[prop]:
                return False
        return True

    def worlds(self):
        """
        Return the set of worlds referenced in the node properties. This combines
        the properties `world`, `world1`, `world2`, and `worlds`.
        """
        worlds = set()
        if self.has('world'):
            worlds.add(self.props['world'])
        if self.has('world1'):
            worlds.add(self.props['world1'])
        if self.has('world2'):
            worlds.add(self.props['world2'])
        if self.has('worlds'):
            worlds.update(self.props['worlds'])
        return worlds

    def atomics(self):
        """
        Return the set of atomics (recursive) of the node's `sentence`
        property, if any. If the node does not have a sentence, return
        an empty set.
        """
        if self.has('sentence'):
            return self.props['sentence'].atomics()
        return set()

    def constants(self):
        """
        Return the set of constants (recursive) of the node's `sentence`
        property, if any. If the node does not have a sentence, return
        the empty set.
        """
        if self.has('sentence'):
            return self.props['sentence'].constants()
        return set()

    def predicates(self):
        """
        Return the set of predicates (recursive) of the node's `sentence`
        property, if any. If the node does not have a sentence, return
        the empty set.
        """
        if self.has('sentence'):
            return self.props['sentence'].predicates()
        return set()

    def __repr__(self):
        return {
            'id'     : self.id,
            'props'  : self.props,
            'ticked' : self.ticked,
            'step'   : self.step,
            'parent' : self.parent.id if self.parent else None,
        }.__repr__()

class StepEntry(object):

    def __init__(self, *entry):
        if len(entry) < 3:
            raise TypeError('Expecting more than {} arguments'.format(len(entry)))
        self.__entry = entry

    @property
    def rule(self):
        return self.__entry[0]

    @property
    def target(self):
        return self.__entry[1]

    @property
    def duration_ms(self):
        return self.__entry[2]

    @property
    def entry(self):
        return self.__entry

    def __getitem__(self, item):
        return getattr(self, item)

def make_tree_structure(branches, node_depth=0, track=None):
    is_root = track == None
    if track == None:
        track = {
            'pos'            : 0,
            'depth'          : 0,
            'distinct_nodes' : 0,
        }
    track['pos'] += 1
    s = {
        # the nodes on this structure.
        'nodes'                 : [],
        # this child structures.
        'children'              : [],
        # whether this is a terminal (childless) structure.
        'leaf'                  : False,
        # whether this is a terminal structure that is closed.
        'closed'                : False,
        # whether this is a terminal structure that is open.
        'open'                  : False,
        # the pre-ordered tree left value.
        'left'                  : track['pos'],
        # the pre-ordered tree right value.
        'right'                 : None,
        # the total node count of all descendants.
        'descendant_node_count' : 0,
        # the node count plus descendant node count.
        'structure_node_count'  : 0,
        # the depth of this structure (ancestor structure count).
        'depth'                 : track['depth'],
        # whether this structure or a descendant is open.
        'has_open'              : False,
        # whether this structure or a descendant is closed.
        'has_closed'            : False,
        # if closed, the step number at which it closed.
        'closed_step'           : None,
        # the step number at which this structure first appears.
        'step'                  : None,
        # the number of descendant terminal structures, or 1.
        'width'                 : 0,
        # 0.5x the width of the first child structure, plus 0.5x the
        # width of the last child structure (if distinct from the first),
        # plus the sum of the widths of the other (distinct) children.
        'balanced_line_width'   : None,
        # 0.5x the width of the first child structure divided by the
        # width of this structure.
        'balanced_line_margin'  : None,
        # the branch id, only set for leaves
        'branch_id'             : None,
        # the model id, if exists, only set for leaves
        'model_id'              : None,
        # whether this is the one and only branch
        'is_only_branch'        : False,
    }
    s['id'] = id(s)
    while True:
        relevant = [branch for branch in branches if len(branch.nodes) > node_depth]
        for branch in relevant:
            if branch.closed:
                s['has_closed'] = True
            else:
                s['has_open'] = True
            if s['has_open'] and s['has_closed']:
                break
        distinct_nodes = []
        distinct_nodeset = set()
        for branch in relevant:
            node = branch.nodes[node_depth]
            if node not in distinct_nodeset:
                distinct_nodeset.add(node)
                distinct_nodes.append(node)
        if len(distinct_nodes) == 1:
            node = relevant[0].nodes[node_depth]
            s['nodes'].append(node)
            if s['step'] == None or s['step'] > node.step:
                s['step'] = node.step
            node_depth += 1
            continue
        break
    track['distinct_nodes'] += len(s['nodes'])
    if len(branches) == 1:
        branch = branches[0]
        s['closed'] = branch.closed
        s['open'] = not branch.closed
        if s['closed']:
            s['closed_step'] = branch.closed_step
            s['has_closed'] = True
        else:
            s['has_open'] = True
        s['width'] = 1
        s['leaf'] = True
        s['branch_id'] = branch.id
        if branch.model != None:
            s['model_id'] = branch.model.id
        if track['depth'] == 0:
            s['is_only_branch'] = True
    else:
        inbetween_widths = 0
        track['depth'] += 1
        first_width = 0
        last_width = 0
        for i, node in enumerate(distinct_nodes):

            child_branches = [
                branch for branch in branches
                if branch.nodes[node_depth] == node
            ]

            # recurse
            child = make_tree_structure(child_branches, node_depth, track)

            s['descendant_node_count'] = len(child['nodes']) + child['descendant_node_count']
            s['width'] += child['width']
            s['children'].append(child)
            if i == 0:
                s['branch_step'] = child['step']
                first_width = float(child['width']) / 2
            elif i == len(distinct_nodes) - 1:
                last_width = float(child['width']) / 2
            else:
                inbetween_widths += child['width']
            s['branch_step'] = min(s['branch_step'], child['step'])
        if s['width'] > 0:
            s['balanced_line_width'] = float(first_width + last_width + inbetween_widths) / s['width']
            s['balanced_line_margin'] = first_width / s['width']
        else:
            s['balanced_line_width'] = 0
            s['balanced_line_margin'] = 0
        track['depth'] -= 1
    s['structure_node_count'] = s['descendant_node_count'] + len(s['nodes'])
    track['pos'] += 1
    s['right'] = track['pos']
    if is_root:
        s['distinct_nodes'] = track['distinct_nodes']
    return s

# def _check_is_rule(obj):
#     """
#     Checks if an object is a rule instance.
#     """
#     if obj.__class__ in _check_is_rule.classes:
#         return True
#     if not (
#         hasattr(obj, 'name') and
#         callable(getattr(obj, 'get_target', None)) and
#         callable(getattr(obj, 'apply', None)) and
#         isinstance(getattr(obj, 'tableau', None), Tableau) and
#         isinstance(getattr(obj, 'apply_count', None), int) and
#         isinstance(getattr(obj, 'timers', None), dict) and
#         isinstance(getattr(obj, 'apply_timer', None), StopWatch) and
#         isinstance(getattr(obj, 'search_timer', None), StopWatch) and
#         True
#     ):
#         return False
#     _check_is_rule.classes.add(obj.__class__)
#     return True
# _check_is_rule.classes = set()