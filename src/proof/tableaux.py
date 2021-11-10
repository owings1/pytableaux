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
from utils import LinkOrderSet, Kwobj, StopWatch, cat, get_logic, \
    EmptySet, typecheck, dictrepr, Decorators, kwrepr, orepr
from errors import DuplicateKeyError, IllegalStateError, NotFoundError, TimeoutError
from events import Events, EventEmitter
from inspect import isclass
from itertools import chain, islice
from .common import Node, StepEntry

lazyget = Decorators.lazyget
setonce = Decorators.setonce
checkstate = Decorators.checkstate

class TableauxSystem(object):

    @classmethod
    def build_trunk(cls, tableau, argument):
        raise NotImplementedError()

    @classmethod
    def branching_complexity(cls, node):
        return 0

    @classmethod
    def add_rules(cls, logic, rules):
        Rules = logic.TableauxRules
        rules.groups.add(Rules.closure_rules, 'closure')
        rules.groups.extend(Rules.rule_groups)

def TabRules():

    writes = checkstate(locked = False)
    def prot(self, name, *_): raise AttributeError(name)

    class Common(object):

        def __init__(self, tableau):
            self.ruleindex = {}
            self.groupindex = {}
            self.stat = Kwobj(len = 0, locked = False)
            self.tab = tableau
            def lock(*_): self.stat.locked = True
            tableau.once(Events.AFTER_BRANCH_ADD, lock)
            self.__setattr__ = self.__delattr__ = prot
        

    class Base(object):
        @property
        def locked(self):
            return self.__c.stat.locked
        @property
        def tab(self):
            return self.__c.tab
        @property
        def logic(self):
            return self.__c.tab.logic
        def __init__(self, common):
            self.__c = common
            self.__setattr__ = prot
        def __delattr__(self, name):
            if name.startswith('_'):
                raise AttributeError(name)
            return super().__delattr__(name)

    class TabRules(Base):

        @property
        def groups(self):
            return self.__groups

        @writes
        def append(self, rule):
            self.groups.create().append(rule)
        add = append

        @writes
        def extend(self, rules):
            self.groups.append(rules)

        @writes
        def clear(self):
            self.groups.clear()
            self.__c.ruleindex.clear()

        def get(self, ref, *d):
            rindex = self.__c.ruleindex
            if ref in rindex:
                return rindex[ref]
            if isclass(ref) and ref.__name__ in rindex:
                return rindex[ref.__name__]
            if ref.__class__.__name__ in rindex:
                return rindex[ref.__class__.__name__]
            if len(d):
                return d[0]
            raise NotFoundError(ref)

        def __init__(self, tableau):
            common = self.__c = Common(tableau)
            self.__groups = RuleGroups(common)
            super().__init__(common)

        def __len__(self):
            return self.__c.stat.len

        def __iter__(self):
            return chain.from_iterable(self.groups)

        def __contains__(self, item):
            return item in self.__c.ruleindex

        def __getattr__(self, name):
            c = self.__c
            if name in c.groupindex:
                return c.groupindex[name]
            if name in c.ruleindex:
                return c.ruleindex[name]
            raise AttributeError(name)

        def __dir__(self):
            return [rule.__class__.__name__ for rule in self]

        def __repr__(self):
            return orepr(self,
                logic  = self.logic,
                groups = len(self.groups),
                rules  = len(self),
            )

    class RuleGroups(Base):

        @writes
        def create(self, name = None):
            c = self.__c
            if name != None:
                if name in c.groupindex or name in c.ruleindex:
                    raise DuplicateKeyError(name)
            group = RuleGroup(name, c)
            self.__groups.append(group)
            if name != None:
                c.groupindex[name] = group
            return group

        @writes
        def append(self, rules, name = None):
            if name == None:
                name = getattr(rules, 'name', None)
            self.create(name).extend(rules)
        add = append

        @writes
        def extend(self, groups):
            for rules in groups:
                self.add(rules)

        @writes
        def clear(self):
            g = self.__groups
            for group in g:
                group.clear()
            g.clear()
            self.__c.groupindex.clear()

        @property
        def names(self):
            return list(filter(bool, (group.name for group in self)))

        def __init__(self, common):
            self.__c = common
            self.__groups = []
            super().__init__(common)
    
        def __iter__(self):
            return iter(self.__groups)

        def __len__(self):
            return len(self.__groups)

        def __getitem__(self, i):
            return self.__groups[i]

        def __getattr__(self, name):
            idx = self.__c.groupindex
            if name in idx:
                return idx[name]
            raise AttributeError(name)

        def __dir__(self):
            return self.names

        def __repr__(self):
            return orepr(self,
                logic = self.logic,
                groups = len(self),
                rules = self.__c.stat.len
            )

    def newrule(arg, tab):
        cls = arg
        if not isclass(cls):
            cls = cls.__class__
        try:
            return cls(tab, **tab.opts)
        except:
            raise TypeError(
                'Failed to instantiate rule: %s (%s, logic: %s)' %
                (arg, type(arg), tab.logic.name if tab.logic else None)
            )

    class RuleGroup(Base):

        def lenchange(method):
            def update(self, *args, **kw):
                mypre = len(self)
                try:
                    return method(self, *args, **kw)
                finally:
                    self.__c.stat.len += len(self) - mypre
            return update

        @property
        def name(self):
            return self.__name

        @writes
        @lenchange
        def append(self, rule):
            c = self.__c
            rule = newrule(rule, self.tab)
            cls = rule.__class__
            clsname = cls.__name__
            if clsname in c.ruleindex or clsname in c.groupindex:
                raise DuplicateKeyError(clsname)
            self.__rules.append(rule)
            c.ruleindex[clsname] = self.__index[rule] = rule
        add = append

        @writes
        def extend(self, rules):
            for rule in rules:
                self.add(rule)

        @writes
        @lenchange
        def clear(self):
            for rule in self.__rules:
                del(self.__c.ruleindex[rule.__class__.__name__])
            self.__rules.clear()

        def __init__(self, name, common):
            self.__name = name
            self.__c = common
            self.__rules = []
            self.__index = {}
            super().__init__(common)

        def __iter__(self):
            return iter(self.__rules)

        def __len__(self):
            return len(self.__rules)

        def __contains__(self, item):
            return item in self.__index

        def __getitem__(self, i):
            return self.__rules[i]

        def __getattr__(self, name):
            if name in self.__index:
                return self.__index[name]
            raise AttributeError(name)

        def __repr__(self):
            return orepr(self, name = self.name, rules = len(self))

    return TabRules

class Tableau(EventEmitter):
    """
    A tableau proof.
    """
    TabRules = TabRules()
    opts = {
        'is_group_optim'  : True,
        'is_build_models' : False,
        'build_timeout'   : None,
        'max_steps'       : None,
    }

    def __init__(self, logic = None, argument = None, **opts):

        super().__init__(
            Events.AFTER_BRANCH_ADD,
            Events.AFTER_BRANCH_CLOSE,
            Events.AFTER_NODE_ADD,
            Events.AFTER_NODE_TICK,
            Events.AFTER_TRUNK_BUILD,
            Events.BEFORE_TRUNK_BUILD,
        )

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

        # Post-build properties

        #: A tree structure of the tableau. This is generated after the tableau
        #: is finished. If the `build_timeout` was exceeded, the tree is `not`
        #: built.
        #:
        #: :type: dict
        self.tree = None
        self.models = None
        self.stats = None

        # Timers
        self.__build_timer = StopWatch()
        self.__models_timer = StopWatch()
        self.__tree_timer = StopWatch()
        self.__tunk_build_timer = StopWatch()

        # Options
        self.opts = self.opts | opts

        self.__branch_list = list()
        self.__trunks = list()
        self.__open_linkset = LinkOrderSet()
        self.__branch_dict = dict()
        self.__finished = False
        self.__premature = True
        self.__timed_out = False
        self.__trunk_built = False

        # Cache for the nodes' branching complexities
        self.__branching_complexities = dict()

        self.__branch_listeners = {
            Events.AFTER_BRANCH_CLOSE : self.__after_branch_close,
            Events.AFTER_NODE_ADD     : self.__after_node_add,
            Events.AFTER_NODE_TICK    : self.__after_node_tick,
        }

        # Rules
        self.__rules = self.TabRules(self)

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
        self.rules.clear()
        self.System.add_rules(self.logic, self.rules)
        if self.argument != None:
            self.build_trunk()

    @property
    def rules(self):
        return self.__rules

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
        typecheck(argument, Argument, 'argument')
        self.__check_trunk_not_built()
        self.__argument = argument
        if self.logic != None:
            self.build_trunk()

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
        return len(self.open) == 0

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
        return len(self.open) > 0

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
    def open(self):
        """
        View of the open branches.
        """
        return self.__open_linkset.view
        return self.__open_view

    def build(self):
        """
        Build the tableau.

        :return: self
        :rtype: Tableau
        """
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

        .. Internally, this calls the ``next_step()`` method to select the
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
                step = self.next_step()
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
            branch = parent.copy(parent = parent)
        self.add(branch)
        return branch

    def add(self, branch):
        """
        Add a new branch to the tableau. Returns self.

        :param Branch branch: The branch to add.
        :return: self
        :rtype: Tableau
        """
        if branch in self:
            raise ValueError(
                'Branch %s already on tableau' % branch.id
            )
        parent = branch.parent
        if parent != None and parent not in self:
            if not isinstance(Branch, parent):
                raise TypeError('Expecting %s, got %s' % (Branch, type(parent)))
        index = len(self)
        self.__branch_list.append(branch)
        if not branch.closed:
            self.__open_linkset.add(branch)
        if not branch.parent:
            self.__trunks.append(branch)
        self.__branch_dict[branch] = {
            'index'  : index,
            'parent' : parent,
            'branch' : branch,
        }
        self.__after_branch_add(branch)
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
                self.tree = make_tree_structure(list(self))

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
        if node not in self.__branching_complexities:
            if self.System == None:
                return 0
            self.__branching_complexities[node] = \
                self.System.branching_complexity(node)
        return self.__branching_complexities[node]

    def __getitem__(self, index):
        return self.__branch_list[index]

    def __len__(self):
        return len(self.__branch_list)

    def __iter__(self):
        return iter(self.__branch_list)

    def __contains__(self, branch):
        return branch in self.__branch_dict

    def __repr__(self):
        return dictrepr({
            self.__class__.__name__: self.id,
            'logic': (self.logic and self.logic.name),
            'len'  : len(self),
            'open' : len(self.open),
            'step' : self.current_step,
            'finished' : self.finished,
        } | {
            key: value
            for key, value in {
                prop: getattr(self, prop)
                for prop in ('premature', 'valid', 'invalid',)
            }.items()
            if self.finished and value
        } | (
            {'argument': self.argument}
            if self.argument else {}
        ))

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
            nodes = list(branch)
        else:
            nodes = None

        self.emit(Events.AFTER_BRANCH_ADD, branch)

        if not branch.parent:
            for node in nodes:
                self.__after_node_add(node, branch)

        branch.on(self.__branch_listeners)

    def __after_branch_close(self, branch):
        branch.closed_step = self.current_step
        self.__open_linkset.remove(branch)
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

    def next_step(self):
        """
        Choose the next rule step to perform. Returns the (rule, target)
        pair, or ``None``if no rule can be applied.

        This iterates over the open branches and calls ``__get_branch_application()``.
        """
        for branch in self.open:
            res = self.__get_branch_application(branch)
            if res:
                return res

    def __get_branch_application(self, branch):
        """
        Find and return the next available rule application for the given open
        branch.
        """
        for group in self.rules.groups:
            res = self.__get_group_application(branch, group)
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
        for i, (rule, target) in enumerate(results):
            if group_scores[i] == max_group_score:
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
        distinct_nodes = self.tree['distinct_nodes'] if self.tree else None
        return {
            'id'                : self.id,
            'result'            : self.__result_word(),
            'branches'          : len(self),
            'open_branches'     : len(self.open),
            'closed_branches'   : len(self) - len(self.open),
            'rules_applied'     : len(self.history),
            'distinct_nodes'    : distinct_nodes,
            'rules_duration_ms' : sum(
                step.duration_ms
                for step in self.history
            ),
            'build_duration_ms' : self.__build_timer.elapsed(),
            'trunk_duration_ms' : self.__tunk_build_timer.elapsed(),
            'tree_duration_ms'  : self.__tree_timer.elapsed(),
            'models_duration_ms': self.__models_timer.elapsed(),
            'rules_time_ms'     : sum(
                sum((rule.search_timer.elapsed(), rule.apply_timer.elapsed()))
                for rule in self.rules
            ),
            'rules' : [
                self.__compute_rule_stats(rule)
                for rule in self.rules
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
        for branch in self.open:
            self.__check_timeout()
            model = self.logic.Model()
            model.read_branch(branch)
            if self.argument != None:
                model.is_countermodel = model.is_countermodel_to(self.argument)
            branch.model = model
            self.models.add(model)
TabRules = None

class Branch(EventEmitter):
    """
    Represents a tableau branch.
    """

    def __init__(self, parent = None):
        super().__init__(
            Events.AFTER_BRANCH_CLOSE,
            Events.AFTER_NODE_ADD,
            Events.AFTER_NODE_TICK,
        )
        # Make sure properties are copied if needed in copy()
        
        self.__parent = parent
        self.__closed = False

        self.__nodes = []
        self.__nodeset = set()
        self.__ticked = set()

        self.__worlds = set()
        self.__nextworld = 0
        self.__constants = set()
        self.__nextconst = Constant.first()
        self.__pidx = {
            'sentence'   : {},
            'designated' : {},
            'world'      : {},
            'world1'     : {},
            'world2'     : {},
            'w1Rw2'      : {},
        }

        self.__closed_step = None
        self.__model = None

    @property
    def id(self):
        return id(self)

    @property
    def parent(self):
        return self.__parent

    @property
    def origin(self):
        return self if self.parent == None else self.parent.origin

    @property
    def closed(self):
        return self.__closed

    @property
    def leaf(self):
        return self[-1] if len(self) else None

    @property
    def closed_step(self):
        return self.__closed_step

    @closed_step.setter
    @setonce
    def closed_step(self, n):
        self.__closed_step = n

    @property
    def model(self):
        return self.__model

    @model.setter
    @setonce
    def model(self, model):
        self.__model = model

    @property
    def world_count(self):
        return len(self.__worlds)

    @property
    def constants_count(self):
        return len(self.__constants)

    @property
    def next_constant(self):
        # TODO: WIP
        return self.__nextconst

    @property
    def next_world(self):
        """
        Return a new world that does not appear on the branch.
        """
        return self.__nextworld

    def has(self, props, ticked = None):
        """
        Check whether there is a node on the branch that matches the given properties,
        optionally filtered by ticked status.
        """
        return self.find(props, ticked = ticked) != None

    def has_access(self, w1, w2):
        """
        Check whether a tuple of the given worlds is on the branch.

        This is a performant way to check typical "access" nodes on the
        branch with `world1` and `world2` properties. For more advanced
        searches, use the ``has()`` method.
        """
        return (w1, w2) in self.__pidx['w1Rw2']

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
        if results:
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
        best_haystack = self.__select_index(props, ticked)
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

    def append(self, node):
        """
        Append a node (Node object or dict of props). Returns self.
        """
        node = Node(node, parent = self.leaf)
        self.__nodes.append(node)
        self.__nodeset.add(node)
        s = node.get('sentence')
        if s:
            if s.constants:
                if self.__nextconst in s.constants:
                    # TODO: new_constant() is still a prettier result, since it
                    #       finds the mimimum available by searching for gaps.
                    self.__nextconst = max(s.constants).next()
                self.__constants.update(s.constants)
        if node.worlds:
            maxworld = max(node.worlds)
            if maxworld >= self.__nextworld:
                self.__nextworld = maxworld + 1
            self.__worlds.update(node.worlds)

        # Add to index *before* after_node_add callback
        self.__add_to_index(node)
        self.emit(Events.AFTER_NODE_ADD, node, self)
        return self
    add = append

    def extend(self, nodes):
        """
        Add multiple nodes. Returns self.
        """
        for node in nodes:
            self.append(node)
        return self

    def tick(self, *nodes):
        """
        Tick a node for the branch. Returns self.
        """
        for node in nodes:
            if not self.is_ticked(node):
                self.__ticked.add(node)
                node.ticked = True
                self.emit(Events.AFTER_NODE_TICK, node, self)
        return self

    def close(self):
        """
        Close the branch. Returns self.
        """
        if not self.closed:
            self.__closed = True
            self.append({'is_flag': True, 'flag': 'closure'})
            self.emit(Events.AFTER_BRANCH_CLOSE, self)
        return self

    def is_ticked(self, node):
        """
        Whether the node is ticked relative to the branch.
        """
        return node in self.__ticked

    def copy(self, parent = None):
        """
        Return a copy of the branch. Event listeners are *not* copied.
        Parent is not copied, but can be explicitly set.
        """
        branch = self.__class__(parent = parent)
        branch.__nodes = list(self.__nodes)
        branch.__nodeset = set(self.__nodeset)
        branch.__ticked = set(self.__ticked)
        branch.__constants = set(self.__constants)
        branch.__nextconst = self.__nextconst
        branch.__worlds = set(self.__worlds)
        branch.__nextworld = self.__nextworld
        branch.__pidx = {
            prop : {
                key : set(self.__pidx[prop][key])
                for key in self.__pidx[prop]
            }
            for prop in self.__pidx
        }
        return branch

    def constants(self):
        """
        Return the set of constants that appear on the branch.
        """
        return self.__constants

    def new_constant(self):
        """
        Return a new constant that does not appear on the branch.
        """
        if not self.__constants:
            return Constant.first()
        maxidx = Constant.TYPE.maxi
        coordset = set(c.coords for c in self.__constants)
        index, sub = 0, 0
        while (index, sub) in coordset:
            index += 1
            if index > maxidx:
                index, sub = 0, sub + 1
        return Constant((index, sub))

    def __add_to_index(self, node):
        for prop in self.__pidx:
            val = None
            found = False
            if prop == 'w1Rw2':
                if node.has('world1', 'world2'):
                    val = (node['world1'], node['world2'])
                    found = True
            elif prop in node:
                val = node[prop]
                found = True
            if found:
                if val not in self.__pidx[prop]:
                    self.__pidx[prop][val] = set()
                self.__pidx[prop][val].add(node)

    def __select_index(self, props, ticked):
        best_index = None
        for prop in self.__pidx:
            val = None
            found = False
            if prop == 'w1Rw2':
                if 'world1' in props and 'world2' in props:
                    val = (props['world1'], props['world2'])
                    found = True
            elif prop in props:
                val = props[prop]
                found = True
            if found:
                if val not in self.__pidx[prop]:
                    return False
                index = self.__pidx[prop][val]
                if best_index == None or len(index) < len(best_index):
                    best_index = index
                # we could do no better
                if len(best_index) == 1:
                    break
        if not best_index:
            if ticked:
                best_index = self.__ticked
            else:
                best_index = self
        return best_index

    def __eq__(self, other):
        return isinstance(other, self.__class__) and self.id == other.id

    def __ne__(self, other):
        return not (isinstance(other, self.__class__) and self.id == other.id)

    def __hash__(self):
        return hash(self.id)

    def __getitem__(self, key):
        return self.__nodes[key]

    def __len__(self):
        return len(self.__nodes)

    def __iter__(self):
        return iter(self.__nodes)

    def __copy__(self):
        return self.copy()

    def __contains__(self, node):
        return node in self.__nodeset

    def __repr__(self):

        return orepr(self, 
            clsname  = self.id,
            nodes  = len(self),
            leaf   = self.leaf.id if self.leaf else None,
            closed = self.closed,
        )



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
        relevant = [branch for branch in branches if len(branch) > node_depth]
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
            node = branch[node_depth]
            if node not in distinct_nodeset:
                distinct_nodeset.add(node)
                distinct_nodes.append(node)
        if len(distinct_nodes) == 1:
            node = relevant[0][node_depth]
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
                if branch[node_depth] == node
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


