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

from errors import (
    Emsg,
    DuplicateKeyError,
    IllegalStateError,
    MissingValueError,
    TimeoutError,
    instcheck,
    subclscheck,
)
from tools.abcs import (
    Abc, AbcMeta, P, T, F,
    MapProxy
)
from tools.callables import preds
from tools.decorators import (
    abstract, final, overload, static,
    wraps,
)
from tools.events import EventEmitter
from tools.hybrids import qsetf, qset
from tools.linked import linqset
from tools.mappings import (
    MapCover,
    MappingApi,
    dmap,
    dmapattr,
)
from tools.misc import get_logic, orepr
from tools.sequences import (
    MutableSequenceApi,
    SequenceApi,
    SequenceCover,
    deqseq,
    seqf,
)
from tools.sets import EMPTY_SET, setf
from tools.timing import StopWatch

from lexicals import Argument, Sentence
from models import BaseModel

from proof.common import (
    FLAG,
    KEY,
    Branch,
    BranchEvent,
    Node,
    RuleEvent,
    TabEvent,
    Target,
)

from collections import deque
from itertools import chain
from types import ModuleType
from typing import (
    Any,
    Callable,
    ClassVar,
    Iterable,
    Iterator,
    Mapping,
    MutableSequence,
    NamedTuple,
    Sequence,
    SupportsIndex,
    TypeVar,
)

NOARG = object()

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
            if isinstance(item, type):
                item = None, item
            instcheck(item, tuple)
            if len(item) != 2:
                raise Emsg.WrongLength(item, 2)
            name, Helper = item
            instcheck(Helper, type)
            if name is None:
                name = getattr(Helper, '_attr', None)
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
        filt = filter(bool, chain(
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
    #: The rule instance that will apply.
    rule   : Rule
    #: The target produced by the rule.
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

    _defaults = MapProxy({
        KEY.FLAGS       : FLAG.NONE,
        KEY.STEP_ADDED  : FLAG.NONE,
        KEY.STEP_TICKED : None,
    })

    def __init__(self):
        super().__init__(self._defaults)

class BranchStat(dict[KEY, FLAG|int|Branch|dict[Node, NodeStat]|None]):

    __slots__ = EMPTY_SET

    _defaults = MapProxy({
        KEY.FLAGS       : FLAG.NONE,
        KEY.STEP_ADDED  : FLAG.NONE,
        KEY.STEP_CLOSED : FLAG.NONE,
        KEY.INDEX       : None,
        KEY.PARENT      : None,
    })

    def __init__(self, mapping: Mapping = None, /, **kw):
        super().__init__(self._defaults)
        self[KEY.NODES] = {}
        if mapping is not None:
            self.update(mapping)
        if len(kw):
            self.update(kw)

    def node(self, node: Node) -> NodeStat:
        'Get the stat info for the node, and create if missing.'
        try:
            return self[KEY.NODES][node]
        except KeyError:
            return self[KEY.NODES].setdefault(node, NodeStat())
        # if node not in self[KEY.NODES]:
        #     self[KEY.NODES][node] = NodeStat()
        # return self[KEY.NODES][node]

    def view(self) -> dict[KEY, FLAG|int|Branch|None]:
        return {k: self[k] for k in self._defaults}

class Rule(EventEmitter, metaclass = RuleMeta):
    'Base class for a Tableau rule.'

    Helpers: Sequence[tuple[str, type]] = ()
    Timers: Sequence[str] = ()
    HelperRuleEventMethods: Sequence[tuple[RuleEvent, str]] = (
        (RuleEvent.AFTER_APPLY  , 'after_apply'),
        (RuleEvent.BEFORE_APPLY , 'before_apply'),
    )
    HelperTabEventMethods: Sequence[tuple[TabEvent, str]] = (
        (TabEvent.AFTER_BRANCH_ADD   , 'after_branch_add'),
        (TabEvent.AFTER_BRANCH_CLOSE , 'after_branch_close'),
        (TabEvent.AFTER_NODE_ADD     , 'after_node_add'),
        (TabEvent.AFTER_NODE_TICK    , 'after_node_tick'),
        (TabEvent.AFTER_TRUNK_BUILD  , 'after_trunk_build'),
        (TabEvent.BEFORE_TRUNK_BUILD , 'before_trunk_build'),
    )
    branch_level: int = 1
    _defaults = dict(is_rank_optim = True)

    #: Reference to the tableau instance.
    tableau: Tableau
    helpers: Mapping[type, object]
    timers: Mapping[str, StopWatch]
    #: The number of times the rule has applied.
    apply_count: int

    __slots__ = 'tableau', 'helpers', 'apply_count', 'timers', 'opts'

    @abstract
    def _get_targets(self, branch: Branch, /) -> Sequence[Target]:
        raise NotImplementedError

    @abstract
    def _apply(self, target: Target, /):
        raise NotImplementedError

    @abstract
    def example_nodes(self) -> Sequence[Mapping]:
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
        return 0

    def __init__(self, tableau: Tableau, /, **opts):
        self.tableau = instcheck(tableau, Tableau)
        super().__init__(*RuleEvent)

        self.search_timer = StopWatch()
        self.apply_timer = StopWatch()
        self.timers = {}
        if self.Timers:
            self.timers |= ((name, StopWatch()) for name in self.Timers)

        self.opts = self._defaults | opts

        self.helpers = {}
        self.apply_count = 0

        for name, helper in self.Helpers:
            self.add_helper(helper, name)

    @final
    @property
    def name(self) -> str:
        'The rule type name.'
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
        :return: The new branch.
        """
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

    def __extend_targets(self, targets: Sequence[Target], /):
        """Augment the targets with the following keys:
        
        - `rule`
        - `is_rank_optim`
        - `candidate_score`
        - `total_candidates`
        - `min_candidate_score`
        - `max_candidate_score`

        :param Sequence[Target] targets: The list of targets.
        """
        # instcheck(targets, Sequence)
        isrankoptim = self.opts['is_rank_optim']
        if isrankoptim:
            scores = tuple(map(self.score_candidate, targets))
        else:
            scores = 0,
        max_score = max(scores)
        min_score = min(scores)
        for score, target in zip(scores, targets):
            target.update(
                rule             = self,
                total_candidates = len(targets),
            )
            if isrankoptim:
                target.update(
                    is_rank_optim       = True,
                    candidate_score     = score,
                    min_candidate_score = min_score,
                    max_candidate_score = max_score,
                )
            else:
                target.update(
                    is_rank_optim       = False,
                    candidate_score     = None,
                    min_candidate_score = None,
                    max_candidate_score = None,
                )

    def __select_best_target(self, targets: Iterable[Target], /) -> Target:
        'Selects the best target. Assumes targets have been extended.'
        for target in targets:
            if not self.opts['is_rank_optim']:
                return target
            if target['candidate_score'] == target['max_candidate_score']:
                return target

RuleT = TypeVar('RuleT', bound = Rule)

class TabRulesSharedData:

    __slots__ = 'ruleindex', 'groupindex', 'locked', 'tab', 'root'

    def lock(self, *_):
        if self.locked:
            raise ValueError('already locked')
        self.ruleindex = MapCover(self.ruleindex)
        self.groupindex = MapCover(self.groupindex)
        self.locked = True

    def __init__(self, tableau: Tableau, root: TabRules):
        self.ruleindex = {}
        self.groupindex = {}
        self.locked = False
        self.tab = tableau
        self.root = root
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

    __slots__ = EMPTY_SET

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
    def _root(self):
        return self._common.root

    def __init__(self, common: TabRulesSharedData):
        self._common = common

    def __delattr__(self, name: str):
        raise AttributeError(name)
    
    def writes(method: F) -> F:
        @wraps(method)
        def fcheckstate(self, *args, **kw):
            if self.locked: raise IllegalStateError('locked')
            return method(self, *args, **kw)
        return fcheckstate

class RuleGroup(Sequence[Rule], TabRulesBase):

    def __init__(self, name: str, common: TabRulesSharedData):
        self.name = name
        self.rules: list[Rule] = []
        self._index = {}
        super().__init__(common)

    @TabRulesBase.writes
    def append(self, RuleCls: type[Rule]):
        subclscheck(RuleCls, Rule)
        clsname = RuleCls.__name__
        if clsname in self._ruleindex or clsname in self._groupindex:
            raise DuplicateKeyError(clsname)
        if hasattr(self._root, clsname):
            raise AttributeError('Duplicate attribute %s' % clsname)
        rule = RuleCls(self.tab, **self.tab.opts)
        self.rules.append(rule)
        self._ruleindex[clsname] = self._index[rule] = rule

    add = append

    @TabRulesBase.writes
    def extend(self, rules: Iterable[type[Rule]]):
        for rule in rules:
            self.add(rule)

    @TabRulesBase.writes
    def clear(self):
        for rule in self.rules:
            del(self._ruleindex[type(rule).__name__])
        self.rules.clear()

    def __iter__(self) -> Iterator[Rule]:
        return iter(self.rules)

    def __len__(self):
        return len(self.rules)

    def __contains__(self, key):
        return key in self._index

    def __getitem__(self, index) -> Rule:
        return self.rules[index]

    def __getattr__(self, name):
        if name in self._index:
            return self._index[name]
        raise AttributeError(name)

    def __repr__(self):
        return orepr(self, name = self.name, rules = len(self))

class RuleGroups(Sequence[RuleGroup], TabRulesBase):

    def __init__(self, common: TabRulesSharedData):
        self.groups: list[RuleGroup] = []
        super().__init__(common)

    @TabRulesBase.writes
    def create(self, name: str = None) -> RuleGroup:
        if name != None:
            if name in self._groupindex or name in self._ruleindex:
                raise DuplicateKeyError(name)
            if hasattr(self._root, name):
                raise AttributeError('Duplicate attribute %s' % name)
        group = RuleGroup(name, self._common)
        self.groups.append(group)
        if name != None:
            self._groupindex[name] = group
        return group

    @TabRulesBase.writes
    def append(self, rules: Iterable[type[Rule]], name: str = None):
        if name == None:
            name = getattr(rules, 'name', None)
        self.create(name).extend(rules)

    add = append

    @TabRulesBase.writes
    def extend(self, groups: Iterable[Iterable[type[Rule]]]):
        for rules in groups:
            self.add(rules)

    @TabRulesBase.writes
    def clear(self):
        self.groups.clear()
        self._groupindex.clear()

    @property
    def names(self):
        return list(filter(bool, (group.name for group in self)))

    def __iter__(self) -> Iterator[RuleGroup]:
        return iter(self.groups)

    def __len__(self):
        return len(self.groups)

    def __getitem__(self, index: int|slice) -> RuleGroup:
        return self.groups[index]

    def __getattr__(self, name):
        idx = self._groupindex
        if name in idx:
            return idx[name]
        raise AttributeError(name)

    def __contains__(self, item):
        return item in self._groupindex or item in self.groups

    def __dir__(self):
        return self.names

    def __repr__(self):
        return orepr(self,
            logic = self.logic,
            groups = len(self),
            rules = sum(map(len, self))
        )

class TabRules(Sequence[Rule], TabRulesBase):

    def __init__(self, tableau: Tableau):
        common = TabRulesSharedData(tableau, self)
        self.groups = RuleGroups(common)
        super().__init__(common)

    @TabRulesBase.writes
    def append(self, rule: type[Rule]):
        self.groups.create().append(rule)

    add = append

    @TabRulesBase.writes
    def extend(self, rules: Iterable[type[Rule]]):
        self.groups.append(rules)

    @TabRulesBase.writes
    def clear(self):
        self.groups.clear()
        self._ruleindex.clear()

    @overload
    def get(self, cls: type[RuleT], default = None, /) -> RuleT: ...
    @overload
    def get(self, rule: RuleT, default = None, /) -> RuleT: ...
    @overload
    def get(self, name: str, default = None, /) -> Rule: ...
    def get(self, ref, default = NOARG, /):
        try:
            if isinstance(ref, str):
                return self._ruleindex[ref]
            if isinstance(ref, type):
                subclscheck(ref, Rule)
                return self._ruleindex[ref.__name__]
            if isinstance(ref, Rule):
                return self._ruleindex[type(ref).__name__]
            raise Emsg.InstCheck(ref, (str, type, Rule))
        except KeyError:
            if default is not NOARG:
                return default
        raise Emsg.MissingValue(ref)

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
        return [type(rule).__name__ for rule in self]

    def __repr__(self):
        return orepr(self,
            logic  = self.logic,
            groups = len(self.groups),
            rules  = len(self),
        )

del(TabRulesBase.writes)

@static
class TableauxSystem(Abc):

    @classmethod
    @abstract
    def build_trunk(cls, tableau: Tableau, argument: Argument, /):
        raise NotImplementedError

    @classmethod
    def branching_complexity(cls, node: Node, /) -> int:
        '''Compute how many new branches would be added if a rule were to be
        applied to the node.'''
        return 0

    @classmethod
    def add_rules(cls, logic: ModuleType, rules: TabRules, /):
        Rules = logic.TabRules
        rules.groups.create('closure').extend(Rules.closure_rules)
        for classes in Rules.rule_groups:
            rules.groups.create().extend(classes)
        # rules.groups.extend(Rules.rule_groups)

class TabTimers(NamedTuple):

    build  : StopWatch
    trunk  : StopWatch
    tree   : StopWatch
    models : StopWatch

    @static
    def create(it = (False,) * 4):
        return TabTimers._make(map(StopWatch, it))

class Tableau(Sequence[Branch], EventEmitter):
    'A tableau proof.'

    #: The unique object ID of the tableau.
    id: int

    #: The logic of the tableau.
    logic: ModuleType|None

    #: The argument of the tableau.
    argument: Argument|None

    #: Alias for ``self.logic.TableauxSystem``
    System: TableauxSystem|None

    #: The rule instances.
    rules: TabRules

    #: The build options.
    opts: MappingApi[str, bool|int|None]

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
    open: SequenceApi[Branch]

    #: The history of rule applications.
    history: SequenceApi[StepEntry]

    #: A tree structure of the tableau. This is generated after the tableau
    #: is finished. If the `build_timeout` was exceeded, the tree is `not`
    #: built.
    tree: TreeStruct
    stats: dict
    models: setf[BaseModel]
    timers: TabTimers


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

        # Protected attributes
        self.__flag = FLAG.PREMATURE
        self.__branch_list = list()
        self.__open = linqset()
        self.__branchstat: dict[Branch, BranchStat] = {}
        self.__history = list()

        # Private
        self.__branching_complexities: dict[Node, int] = {}

        # Exposed attributes
        self.history = SequenceCover(self.__history)
        self.opts = self._defaults | opts
        self.timers = TabTimers.create()
        self.rules = TabRules(self)
        self.open = SequenceCover(self.__open)

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
    def System(self) -> TableauxSystem:
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
    def logic(self, logic: LogicRef):
        'Setter for ``logic``. Assumes building has not started.'
        self.__check_not_started()
        self.__logic = get_logic(logic)
        self.rules.clear()
        self.System.add_rules(self.logic, self.rules)
        if self.argument is not None:
            self.__build_trunk()

    @property
    def finished(self):
        return FLAG.FINISHED in self.__flag

    @property
    def completed(self):
        return FLAG.FINISHED in self.__flag and FLAG.PREMATURE not in self.__flag

    @property
    def premature(self):
        return FLAG.FINISHED in self.__flag and FLAG.PREMATURE in self.__flag

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
        return len(self.history) + (FLAG.TRUNK_BUILT in self.__flag)

    def build(self):
        'Build the tableau. Returns self.'
        with self.timers.build:
            while not self.finished:
                self.__check_timeout()
                self.step()
        self.finish()
        return self

    def next_step(self):
        """Choose the next rule step to perform. Returns the (rule, target)
        pair, or ``None``if no rule can be applied.

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

        .. Internally, this calls the ``next_step()`` method to select the
        .. next step, and, if non-empty, applies the rule and appends the entry
        .. to the history.

        :return: The history entry, or ``None`` if just finished, or ``False``
          if previously finished.
        :raises errors.IllegalStateError: if the trunk is not built.
        """
        if FLAG.FINISHED in self.__flag:
            return False
        ruletarget = stepentry = None
        with StopWatch() as timer:
            if not self.__is_max_steps_exceeded():
                ruletarget = self.next_step()
                if not ruletarget:
                    self.__flag &= ~FLAG.PREMATURE
            if ruletarget:
                ruletarget.rule.apply(ruletarget.target)
                stepentry = StepEntry(*ruletarget, timer.elapsed)
                self.__history.append(stepentry)
            else:
                self.finish()
        return stepentry

    def branch(self, /, parent: Branch = None):
        """
        Create a new branch on the tableau, as a copy of ``parent``, if given.
        This calls the ``after_branch_add()`` callback on all the rules of the
        tableau.

        :param Branch parent: The parent branch, if any.
        :return: The new branch.
        """
        if parent is None:
            branch = Branch()
        else:
            branch = parent.copy(parent = parent)
        self.add(branch)
        return branch

    def add(self, /, branch: Branch):
        """Add a new branch to the tableau. Returns self.

        :param Branch branch: The branch to add.
        :return: self
        """
        index = len(self)
        if not branch.closed:
            # Append to linqset will raise duplicate value error.
            self.__open.append(branch)
        elif branch in self:
            raise Emsg.DuplicateValue(branch.id)
        self.__branch_list.append(branch)
        self.__branchstat[branch] = BranchStat({
            KEY.STEP_ADDED : self.current_step,
            KEY.INDEX      : index,
            KEY.PARENT     : branch.parent,
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

    def __build_trunk(self):
        """Build the trunk of the tableau. Delegates to the ``build_trunk()``
        method of ``TableauxSystem``. This is called automatically when the
        tableau has non-empty ``argument`` and ``logic`` properties.
        Returns self.

        :return: self
        :raises errors.IllegalStateError: if the trunk is already built.
        """
        self.__check_not_started()
        with self.timers.trunk:
            self.emit(TabEvent.BEFORE_TRUNK_BUILD, self)
            self.System.build_trunk(self, self.argument)
            self.__flag |= FLAG.TRUNK_BUILT
            self.emit(TabEvent.AFTER_TRUNK_BUILD, self)
        return self

    def finish(self):
        """Mark the tableau as finished, and perform post-build tasks, including
        populating the ``tree``, ``stats``, and ``models`` properties.
        
        When using the ``build()`` or ``step()`` methods, there is never a need
        to call this method, since it is handled internally. However, this
        method *is* safe to call multiple times. If the tableau is already
        finished, it will be a no-op.

        :return: self
        """
        if FLAG.FINISHED in self.__flag:
            return self
        self.__flag |= FLAG.FINISHED
        if self.invalid and self.opts['is_build_models'] and self.logic is not None:
            with self.timers.models:
                self.models = setf(self._gen_models())
        if FLAG.TIMED_OUT not in self.__flag:
            # In case of a timeout, we do `not` build the tree in order to best
            # respect the timeout. In case of `max_steps` excess, however, we
            # `do` build the tree.
            with self.timers.tree:
                self.tree = self._build_tree(self)
        self.stats = self.__compute_stats()
        return self

    def branching_complexity(self, node: Node, /):
        """Caching method for the logic's ``TableauxSystem.branching_complexity()``
        method. If the tableau has no logic, then ``0`` is returned.

        :param node: The node to evaluate.
        :return: The branching complexity.
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

    def stat(self, branch: Branch, /, *keys: Node|KEY) -> Any:
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
        return orepr(self, dict(
            id    = self.id,
            logic = (self.logic and self.logic.name),
            len   = len(self),
            open  = len(self.open),
            step  = self.current_step,
            finished = self.finished,
         ) | {
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
        stat = self.__branchstat[branch].node(node)
        stat[KEY.STEP_ADDED] = node.step = self.current_step
        self.emit(TabEvent.AFTER_NODE_ADD, node, branch)

    def __after_node_tick(self, node: Node, branch: Branch):
        stat = self.__branchstat[branch].node(node)
        stat[KEY.STEP_TICKED] = self.current_step
        stat[KEY.FLAGS] |= FLAG.TICKED
        self.emit(TabEvent.AFTER_NODE_TICK, node, branch)

    # :-----------:
    # : Util      :
    # :-----------:

    def __get_group_application(self, branch: Branch, rules: Sequence[Rule]) -> RuleTarget:
        """Find and return the next available rule application for the given open
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
        is_group_optim = self.opts['is_group_optim']
        results = deque(maxlen = len(rules) if is_group_optim else 1)
        for rule in rules:
            with rule.search_timer:
                target = rule.get_target(branch)
            if target:
                ruletarget = RuleTarget(rule, target)
                if not is_group_optim:
                    target.update(
                        group_score         = None,
                        total_group_targets = 1,
                        min_group_score     = None,
                        is_group_optim      = False,
                    )
                    return ruletarget
                results.append(ruletarget)
        if results:
            return self.__select_optim_group_application(results)

    def __select_optim_group_application(self, results: Sequence[RuleTarget]) -> RuleTarget:
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

        :param list results: A list/tuple of (Rule, dict) pairs.
        :return: The highest scoring element.
        """
        group_scores = tuple(rule.group_score(target) for rule, target in results)
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

    def __compute_stats(self):
        'Compute the stats property after the tableau is finished.'
        try:
            distinct_nodes = self.tree.root.distinct_nodes
        except AttributeError:
            distinct_nodes = None
        timers = self.timers
        return dict(
            id              = self.id,
            result          = self.__result_word(),
            branches        = len(self),
            open_branches   = len(self.open),
            closed_branches = len(self) - len(self.open),
            rules_applied   = len(self.history),
            distinct_nodes  = distinct_nodes,
            rules_duration_ms = sum(
                step.duration_ms
                for step in self.history
            ),
            build_duration_ms  = timers.build.elapsed,
            trunk_duration_ms  = timers.trunk.elapsed,
            tree_duration_ms   = timers.tree.elapsed,
            models_duration_ms = timers.models.elapsed,
            rules_time_ms = sum(
                sum((rule.search_timer.elapsed, rule.apply_timer.elapsed))
                for rule in self.rules
            ),
            rules = tuple(map(self.__compute_rule_stats, self.rules)),
        )

    def __compute_rule_stats(self, rule: Rule):
        'Compute the stats for a rule after the tableau is finished.'
        return dict(
            name            = rule.name,
            queries         = rule.search_timer.count,
            search_time_ms  = rule.search_timer.elapsed,
            search_time_avg = rule.search_timer.elapsed_avg,
            apply_count     = rule.apply_count,
            apply_time_ms   = rule.apply_timer.elapsed,
            apply_time_avg  = rule.apply_timer.elapsed_avg,
            timers          = {
                name : dict(
                    duration_ms  = timer.elapsed,
                    duration_avg = timer.elapsed_avg,
                    count        = timer.count,
                )
                for name, timer in rule.timers.items()
            },
        )

    def __check_timeout(self):
        timeout = self.opts['build_timeout']
        if timeout is None or timeout < 0:
            return
        if self.timers.build.elapsed > timeout:
            self.timers.build.stop()
            self.__flag |= FLAG.TIMED_OUT
            self.finish()
            raise TimeoutError('Timeout of %dms exceeded.' % timeout)

    def __is_max_steps_exceeded(self):
        max_steps = self.opts['max_steps']
        return max_steps is not None and len(self.history) >= max_steps

    def __check_not_started(self):
        if FLAG.TRUNK_BUILT in self.__flag or len(self.history) > 0:
            raise IllegalStateError("Tableau already started.")

    def __result_word(self):
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
        argument = self.argument
        model: BaseModel
        for branch in self.open:
            self.__check_timeout()
            model = Model()
            model.read_branch(branch)
            model.is_countermodel = argument and model.is_countermodel_to(argument)
            branch.model = model
            yield model

    def _build_tree(self, branches: Sequence[Branch], node_depth = 0, track = None,/):

        s = TreeStruct()

        if track is None:
            track = dict(pos = 1, depth = 0, distinct_nodes = 0, root = s)
        else:
            track['pos'] += 1

        s.update(
            root  = track['root'],
            depth = track['depth'],
            left  = track['pos'],
        )

        while True:

            relevant = tuple(b for b in branches if len(b) > node_depth)
            relnodes = qset()

            for b in relevant:
                relnodes.add(b[node_depth])
                if FLAG.CLOSED in self.stat(b, KEY.FLAGS):
                    s.has_closed = True
                else:
                    s.has_open = True
                if s.has_open and s.has_closed:
                    break

            if len(relnodes) != 1:
                break

            node = relevant[0][node_depth]
            step_added = self.stat(relevant[0], node, KEY.STEP_ADDED)
            s.nodes.append(node)
            if s.step is None or step_added < s.step:
                s.step = step_added
            node_depth += 1

        track['distinct_nodes'] += len(s.nodes)

        if len(branches) == 1:
            self._build_tree_leaf(s, branches[0], track)
        else:
            track['depth'] += 1
            self._build_tree_branches(s, branches, relnodes, node_depth, track)
            track['depth'] -= 1

        s.structure_node_count = s.descendant_node_count + len(s.nodes)

        track['pos'] += 1
        s.right = track['pos']

        if s.root is s:
            s.distinct_nodes = track['distinct_nodes']

        return s

    def _build_tree_leaf(self, s: TreeStruct, branch: Branch, track: dict, /):
        stat = self.stat(branch)
        s.closed = FLAG.CLOSED in stat[KEY.FLAGS]
        # TODO: remove reference branch.closed
        # assert s.closed == branch.closed
        s.open = not branch.closed
        if s.closed:
            s.closed_step = stat[KEY.STEP_CLOSED]
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
        branches: Sequence[Branch],
        relnodes: Sequence[Node],
        node_depth: int,
        track: dict, /
    ):
            w_first = w_last = w_mid = 0

            for i, node in enumerate(relnodes):

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
                elif i == len(relnodes) - 1:
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

class TreeStruct(dmapattr):

    def __init__(self, values = None, /, **kw):
        self.root: TreeStruct = None
        #: The nodes on this structure.
        self.nodes: MutableSequence[Node] = list()
        #: This child structures.
        self.children: MutableSequence[TreeStruct] = list()
        #: Whether this is a terminal (childless) structure.
        self.leaf: bool = False
        #: Whether this is a terminal structure that is closed.
        self.closed: bool = False
        #: Whether this is a terminal structure that is open.
        self.open: bool = False
        #: The pre-ordered tree left value.
        self.left: int = None
        #: The pre-ordered tree right value.
        self.right: int = None
        #: The total node count of all descendants.
        self.descendant_node_count: int = 0
        #: The node count plus descendant node count.
        self.structure_node_count: int  = 0
        #: The depth of this structure (ancestor structure count).
        self.depth: int = None
        #: Whether this structure or a descendant is open.
        self.has_open: bool = False
        #: Whether this structure or a descendant is closed.
        self.has_closed: bool = False
        #: If closed, the step number at which it closed.
        self.closed_step: int|None = None
        #: The step number at which this structure first appears.
        self.step: int = None
        #: The number of descendant terminal structures, or 1.
        self.width: int = 0
        #: 0.5x the width of the first child structure, plus 0.5x the
        #: width of the last child structure (if distinct from the first),
        #: plus the sum of the widths of the other (distinct) children.
        self.balanced_line_width: float = None
        #: 0.5x the width of the first child structure divided by the
        #: width of this structure.
        self.balanced_line_margin: float = None
        #: The branch id, only set for leaves
        self.branch_id: int|None = None
        #: The model id, if exists, only set for leaves
        self.model_id: int|None = None
        #: Whether this is the one and only branch
        self.is_only_branch: bool = False
        #: The step at which the branch was added.
        self.branch_step: int = None

        if values is not None:
            self.update(values)
        if len(kw):
            self.update(kw)

        self.id = id(self)
