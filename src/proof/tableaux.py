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
from lexicals import Argument, Constant, Sentence
from utils import LinkOrderSet, Kwobj, StopWatch, cat, get_logic, \
    EmptySet, typecheck, Decorators, orepr
from errors import DuplicateKeyError, IllegalStateError, NotFoundError, TimeoutError
from events import Events, EventEmitter
from inspect import isclass
from itertools import chain, islice
from .common import Branch, Node, NodeType, Target
from past.builtins import basestring
from enum import auto, Enum, Flag
from types import ModuleType
from typing import Any, Callable, Collection, Iterator, Iterable, NamedTuple, Union, final

LogicRef = Union[ModuleType, str]

class RuleMeta(type):
    def __new__(cls, clsname, bases, attrs, **kw):
        for attr, value in attrs.items():
            try:
                if attr == 'Helpers':
                    if not isinstance(value, tuple):
                        raise TypeError()
                    clsset = set()
                    nameset = set()                
                    for item in value:
                        if not isinstance (item, tuple):
                            raise TypeError()
                        if len(item) != 2:
                            raise TypeError()
                        hattr, hcls = item
                        if hattr != None and not isinstance(hattr, basestring):
                            raise TypeError()
                        if not isinstance(hcls, type):
                            raise TypeError()
                        if hattr != None and hattr in nameset:
                            raise TypeError()
                        if hcls in clsset:
                            raise TypeError()
            except TypeError:
                raise TypeError('Invalid %s attribute for class %s' % (attr, clsname))
        rulecls = super().__new__(cls, clsname, bases, attrs, **kw)
        return rulecls

class Rule(EventEmitter, metaclass = RuleMeta):
    class HelperInfo(NamedTuple):
        cls  : type
        inst : object
        attr : str

    RuleEvents = (
        Events.AFTER_APPLY,
        Events.BEFORE_APPLY,
    )
    DefaultHelperRuleEventMethods = (
        (Events.AFTER_APPLY  , 'after_apply'),
        (Events.BEFORE_APPLY , 'before_apply'),
    )
    DefaultHelperTabEventMethods = (
        (Events.AFTER_BRANCH_ADD   , 'after_branch_add'),
        (Events.AFTER_BRANCH_CLOSE , 'after_branch_close'),
        (Events.AFTER_NODE_ADD     , 'after_node_add'),
        (Events.AFTER_NODE_TICK    , 'after_node_tick'),
        (Events.AFTER_TRUNK_BUILD  , 'after_trunk_build'),
        (Events.BEFORE_TRUNK_BUILD , 'before_trunk_build'),
    )
class KEY(Enum):
    FLAGS       = auto()
    STEP_ADDED  = auto()
    STEP_TICKED = auto()
    STEP_CLOSED = auto()
    INDEX       = auto()
    PARENT      = auto()
    NODES       = auto()

class FLAG(Flag):
    NONE   = 0
    TICKED = 1
    CLOSED = 2
    PREMATURE   = 4
    FINISHED    = 8
    TIMED_OUT   = 16
    TRUNK_BUILT = 32

class Tableau(EventEmitter):

    class RuleTarget(NamedTuple):
        rule   : Rule
        target : Target

    class StepEntry(NamedTuple):
        rule   : Rule
        target : Target
        duration_ms: int

    TableauEvents = (
        Events.AFTER_BRANCH_ADD,
        Events.AFTER_BRANCH_CLOSE,
        Events.AFTER_NODE_ADD,
        Events.AFTER_NODE_TICK,
        Events.AFTER_TRUNK_BUILD,
        Events.BEFORE_TRUNK_BUILD,
    )
    class NodeStat(dict):

        def __init__(self):
            super().__init__()
            self.update({
                KEY.FLAGS       : FLAG.NONE,
                KEY.STEP_ADDED  : FLAG.NONE,
                KEY.STEP_TICKED : None,
            })

    class BranchStat(dict):

        def __init__(self):
            super().__init__()
            self.update({
                KEY.FLAGS       : FLAG.NONE,
                KEY.STEP_ADDED  : FLAG.NONE,
                KEY.STEP_CLOSED : FLAG.NONE,
                KEY.INDEX       : None,
                KEY.PARENT      : None,
                KEY.NODES       : {},
            })

        def node(self, node: Node) -> dict:
            try:
                return self[KEY.NODES][node]
            except KeyError:
                self[KEY.NODES][node] = Tableau.NodeStat()
            return self[KEY.NODES][node]

        def view(self) -> dict:
            return {
                k: self[k]
                for k in self
                if k in KEY and 
                k not in (KEY.NODES,)
            }

class Rule(Rule):
    """
    Base class for a Tableau rule.
    """

    Helpers = tuple()
    Timers = tuple()

    branch_level = 1

    opts = {'is_rank_optim': True}

    def __init__(self, tableau: Tableau, **opts):
        if not isinstance(tableau, Tableau):
            raise TypeError(tableau.__class__)
        super().__init__(*Rule.RuleEvents)

        self.search_timer: StopWatch = StopWatch()
        self.apply_timer: StopWatch = StopWatch()
        self.timers: dict[str, StopWatch] = {}

        self.opts = self.opts | opts

        self.helpers = {}
        self.__apply_count = 0
        self.__helpers = []
        self.__tableau = tableau

        for name, helper in self.Helpers:
            self.add_helper(helper, name)
        self.add_timer(*self.Timers)

    @final
    @property
    def apply_count(self):
        """
        The number of times the rule has applied.

        :type: int
        """
        return self.__apply_count

    @property
    def is_closure(self) -> bool:
        """
        Whether this is an instance of :class:`~rules.ClosureRule`.

        :type: bool
        """
        return False

    @property
    def name(self) -> str:
        """
        The rule name, default it the class name.

        :type: str
        """
        return self.__class__.__name__

    @final
    @property
    def tableau(self) -> Tableau:
        """
        Reference to the tableau instance.

        :type: Tableau
        """
        return self.__tableau

    @final
    def get_target(self, branch: Branch) -> Target:
        """
        :meta public final:
        """
        targets = self._get_targets(branch)
        if targets:
            self.__extend_targets(targets)
            return self.__select_best_target(targets)

    @final
    def apply(self, target: Target):
        """
        :meta public final:
        """
        with self.apply_timer:
            self.emit(Events.BEFORE_APPLY, target)
            self._apply(target)
            self.__apply_count += 1
            self.emit(Events.AFTER_APPLY, target)

    @final
    def branch(self, parent: Branch = None) -> Branch:
        """
        Create a new branch on the tableau. Convenience for ``self.tableau.branch()``.

        :param tableaux.Branch parent: The parent branch, if any.
        :return: The new branch.
        :rtype: tableaux.Branch
        :meta public final:
        """
        return self.tableau.branch(parent)

    @final
    def add_timer(self, *names: str):
        """
        Add a timer.

        :meta public:
        """
        for name in names:
            if name in self.timers:
                raise KeyError("Timer '%s' already exists" % name)
            self.timers[name] = StopWatch()

    @final
    def add_helper(self, cls: type, attr: str = None, **opts) -> Rule.HelperInfo:
        """
        Add a helper.

        :meta public:
        """
        inst = cls(self, **opts)
        info = Rule.HelperInfo(cls, inst, attr)
        self.helpers[cls] = inst
        if attr != None:
            setattr(self, attr, inst)
        for event, meth in Rule.DefaultHelperRuleEventMethods:
            if hasattr(inst, meth):
                self.on(event, getattr(inst, meth))
        for event, meth in Rule.DefaultHelperTabEventMethods:
            if hasattr(inst, meth):
                self.tableau.on(event, getattr(inst, meth))
        self.__helpers.append(info)
        return info

    # Abstract methods
    def example_nodes(self) -> list[NodeType]:
        """
        :meta abstract:
        """
        raise NotImplementedError()

    def _get_targets(self, branch: Branch) -> list[Target]:
        """
        :meta protected abstract:
        """
        # Intermediate classes such as ``ClosureRule``, ``PotentialNodeRule``,
        # (and its child ``FilterNodeRule``) implement this and ``select_best_target()``,
        # and define finer-grained methods for concrete classes to implement.
        raise NotImplementedError()

    def _apply(self, target: Target):
        """
        Apply the rule to the target. Implementations should modify the tableau directly,
        with no return value.

        :meta abstract:
        """
        raise NotImplementedError()

    # Default implementation

    def sentence(self, node: Node) -> Sentence:
        """
        Get the sentence for the node, or ``None``.

        :param tableaux.Node node:
        :rtype: lexicals.Sentence
        """
        return node.get('sentence')

    # Scoring

    def group_score(self, target: Target) -> float:
        # Called in tableau
        return self.score_candidate(target) / max(1, self.branch_level)

    # Candidate score implementation options ``is_rank_optim``

    def score_candidate(self, target: Target) -> float:
        return sum(self.score_candidate_list(target))

    def score_candidate_list(self, target: Target) -> Collection[float]:
        return self.score_candidate_map(target).values()

    def score_candidate_map(self, target: Target) -> dict[Any: float]:
        # Will sum to 0 by default
        return {}

    # Other

    def __repr__(self):
        return orepr(self,
            module      = self.__module__,
            apply_count = self.apply_count,
            helpers     = len(self.__helpers),
        )

    # Private Util

    def __extend_targets(self, targets: Collection[Target]):
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
        if not isinstance(targets, (tuple, list)):
            raise TypeError('Targets must be a (tuple, list): %s' % type(targets))
        if self.opts['is_rank_optim']:
            # if isinstance(targets, Generator):
            #     targets, scores = zip()
            # targets, scores = zip(*(
            #      (target, self.score_candidate(target))
            #      for target in targets
            # ))
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

    def __select_best_target(self, targets: Collection[Target]):
        """
        Selects the best target. Assumes targets have been extended.
        """
        for target in targets:
            if not self.opts['is_rank_optim']:
                return target
            if target['candidate_score'] == target['max_candidate_score']:
                return target

RuleType = Union[RuleMeta, Rule]
RuleRef = Union[RuleType, str]

class TabRules(object):

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
            self.__setattr__ = TabRules._prot

        def __delattr__(self, name):
            if name.startswith('_'):
                raise AttributeError(name)
            return super().__delattr__(name)

class TabRules(TabRules.Base):

    def _prot(self, name, *_):
        raise AttributeError(name)
    
    writes = Decorators.checkstate(locked = False)

    class RuleGroup(TabRules.Base):
        pass

    class RuleGroups(TabRules.Base):
        pass

    class Common(object):

        def __init__(self, tableau: Tableau):
            self.ruleindex = {}
            self.groupindex = {}
            self.stat = Kwobj(len = 0, locked = False)
            self.tab = tableau
            def lock(*_): self.stat.locked = True
            tableau.once(Events.AFTER_BRANCH_ADD, lock)
            self.__setattr__ = self.__delattr__ = TabRules._prot

class TabRules(TabRules):

    @property
    def groups(self):
        return self.__groups

    @TabRules.writes
    def append(self, rule: RuleType):
        self.groups.create().append(rule)
    add = append

    @TabRules.writes
    def extend(self, rules: Iterable[RuleType]):
        self.groups.append(rules)

    @TabRules.writes
    def clear(self):
        self.groups.clear()
        self.__c.ruleindex.clear()

    def get(self, ref: RuleRef, *dflt: Any) -> Rule:
        rindex = self.__c.ruleindex
        if ref in rindex:
            return rindex[ref]
        if isclass(ref) and ref.__name__ in rindex:
            return rindex[ref.__name__]
        if ref.__class__.__name__ in rindex:
            return rindex[ref.__class__.__name__]
        if len(dflt):
            return dflt[0]
        raise NotFoundError(ref)

    def __init__(self, tableau: Tableau):
        common = self.__c = TabRules.Common(tableau)
        self.__groups = TabRules.RuleGroups(common)
        super().__init__(common)

    def __len__(self):
        return self.__c.stat.len

    def __iter__(self) -> Iterator[Rule]:
        return chain.from_iterable(self.groups)

    def __contains__(self, item: RuleRef):
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

    @staticmethod
    def _create_rule(arg: RuleType, tab: Tableau) -> Rule:
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

    class RuleGroups(TabRules.RuleGroups):

        @TabRules.writes
        def create(self, name: str = None) -> TabRules.RuleGroup:
            c = self.__c
            if name != None:
                if name in c.groupindex or name in c.ruleindex:
                    raise DuplicateKeyError(name)
            group = TabRules.RuleGroup(name, c)
            self.__groups.append(group)
            if name != None:
                c.groupindex[name] = group
            return group

        @TabRules.writes
        def append(self, rules: Iterable[RuleType], name: str = None):
            if name == None:
                name = getattr(rules, 'name', None)
            self.create(name).extend(rules)
        add = append

        @TabRules.writes
        def extend(self, groups: Iterable[Iterable[RuleType]]):
            for rules in groups:
                self.add(rules)

        @TabRules.writes
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
    
        def __iter__(self) -> Iterator[TabRules.RuleGroup]:
            return iter(self.__groups)

        def __len__(self):
            return len(self.__groups)

        def __getitem__(self, index: Union[int, slice]) -> TabRules.RuleGroup:
            return self.__groups[index]

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

    class RuleGroup(TabRules.RuleGroup):

        def lenchange(method: Callable) -> Callable:
            def update(self, *args, **kw):
                mypre = len(self)
                try:
                    return method(self, *args, **kw)
                finally:
                    self.__c.stat.len += len(self) - mypre
            return update

        @property
        def name(self) -> str:
            return self.__name

        @TabRules.writes
        @lenchange
        def append(self, rule: RuleType):
            c = self.__c
            rule = TabRules._create_rule(rule, self.tab)
            cls = rule.__class__
            clsname = cls.__name__
            if clsname in c.ruleindex or clsname in c.groupindex:
                raise DuplicateKeyError(clsname)
            self.__rules.append(rule)
            c.ruleindex[clsname] = self.__index[rule] = rule
        add = append

        @TabRules.writes
        def extend(self, rules: Iterable[RuleType]):
            for rule in rules:
                self.add(rule)

        @TabRules.writes
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

        def __iter__(self) -> Iterator[Rule]:
            return iter(self.__rules)

        def __len__(self):
            return len(self.__rules)

        def __contains__(self, item: RuleRef):
            return item in self.__index

        def __getitem__(self, i) -> Rule:
            return self.__rules[i]

        def __getattr__(self, name):
            if name in self.__index:
                return self.__index[name]
            raise AttributeError(name)

        def __repr__(self):
            return orepr(self, name = self.name, rules = len(self))

class TableauxSystem(object):

    @classmethod
    def build_trunk(cls, tableau: Tableau, argument: Argument):
        raise NotImplementedError()

    @classmethod
    def branching_complexity(cls, node: Node) -> int:
        return 0

    @classmethod
    def add_rules(cls, logic: ModuleType, rules: TabRules):
        Rules = logic.TableauxRules
        rules.groups.add(Rules.closure_rules, 'closure')
        rules.groups.extend(Rules.rule_groups)

class Tableau(Tableau):
    """
    A tableau proof.
    """

    # TabRules = TabRules()
    opts = {
        'is_group_optim'  : True,
        'is_build_models' : False,
        'build_timeout'   : None,
        'max_steps'       : None,
    }

    def __init__(self, logic: LogicRef = None, argument: Argument = None, **opts):

        super().__init__(*Tableau.TableauEvents)

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
        self.history: list[Tableau.StepEntry] = list()

        # Post-build properties

        #: A tree structure of the tableau. This is generated after the tableau
        #: is finished. If the `build_timeout` was exceeded, the tree is `not`
        #: built.
        #:
        #: :type: dict
        self.tree = None
        self.models = None
        self.stats = None

        self._flag = FLAG.PREMATURE
        # Timers
        self.__build_timer     : StopWatch = StopWatch()
        self.__models_timer    : StopWatch = StopWatch()
        self.__tree_timer      : StopWatch = StopWatch()
        self.__tunk_build_timer: StopWatch = StopWatch()

        # Options
        self.opts = self.opts | opts

        self.__branch_list: list[Branch] = list()
        self.__trunks     : list[Branch] = list()
        self.__open_linkset = LinkOrderSet()
        self.__branchstat = dict()

        # Cache for the nodes' branching complexities
        self.__branching_complexities = {}

        self.__branch_listeners = {
            Events.AFTER_BRANCH_CLOSE : self.__after_branch_close,
            Events.AFTER_NODE_ADD     : self.__after_node_add,
            Events.AFTER_NODE_TICK    : self.__after_node_tick,
        }

        # Rules
        self.__rules = TabRules(self)

        self.__logic = self.__argument = None
        if logic != None:
            self.logic = logic
        if argument != None:
            self.argument = argument

    @property
    def id(self) -> int:
        """
        The unique object ID of the tableau.

        :type: int
        """
        return id(self)

    @property
    def logic(self) -> ModuleType:
        """
        The logic of the tableau.

        :type: ModuleType
        """
        return self.__logic

    @logic.setter
    def logic(self, logic: LogicRef):
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
    def rules(self) -> TabRules:
        return self.__rules

    @property
    def System(self) -> TableauxSystem:
        """
        Convenience property for ``self.logic.TableauxSystem``. If the ``logic``
        property is ``None``, the value will be ``None``.

        :type: TableauxSystem
        """
        if self.logic == None:
            return None
        return self.logic.TableauxSystem

    @property
    def argument(self) -> Argument:
        """
        The argument of the tableau.

        :type: lexicals.Argument
        """
        return self.__argument

    @argument.setter
    def argument(self, argument: Argument):
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
    def finished(self) -> bool:
        """
        Whether the tableau is finished. A tableau is `finished` iff `any` of the
        following conditions apply:

        i. The tableau is `completed`.
        ii. The `max_steps` option is met or exceeded.
        iii. The `build_timeout` option is exceeded.
        iv. The ``finish()`` method is manually invoked.

        :type: bool
        """
        return FLAG.FINISHED in self._flag

    @property
    def completed(self) -> bool:
        """
        Whether the tableau is completed. A tableau is `completed` iff all rules
        that can be applied have been applied.

        :type: bool
        """
        return FLAG.FINISHED in self._flag and FLAG.PREMATURE not in self._flag

    @property
    def premature(self) -> bool:
        """
        Whether the tableau is finished prematurely. A tableau is `premature` iff
        it is `finished` but not `completed`.

        :type: bool
        """
        return FLAG.FINISHED in self._flag and FLAG.PREMATURE in self._flag

    @property
    def valid(self) -> bool:
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
    def invalid(self) -> bool:
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
    def trunk_built(self) -> bool:
        """
        Whether the trunk has been built.

        :type: bool
        """
        return FLAG.TRUNK_BUILT in self._flag

    @property
    def current_step(self) -> int:
        """
        The current step number. This is the number of rule applications, plus ``1``
        if the trunk is built.

        :type: int
        """
        return len(self.history) + int(self.trunk_built)

    @property
    def open(self) -> Collection:
        """
        View of the open branches.
        """
        return self.__open_linkset.view

    def build(self) -> Tableau:
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

    def step(self) -> Union[Tableau.StepEntry, None, bool]:
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
        ruletarget = stepentry = None
        with StopWatch() as timer:
            if not self.__is_max_steps_exceeded():
                ruletarget = self.next_step()
                if not ruletarget:
                    self._flag = self._flag & ~FLAG.PREMATURE
            if ruletarget:
                ruletarget.rule.apply(ruletarget.target)
                stepentry = Tableau.StepEntry(*ruletarget, timer.elapsed())
                self.history.append(stepentry)
            else:
                self.finish()
        return stepentry

    def branch(self, parent: Branch = None) -> Branch:
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

    def add(self, branch: Branch) -> Tableau:
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
        index = len(self)
        self.__branch_list.append(branch)
        if not branch.closed:
            self.__open_linkset.add(branch)
        if not branch.parent:
            self.__trunks.append(branch)
        stat = self.__branchstat[branch] = Tableau.BranchStat()
        stat.update({
            KEY.STEP_ADDED: self.current_step,
            KEY.INDEX     : index,
            KEY.PARENT    : branch.parent,
        })
        self.__after_branch_add(branch)
        return self

    def build_trunk(self) -> Tableau:
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
            self._flag |= FLAG.TRUNK_BUILT
            self.emit(Events.AFTER_TRUNK_BUILD, self)
        return self

    def finish(self) -> Tableau:
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
        self._flag |= FLAG.FINISHED
        if self.invalid and self.opts.get('is_build_models'):
            with self.__models_timer:
                self.__build_models()
        if FLAG.TIMED_OUT not in self._flag:
            # In case of a timeout, we do `not` build the tree in order to best
            # respect the timeout. In case of `max_steps` excess, however, we
            # `do` build the tree.
            with self.__tree_timer:
                self.tree = make_tree_structure(self, list(self))
        self.stats = self.__compute_stats()
        return self

    def branching_complexity(self, node: Node) -> int:
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

    def stat(self, branch: Branch, *keys: Union[Node, KEY]) -> Any:
        # branch -> key
        # branch -> node
        # branch -> node -> key
        stat = self.__branchstat[branch]
        # branch
        if len(keys) == 0:
            return stat.view()
        kit = iter(keys)
        key = next(kit)
        if isinstance(key, Node):
            # branch -> node [-> key]
            stat = stat[KEY.NODES][key]
            try:
                key = next(kit)
                stat = stat[KEY(key)]
                next(kit)
            except StopIteration:
                return stat
            raise ValueError('Too many keys to lookup')
        # branch -> key
        try:
            stat = stat[KEY(key)]
            next(kit)
        except StopIteration:
            if key == KEY.NODES:
                return dict(stat)
            return stat
        raise ValueError('Too many keys to lookup')

    def __getitem__(self, index: Union[int, slice]) -> Branch:
        return self.__branch_list[index]

    def __len__(self):
        return len(self.__branch_list)

    def __iter__(self) -> Iterator[Branch]:
        return iter(self.__branch_list)

    def __contains__(self, branch: Branch):
        return branch in self.__branchstat

    def __repr__(self):
        return orepr(self, {
            'id'   : self.id,
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

    def __after_branch_add(self, branch: Branch):
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

    def __after_branch_close(self, branch: Branch):
        stat = self.__branchstat[branch]
        stat[KEY.STEP_CLOSED] = self.current_step
        stat[KEY.FLAGS] |= FLAG.CLOSED
        self.__open_linkset.remove(branch)
        self.emit(Events.AFTER_BRANCH_CLOSE, branch)

    def __after_node_add(self, node: Node, branch: Branch):
        curstep = self.current_step
        stat = self.__branchstat[branch].node(node)
        stat[KEY.STEP_ADDED] = curstep
        node.step = curstep
        self.emit(Events.AFTER_NODE_ADD, node, branch)

    def __after_node_tick(self, node: Node, branch: Branch):
        curstep = self.current_step
        stat = self.__branchstat[branch].node(node)
        stat[KEY.FLAGS] = stat[KEY.FLAGS] | FLAG.TICKED
        stat[KEY.STEP_TICKED] = curstep
        self.emit(Events.AFTER_NODE_TICK, node, branch)

    # :-----------:
    # : Util      :
    # :-----------:

    def next_step(self) -> Tableau.RuleTarget:
        """
        Choose the next rule step to perform. Returns the (rule, target)
        pair, or ``None``if no rule can be applied.

        This iterates over the open branches and calls ``__get_branch_application()``.
        """
        for branch in self.open:
            res = self.__get_branch_application(branch)
            if res:
                return res

    def __get_branch_application(self, branch: Branch) -> Tableau.RuleTarget:
        """
        Find and return the next available rule application for the given open
        branch.
        """
        for group in self.rules.groups:
            res = self.__get_group_application(branch, group)
            if res:
                return res

    def __get_group_application(self, branch: Branch, rules: Iterable[Rule]) -> Tableau.RuleTarget:
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
                rule_target = Tableau.RuleTarget(rule, target)
                if not self.opts.get('is_group_optim'):
                    target.update({
                        'group_score'         : None,
                        'total_group_targets' : 1,
                        'min_group_score'     : None,
                        'is_group_optim'      : False,
                    })
                    return rule_target
                results.append(rule_target)
        if results:
            return self.__select_optim_group_application(results)

    def __select_optim_group_application(self, results: list[Tableau.RuleTarget]) -> Tableau.RuleTarget:
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
        for i, res in enumerate(results):
            if group_scores[i] == max_group_score:
                res.target.update({
                    'group_score'         : max_group_score,
                    'total_group_targets' : len(results),
                    'min_group_score'     : min_group_score,
                    'is_group_optim'      : True,
                })
                return res

    def __compute_stats(self) -> dict:
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

    def __compute_rule_stats(self, rule: Rule) -> dict:
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
            self._flag |= FLAG.TIMED_OUT
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

    def __result_word(self) -> str:
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

def make_tree_structure(tab: Tableau, branches: list[Branch], node_depth=0, track=None):
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
            if FLAG.CLOSED in tab.stat(branch, KEY.FLAGS):
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
            node: Node = relevant[0][node_depth]
            step_added = tab.stat(relevant[0], node, KEY.STEP_ADDED)
            s['nodes'].append(node)
            if s['step'] == None or step_added < s['step']:
                s['step'] = step_added
            node_depth += 1
            continue
        break
    track['distinct_nodes'] += len(s['nodes'])
    if len(branches) == 1:
        stat = tab.stat(branch)
        flags = stat[KEY.FLAGS]
        branch = branches[0]
        s['closed'] = FLAG.CLOSED in flags
        s['open'] = not branch.closed
        if s['closed']:
            s['closed_step'] = stat[KEY.STEP_CLOSED]
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
            child = make_tree_structure(tab, child_branches, node_depth, track)

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
