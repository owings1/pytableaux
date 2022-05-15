# -*- coding: utf-8 -*-
# pytableaux, a multi-logic proof generator.
# Copyright (C) 2014-2022 Doug Owings.
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
"""
pytableaux.proof.tableaux
^^^^^^^^^^^^^^^^^^^^^^^^^

"""
from __future__ import annotations

import operator as opr
from collections import deque
from collections.abc import Set
from typing import (TYPE_CHECKING, Any, Callable, Collection, Iterable,
                    Iterator, Mapping, Sequence, SupportsIndex, final)

from pytableaux import __docformat__
from pytableaux.errors import Emsg, check
from pytableaux.lang.collect import Argument
from pytableaux.lang.lex import Sentence
from pytableaux.logics import registry
from pytableaux.proof import RuleHelper, RuleMeta
from pytableaux.proof.common import Branch, Node, Target
from pytableaux.proof import (BranchEvent, BranchStat, RuleClassFlag,
                                   RuleEvent, RuleState, StepEntry, TabEvent,
                                   TabFlag, TabStatKey, TabTimers)
from pytableaux.tools import EMPTY_MAP, abstract, closure, isstr
from pytableaux.tools.decorators import wraps
from pytableaux.tools.events import EventEmitter
from pytableaux.tools.hybrids import EMPTY_QSET, qset, qsetf
from pytableaux.tools.linked import linqset
from pytableaux.tools.mappings import MapProxy, dmap, dmapns
from pytableaux.tools.sequences import (SeqCover, SequenceApi, absindex, seqf,
                                        seqm)
from pytableaux.tools.sets import EMPTY_SET, setf
from pytableaux.tools.timing import Counter, StopWatch

if TYPE_CHECKING:
    from typing import ClassVar, overload

    from pytableaux.logics import LogicLookupKey
    from pytableaux.models import BaseModel
    from pytableaux.proof import TableauxSystem
    from pytableaux.tools.typing import F, LogicModule, RuleT, T, TypeInstDict


__all__ = (
    'Rule',
    'RuleGroup',
    'RuleGroups',
    'Tableau',
    'TabRuleGroups',
    'TreeStruct',
)

NOARG = object()
NOGET = object()


# ----------------------------------------------

class Rule(EventEmitter, metaclass = RuleMeta):
    'Base class for a Tableau rule.'

    _defaults: ClassVar[Mapping[str, Any]] = MapProxy(dict(
        is_rank_optim = True,
        nolock = False,
    ))
    _optkeys: ClassVar[setf[str]] = setf(_defaults)

    FLAGS: ClassVar[RuleClassFlag] = RuleClassFlag(0)
    legend: ClassVar[tuple]

    Helpers: ClassVar[Mapping[type[RuleHelper], Any]] = {}
    "Helper classes mapped to their settings."

    Timers: ClassVar[qsetf[str]] = qsetf(('search', 'apply'))
    "StopWatch names to create in ``timers`` mapping."

    name: ClassVar[str]
    "The rule class name."

    branch_level: ClassVar[int] = 1
    """The number of branches resulting from an application. A value
    of ``1`` means no additional branches. A value of ``2`` means
    one additional branch, etc.
    """

    tableau: Tableau
    "The tableau instance."

    opts: Mapping[str, bool]
    "The options."

    helpers: TypeInstDict[RuleHelper]
    """Helper instances mapped by class.
    
    :type: Mapping[type[RuleHelper], RuleHelper]
    """

    timers: Mapping[str, StopWatch]
    "StopWatch instances mapped by name."

    history: Sequence[Target]
    "The targets applied to."

    state: RuleState
    "The state bit flag."

    __slots__ = ('tableau', 'helpers', 'timers', 'opts', 'history',
        'state', '__getitem__')

    __iter__ = None

    if TYPE_CHECKING:
        @overload
        def __getitem__(self, key: type[T]) -> T: # type: ignore
            'Get a helper instance by class.'

    def __new__(cls, *args, **kw):
        inst = super().__new__(cls)
        object.__setattr__(inst, 'state', RuleState.NONE)
        return inst

    def __init__(self, tableau: Tableau, /, **opts):

        # events
        EventEmitter.__init__(self, *RuleEvent)

        self.tableau = tableau

        # options
        if opts:
            opts = dmap(opts)
            opts &= self._optkeys
            opts %= self._defaults
        else:
            opts = self._defaults
        self.opts = MapProxy(opts)

        # timers
        self.timers = {
            name: StopWatch() for name in self.Timers
        }

        # history
        history = deque()
        self.on(RuleEvent.AFTER_APPLY, history.append)
        self.history = SeqCover(history)

        # helpers
        self.helpers = helpers = {}
        self.__getitem__ = helpers.__getitem__
        # Add one at a time, to support helper dependency checks.
        for Helper in self.Helpers:
            helpers[Helper] = Helper(self)

        # flag/lock
        if not self.opts['nolock']:
            tableau.once(TabEvent.AFTER_BRANCH_ADD, self.__lock)
        self.state |= RuleState.INIT

    @abstract
    def _get_targets(self, branch: Branch, /) -> Sequence[Target]|None:
        "Return targets that the rule should apply to."
        return None

    @abstract
    def _apply(self, target: Target, /) -> None:
        "Apply the rule to a target returned from ``._get_targets()``."
        raise NotImplementedError

    @abstract
    def example_nodes(self) -> Iterable[Mapping]:
        "Return example nodes that would trigger the rule."
        raise NotImplementedError

    def sentence(self, node: Node, /) -> Sentence|None:
        'Get the sentence for the node, or ``None``.'
        return node.get('sentence')

    # Scoring
    def group_score(self, target: Target, /) -> float:
        # Called in tableau
        return self.score_candidate(target) / max(1, self.branch_level)

    # Candidate score implementation options ``is_rank_optim``
    def score_candidate(self, target: Target, /) -> float:
        return 0.0

    @final
    def target(self, branch: Branch, /) -> Target|None:
        "Get the rule target if it applies."
        with self.timers['search']:
            targets = self._get_targets(branch)
            if targets:
                self.__extend_targets(targets)
                return self.__select_best_target(targets)

    @final
    def apply(self, target: Target, /) -> None:
        "Apply the rule to a target returned from ``.target()``."
        with self.timers['apply']:
            self.emit(RuleEvent.BEFORE_APPLY, target)
            self._apply(target)
            self.emit(RuleEvent.AFTER_APPLY, target)

    @final
    def branch(self, parent: Branch = None, /) -> Branch:
        """Create a new branch on the tableau. Convenience for
        ``self.tableau.branch()``.

        Args:
            parent: The parent branch, if any.

        Returns:
            The new branch.
        """
        return self.tableau.branch(parent)

    def stats(self) -> dict[str, Any]:
        "Compute the rule stats."
        dict(
            name    = self.name,
            applied = len(self.history),
            timers  = {
                name : dict(
                    duration_ms  = timer.elapsed_ms(),
                    duration_avg = timer.elapsed_avg(),
                    count        = timer.count,
                )
                for name, timer in self.timers.items()
            },
        )

    @classmethod
    def test(cls, /, *, noassert = False):
        """Run a simple test on the rule."""
        (tab := Tableau()).rules.append(cls)
        rule = tab.rules.get(cls)
        branch = tab.branch()
        branch.extend(nodes := rule.example_nodes())
        result = tab.step()
        tab.finish()
        if not noassert:
            assert len(rule.history) > 0
        return dmapns(
            cls     = cls,
            rule    = rule,
            tableau = tab,
            branch  = branch,
            nodes   = nodes,
            result  = result,
        )

    def __repr__(self):
        return (f'<{type(self).__name__} module:{self.__module__} '
            f'applied:{len(self.history)}>')

    @closure
    def __setattr__(*, slots = __slots__):
        LockedVal = RuleState.LOCKED.value
        protected: Callable[[str], bool] = set(slots).__contains__
        def fset(self: Rule, name, value, /):
            statev = self.state.value
            if statev and statev & LockedVal == statev and protected(name):
                raise Emsg.ReadOnly(self, name)
            super().__setattr__(name, value)
        return fset

    @closure
    def __delattr__(*, slots = __slots__):
        protected: Callable[[str], bool] = set(slots).__contains__
        def fdel(self: Rule, name,/):
            if protected(name):
                raise Emsg.ReadOnly(self, name)
            super().__delattr__(name)
        return fdel

    @final
    @closure
    def __lock():
        sa = object.__setattr__
        LockedVal = RuleState.LOCKED.value
        def lock(self: Rule, *_):
            statev = self.state.value
            newval = statev | LockedVal
            if newval == statev:
                raise Emsg.IllegalState('Already locked')
            sa(self, 'helpers', MapProxy(self.helpers))
            sa(self, 'timers' , MapProxy(self.timers))
            sa(self, 'state'   , RuleState(newval))
        return lock

    def __extend_targets(self, targets: Sequence[Target], /):
        """Augment the targets with the following keys:
        
        - `rule`
        - `is_rank_optim`
        - `candidate_score`
        - `total_candidates`
        - `min_candidate_score`
        - `max_candidate_score`

        Args:
            targets: The sequence of targets.
        """
        is_rank_optim = self.opts['is_rank_optim']
        if is_rank_optim:
            scores = tuple(map(self.score_candidate, targets))
            max_score = max(scores)
            min_score = min(scores)
        else:
            scores = None,
            max_score = min_score = None
        for score, target in zip(scores, targets):
            target.update(
                rule             = self,
                is_rank_optim    = is_rank_optim,
                total_candidates = len(targets),
                candidate_score  = score,
                min_candidate_score = min_score,
                max_candidate_score = max_score,
            )

    def __select_best_target(self, targets: Iterable[Target], /) -> Target:
        'Selects the best target. Assumes targets have been extended.'
        is_rank_optim = self.opts['is_rank_optim']
        for target in targets:
            if not is_rank_optim:
                return target
            if target['candidate_score'] == target['max_candidate_score']:
                return target

# ----------------------------------------------

def locking(method: F) -> F:
    'Decorator for locking TabRuleGroups methods after Tableau is started.'
    @wraps(method)
    def f(self: TabRuleGroups, *args, **kw):
        try:
            if self._root._locked:
                raise Emsg.IllegalState('locked')
        except AttributeError:
            pass
        return method(self, *args, **kw)
    return f

class TabRuleGroups(SequenceApi[Rule]):
    'Grouped and named collection of rules for a tableau.'

    __slots__ = (
        '_groupindex',
        '_locked',
        '_root',
        '_ruleindex',
        '_tab',
        'groups',
    )
 
    #: The rule groups sequence view.
    groups: RuleGroups

    def __init__(self, tab: Tableau, /):
        self._locked: bool = False
        self._root = self
        #: Rule class name to rule instance.
        self._ruleindex: dict[str, Rule] = {}
        #: Named groups index.
        self._groupindex: dict[str, RuleGroup] = {}
        self._tab = tab
        self.groups = RuleGroups(self)
        tab.once(TabEvent.AFTER_BRANCH_ADD, self._lock)

    def append(self, rule: type[Rule]):
        'Add a single Rule to a new (unnamed) group.'
        self.groups.create(None).append(rule)

    def extend(self, rules: Iterable[type[Rule]], /, name: str|None = NOARG):
        'Create a new group from a collection of Rule classes.'
        self.groups.append(rules, name = name)

    def clear(self):
        'Clear all the rules. Raises IllegalStateError if tableau is started.'
        self.groups.clear()
        self._ruleindex.clear()
        self._groupindex.clear()

    def get(self, ref: type[RuleT]|str, default = NOARG, /) -> RuleT:
        'Get a rule instance by name or type.'
        return self._ruleindex_get(self._ruleindex, ref, default)

    def names(self) -> list[str]:
        'List all the rule names in the sequence.'
        return list(R.__name__ for R in map(type, self))

    def __len__(self):
        return len(self._ruleindex)

    def __contains__(self, ref):
        return self.get(ref, NOGET) is not NOGET

    def __iter__(self) -> Iterator[Rule]:
        for group in self.groups:
            yield from group

    def __reversed__(self) -> Iterator[Rule]:
        for group in reversed(self.groups):
            yield from reversed(group)

    @closure
    def __getitem__():

        select = {
            False : ( (0).__mul__, iter,     opr.add, opr.gt ),
            True  : ( (1).__mul__, reversed, opr.sub, opr.le ),
        }.__getitem__

        def getitem(self: TabRuleGroups, index: SupportsIndex, /,) -> Rule:
            length = len(self)
            index = absindex(length, index)
            istart, iterfunc, adjust, compare = select(2 * index > length)
            i = istart(length)
            for group in iterfunc(self.groups):
                inext = adjust(i, len(group))
                if compare(inext, index):
                    return group[index - i]
                i = inext
            raise TypeError # should never run.
        return getitem

    def __repr__(self):
        logic = self._tab.logic
        lname = logic.name if logic else None
        return (f'<{type(self).__name__} logic:{lname} '
            f'groups:{len(self.groups)} rules:{len(self)}>')

    __delattr__ = Emsg.ReadOnly.razr
    __setattr__ = locking(object.__setattr__)

    @locking
    def _lock(self, _ = None):
        self._tab.off(TabEvent.AFTER_BRANCH_ADD, self._lock)
        self.groups._lock()
        self._ruleindex  = MapProxy(self._ruleindex)
        self._groupindex = MapProxy(self._groupindex)
        self._locked = True

    def _checkname(self, name: str, /):
        'Validate a new rule or group name before it is added.'
        if name in self._groupindex or name in self._ruleindex:
            raise Emsg.DuplicateKey(name)

    @staticmethod
    def _ruleindex_get(idx: Mapping[str, Rule], ref: str|type[RuleT], default = NOARG, /) -> RuleT:
        '''Retrieve a rule instance from the given index, by name or type.
        '''
        try:
            if isinstance(ref, str):
                return idx[ref]
            return idx[check.subcls(ref, Rule).__name__]
        except KeyError:
            if default is not NOARG:
                return default
        raise Emsg.MissingValue(ref)

class RuleGroup(SequenceApi[Rule]):
    """A rule group of a Tableau's ``rules``.
    
    This class supports the full ``Sequence`` standard interface for iterating,
    subscripting, and slicing.

    The ``append``, ``extend``, and ``clear`` methods provide mutability
    until the instance is locked. An input value is a subclass of ``Rule``,
    which is then instantiated for the tableau before it is added to the
    sequence.
    
    Rule instances are indexed, and can be retrieved by its class or class
    name using the ``get`` method.
    """

    __slots__ = '_root', '_seq', '_name', '_ruleindex'

    #: The group name, or ``None``.
    name: str|None

    def __init__(self, name: str|None, root: TabRuleGroups):
        self._name = name
        self._root = root
        self._seq: list[Rule] = []
        #: Rule classname to instance.
        self._ruleindex: dict[str, Rule] = {}

    @property
    def name(self) -> str|None:
        return self._name

    @locking
    def append(self, value: type[Rule], /):
        """Instantiate and append a rule class.

        Args:
          value: A ``Rule`` class.

        Raises:
          ValueError: If there is a duplicate name.
          TypeError: If ``value`` is not a subclass of ``Rule``.
          errors.IllegalStateError: If locked.
        """
        root = self._root
        name = check.subcls(value, Rule).__name__
        root._checkname(name)
        rule = value(root._tab, **root._tab.opts)
        self._seq.append(rule)
        root._ruleindex[name] = self._ruleindex[name] = rule
        rule.on(RuleEvent.AFTER_APPLY, root._tab._after_rule_apply)

    def extend(self, values: Iterable[type[Rule]], /):
        """Append multiple rules.

        Args:
          values: An iterable of ``Rule`` classes.

        Raises:
          ValueError: If there is a duplicate name.
          TypeError: If an element is not a subclass of ``Rule``.
          errors.IllegalStateError: If locked.
        """
        for _ in map(self.append, values): pass

    @locking
    def clear(self):
        """Clear the rule group.

        Raises:
          errors.IllegalStateError: If locked.
        """
        self._seq.clear()
        self._ruleindex.clear()

    def get(self, ref:str|type[RuleT], default = NOARG, /) -> RuleT:
        """Get a member instance by name, type, or instance of same type.

        Args:
          ref: A :class:`Rule` class or name.
          default: A value to return if rule not found.

        Returns:
          The rule instance, or ``default`` if it is specified and the rule was
          not found.

        Raises:
          ValueError: If rule not found and ``default`` not passed.
          TypeError: For bad ``ref`` type.
        """
        return self._root._ruleindex_get(self._ruleindex, ref, default)

    if TYPE_CHECKING:
        @overload
        def names(self) -> list[str]: ...

        @overload
        def __getitem__(self, i:SupportsIndex) -> Rule:...

        @overload
        def __getitem__(self, s:slice) -> SequenceApi[Rule]:...

    names = TabRuleGroups.names

    def __getitem__(self, index):
        return self._seq[index]

    def __iter__(self) -> Iterator[Rule]:
        return iter(self._seq)

    def __len__(self):
        return len(self._seq)

    def __contains__(self, ref):
        return self.get(ref, NOGET) is not NOGET

    def __repr__(self):
        return f'<{type(self).__name__} name:{self.name} rules:{len(self)}>'

    __delattr__ = Emsg.ReadOnly.razr
    __setattr__ = locking(object.__setattr__)

    def _lock(self):
        self._seq = SeqCover(self._seq)
        self._ruleindex = MapProxy(self._ruleindex)

class RuleGroups(SequenceApi[RuleGroup]):

    __slots__ = '_root', '_seq',

    def __init__(self, root: TabRuleGroups):
        self._root = root
        self._seq: list[RuleGroup] = []

    @locking
    def create(self, name: str = None) -> RuleGroup:
        'Create and return a new emtpy rule group.'
        root = self._root
        if name is not None:
            root._checkname(name)
        group = RuleGroup(name, root)
        self._seq.append(group)
        if name is not None:
            root._groupindex[name] = group
        return group

    def append(self, Rules: Iterable[type[Rule]], /, name: str|None = NOARG):
        'Create a new group with the given rules. Raise IllegalStateError if locked.'
        if name is NOARG:
            if isinstance(Rules, RuleGroup):
                name = Rules.name
            else:
                name = None
        self.create(name).extend(Rules)

    def extend(self, groups: Iterable[Iterable[type[Rule]]]):
        'Add multiple groups. Raise IllegalStateError if locked.'
        for _ in map(self.append, groups): pass

    @locking
    def clear(self):
        'Clear the groups. Raise IllegalStateError if locked.'
        for _ in map(RuleGroup.clear, self): pass
        self._seq.clear()

    def get(self, name: str, default = NOARG, /) -> RuleGroup:
        'Get a rule group by name.'
        try:
            return self._root._groupindex[name]
        except KeyError:
            if default is NOARG:
                raise
            return default

    def names(self) -> seqm[str]:
        'List the named groups.'
        return seqm(filter(
            isstr, (group.name for group in self)
        ))

    def __iter__(self) -> Iterator[RuleGroup]:
        return iter(self._seq)

    def __len__(self):
        return len(self._seq)

    def __getitem__(self, index: SupportsIndex) -> RuleGroup:
        return self._seq[check.inst(index, SupportsIndex)]

    def __contains__(self, item: str|RuleGroup):
        if isinstance(item, str):
            return item in self._root._groupindex
        check.inst(item (str, RuleGroup))
        for grp in self:
            if item is grp:
                return True
        return False

    def __repr__(self):
        logic = self._root._tab.logic
        lname = logic.name if logic else None
        return (f'<{type(self).__name__} logic:{lname} groups:{len(self)} '
            f'names:{self.names()} rules:{sum(map(len, self))}>')

    __delattr__ = Emsg.ReadOnly.razr
    __setattr__ = locking(object.__setattr__)

    def _lock(self):
        for _ in map(RuleGroup._lock, self): pass
        self._seq = SeqCover(self._seq)

# ----------------------------------------------

class Tableau(Sequence[Branch], EventEmitter):
    'A tableau proof.'

    #: The unique object ID of the tableau.
    id: int

    #: The logic of the tableau.
    logic: LogicModule|None

    #: The argument of the tableau.
    argument: Argument|None

    #: Alias for ``self.logic.TableauxSystem``
    System: TableauxSystem|None

    #: The rule instances.
    rules: TabRuleGroups

    #: The build options.
    opts: Mapping[str, bool|int|None]

    #: The FlagEnum value.
    flag: TabFlag

    #: Whether the tableau is completed. A tableau is `completed` iff all rules
    #: that can be applied have been applied.
    completed: bool

    #: Whether the tableau is finished. A tableau is `finished` iff `any` of the
    #: following conditions apply:
    #:
    #: i. The tableau is `completed`.
    #: ii. The `max_steps` option is met or exceeded.
    #: iii. The `build_timeout` option is exceeded.
    #: iv. The ``finish()`` method is manually invoked.
    finished: bool

    #: Whether the tableau is finished prematurely. A tableau is `premature` iff
    #: it is `finished` but not `completed`.
    premature: bool

    #: Whether the tableau's argument is valid (proved). A tableau with an
    #: argument is `valid` iff it is `completed` and it has no open branches.
    #: If the tableau is not completed, or it has no argument, the value will
    #: be ``None``.
    valid: bool|None

    #: Whether the tableau's argument is invalid (disproved). A tableau with
    #: an argument is `invalid` iff it is `completed` and it has at least one
    #: open branch. If the tableau is not completed, or it has no argument,
    #: the value will be ``None``.
    invalid: bool|None

    #: The current step number. This is the number of rule applications, plus ``1``
    #: if the argument trunk is built.
    current_step: int

    #: Ordered view of the open branches.
    open: Sequence[Branch]

    #: The history of rule applications.
    history: Sequence[StepEntry]

    #: A tree structure of the tableau. This is generated after the tableau
    #: is finished. If the `build_timeout` was exceeded, the tree is `not`
    #: built.
    tree: TreeStruct

    #: The stats, built after finished.
    stats: dict[str, Any]

    #: The models, built after finished if the tableau is `invalid` and the
    #: `is_build_models` option is enabled.
    models: setf[BaseModel]

    #: The tableau timers.
    timers: TabTimers

    _defaults = MapProxy(dict(
        is_group_optim  = True,
        is_build_models = False,
        build_timeout   = None,
        max_steps       = None,
    ))

    def __init__(self, logic: LogicLookupKey = None, argument: Argument = None, /, **opts):

        # Events init
        super().__init__(*TabEvent)
        self.__branch_listeners = MapProxy({
            BranchEvent.AFTER_CLOSE : self.__after_branch_close,
            BranchEvent.AFTER_ADD   : self.__after_node_add,
            BranchEvent.AFTER_TICK  : self.__after_node_tick,
        })

        # Protected attributes
        self.__flag        : TabFlag         = TabFlag.PREMATURE
        self.__history     : list[StepEntry] = []
        self.__branch_list : list[Branch]    = []
        self.__open        : linqset[Branch] = linqset()
        self.__branchstat  : dict[Branch, BranchStat] = {}

        # Private
        self.__branching_complexities: dict[Node, int] = {}

        # Exposed attributes
        self.history = SeqCover(self.__history)
        self.opts    = self._defaults | opts
        self.timers  = TabTimers.create()
        self.rules   = TabRuleGroups(self)
        self.open    = SeqCover(self.__open)

        # Init
        if logic is not None:
            self.logic = logic
        if argument is not None:
            self.argument = argument

    @property
    def id(self) -> int:
        return id(self)

    @property
    def flag(self):
        return self.__flag

    @property
    def argument(self):
        try:
            return self.__argument
        except AttributeError:
            self.__argument = None
            return self.__argument

    @property
    def logic(self):
        try:
            return self.__logic
        except AttributeError:
            self.__logic = None
            return self.__logic

    @property
    def System(self) -> TableauxSystem|None:
        try:
            return self.logic.TableauxSystem
        except AttributeError:
            return None

    @argument.setter
    def argument(self, argument: Argument):
        """Setter for ``argument``. If the tableau has a logic set, then the
        trunk is automatically built."""
        self.__check_not_started()
        self.__argument = Argument(argument)
        if self.logic is not None:
            self.__build_trunk()

    @logic.setter
    def logic(self, logic: LogicLookupKey):
        'Setter for ``logic``. Assumes building has not started.'
        self.__check_not_started()
        self.__logic = registry(logic)
        self.rules.clear()
        self.System.add_rules(self.logic, self.rules)
        if self.argument is not None:
            self.__build_trunk()

    @property
    def finished(self):
        return TabFlag.FINISHED in self.__flag

    @property
    def completed(self):
        return TabFlag.FINISHED in self.__flag and TabFlag.PREMATURE not in self.__flag

    @property
    def premature(self):
        return TabFlag.FINISHED in self.__flag and TabFlag.PREMATURE in self.__flag

    @property
    def valid(self):
        if not self.completed or self.argument is None:
            return None
        return len(self.open) == 0

    @property
    def invalid(self) -> bool:
        if not self.completed or self.argument is None:
            return None
        return len(self.open) > 0

    @property
    def current_step(self) -> int:
        return len(self.history) + (TabFlag.TRUNK_BUILT in self.__flag)

    def build(self) -> Tableau:
        'Build the tableau. Returns self.'
        with self.timers.build:
            while not self.finished:
                self.__check_timeout()
                self.step()
        self.finish()
        return self

    def next(self) -> StepEntry|None:
        """Choose the next rule step to perform. Returns the StepEntry or ``None``
        if no rule can be applied.

        This iterates over the open branches, then over rule groups.
        """
        for branch in self.open:
            for group in self.rules.groups:
                res = self.__get_group_application(branch, group)
                if res:
                    return res

    def step(self):
        """Find, execute, and return the next rule application. If no rule can
        be applied, the ``finish()`` method is called, and ``None`` is returned.
        If the tableau is already finished when this method is called, return
        ``False``.

        .. Internally, this calls the ``next()`` method to select the
        .. next step, and, if non-empty, applies the rule and appends the entry
        .. to the history.

        Returns:
            The history entry, or ``None`` if just finished, or ``False``
            if previously finished.
        
        Raises:
            errors.IllegalStateError: if the trunk is not built.
        """
        if TabFlag.FINISHED in self.__flag:
            return False
        entry = None
        with StopWatch() as timer:
            if not self.__is_max_steps_exceeded():
                entry = self.next()
                if entry is None:
                    self.__flag &= ~TabFlag.PREMATURE
            if entry is not None:
                entry.rule.apply(entry.target)
                entry.duration.inc(timer.elapsed_ms())
                # self.__history.append(entry)
            else:
                self.finish()
        return entry

    def branch(self, /, parent: Branch = None) -> Branch:
        """Create a new branch on the tableau, as a copy of ``parent``, if given.

        Args:
            parent: The parent branch, if any.

        Returns:
            The new branch.
        """
        if parent is None:
            branch = Branch()
        else:
            branch = parent.copy(parent = parent)
        self.add(branch)
        return branch

    def add(self, /, branch: Branch) -> Tableau:
        """Add a new branch to the tableau. Returns self.

        Args:
            branch: The branch to add.

        Returns:
            self
        """
        index = len(self)
        if not branch.closed:
            # Append to linqset will raise duplicate value error.
            self.__open.append(branch)
        elif branch in self:
            raise Emsg.DuplicateValue(branch.id)
        self.__branch_list.append(branch)
        self.__branchstat[branch] = BranchStat({
            TabStatKey.STEP_ADDED : self.current_step,
            TabStatKey.INDEX      : index,
            TabStatKey.PARENT     : branch.parent,
        })
        # self.__after_branch_add(branch)
        # For corner case of an AFTER_BRANCH_ADD callback adding a node, make
        # sure we don't emit AFTER_NODE_ADD twice, so prefetch the nodes.
        nodes = tuple(branch) if branch.parent is None else EMPTY_SET
        # This means we need to start listening before we emit. There
        # could be the possibility of recursion.
        branch.on(self.__branch_listeners)
        self.emit(TabEvent.AFTER_BRANCH_ADD, branch)
        if len(nodes):
            afteradd = self.__after_node_add
            for node in nodes:
                afteradd(node, branch)
        return self

    def finish(self) -> Tableau:
        """Mark the tableau as finished, and perform post-build tasks, including
        populating the ``tree``, ``stats``, and ``models`` properties.
        
        When using the ``build()`` or ``step()`` methods, there is never a need
        to call this method, since it is handled internally. However, this
        method *is* safe to call multiple times. If the tableau is already
        finished, it will be a no-op.

        Returns:
            self
        """
        if TabFlag.FINISHED in self.__flag:
            return self
        self.__flag |= TabFlag.FINISHED
        if self.invalid and self.opts['is_build_models'] and self.logic is not None:
            with self.timers.models:
                self.models = setf(self._gen_models())
        if TabFlag.TIMED_OUT not in self.__flag:
            # In case of a timeout, we do `not` build the tree in order to best
            # respect the timeout. In case of `max_steps` excess, however, we
            # `do` build the tree.
            with self.timers.tree:
                self.tree = self._build_tree(self)
        self.stats = self.__compute_stats()
        self.emit(TabEvent.AFTER_FINISH, self)
        return self

    def branching_complexity(self, node: Node, /) -> int:
        """Caching method for the logic's ``TableauxSystem.branching_complexity()``
        method. If the tableau has no logic, then ``0`` is returned.

        Args:
            node: The node to evaluate.
        
        Returns:
            int: The branching complexity.
        """
        # TODO: Consider potential optimization using hash equivalence for nodes,
        #       to avoid redundant calculations. Perhaps the TableauxSystem should
        #       provide a special branch-complexity node hashing function.
        cache = self.__branching_complexities
        if node not in cache:
            sys = self.System
            if sys is None:
                return 0
            cache[node] = sys.branching_complexity(node)
        return cache[node]

    def stat(self, branch: Branch, /, *keys: Node|TabStatKey) -> Any:
        # Lookup options:
        # - branch
        # - branch, key
        # - branch, node
        # - branch, node, key
        stat = self.__branchstat[branch]
        if len(keys) == 0:
            # branch
            return stat.view()
        kit = iter(keys)
        key = next(kit)
        if isinstance(key, Node):
            # branch, node
            stat = stat[TabStatKey.NODES][key]
            try:
                key = next(kit)
                # branch, node, key
                stat = stat[TabStatKey(key)]
                next(kit)
            except StopIteration:
                return stat
            raise ValueError('Too many keys to lookup')
        try:
            # branch, key
            stat = stat[TabStatKey(key)]
            next(kit)
        except StopIteration:
            if key == TabStatKey.NODES:
                return stat.copy()
            return stat
        raise ValueError('Too many keys to lookup')

    # *** Behaviors

    if TYPE_CHECKING:
        @overload
        def __getitem__(self, s: slice) -> list[Branch]: ...

        @overload
        def __getitem__(self, i: SupportsIndex) -> Branch: ...

    def __getitem__(self, index):
        return self.__branch_list[index]

    def __len__(self):
        return len(self.__branch_list)

    def __bool__(self):
        return True

    def __iter__(self) -> Iterator[Branch]:
        return iter(self.__branch_list)

    def __reversed__(self) -> Iterator[Branch]:
        return reversed(self.__branch_list)

    def __contains__(self, branch: Branch):
        return branch in self.__branchstat

    def __repr__(self):
        info = dict(
            id    = self.id,
            logic = (self.logic and self.logic.name),
            len   = len(self),
            open  = len(self.open),
            step  = self.current_step,
            finished = self.finished,
        )
        if self.finished:
            if self.premature:
                info['premature'] = True
            elif self.valid:
                info['valid'] = True
            elif self.invalid:
                info['invalid'] = True
        if self.argument is not None:
            info['argument'] = self.argument
        istr = ' '.join(f'{k}:{v}' for k, v in info.items())
        return f'<{type(self).__name__} {istr}>'

    # *** Events

    def __after_branch_close(self, branch: Branch):
        stat = self.__branchstat[branch]
        stat[TabStatKey.STEP_CLOSED] = self.current_step
        stat[TabStatKey.FLAGS] |= TabFlag.CLOSED
        self.__open.remove(branch)
        self.emit(TabEvent.AFTER_BRANCH_CLOSE, branch)

    def __after_node_add(self, node: Node, branch: Branch):
        stat = self.__branchstat[branch].node(node)
        stat[TabStatKey.STEP_ADDED] = node.step = self.current_step
        self.emit(TabEvent.AFTER_NODE_ADD, node, branch)

    def __after_node_tick(self, node: Node, branch: Branch):
        stat = self.__branchstat[branch].node(node)
        stat[TabStatKey.STEP_TICKED] = self.current_step
        stat[TabStatKey.FLAGS] |= TabFlag.TICKED
        self.emit(TabEvent.AFTER_NODE_TICK, node, branch)

    def _after_rule_apply(self, target: Target):
        try:
            self.__history.append(target._entry)
        except AttributeError:
            self.__history.append(StepEntry(target.rule, target, Counter()))
            self.__flag |= TabFlag.TIMING_INACCURATE
    # *** Util

    def __get_group_application(self, branch: Branch, group: RuleGroup, /) -> StepEntry:
        """Find and return the next available rule application for the given open
        branch and rule group. 
        
        This calls the ``rule.target(branch)`` on the rules.

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

        Returns:
            A (rule, target) pair, or ``None``.
        """
        is_group_optim = self.opts['is_group_optim']
        results = deque(maxlen = len(group) if is_group_optim else 0)
        for rule in group:
            target = rule.target(branch)
            if target is not None:
                entry = StepEntry(rule, target, Counter())
                target._entry = entry
                if not is_group_optim:
                    target.update(
                        group_score         = None,
                        total_group_targets = 1,
                        min_group_score     = None,
                        is_group_optim      = False,
                    )
                    return entry
                results.append(entry)
        if results:
            return self.__select_optim_group_application(results)

    def __select_optim_group_application(self, results: Sequence[StepEntry], /) -> StepEntry:
        """Choose the highest scoring element from given results. The ``results``
        parameter is assumed to be a non-empty list/tuple of (rule, target) pairs.

        This calls ``rule.group_score(target)`` on each element to compute the
        score. In case of a tie, the earliest element wins.

        Before the selected result is returned, the ``target`` dict is updated
        with the following:
        
        - `group_score`        : int
        - `total_group_targets`: int
        - `min_group_score`    : int
        - `is_group_optim`     : True

        Args:
            results: A list/tuple of (Rule, dict) pairs.

        Returns:
            The highest scoring element.
        """
        group_scores = tuple(entry.rule.group_score(entry.target) for entry in results)
        max_group_score = max(group_scores)
        min_group_score = min(group_scores)
        for group_score, res in zip(group_scores, results):
            if group_score == max_group_score:
                res.target.update(
                    group_score         = max_group_score,
                    total_group_targets = len(results),
                    min_group_score     = min_group_score,
                    is_group_optim      = True,
                )
                return res

    def __build_trunk(self):
        """Build the trunk of the tableau. Delegates to the ``build_trunk()``
        method of ``TableauxSystem``. This is called automatically when the
        tableau has non-empty ``argument`` and ``logic`` properties.

        Raises:
            errors.IllegalStateError: if the trunk is already built.
        """
        self.__check_not_started()
        with self.timers.trunk:
            self.emit(TabEvent.BEFORE_TRUNK_BUILD, self)
            self.System.build_trunk(self, self.argument)
            self.__flag |= TabFlag.TRUNK_BUILT
            self.emit(TabEvent.AFTER_TRUNK_BUILD, self)

    def __compute_stats(self) -> dict[str, Any]:
        'Compute the stats property after the tableau is finished.'
        try:
            distinct_nodes = self.tree.distinct_nodes
        except AttributeError:
            distinct_nodes = None
        timers = self.timers
        return dict(
            # id              = self.id,
            result          = self.__result_word(),
            branches        = len(self),
            open_branches   = len(self.open),
            closed_branches = len(self) - len(self.open),
            steps           = len(self.history),
            distinct_nodes  = distinct_nodes,
            rules_duration_ms = sum(
                step.duration.value
                for step in self.history
            ),
            build_duration_ms  = timers.build.elapsed_ms(),
            trunk_duration_ms  = timers.trunk.elapsed_ms(),
            tree_duration_ms   = timers.tree.elapsed_ms(),
            models_duration_ms = timers.models.elapsed_ms(),
            rules_time_ms = sum(
                rule.timers[name].elapsed_ms()
                for rule in self.rules
                    for name in (
                        'search',
                        'apply',
                    )
            ),
            #rules = tuple(map(self.__compute_rule_stats, self.rules)),
        )

    # def __compute_rule_stats(self, rule: Rule, /) -> dict[str, Any]:
    #     'Compute the stats for a rule after the tableau is finished.'
    #     return dict(
    #         name    = rule.name,
    #         applied = len(rule.history),
    #         timers  = {
    #             name : dict(
    #                 duration_ms  = timer.elapsed_ms(),
    #                 duration_avg = timer.elapsed_avg(),
    #                 count        = timer.count,
    #             )
    #             for name, timer in rule.timers.items()
    #         },
    #     )

    def __check_timeout(self):
        timeout = self.opts['build_timeout']
        if timeout is None or timeout < 0:
            return
        if self.timers.build.elapsed_ms() > timeout:
            self.timers.build.stop()
            self.__flag |= TabFlag.TIMED_OUT
            self.finish()
            raise Emsg.Timeout(timeout)

    def __is_max_steps_exceeded(self) -> bool:
        max_steps = self.opts['max_steps']
        return (
            max_steps is not None and
            max_steps >= 0 and
            len(self.history) >= max_steps
        )

    def __check_not_started(self):
        if TabFlag.TRUNK_BUILT in self.__flag or len(self.history) > 0:
            raise Emsg.IllegalState("Tableau already started.")

    def __result_word(self) -> str:
        if self.valid:
            return 'Valid'
        if self.invalid:
            return 'Invalid'
        if self.completed:
            return 'Completed'
        return 'Unfinished'

    def _gen_models(self):
        'Build models for the open branches.'
        Model: type[BaseModel] = self.logic.Model
        for branch in self.open:
            self.__check_timeout()
            model = Model()
            model.read_branch(branch)
            branch.model = model
            yield model

    def _build_tree(self, branches: Sequence[Branch], node_depth = 0, track = None,/) -> TreeStruct:

        s = TreeStruct()

        if track is None:
            track = dict(pos = 1, depth = 0, distinct_nodes = 0, root = s)
        else:
            track['pos'] += 1

        s.update(
            depth = track['depth'],
            left  = track['pos'],
        )

        branchstat = self.__branchstat

        while True:
            # Branches with a node at node_depth.
            relbranches = tuple(b for b in branches if len(b) > node_depth)
            # Each branch's node at node_depth.
            depth_nodes = qset()

            for b in relbranches:
                depth_nodes.add(b[node_depth])
                if TabFlag.CLOSED in branchstat[b][TabStatKey.FLAGS]:
                    s.has_closed = True
                else:
                    s.has_open = True

            if len(depth_nodes) != 1:
                # There is *not* a singular node shared by all branches at node_depth.
                break
    
            # There is one node shared by all branches at node_depth, thus the
            # branches are equivalent up to this depth.
            node = depth_nodes[0]
            s.nodes.append(node)
            nodestat = branchstat[relbranches[0]][TabStatKey.NODES][node]
            s.ticksteps.append(nodestat[TabStatKey.STEP_TICKED])
            step_added = nodestat[TabStatKey.STEP_ADDED]
            if s.step is None or step_added < s.step:
                s.step = step_added
            node_depth += 1

        track['distinct_nodes'] += len(s.nodes)

        if len(branches) == 1:
            # Finalize leaf attributes.
            self._build_tree_leaf(s, branches[0], track)
        else:
            # Build child structures for each distinct node at node_depth.
            track['depth'] += 1
            self._build_tree_branches(s, branches, depth_nodes, node_depth, track)
            track['depth'] -= 1

        s.structure_node_count = s.descendant_node_count + len(s.nodes)

        track['pos'] += 1
        s.right = track['pos']

        if track['root'] is s:
            s.distinct_nodes = track['distinct_nodes']

        return s

    def _build_tree_leaf(self, s: TreeStruct, branch: Branch, track: dict, /):
        'Finalize attributes for leaf structure.'
        stat = self.__branchstat[branch]
        s.closed = TabFlag.CLOSED in stat[TabStatKey.FLAGS]
        # s.open = not branch.closed
        # assert s.closed == branch.closed
        s.open = not s.closed
        if s.closed:
            s.closed_step = stat[TabStatKey.STEP_CLOSED]
            s.has_closed = True
        else:
            s.has_open = True
        s.width = 1
        s.leaf = True
        s.branch_id = branch.id
        if branch.model is not None:
            s.model_id = branch.model.id
        if track['depth'] == 0:
            s.is_only_branch = True

    def _build_tree_branches(self,
        s: TreeStruct,
        branches: Collection[Branch],
        depth_nodes: Set[Node],
        node_depth: int,
        track: dict, /
    ):
        'Build child structures for each distinct node.'
        w_first = w_last = w_mid = 0

        for i, node in enumerate(depth_nodes):

            # recurse
            child = self._build_tree(seqf(
                b for b in branches if b[node_depth] == node
            ), node_depth, track)

            s.descendant_node_count = len(child.nodes) + child.descendant_node_count
            s.width += child.width

            s.children.append(child)

            if i == 0:
                # first node
                s.branch_step = child.step
                w_first = child.width / 2
            elif i == len(depth_nodes) - 1:
                # last node
                w_last = child.width / 2
            else:
                w_mid += child.width

            s.branch_step = min(s.branch_step, child.step)

        if s.width > 0:
            s.balanced_line_width = (w_first + w_last + w_mid) / s.width
            s.balanced_line_margin = w_first / s.width
        else:
            s.balanced_line_width = s.balanced_line_margin = 0


class TreeStruct(dmapns):
    'Recursive tree structure representation of a tableau.'

    root: bool
    
    nodes: list[Node]
    "The nodes on this structure."

    ticksteps: list[int|None]
    "The ticked steps list."

    children: list[TreeStruct]
    "The child structures."

    leaf: bool = False
    "Whether this is a terminal (childless) structure."

    closed: bool = False
    "Whether this is a terminal structure that is closed."

    open: bool = False
    "Whether this is a terminal structure that is open."

    left: int = None
    "The pre-ordered tree left value."

    right: int = None
    "The pre-ordered tree right value."

    descendant_node_count: int = 0
    "The total node count of all descendants."

    structure_node_count: int = 0
    "The node count plus descendant node count."

    depth: int = 0
    "The depth of this structure (ancestor structure count)."

    has_open: bool = False
    "Whether this structure or a descendant is open."

    has_closed: bool = False
    "Whether this structure or a descendant is closed."

    closed_step: int|None
    "If closed, the step number at which it closed."

    step: int = None
    "The step number at which this structure first appears."

    width: int = 0
    "The number of descendant terminal structures, or 1."

    balanced_line_width: float = 0.0
    """0.5x the width of the first child structure, plus 0.5x the
    width of the last child structure (if distinct from the first),
    plus the sum of the widths of the other (distinct) children.
    """

    balanced_line_margin: float = 0.0
    """0.5x the width of the first child structure divided by the
    width of this structure.
    """

    branch_id: int|None = None
    "The branch id, only set for leaves"

    model_id: int|None = None
    "The model id, if exists, only set for leaves"

    is_only_branch: bool = False
    "Whether this is the one and only branch"

    branch_step: int = None
    "The step at which the branch was added"

    def __init__(self):

        self.nodes = []
        self.ticksteps = []
        self.children = []

        self.id = id(self)

    @classmethod
    def _from_iterable(cls, it):
        inst = cls()
        inst.update(it)
        return inst

    _from_mapping = _from_iterable

# ----------------------------------------------

del(abstract, final, locking)
