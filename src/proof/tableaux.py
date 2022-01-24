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
from __future__ import annotations

__all__ = 'Rule', 'TableauxSystem', 'Tableau'

from callables import preds
from .common import FLAG, KEY, Branch, BranchEvent, Node, RuleEvent, TabEvent, Target
from decorators import abstract, final, overload, static, wraps
from errors import (
    Emsg, DuplicateKeyError, IllegalStateError, MissingValueError,
    TimeoutError, instcheck
)
from events import EventEmitter
from lexicals import Argument, Sentence
from models import BaseModel
from tools.abcs import Abc, AbcMeta, abcm, P, T
from tools.sets import EMPTY_SET
from tools.sequences import (
    MutableSequenceApi, SequenceApi, SequenceProxy, DeqSeq,
)
from tools.mappings import MapCover, dmap
from tools.hybrids import qsetf
from tools.linked import linqset
from tools.timing import StopWatch
from utils import get_logic, orepr

from itertools import chain
import itertools
from types import ModuleType
from typing import (
    Callable, Iterator, Iterable, Mapping, Sequence,
    Any, ClassVar, NamedTuple, SupportsIndex
)

LogicRef = ModuleType | str


class RuleMeta(AbcMeta):

    def __new__(cls, clsname, bases, ns: dict, **kw):
        helpers_attr = 'Helpers'
        helper_attrs = cls._get_helper_attrs(ns, helpers_attr)
        Class = super().__new__(cls, clsname, bases, ns, **kw)
        cls._set_helper_attrs(Class, helper_attrs, helpers_attr)
        return Class

    @staticmethod
    def _get_helper_attrs(ns: dict, clsattr: str):
        taken = dict(ns)
        attrs = dict[type, str]()
        raw = ns.get(clsattr, ())
        instcheck(raw, tuple)
        for item in raw:
            if isinstance(item, type): item = None, item
            instcheck(item, tuple)
            if len(item) != 2: raise Emsg.WrongLength(item, 2)
            name, Helper = item
            instcheck(Helper, type)
            if name is None: name = getattr(Helper, '_attr', None)
            else:
                name = instcheck(name, str)
                if name in taken:
                    raise ValueError("Conflict for '%s'" % name)
                if not preds.isattrstr(name):
                    raise ValueError('Invalid attribute: %s' % name)
            if Helper in attrs:
                # Helper class already added
                if name is not None:
                    # Check for attr name conflict.
                    if attrs[Helper] is None:
                        # Prefer named attr to unnamed.
                        attrs[Helper] = name
                        taken[name] = Helper
                    elif name != attrs[Helper]:
                        raise ValueError(
                            'Duplicate helper class: %s as attr: %s (was: %s)' %
                            (Helper, name, attrs[Helper])
                        )
            else:
                attrs[Helper] = name
                if name is not None:
                    taken[name] = Helper
        return attrs

    @staticmethod
    def _set_helper_attrs(Class: type, attrs: dict, clsattr: str):
        filt = filter(bool, itertools.chain(
            * (
                c.__dict__.get(clsattr, EMPTY_SET)
                for c in reversed(Class.mro()[1:])
            ),
            (
                (v, k) for k,v in attrs.items()
            )
        ))
        hlist = qsetf((item for item in filt if item[1] != None))
        setattr(Class, clsattr, tuple(hlist))

class RuleHelperInfo(NamedTuple):
    #: The helper class.
    cls  : type
    #: The helper instance.
    inst : object
    #: The rule attribute name.
    attr : str

class RuleTarget(NamedTuple):
    rule   : Rule
    target : Target

class StepEntry(NamedTuple):
    #: The rule instance that was applied.
    rule   : Rule
    #: The target returned by the rule.
    target : Target
    #: The duration in milliseconds of the application.
    duration_ms: int

class NodeStat(dict[KEY, FLAG|int|None]):

    __slots__ = EMPTY_SET

    _defaults = MapCover({
        KEY.FLAGS       : FLAG.NONE,
        KEY.STEP_ADDED  : FLAG.NONE,
        KEY.STEP_TICKED : None,
    })

    def __init__(self):
        super().__init__(self._defaults)

class BranchStat(dict[KEY, FLAG|int|Branch|dict[Node, NodeStat]|None]):

    __slots__ = EMPTY_SET

    _defaults = MapCover({
        KEY.FLAGS       : FLAG.NONE,
        KEY.STEP_ADDED  : FLAG.NONE,
        KEY.STEP_CLOSED : FLAG.NONE,
        KEY.INDEX       : None,
        KEY.PARENT      : None,
    })

    def __init__(self):
        super().__init__(self._defaults)
        self[KEY.NODES] = {}

    def node(self, node: Node) -> NodeStat:
        if node not in self[KEY.NODES]:
            self[KEY.NODES][node] = NodeStat()
        return self[KEY.NODES][node]

    def view(self) -> dict[KEY, FLAG|int|Branch|None]:
        return {k: self[k] for k in self._defaults}

class Rule(EventEmitter, metaclass = RuleMeta):
    'Base class for a Tableau rule.'

    Helpers: ClassVar[Sequence[tuple[str, type]]] = ()
    Timers: ClassVar[Sequence[str]] = ()
    HelperRuleEventMethods: ClassVar[Sequence[tuple[RuleEvent, str]]] = (
        (RuleEvent.AFTER_APPLY  , 'after_apply'),
        (RuleEvent.BEFORE_APPLY , 'before_apply'),
    )
    HelperTabEventMethods: ClassVar[Sequence[tuple[TabEvent, str]]] = (
        (TabEvent.AFTER_BRANCH_ADD   , 'after_branch_add'),
        (TabEvent.AFTER_BRANCH_CLOSE , 'after_branch_close'),
        (TabEvent.AFTER_NODE_ADD     , 'after_node_add'),
        (TabEvent.AFTER_NODE_TICK    , 'after_node_tick'),
        (TabEvent.AFTER_TRUNK_BUILD  , 'after_trunk_build'),
        (TabEvent.BEFORE_TRUNK_BUILD , 'before_trunk_build'),
    )
    branch_level: ClassVar[int] = 1
    _defaults: ClassVar[dict[str, bool]] = {'is_rank_optim': True}

    #: Reference to the tableau instance.
    tableau: Tableau
    helpers: Mapping[type, object]
    timers: Mapping[str, StopWatch]
    #: The number of times the rule has applied.
    apply_count: int

    __slots__ = 'tableau', 'helpers', 'apply_count', 'timers', 'opts', '__dict__'

    @abstract
    def _get_targets(self, branch: Branch) -> Sequence[Target]:
        raise NotImplementedError

    @abstract
    def _apply(self, target: Target):
        raise NotImplementedError

    @abstract
    def example_nodes(self) -> Sequence[Mapping]:
        raise NotImplementedError

    def sentence(self, node: Node) -> Sentence:
        """Get the sentence for the node, or ``None``."""
        return node.get('sentence')

    # Scoring
    def group_score(self, target: Target) -> float:
        # Called in tableau
        return self.score_candidate(target) / max(1, self.branch_level)

    # Candidate score implementation options ``is_rank_optim``
    def score_candidate(self, target: Target) -> float:
        return 0

    def __init__(self, tableau: Tableau, **opts):
        self.tableau = instcheck(tableau, Tableau)
        super().__init__(*RuleEvent)

        self.search_timer = StopWatch()
        self.apply_timer = StopWatch()
        self.timers = dict[str, StopWatch]()
        if self.Timers:
            self.timers |= ((name, StopWatch()) for name in self.Timers)

        self.opts = self._defaults | opts

        self.helpers = {}
        self.apply_count = 0

        for name, helper in self.Helpers:
            self.add_helper(helper, name)

    @property
    def name(self) -> str:
        'The rule name, default it the class name.'
        return type(self).__name__

    @final
    def get_target(self, branch: Branch) -> Target:
        targets = self._get_targets(branch)
        if targets:
            self.__extend_targets(targets)
            return self.__select_best_target(targets)

    @final
    def apply(self, target: Target):
        with self.apply_timer:
            self.emit(RuleEvent.BEFORE_APPLY, target)
            self._apply(target)
            self.apply_count += 1
            self.emit(RuleEvent.AFTER_APPLY, target)

    @final
    def branch(self, parent: Branch = None) -> Branch:
        """Create a new branch on the tableau. Convenience for
        ``self.tableau.branch()``.

        :param tableaux.Branch parent: The parent branch, if any.
        :return: The new branch."""
        return self.tableau.branch(parent)

    @final
    def add_helper(self, cls: type, attr: str = None, **opts) -> RuleHelperInfo:
        'Add a helper.'
        inst = cls(self, **opts)
        info = RuleHelperInfo(cls, inst, attr)
        self.helpers[cls] = inst
        if attr != None:
            setattr(self, attr, inst)
        for event, meth in self.HelperRuleEventMethods:
            if hasattr(inst, meth):
                self.on(event, getattr(inst, meth))
        for event, meth in self.HelperTabEventMethods:
            if hasattr(inst, meth):
                self.tableau.on(event, getattr(inst, meth))
        return info

    def __repr__(self):
        return orepr(self,
            module      = self.__module__,
            apply_count = self.apply_count,
        )

    def __setattr__(self, name, value):
        if name == 'tableau' and hasattr(self, name):
            raise AttributeError(name)
        super().__setattr__(name, value)

    def __delattr__(self, name):
        if name == 'tableau':
            raise AttributeError(name)
        super().__delattr__(name)

    def __extend_targets(self, targets: Sequence[Target]):
        """
        Augment the targets with the following keys:
        
        - `rule`
        - `is_rank_optim`
        - `candidate_score`
        - `total_candidates`
        - `min_candidate_score`
        - `max_candidate_score`

        :param Sequence[Target] targets: The list of targets.
        :param common.Branch branch: The branch.
        """
        instcheck(targets, Sequence)
        if self.opts['is_rank_optim']:
            scores = tuple(map(self.score_candidate, targets))
        else:
            scores = 0,
        max_score = max(scores)
        min_score = min(scores)
        for score, target in zip(scores, targets):
            target.update({
                'rule'            : self,
                'total_candidates': len(targets),
            })
            if self.opts['is_rank_optim']:
                target.update({
                    'is_rank_optim'       : True,
                    'candidate_score'     : score,
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

    def __select_best_target(self, targets: Iterable[Target]) -> Target:
        """
        Selects the best target. Assumes targets have been extended.
        """
        for target in targets:
            if not self.opts['is_rank_optim']:
                return target
            if target['candidate_score'] == target['max_candidate_score']:
                return target


class TabRulesSharedData:

    __slots__ = 'ruleindex', 'groupindex', 'locked', 'tab', 'root'

    def lock(self, *_):
        if self.locked:
            raise ValueError('already locked')
        self.ruleindex = MapCover(self.ruleindex)
        self.groupindex = MapCover(self.groupindex)
        self.locked = True

    def __init__(self, tableau: Tableau, root):
        self.ruleindex = {}
        self.groupindex = {}
        self.locked = False
        self.tab: Tableau = tableau
        self.root: TabRules = root
        tableau.once(TabEvent.AFTER_BRANCH_ADD, self.lock)

    def __delattr__(self, name):
        raise AttributeError(name)

    def __setattr__(self, attr, val):
        if getattr(self, 'locked', False):
            raise AttributeError('locked (%s)' % attr)
        if hasattr(self, 'root') and attr != 'locked':
            if attr in ('ruleindex', 'groupindex') and (
                isinstance(val, MapCover) and
                not isinstance(getattr(self, attr), MapCover)
            ):
                pass
            else:
                raise AttributeError(attr)
        super().__setattr__(attr, val)

class TabRulesBase:

    @property
    def locked(self) -> bool:
        return self._common.locked

    @property
    def tab(self) -> Tableau:
        return self._common.tab

    @property
    def logic(self) -> ModuleType:
        return self._common.tab.logic

    @property
    def _ruleindex(self) -> dict:
        return self._common.ruleindex

    @property
    def _groupindex(self) -> dict:
        return self._common.groupindex

    @property
    def _common(self) -> TabRulesSharedData:
        return self.__common

    @property
    def _root(self):
        return self._common.root

    def __init__(self, common: TabRulesSharedData):
        self.__common: TabRulesSharedData = common

    def __delattr__(self, name: str):
        raise AttributeError(name)

    def __setattr__(self, attr, val):
        if '_' + __class__.__name__ + '__common' in self.__dict__:
            raise AttributeError(attr)
        super().__setattr__(attr, val)
    
    def writes(method: Callable[P, T]) -> Callable[..., T]:
        @wraps(method)
        def fcheckstate(self, *args, **kw):
            if self.locked: raise IllegalStateError('locked')
            return method(self, *args, **kw)
        return fcheckstate


class RuleGroup(Sequence[Rule], TabRulesBase):

    writes = TabRulesBase.writes

    @property
    def name(self) -> str:
        return self.__name

    @writes
    def append(self, RuleCls: type[Rule]):
        if not issubclass(RuleCls, Rule):
            raise TypeError(RuleCls)
        clsname = RuleCls.__name__
        if clsname in self._ruleindex or clsname in self._groupindex:
            raise DuplicateKeyError(clsname)
        if hasattr(self._root, clsname):
            raise AttributeError('Duplicate attribute %s' % clsname)
        rule = RuleCls(self.tab, **self.tab.opts)
        self.__rules.append(rule)
        self._ruleindex[clsname] = self.__index[rule] = rule

    add = append

    @writes
    def extend(self, rules: Iterable[type[Rule]]):
        for rule in rules:
            self.add(rule)

    @writes
    def clear(self):
        for rule in self.__rules:
            del(self._ruleindex[rule.__class__.__name__])
        self.__rules.clear()

    def __init__(self, name: str, common: TabRulesSharedData):
        self.__name = name
        self.__rules = []
        self.__index = {}
        super().__init__(common)

    def __iter__(self) -> Iterator[Rule]:
        return iter(self.__rules)

    def __len__(self):
        return len(self.__rules)

    def __contains__(self, key):
        return key in self.__index

    def __getitem__(self, index) -> Rule:
        return self.__rules[index]

    def __getattr__(self, name):
        if name in self.__index:
            return self.__index[name]
        raise AttributeError(name)

    def __repr__(self):
        return orepr(self, name = self.name, rules = len(self))

    del(writes)

class RuleGroups(Sequence[RuleGroup], TabRulesBase):

    writes = TabRulesBase.writes

    @writes
    def create(self, name: str = None) -> RuleGroup:
        if name != None:
            if name in self._groupindex or name in self._ruleindex:
                raise DuplicateKeyError(name)
            if hasattr(self._root, name):
                raise AttributeError('Duplicate attribute %s' % name)
        group = RuleGroup(name, self._common)
        self.__groups.append(group)
        if name != None:
            self._groupindex[name] = group
        return group

    @writes
    def append(self, rules: Iterable[type[Rule]], name: str = None):
        if name == None:
            name = getattr(rules, 'name', None)
        self.create(name).extend(rules)

    add = append

    @writes
    def extend(self, groups: Iterable[Iterable[type[Rule]]]):
        for rules in groups:
            self.add(rules)

    @writes
    def clear(self):
        g = self.__groups
        for group in g:
            group.clear()
        g.clear()
        self._groupindex.clear()

    @property
    def names(self):
        return list(filter(bool, (group.name for group in self)))

    def __init__(self, common: TabRulesSharedData):
        self.__groups: list[RuleGroup] = []
        super().__init__(common)

    def __iter__(self) -> Iterator[RuleGroup]:
        return iter(self.__groups)

    def __len__(self):
        return len(self.__groups)

    def __getitem__(self, index: int|slice) -> RuleGroup:
        return self.__groups[index]

    def __getattr__(self, name):
        idx = self._groupindex
        if name in idx:
            return idx[name]
        raise AttributeError(name)

    def __contains__(self, item):
        return item in self._groupindex or item in self.__groups

    def __dir__(self):
        return self.names

    def __repr__(self):
        return orepr(self,
            logic = self.logic,
            groups = len(self),
            rules = sum(len(g) for g in self)
        )

    del(writes)

class TabRules(Sequence[Rule], TabRulesBase):

    writes = TabRulesBase.writes

    @property
    def groups(self) -> RuleGroups:
        return self.__groups

    @writes
    def append(self, rule: type[Rule]):
        self.groups.create().append(rule)

    add = append

    @writes
    def extend(self, rules: Iterable[type[Rule]]):
        self.groups.append(rules)

    @writes
    def clear(self):
        self.groups.clear()
        self._ruleindex.clear()

    def get(self, ref, *default: Any) -> Rule:
        idx = self._ruleindex
        if ref in idx:
            return idx[ref]
        if isinstance(ref, type) and ref.__name__ in idx:
            return idx[ref.__name__]
        if ref.__class__.__name__ in idx:
            return idx[ref.__class__.__name__]
        if len(default):
            return default[0]
        raise Emsg.MissingValue(ref)

    def __init__(self, tableau: Tableau):
        common = TabRulesSharedData(tableau, self)
        self.__groups = RuleGroups(common)
        super().__init__(common)

    def __len__(self):
        return len(self._ruleindex)

    def __iter__(self) -> Iterator[Rule]:
        return chain.from_iterable(self.groups)

    def __contains__(self, key):
        return key in self._ruleindex

    def __getitem__(self, key) -> Rule:
        if isinstance(key, (int, slice)):
            return list(self)[key]
        try:
            return self.get(key)
        except MissingValueError:
            raise KeyError(key) from None

    def __getattr__(self, attr):
        if attr in self._groupindex:
            return self._groupindex[attr]
        if attr in self._ruleindex:
            return self._ruleindex[attr]
        raise AttributeError(attr)

    def __dir__(self):
        return [rule.__class__.__name__ for rule in self]

    def __repr__(self):
        return orepr(self,
            logic  = self.logic,
            groups = len(self.groups),
            rules  = len(self),
        )

    del(writes)

del(TabRulesBase.writes)

@static
class TableauxSystem(Abc):


    @classmethod
    @abstract
    def build_trunk(cls, tableau: Tableau, argument: Argument):
        raise NotImplementedError

    @classmethod
    def branching_complexity(cls, node: Node) -> int:
        '''Compute how many new branches would be added if a rule were to be
        applied to the node.'''
        return 0

    @classmethod
    def add_rules(cls, logic: ModuleType, rules: TabRules):
        Rules = logic.TabRules
        rules.groups.add(Rules.closure_rules, 'closure')
        rules.groups.extend(Rules.rule_groups)

class TabTimers(NamedTuple):
    build  : StopWatch
    trunk  : StopWatch
    tree   : StopWatch
    models : StopWatch
    @staticmethod
    def create(it = (False,) * 4):
        return TabTimers._make(map(StopWatch, it))

class Tableau(Sequence[Branch], EventEmitter):
    'A tableau proof.'
    #: The unique object ID of the tableau.
    id: int

    #: The logic of the tableau.
    logic: ModuleType

    #: The argument of the tableau.
    argument: Argument

    #: Alias for ``self.logic.TableauxSystem``
    System: TableauxSystem

    #: The rule instances.
    rules: TabRules

    #: The build options.
    opts: Mapping[str, bool|int|None]

    #: The FlagEnum value.
    flag: FLAG

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
    valid: bool

    #: Whether the tableau's argument is invalid (disproved). A tableau with
    #: an argument is `invalid` iff it is `completed` and it has at least one
    #: open branch. If the tableau is not completed, or it has no argument,
    #: the value will be ``None``.
    invalid: bool

    trunk_built: bool

    #: The current step number. This is the number of rule applications, plus ``1``
    #: if the argument trunk is built.
    current_step: int

    #: Ordered view of the open branches.
    open: SequenceApi[Branch]

    #: The history of rule applications.
    history: DeqSeq[StepEntry]

    #: A tree structure of the tableau. This is generated after the tableau
    #: is finished. If the `build_timeout` was exceeded, the tree is `not`
    #: built.
    tree: dict
    stats: dict
    models: set[BaseModel]

    _defaults = MapCover(dict(
        is_group_optim  = True,
        is_build_models = False,
        build_timeout   = None,
        max_steps       = None,
    ))

    def __init__(self, logic: LogicRef = None, argument: Argument = None, /, **opts):

        # Events init
        super().__init__(*TabEvent)
        self.__branch_listeners = MapCover({
            BranchEvent.AFTER_BRANCH_CLOSE : self.__after_branch_close,
            BranchEvent.AFTER_NODE_ADD     : self.__after_node_add,
            BranchEvent.AFTER_NODE_TICK    : self.__after_node_tick,
        })

        # Exposed attributes
        self.history = DeqSeq()
        self.opts = self._defaults | opts
        self.timers = TabTimers.create()
        # Deferred init.
        # self.tree = self.models = self.stats = None

        # Property attributes
        self.__logic = self.__argument = None
        self.__flag = FLAG.PREMATURE
        self.__branch_list = []
        self.__open  = linqset()
        self.__branchstat: dict[Branch, BranchStat] = {}
        self.__rules = TabRules(self)
        # Deferred init.
        # self.__openview = None

        # Private
        self.__branching_complexities: dict[Node, int] = {}

        # Init
        if logic is not None:
            self.logic = logic
        if argument is not None:
            self.argument = argument

    @property
    def id(self) -> int:
        return id(self)

    @property
    def logic(self) -> ModuleType:
        return self.__logic

    @logic.setter
    def logic(self, logic: LogicRef):
        'Setter for ``logic``. Assumes building has not started.'
        self.__check_not_started()
        self.__logic = get_logic(logic)
        self.rules.clear()
        self.System.add_rules(self.logic, self.rules)
        if self.argument is not None:
            self.__build_trunk()

    @property
    def rules(self) -> TabRules:
        return self.__rules

    @property
    def flag(self) -> FLAG:
        return self.__flag

    @property
    def System(self) -> TableauxSystem:
        if self.logic is None:
            return None
        return self.logic.TableauxSystem

    @property
    def argument(self) -> Argument:
        return self.__argument

    @argument.setter
    def argument(self, argument: Argument):
        """Setter for ``argument``. If the tableau has a logic set, then the
        trunk is automatically built."""
        self.__check_trunk_not_built()
        self.__argument = Argument(argument)
        if self.logic is not None:
            self.__build_trunk()

    @property
    def finished(self) -> bool:
        return FLAG.FINISHED in self.__flag

    @property
    def completed(self) -> bool:
        return FLAG.FINISHED in self.__flag and FLAG.PREMATURE not in self.__flag

    @property
    def premature(self) -> bool:
        return FLAG.FINISHED in self.__flag and FLAG.PREMATURE in self.__flag

    @property
    def trunk_built(self) -> bool:
        return FLAG.TRUNK_BUILT in self.__flag

    @property
    def valid(self) -> bool:
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
        return len(self.history) + (FLAG.TRUNK_BUILT in self.__flag)

    @property
    def open(self) -> SequenceProxy[Branch]:
        'View of the open branches.'
        try:
            return self.__openview
        except AttributeError:
            self.__openview = SequenceProxy(self.__open)
        return self.__openview

    def build(self) -> Tableau:
        'Build the tableau. Returns self.'
        with self.timers.build:
            while not self.finished:
                self.__check_timeout()
                self.step()
        self.finish()
        return self

    def next_step(self) -> RuleTarget:
        """
        Choose the next rule step to perform. Returns the (rule, target)
        pair, or ``None``if no rule can be applied.

        This iterates over the open branches and calls ``__get_branch_application()``.
        """
        for branch in self.open:
            res = self.__get_branch_application(branch)
            if res:
                return res

    def step(self) -> StepEntry|None|bool:
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
        if FLAG.FINISHED in self.__flag:
            return False
        self.__check_trunk_built()
        ruletarget = stepentry = None
        with StopWatch() as timer:
            if not self.__is_max_steps_exceeded():
                ruletarget = self.next_step()
                if not ruletarget:
                    self.__flag = self.__flag & ~FLAG.PREMATURE
            if ruletarget:
                ruletarget.rule.apply(ruletarget.target)
                stepentry = StepEntry(*ruletarget, timer.elapsed)
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
        if parent is None:
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
        index = len(self)
        if not branch.closed:
            self.__open.add(branch)
        elif branch in self:
            raise ValueError('Branch %s already on tableau' % branch.id)
        self.__branch_list.append(branch)
        stat = self.__branchstat[branch] = BranchStat()
        stat.update({
            KEY.STEP_ADDED: self.current_step,
            KEY.INDEX     : index,
            KEY.PARENT    : branch.parent,
        })
        # self.__after_branch_add(branch)
        # For corner case of an AFTER_BRANCH_ADD callback adding a node, make
        # sure we don't emit AFTER_NODE_ADD twice, so prefetch the nodes.
        nodes = tuple(branch) if branch.parent is None else EMPTY_SET
        self.emit(TabEvent.AFTER_BRANCH_ADD, branch)
        for node in nodes:
            self.__after_node_add(node, branch)
        branch.on(self.__branch_listeners)
        return self

    def __build_trunk(self) -> Tableau:
        """
        Build the trunk of the tableau. Delegates to the ``build_trunk()`` method
        of ``TableauxSystem``. This is called automatically when the
        tableau has non-empty ``argument`` and ``logic`` properties. Returns self.

        :return: self
        :rtype: Tableau
        :raises errors.IllegalStateError: if the trunk is already built.
        """
        self.__check_trunk_not_built()
        with self.timers.trunk:
            self.emit(TabEvent.BEFORE_TRUNK_BUILD, self)
            self.System.build_trunk(self, self.argument)
            self.__flag |= FLAG.TRUNK_BUILT
            self.emit(TabEvent.AFTER_TRUNK_BUILD, self)
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
        if FLAG.FINISHED in self.__flag:
            return self
        self.__flag |= FLAG.FINISHED
        if self.invalid and self.opts.get('is_build_models'):
            with self.timers.models:
                self.__build_models()
        if FLAG.TIMED_OUT not in self.__flag:
            # In case of a timeout, we do `not` build the tree in order to best
            # respect the timeout. In case of `max_steps` excess, however, we
            # `do` build the tree.
            with self.timers.tree:
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
        cache = self.__branching_complexities
        if node not in cache:
            sys = self.System
            if sys is None:
                return 0
            cache[node] = sys.branching_complexity(node)
        return cache[node]

    def stat(self, branch: Branch, *keys: Node|KEY) -> Any:
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
            stat = stat[KEY.NODES][key]
            try:
                key = next(kit)
                # branch, node, key
                stat = stat[KEY(key)]
                next(kit)
            except StopIteration:
                return stat
            raise ValueError('Too many keys to lookup')
        try:
            # branch, key
            stat = stat[KEY(key)]
            next(kit)
        except StopIteration:
            if key == KEY.NODES:
                return stat.copy()
            return stat
        raise ValueError('Too many keys to lookup')

    @overload
    def __getitem__(self, s: slice) -> Sequence[Branch]: ...
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

    def __after_branch_close(self, branch: Branch):
        stat = self.__branchstat[branch]
        stat[KEY.STEP_CLOSED] = self.current_step
        stat[KEY.FLAGS] |= FLAG.CLOSED
        self.__open.remove(branch)
        self.emit(TabEvent.AFTER_BRANCH_CLOSE, branch)

    def __after_node_add(self, node: Node, branch: Branch):
        curstep = self.current_step
        stat = self.__branchstat[branch].node(node)
        stat[KEY.STEP_ADDED] = curstep
        node.step = curstep
        self.emit(TabEvent.AFTER_NODE_ADD, node, branch)

    def __after_node_tick(self, node: Node, branch: Branch):
        curstep = self.current_step
        stat = self.__branchstat[branch].node(node)
        stat[KEY.FLAGS] |= FLAG.TICKED
        stat[KEY.STEP_TICKED] = curstep
        self.emit(TabEvent.AFTER_NODE_TICK, node, branch)

    # :-----------:
    # : Util      :
    # :-----------:

    def __get_branch_application(self, branch: Branch) -> RuleTarget:
        """
        Find and return the next available rule application for the given open
        branch.
        """
        for group in self.rules.groups:
            res = self.__get_group_application(branch, group)
            if res:
                return res

    def __get_group_application(self, branch: Branch, rules: Iterable[Rule]) -> RuleTarget:
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
        is_group_optim = self.opts.get('is_group_optim')
        for rule in rules:
            with rule.search_timer:
                target = rule.get_target(branch)
            if target:
                ruletarget = RuleTarget(rule, target)
                if not is_group_optim:
                    target.update({
                        'group_score'         : None,
                        'total_group_targets' : 1,
                        'min_group_score'     : None,
                        'is_group_optim'      : False,
                    })
                    return ruletarget
                results.append(ruletarget)
        if results:
            return self.__select_optim_group_application(results)

    def __select_optim_group_application(self, results: Sequence[RuleTarget]) -> RuleTarget:
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
        group_scores = tuple(rule.group_score(target) for rule, target in results)
        max_group_score = max(group_scores)
        min_group_score = min(group_scores)
        for group_score, res in zip(group_scores, results):
            if group_score == max_group_score:
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
        try:
            distinct_nodes = self.tree['distinct_nodes']
        except AttributeError:
            distinct_nodes = None# if self.tree else None
        timers = self.timers
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
            'build_duration_ms' : timers.build.elapsed,
            'trunk_duration_ms' : timers.trunk.elapsed,
            'tree_duration_ms'  : timers.tree.elapsed,
            'models_duration_ms': timers.models.elapsed,
            'rules_time_ms'     : sum(
                sum((rule.search_timer.elapsed, rule.apply_timer.elapsed))
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
            'queries'         : rule.search_timer.count,
            'search_time_ms'  : rule.search_timer.elapsed,
            'search_time_avg' : rule.search_timer.elapsed_avg,
            'apply_count'     : rule.apply_count,
            'apply_time_ms'   : rule.apply_timer.elapsed,
            'apply_time_avg'  : rule.apply_timer.elapsed_avg,
            'timers'          : {
                name : {
                    'duration_ms'   : timer.elapsed,
                    'duration_avg'  : timer.elapsed_avg,
                    'count' : timer.count,
                }
                for name, timer in rule.timers.items()
            },
        }

    def __check_timeout(self):
        timeout = self.opts.get('build_timeout')
        if timeout is None or timeout < 0:
            return
        if self.timers.build.elapsed > timeout:
            self.timers.build.stop()
            self.__flag |= FLAG.TIMED_OUT
            self.finish()
            raise TimeoutError('Timeout of {0}ms exceeded.'.format(timeout))

    def __is_max_steps_exceeded(self):
        max_steps = self.opts.get('max_steps')
        return max_steps is not None and len(self.history) >= max_steps

    def __check_trunk_built(self):
        if FLAG.TRUNK_BUILT not in self.__flag and self.argument is not None:
            raise IllegalStateError("Trunk is not built.")

    def __check_trunk_not_built(self):
        if FLAG.TRUNK_BUILT in self.__flag:
            raise IllegalStateError("Trunk is already built.")

    def __check_not_started(self):
        if FLAG.TRUNK_BUILT in self.__flag or len(self.history) > 0:
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
        'Build models for the open branches.'
        if self.logic is None:
            return
        self.models = set()
        for branch in self.open:
            self.__check_timeout()
            model: BaseModel = self.logic.Model()
            model.read_branch(branch)
            if self.argument is not None:
                model.is_countermodel = model.is_countermodel_to(self.argument)
            branch.model = model
            self.models.add(model)

def make_tree_structure(tab: Tableau, branches: Sequence[Branch], node_depth=0, track=None):
    is_root = track is None
    if track is None:
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
        relevant = tuple(branch for branch in branches if len(branch) > node_depth)
        for branch in relevant:
            if FLAG.CLOSED in tab.stat(branch, KEY.FLAGS):
                s['has_closed'] = True
            else:
                s['has_open'] = True
            if s['has_open'] and s['has_closed']:
                break
        distinct_nodes = DeqSeq()
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
            if s['step'] is None or step_added < s['step']:
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
        if branch.model is not None:
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
