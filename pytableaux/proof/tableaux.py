# -*- coding: utf-8 -*-
# pytableaux, a multi-logic proof generator.
# Copyright (C) 2014-2023 Doug Owings.
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
"""
pytableaux.proof.tableaux
^^^^^^^^^^^^^^^^^^^^^^^^^

"""
from __future__ import annotations

import operator as opr
from abc import abstractmethod
from collections import deque
from collections.abc import Set
from types import MappingProxyType as MapProxy
from typing import (TYPE_CHECKING, Callable, ClassVar, Iterable, Mapping,
                    Optional, Sequence, TypeVar, final)

from .. import __docformat__
from ..errors import Emsg, check
from ..lang.collect import Argument
from ..lang.lex import Sentence
from ..logics import registry
from ..tools import (EMPTY_SET, SeqCover, absindex, dictns, for_defaults, qset, EMPTY_MAP,
                     qsetf, wraps)
from ..tools.events import EventEmitter
from ..tools.linked import linqset
from ..tools.timing import Counter, StopWatch
from . import RuleMeta, TableauMeta
from .common import Branch, Node, Target

if TYPE_CHECKING:
    from typing import overload
    from ..tools import TypeInstMap
    from ..models import BaseModel

_F = TypeVar('_F', bound=Callable)
_RHT = TypeVar('_RHT', bound='Rule.Helper')

__all__ = (
    'Rule',
    'RuleGroup',
    'RuleGroups',
    'Tableau',
    'RulesRoot')

NOARG = object()
NOGET = object()
# ----------------------------------------------

class Rule(EventEmitter, metaclass = RuleMeta):
    'Base class for a Tableau rule.'

    _defaults = MapProxy(dict(
        is_rank_optim = True,
        nolock = False))

    legend: ClassVar[tuple]
    "The rule class legend."

    Helpers = {}
    "Helper classes mapped to their settings."

    timer_names: ClassVar[Sequence[str]] = qsetf(('search', 'apply'))
    "StopWatch names to create in ``timers`` mapping."

    name: ClassVar[str]
    "The rule class name."

    ticking: ClassVar[bool] = False
    "Whether this is a ticking rule."

    modal: ClassVar[bool|None] = None
    "Whether this is a modal rule."

    branching: ClassVar[int] = 0
    "The number of additional branches created."

    tableau: Tableau
    "The tableau instance."

    opts: Mapping
    "The options."

    helpers: TypeInstMap[Rule.Helper]
    "Helper instances mapped by class."

    timers: Mapping[str, StopWatch]
    "StopWatch instances mapped by name."

    history: Sequence[Target]
    "The targets applied to."

    state: Rule.State
    "The state bit flag."

    __slots__ = ('tableau', 'helpers', 'timers', 'opts', 'history', 'state')

    @property
    def locked(self) -> bool:
        try:
            return self.state.LOCKED in self.state
        except AttributeError:
            return False

    def __init__(self, tableau: Tableau, /, **opts):
        self.state = Rule.State(0)
        super().__init__(*Rule.Events)
        self.tableau = tableau
        self.opts = MapProxy(for_defaults(self._defaults, opts))
        self.timers = {name: StopWatch() for name in self.timer_names}
        self.history = SeqCover(history := deque())
        self.on(Rule.Events.AFTER_APPLY, history.append)
        self.helpers = {}
        # Add one at a time, to support helper dependency checks.
        for Helper in self.Helpers:
            self.helpers[Helper] = Helper(self)
        if not self.opts['nolock']:
            tableau.once(Tableau.Events.AFTER_BRANCH_ADD, self.lock)
        self.state |= self.state.INIT

    @abstractmethod
    def _get_targets(self, branch: Branch, /) -> Optional[Sequence[Target]]:
        "Return targets that the rule should apply to."
        return None

    @abstractmethod
    def _apply(self, target: Target, /) -> None:
        "Apply the rule to a target returned from ``._get_targets()``."
        raise NotImplementedError

    @abstractmethod
    def example_nodes(self) -> Iterable[Mapping]:
        "Return example nodes that would trigger the rule."
        raise NotImplementedError

    def sentence(self, node: Node, /) -> Optional[Sentence]:
        'Get the relevant sentence for the node, or ``None``.'
        return node.get('sentence')

    # Scoring
    def group_score(self, target: Target, /) -> float:
        # Called in tableau
        return self.score_candidate(target) / max(1, 1 + self.branching)

    # Candidate score implementation options ``is_rank_optim``
    def score_candidate(self, target: Target, /) -> float:
        return 0.0

    @final
    def target(self, branch: Branch, /) -> Optional[Target]:
        "Get the rule target if it applies."
        with self.timers['search']:
            targets = self._get_targets(branch)
            if targets:
                self._extend_targets(targets)
                return self._select_best_target(targets)

    @final
    def apply(self, target: Target, /) -> None:
        "Apply the rule to a target returned from ``.target()``."
        with self.timers['apply']:
            self.emit(Rule.Events.BEFORE_APPLY, target)
            self._apply(target)
            self.emit(Rule.Events.AFTER_APPLY, target)
            self.tableau.emit(Tableau.Events.AFTER_RULE_APPLY, target)

    def branch(self, parent: Branch|None = None, /):
        """Create a new branch on the tableau. Convenience for
        ``self.tableau.branch()``.

        Args:
            parent: The parent branch, if any.

        Returns:
            The new branch.
        """
        return self.tableau.branch(parent)

    def stats(self):
        "Compute the rule stats."
        return dict(
            name    = self.name,
            applied = len(self.history),
            timers  = {
                name: dict(
                    duration_ms  = timer.elapsed_ms(),
                    duration_avg = timer.elapsed_avg(),
                    count        = timer.count)
                for name, timer in self.timers.items()})

    def lock(self, *_):
        if self.locked:
            raise Emsg.IllegalState('Already locked')
        self.helpers = MapProxy(self.helpers)
        self.timers = MapProxy(self.timers)
        self.state |= self.state.LOCKED

    def _extend_targets(self, targets: Sequence[Target], /):
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
            max_score = None
            min_score = None
        for score, target in zip(scores, targets):
            target.update(
                rule             = self,
                is_rank_optim    = is_rank_optim,
                total_candidates = len(targets),
                candidate_score  = score,
                min_candidate_score = min_score,
                max_candidate_score = max_score)

    def _select_best_target(self, targets: Iterable[Target], /) -> Target:
        'Selects the best target. Assumes targets have been extended.'
        is_rank_optim = self.opts['is_rank_optim']
        for target in targets:
            if not is_rank_optim:
                return target
            if target['candidate_score'] == target['max_candidate_score']:
                return target

    def __getitem__(self, key: type[_RHT]) -> _RHT:
        return self.helpers[key]

    __iter__ = None

    def __setattr__(self, name, value):
        if self.locked and name in __class__.__slots__:
            raise Emsg.ReadOnly(self, name)
        super().__setattr__(name, value)

    __delattr__ = Emsg.ReadOnly.razr

    def __repr__(self):
        return (f'<{type(self).__name__} module:{self.__module__} '
            f'applied:{len(self.history)}>')

    @classmethod
    def test(cls, /, *, noassert = False):
        """Run a simple test on the rule."""
        tab = Tableau()
        tab.rules.append(cls)
        rule = tab.rules.get(cls)
        nodes = rule.example_nodes()
        branch = tab.branch()
        branch.extend(nodes)
        result = tab.step()
        tab.finish()
        if not noassert:
            assert len(rule.history) > 0
        return dictns(
            cls     = cls,
            rule    = rule,
            tableau = tab,
            branch  = branch,
            nodes   = nodes,
            result  = result)

# ----------------------------------------------

def locking(method: _F) -> _F:
    'Decorator for locking RulesRoot methods after Tableau is started.'
    @wraps(method)
    def f(self: RulesRoot, *args, **kw):
        try:
            if self.root.locked:
                raise Emsg.IllegalState('locked')
        except AttributeError:
            pass
        return method(self, *args, **kw)
    return f

class RuleGroup(Sequence[Rule]):
    """A rule group of a Tableau's ``rules``.
    
    This class supports the full ``Sequence`` standard interface for iterating,
    subscripting, and slicing.

    The :attr:`append`, :attr:`extend`, and :attr:`clear` methods provide
    mutability until the instance is locked. An input value is a subclass of
    :class:`Rule`, which is instantiated for the tableau before it is added to
    the sequence.
    
    Rule instances are indexed, and can be retrieved by its class or name
    using the :attr:`get` method.
    """

    __slots__ = ('_map', '_seq', 'name', 'root')

    name: str|None
    "The group name."
    root: RulesRoot
    _map: dict[str, Rule]
    _seq: list[Rule]

    def __init__(self, name: str|None, root:RulesRoot, /):
        self.name = name
        self.root = root
        self._seq = []
        self._map = {}

    @locking
    def append(self, rulecls: type[Rule], /):
        """Instantiate and append a rule class.

        Args:
          rulecls: A :class:`Rule` class.

        Raises:
          ValueError: If there is a duplicate name.
          TypeError: If `value` is not a subclass of :class:`Rule`.
          errors.IllegalStateError: If locked.
        """
        rulecls = check.subcls(rulecls, Rule)
        name = rulecls.name
        root = self.root
        tab = root.tableau
        root._checkname(name)
        rule = rulecls(tab, **tab.opts)
        self._seq.append(rule)
        self._map[name] = rule
        root._map[name] = rule
        # rule.on(Rule.Events.AFTER_APPLY, tab._after_rule_apply)

    def extend(self, classes, /):
        """Append multiple rules.

        Args:
          classes: An iterable of :class:`Rule` classes.

        Raises:
          ValueError: If there is a duplicate name.
          TypeError: If an element is not a subclass of :class:`Rule`.
          errors.IllegalStateError: If locked.
        """
        for _ in map(self.append, classes): pass

    @locking
    def clear(self):
        """Clear the rule group.

        Raises:
          errors.IllegalStateError: If locked.
        """
        self._seq.clear()
        self._map.clear()

    def get(self, ref, default = NOARG, /) -> Rule:
        """Get rule instance by name or type.

        Args:
          ref: A :class:`Rule` class or name.
          default: A value to return if rule not found.

        Returns:
          The rule instance, or ``default`` if it is specified and the rule was
          not found.

        Raises:
          KeyError: If rule not found and ``default`` not passed.
          TypeError: For bad ``ref`` type.
        """
        if not isinstance(ref, str):
            ref = check.subcls(ref, Rule).name
        try:
            return self._map[ref]
        except KeyError:
            if default is NOARG:
                raise
            return default

    def names(self):
        'Return all the rule names.'
        return self._map.keys()

    def lock(self):
        self._seq = SeqCover(self._seq)
        self._map = MapProxy(self._map)

    def __getitem__(self, index):
        return self._seq[index]

    def __len__(self):
        return len(self._seq)

    def __contains__(self, ref):
        if isinstance(ref, type): # class
            ref = check.subcls(ref, Rule).name
        if isinstance(ref, str): # name
            return ref in self._map
        if isinstance(ref, Rule): # instance
            return self._map.get(ref.name, None) is ref
        raise Emsg.InstCheck(ref, (str, Rule, type))

    __delattr__ = Emsg.ReadOnly.razr
    __setattr__ = locking(object.__setattr__)

    def __repr__(self):
        return f'<{type(self).__name__} name:{self.name} rules:{len(self)}>'

class RuleGroups(Sequence[RuleGroup]):

    __slots__ = ('root', '_seq', '_map')

    _seq: list[RuleGroup]
    _map: dict[str, RuleGroup]
    root: RulesRoot

    def __init__(self, root, /):
        self.root = root
        self._seq = []
        self._map = {}

    @locking
    def create(self, name = None):
        'Create and return a new emtpy rule group.'
        if name is not None:
            self.root._checkname(name)
        group = RuleGroup(name, self.root)
        self._seq.append(group)
        if name is not None:
            self._map[name] = group
        return group

    def append(self, classes, /, name = NOARG):
        'Create a new group with the given rules. Raise IllegalStateError if locked.'
        if name is NOARG:
            name = None
        self.create(name).extend(classes)

    def extend(self, groups):
        'Add multiple groups. Raise IllegalStateError if locked.'
        for _ in map(self.append, groups): pass

    @locking
    def clear(self):
        'Clear the groups. Raise IllegalStateError if locked.'
        for _ in map(RuleGroup.clear, self): pass
        self._seq.clear()
        self._map.clear()

    def get(self, name, default = NOARG, /) -> RuleGroup:
        'Get a group by name.'
        try:
            return self._map[name]
        except KeyError:
            if default is NOARG:
                raise
            return default

    def names(self) -> Set[str]:
        'List the named groups.'
        return self._map.keys()

    def lock(self):
        for _ in map(RuleGroup.lock, self): pass
        self._seq = SeqCover(self._seq)

    def __contains__(self, item):
        if isinstance(item, str): # group name
            return item in self._map
        return item in self._seq # group instance

    __len__ = RuleGroup.__len__
    __getitem__ = RuleGroup.__getitem__
    __delattr__ = Emsg.ReadOnly.razr
    __setattr__ = locking(object.__setattr__)

    def __repr__(self):
        logic = self.root.tableau.logic
        lname = logic.name if logic else None
        return (f'<{type(self).__name__} logic:{lname} groups:{len(self)} '
            f'names:{list(self.names())} rules:{sum(map(len, self))}>')

class RulesRoot(Sequence[Rule]):
    'Grouped and named collection of rules for a tableau.'

    __slots__ = ('_map', 'groups', 'locked', 'root', 'tableau')
 
    groups: RuleGroups
    "The rule groups sequence view."
    locked: bool
    root: RulesRoot
    tableau: Tableau
    _map: dict[str, Rule]

    def __init__(self, tableau: Tableau, /):
        self._map = {}
        self.locked = False
        self.root = self
        self.tableau = tableau
        self.groups = RuleGroups(self)
        tableau.once(Tableau.Events.AFTER_BRANCH_ADD, self.lock)

    def append(self, rulecls, /, name = None):
        'Add a single Rule to a new group.'
        self.groups.create(name).append(rulecls)

    def extend(self, classes, /, name = None):
        'Create a new group from a collection of Rule classes.'
        self.groups.create(name).extend(classes)

    def clear(self):
        'Clear all the rules. Raises IllegalStateError if tableau is started.'
        self.groups.clear()
        self._map.clear()

    get = RuleGroup.get
    names = RuleGroup.names

    @locking
    def lock(self, _ = None):
        self.tableau.off(Tableau.Events.AFTER_BRANCH_ADD, self.lock)
        self.groups.lock()
        self._map = MapProxy(self._map)
        self.locked = True

    def __len__(self):
        return len(self._map)

    __contains__ = RuleGroup.__contains__

    def __iter__(self):
        for group in self.groups:
            yield from group

    def __reversed__(self):
        for group in reversed(self.groups):
            yield from reversed(group)

    def __getitem__(self, index, /):
        length = len(self)
        index = absindex(length, index)
        if 2 * index > length:
            i, iterfunc, adjust, compare = length, reversed, opr.sub, opr.le
        else:
            i, iterfunc, adjust, compare = 0, iter, opr.add, opr.gt
        for group in iterfunc(self.groups):
            inext = adjust(i, len(group))
            if compare(inext, index):
                return group[index - i]
            i = inext
        raise TypeError # should never run.

    def __repr__(self):
        logic = self.tableau.logic
        lname = logic.name if logic else None
        return (f'<{type(self).__name__} logic:{lname} '
            f'groups:{len(self.groups)} rules:{len(self)}>')

    __delattr__ = Emsg.ReadOnly.razr
    __setattr__ = locking(object.__setattr__)

    def _checkname(self, name: str, /):
        'Validate a new rule or group name before it is added.'
        check.inst(name, str)
        if name in self.groups or name in self._map:
            raise Emsg.DuplicateKey(name)

# ----------------------------------------------

class Tableau(Sequence[Branch], EventEmitter, metaclass=TableauMeta):
    'A tableau proof.'

    rules: RulesRoot
    "The rule instances."

    opts: Mapping
    "The build options."

    open: Sequence[Branch]
    "Ordered view of the open branches."

    history: Sequence[Tableau.StepEntry]
    "The history of rule applications."

    tree: Tableau.Tree
    """A tree structure of the tableau. This is generated after the tableau
    is finished. If the `build_timeout` was exceeded, the tree is `not`
    built."""

    stats: dict
    "The stats, built after finished."

    models: frozenset[BaseModel]
    """The models, built after finished if the tableau is `invalid` and the
    `is_build_models` option is enabled."""

    timers: Tableau.Timers
    "The tableau timers."

    flag: Tableau.Flag
    "The :class:`Tableau.Flag` value."

    _defaults = MapProxy(dict(
        is_group_optim  = True,
        is_build_models = False,
        build_timeout   = None,
        max_steps       = None))

    def __init__(self, logic=None, argument=None, /, **opts):
        """
        Args:
            logic: The logic name or module.
            argument: The argument for the tableau.
            **opts: The build options.
        """
        # Events init
        EventEmitter.__init__(self, *Tableau.Events)
        # Protected attributes
        self._branches: list[Branch] = []
        self._open: linqset[Branch] = linqset()
        self._stat = self.Stat()
        # Exposed attributes
        self.flag = Tableau.Flag.PREMATURE
        self.history = SeqCover(history := [])
        self.opts = self._defaults | opts
        self.timers = Tableau.Timers.create()
        self.rules = RulesRoot(self)
        self.open = SeqCover(self._open)
        # Private
        self._complexities: dict[Node, int] = {}
        self._branch_listeners = MapProxy(
            self._make_branch_listeners(self._stat, self._open))
        self._tab_listeners = MapProxy(self._make_tab_listeners(history))
        # Init
        self.stat = self._stat.query
        self.on(self._tab_listeners)
        maxsteps = self.opts['max_steps']
        if maxsteps is not None and maxsteps > 0:
            self.flag |= self.flag.HAS_STEP_LIMIT
        timeout = self.opts['build_timeout']
        if timeout is not None and timeout > 0:
            self.flag |= self.flag.HAS_TIME_LIMIT
        if logic is not None:
            self.logic = logic
        if argument is not None:
            self.argument = argument

    @property
    def id(self):
        "The unique object ID of the tableau."
        return id(self)

    @property
    def argument(self):
        """The argument of the tableau.

        When setting this value, if the tableau has a logic set, then the
        trunk is automatically built.
        """
        try:
            return self.__argument
        except AttributeError:
            pass

    @property
    def logic(self):
        "The logic of the tableau."
        try:
            return self.__logic
        except AttributeError:
            pass

    @property
    def System(self):
        "Alias for :attr:`logic.TableauxSystem`"
        try:
            return self.logic.TableauxSystem
        except AttributeError:
            pass

    @argument.setter
    def argument(self, value):
        self._check_not_started()
        self.__argument = Argument(value)
        if self.logic is not None:
            self._build_trunk()

    @logic.setter
    def logic(self, value):
        self._check_not_started()
        self.__logic = registry(value)
        self.rules.clear()
        self.System.add_rules(self.logic, self.rules)
        if self.argument is not None:
            self._build_trunk()

    @property
    def finished(self):
        """Whether the tableau is finished. A tableau is `finished` iff `any` of the
        following conditions apply:
        
        * The tableau is `completed`.
        * The `max_steps` option is met or exceeded.
        * The `build_timeout` option is exceeded.
        * The :attr:`finish` method is manually invoked.
        """
        return self.flag.FINISHED in self.flag

    @property
    def completed(self):
        """Whether the tableau is completed. A tableau is `completed` iff all rules
        that can be applied have been applied."""
        return self.flag.FINISHED in self.flag and self.flag.PREMATURE not in self.flag

    @property
    def premature(self):
        """Whether the tableau is finished prematurely. A tableau is `premature` iff
        it is `finished` but not `completed`."""
        return self.flag.FINISHED in self.flag and self.flag.PREMATURE in self.flag

    @property
    def valid(self):
        """Whether the tableau's argument is valid (proved). A tableau with an
        argument is `valid` iff it is :attr:`completed` and it has no open branches.
        If the tableau is not completed, or it has no argument, the value will
        be None."""
        if self.completed and self.argument is not None:
            return len(self.open) == 0

    @property
    def invalid(self):
        """Whether the tableau's argument is invalid (disproved). A tableau with
        an argument is `invalid` iff it is :attr:`completed` and it has at least one
        open branch. If the tableau is not completed, or it has no argument,
        the value will be None."""
        if self.completed and self.argument is not None:
            return len(self.open) > 0

    @property
    def current_step(self):
        """The current step number. This is the number of rule applications, plus 1
        if the argument trunk is built."""
        return len(self.history) + (self.flag.TRUNK_BUILT in self.flag)

    if TYPE_CHECKING:
        @overload
        def stat(self, branch: Branch, /, *keys): ...

    def build(self):
        'Build the tableau. Returns self.'
        with self.timers.build:
            while not self.finished:
                self._check_timeout()
                self.step()
        self.finish()
        return self

    def next(self) -> Optional[Tableau.StepEntry]:
        """Choose the next rule step to perform. Returns the StepEntry or ``None``
        if no rule can be applied.

        This iterates over the open branches, then over rule groups.
        """
        for branch in self.open:
            for group in self.rules.groups:
                res = self._get_group_application(branch, group)
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
        if self.flag.FINISHED in self.flag:
            return False
        entry = None
        with StopWatch() as timer:
            if not self._is_max_steps_exceeded():
                entry = self.next()
                if entry is None:
                    self.flag &= ~self.flag.PREMATURE
            if entry is not None:
                entry.rule.apply(entry.target)
                entry.duration.inc(timer.elapsed_ms())
            else:
                self.finish()
        return entry

    def stepiter(self):
        while True:
            step = self.step()
            if not step:
                break
            yield step

    def branch(self, /, parent: Branch = None):
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

    def add(self, /, branch: Branch):
        """Add a new branch to the tableau. Returns self.

        Args:
            branch: The branch to add.

        Returns:
            self
        """
        index = len(self)
        if not branch.closed:
            # Append to linqset will raise duplicate value error.
            self._open.append(branch)
        elif branch in self:
            raise Emsg.DuplicateValue(branch.id)
        self._branches.append(branch)
        self._stat[branch] = self.BranchStat({
            Tableau.StatKey.STEP_ADDED : self.current_step,
            Tableau.StatKey.INDEX      : index,
            Tableau.StatKey.PARENT     : branch.parent})
        # For corner case of an AFTER_BRANCH_ADD callback adding a node, make
        # sure we don't emit AFTER_NODE_ADD twice, so prefetch the nodes.
        nodes = tuple(branch) if branch.parent is None else EMPTY_SET
        # This means we need to start listening before we emit. There
        # could be the possibility of recursion.
        branch.on(self._branch_listeners)
        self.emit(Tableau.Events.AFTER_BRANCH_ADD, branch)
        if len(nodes):
            afteradd = self._branch_listeners[Branch.Events.AFTER_ADD]
            for node in nodes:
                afteradd(node, branch)
        return self

    def finish(self):
        """Mark the tableau as finished, and perform post-build tasks, including
        populating the ``tree``, ``stats``, and ``models`` properties.
        
        When using the ``build()`` or ``step()`` methods, there is never a need
        to call this method, since it is handled internally. However, this
        method *is* safe to call multiple times. If the tableau is already
        finished, it will be a no-op.

        Returns:
            self
        """
        if self.flag.FINISHED in self.flag:
            return self
        self.flag |= self.flag.FINISHED
        if self.invalid and self.opts['is_build_models'] and self.logic is not None:
            with self.timers.models:
                self.models = frozenset(self._gen_models())
        if self.flag.TIMED_OUT not in self.flag:
            # In case of a timeout, we do `not` build the tree in order to best
            # respect the timeout. In case of `max_steps` excess, however, we
            # `do` build the tree.
            with self.timers.tree:
                self.tree = self._build_tree(self)
        self.stats = self._compute_stats()
        self.emit(Tableau.Events.AFTER_FINISH, self)
        return self

    def branching_complexity(self, node: Node, /):
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
        cache = self._complexities
        if node not in cache:
            system = self.System
            if system is None:
                return 0
            cache[node] = system.branching_complexity(node)
        return cache[node]

    def __getitem__(self, index):
        return self._branches[index]

    def __len__(self):
        return len(self._branches)

    def __bool__(self):
        return True

    def __contains__(self, branch):
        return branch in self._stat

    def __repr__(self):
        info = dict(
            id    = self.id,
            logic = (self.logic and self.logic.name),
            len   = len(self),
            open  = len(self.open),
            step  = self.current_step,
            finished = self.finished)
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

    def _make_branch_listeners(self, stat: Tableau.Stat, opens: linqset[Branch]):

        def after_close(branch: Branch):
            bstat = stat[branch]
            bstat[Tableau.StatKey.STEP_CLOSED] = self.current_step
            bstat[Tableau.StatKey.FLAGS] |= self.flag.CLOSED
            opens.remove(branch)
            self.emit(Tableau.Events.AFTER_BRANCH_CLOSE, branch)

        def after_add(node: Node, branch: Branch):
            bstat = stat[branch].node(node)
            bstat[Tableau.StatKey.STEP_ADDED] = node.step = self.current_step
            self.emit(Tableau.Events.AFTER_NODE_ADD, node, branch)

        def after_tick(node: Node, branch: Branch):
            bstat = stat[branch].node(node)
            bstat[Tableau.StatKey.STEP_TICKED] = self.current_step
            bstat[Tableau.StatKey.FLAGS] |= self.flag.TICKED
            self.emit(Tableau.Events.AFTER_NODE_TICK, node, branch)

        return {
            Branch.Events.AFTER_CLOSE : after_close,
            Branch.Events.AFTER_ADD   : after_add,
            Branch.Events.AFTER_TICK  : after_tick}

    def _make_tab_listeners(self, history: list):
        def after_rule_apply(target: Target):
            try:
                history.append(target._entry)
            except AttributeError:
                history.append(Tableau.StepEntry(target.rule, target, Counter()))
                self.flag |= self.flag.TIMING_INACCURATE
            self.flag |= self.flag.STARTED
        return {
            Tableau.Events.AFTER_RULE_APPLY: after_rule_apply}

    def _get_group_application(self, branch, group: Sequence[Rule], /) -> Tableau.StepEntry:
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
                entry = Tableau.StepEntry(rule, target, Counter())
                target._entry = entry
                if not is_group_optim:
                    target.update(
                        group_score         = None,
                        total_group_targets = 1,
                        min_group_score     = None,
                        is_group_optim      = False)
                    return entry
                results.append(entry)
        if results:
            return self._select_optim_group_application(results)

    def _select_optim_group_application(self, results: Sequence[Tableau.StepEntry], /) -> Tableau.StepEntry:
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
        group_scores = tuple(entry.rule.group_score(entry.target)
            for entry in results)
        max_group_score = max(group_scores)
        min_group_score = min(group_scores)
        for group_score, res in zip(group_scores, results):
            if group_score == max_group_score:
                res.target.update(
                    group_score         = max_group_score,
                    total_group_targets = len(results),
                    min_group_score     = min_group_score,
                    is_group_optim      = True)
                return res

    def _build_trunk(self):
        """Build the trunk of the tableau. Delegates to the ``build_trunk()``
        method of ``TableauxSystem``. This is called automatically when the
        tableau has non-empty ``argument`` and ``logic`` properties.

        Raises:
            errors.IllegalStateError: if the trunk is already built.
        """
        self._check_not_started()
        with self.timers.trunk:
            self.emit(Tableau.Events.BEFORE_TRUNK_BUILD, self)
            self.System.build_trunk(self, self.argument)
            self.flag |= self.flag.TRUNK_BUILT | self.flag.STARTED
            self.emit(Tableau.Events.AFTER_TRUNK_BUILD, self)

    def _compute_stats(self):
        'Compute the stats property after the tableau is finished.'
        try:
            distinct_nodes = self.tree.distinct_nodes
        except AttributeError:
            distinct_nodes = None
        timers = self.timers
        return dict(
            result          = self._result_word(),
            branches        = len(self),
            open_branches   = len(self.open),
            closed_branches = len(self) - len(self.open),
            steps           = len(self.history),
            distinct_nodes  = distinct_nodes,
            rules_duration_ms = sum(
                step.duration.value
                for step in self.history),
            build_duration_ms  = timers.build.elapsed_ms(),
            trunk_duration_ms  = timers.trunk.elapsed_ms(),
            tree_duration_ms   = timers.tree.elapsed_ms(),
            models_duration_ms = timers.models.elapsed_ms(),
            rules_time_ms = sum(
                rule.timers[name].elapsed_ms()
                for rule in self.rules
                    for name in ('search', 'apply')))

    def _check_timeout(self):
        if self.flag.HAS_TIME_LIMIT not in self.flag:
            return
        if self.timers.build.elapsed_ms() > self.opts['build_timeout']:
            self.timers.build.stop()
            self.flag |= self.flag.TIMED_OUT
            self.finish()
            raise Emsg.Timeout(self.opts['build_timeout'])

    def _is_max_steps_exceeded(self) -> bool:
        return (
            self.flag.HAS_STEP_LIMIT in self.flag and
            len(self.history) >= self.opts['max_steps'])

    def _check_not_started(self):
        # if self.flag.TRUNK_BUILT in self.flag or len(self.history) > 0:
        if self.flag.STARTED in self.flag:
            raise Emsg.IllegalState("Tableau already started.")

    def _result_word(self) -> str:
        if self.valid:
            return 'Valid'
        if self.invalid:
            return 'Invalid'
        if self.completed:
            return 'Completed'
        return 'Unfinished'

    def _gen_models(self):
        'Build models for the open branches.'
        Model = self.logic.Model
        for branch in self.open:
            self._check_timeout()
            model = Model()
            model.read_branch(branch)
            branch.model = model
            yield model

    def _build_tree(self, branches: Sequence[Branch], depth=0, memo=None,/) -> Tableau.Tree:
        tree = self.Tree()
        if memo is None:
            memo = dict(pos=1, depth=0, distinct_nodes=0, root=tree)
            tree.root = True
        else:
            memo['pos'] += 1
        tree.update(
            depth = memo['depth'],
            left  = memo['pos'])
        while True:
            # Each branch's node at depth.
            nodes = set()
            specimen = None
            for branch in branches:
                if len(branch) <= depth:
                    # Consider only branches with a node at depth.
                    continue
                if specimen is None:
                    specimen = branch
                nodes.add(branch[depth])
                if self.flag.CLOSED in self.stat(branch, Tableau.StatKey.FLAGS):
                    tree.has_closed = True
                else:
                    tree.has_open = True
            if len(nodes) != 1:
                # There is *not* a singular node shared by all branches at depth.
                break
            # There is one node shared by all branches at depth, thus the
            # branches are equivalent up to this depth.
            branch = specimen
            node, = nodes
            tree.nodes.append(node)
            tree.ticksteps.append(self.stat(branch, node, Tableau.StatKey.STEP_TICKED))
            step_added = self.stat(branch, node, Tableau.StatKey.STEP_ADDED)
            if tree.step is None or step_added < tree.step:
                tree.step = step_added
            depth += 1
        memo['distinct_nodes'] += len(tree.nodes)
        if len(branches) == 1:
            # Finalize leaf attributes.
            self._build_tree_leaf(tree, branches[0], memo)
        else:
            # Build child structures for each distinct node at node_depth.
            memo['depth'] += 1
            self._build_tree_branches(tree, branches, nodes, depth, memo)
            memo['depth'] -= 1
        tree.structure_node_count = tree.descendant_node_count + len(tree.nodes)
        memo['pos'] += 1
        tree.right = memo['pos']
        if memo['root'] is tree:
            tree.distinct_nodes = memo['distinct_nodes']
        return tree

    def _build_tree_leaf(self, tree: Tableau.Tree, branch: Branch, memo: dict, /):
        'Finalize attributes for leaf structure.'
        tree.closed = self.flag.CLOSED in self.stat(branch, Tableau.StatKey.FLAGS)
        tree.open = not tree.closed
        if tree.closed:
            tree.closed_step = self.stat(branch, Tableau.StatKey.STEP_CLOSED)
            tree.has_closed = True
        else:
            tree.has_open = True
        tree.width = 1
        tree.leaf = True
        tree.branch_id = branch.id
        if branch.model is not None:
            tree.model_id = branch.model.id
        if memo['depth'] == 0:
            tree.is_only_branch = True

    def _build_tree_branches(self, tree: Tableau.Tree, branches: Sequence[Branch], nodes: Set[Node], depth: int, memo: dict, /):
        'Build child structures for each distinct node.'

        # Widths of first, middle, last
        widths = [0] * 3
        for i, node in enumerate(nodes):
            # recurse
            next_branches = tuple(b for b in branches if b[depth] == node)
            child = self._build_tree(next_branches, depth, memo)
            tree.descendant_node_count = len(child.nodes) + child.descendant_node_count
            tree.width += child.width
            tree.children.append(child)
            if i == 0:
                # first node
                tree.branch_step = child.step
                widths[0] = child.width / 2
            elif i == len(nodes) - 1:
                # last node
                widths[2] = child.width / 2
            else:
                widths[1] += child.width
            tree.branch_step = min(tree.branch_step, child.step)
        if tree.width > 0:
            tree.balanced_line_width = sum(widths) / tree.width
            tree.balanced_line_margin = widths[0] / tree.width
        else:
            tree.balanced_line_width = tree.balanced_line_margin = 0

    class NodeStat(dict):
        __slots__ = EMPTY_SET
        Flag = TableauMeta.Flag
        Key = TableauMeta.StatKey
        _defaults = MapProxy({
            Key.FLAGS       : Flag(0),
            Key.STEP_ADDED  : Flag(0),
            Key.STEP_TICKED : None})

        def __init__(self):
            super().__init__(self._defaults)

    class BranchStat(dict):
        __slots__ = EMPTY_SET
        Flag = TableauMeta.Flag
        Key = TableauMeta.StatKey
        _defaults = MapProxy({
            Key.FLAGS       : Flag(0),
            Key.STEP_ADDED  : Flag(0),
            Key.STEP_CLOSED : Flag(0),
            Key.INDEX       : None,
            Key.PARENT      : None})

        def __init__(self, mapping = None, /, **kw):
            super().__init__(self._defaults)
            self[self.Key.NODES] = {}
            if mapping is not None:
                self.update(mapping)
            if len(kw):
                self.update(kw)

        def node(self, node, /):
            'Get the stat info for the node, and create if missing.'
            # Avoid using defaultdict, since it may hide problems.
            try:
                return self[self.Key.NODES][node]
            except KeyError:
                return self[self.Key.NODES].setdefault(node, Tableau.NodeStat())

        def view(self):
            return {k: self[k] for k in self._defaults}


    class Stat(dict[Branch, BranchStat]):

        __slots__ = EMPTY_SET
        Key = TableauMeta.StatKey

        def query(self, branch: Branch, /, *keys):
            # Lookup options:
            # - branch
            # - branch, key
            # - branch, node
            # - branch, node, key
            stat = self[branch]
            kit = iter(keys)
            try:
                key = next(kit)
            except StopIteration:
                # branch
                return stat.view()
            if isinstance(key, Node):
                # branch, node
                stat = stat[self.Key.NODES][key]
                try:
                    key = self.Key(next(kit))
                except StopIteration:
                    return MapProxy(stat)
                else:
                    # branch, node, key
                    stat = stat[key]
                    try:
                        next(kit)
                    except StopIteration:
                        # literal value
                        return stat
                    raise ValueError('Too many keys to lookup')
            key = self.Key(key)
            try:
                # branch, key
                stat = stat[key]
                next(kit)
            except StopIteration:
                if key is self.Key.NODES:
                    raise NotImplementedError('Full nodes view not supported')
                # literal value
                return stat
            raise ValueError('Too many keys to lookup')


    class Tree(dictns):
        'Recursive tree structure representation of a tableau.'

        root: bool = False
        
        nodes: list[Node]
        "The nodes on this structure."

        ticksteps: list[int|None]
        "The ticked steps list."

        children: list[Tableau.Tree]
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

        closed_step: Optional[int] = None
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

        branch_id: Optional[int] = None
        "The branch id, only set for leaves"

        model_id: Optional[int] = None
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
