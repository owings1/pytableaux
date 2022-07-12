from typing import (Any, ClassVar, Iterable, Literal, Mapping, Optional,
                    Sequence, SupportsIndex, overload)
from collections.abc import Set

from pytableaux.lang import Argument, Sentence
from pytableaux.models import BaseModel
from pytableaux.proof import (Branch, LogicType, Node,
                              RuleHelper, RuleMeta, RuleState, StepEntry,
                              TabFlag, TableauxSystem, TabStatKey, TabTimers,
                              Target)
from pytableaux.tools.events import EventEmitter
from pytableaux.tools.hybrids import qsetf
from pytableaux.tools.mappings import dictns
from pytableaux.tools.sequences import SequenceApi
from pytableaux.tools.timing import StopWatch
from pytableaux.typing import _T, _LogicLookupKey, _RuleT, _Self, _TypeInstDict


class Rule(EventEmitter, metaclass=RuleMeta):
    _defaults: ClassVar[Mapping[str, Any]]
    Helpers: ClassVar[Mapping[type[RuleHelper], Any]]
    Timers: ClassVar[qsetf[str]]
    branching: ClassVar[int]
    helpers: _TypeInstDict[RuleHelper]
    history: Sequence[Target]
    legend: ClassVar[tuple]
    name: ClassVar[str]
    opts: Mapping[str, bool]
    state: RuleState
    tableau: Tableau
    timers: Mapping[str, StopWatch]
    def __getitem__(self, key: type[_T]) -> _T: ...
    def __init__(self, tableau: Tableau, **opts) -> None: ...
    def apply(self, target: Target) -> None: ...
    def branch(self, parent: Optional[Branch] = ...) -> Branch: ...
    def example_nodes(self) -> Iterable[Mapping]: ...
    def group_score(self, target: Target) -> float: ...
    def score_candidate(self, target: Target) -> float: ...
    def sentence(self, node: Node) -> Optional[Sentence]: ...
    def stats(self) -> dict[str, Any]: ...
    def target(self, branch: Branch) -> Optional[Target]: ...
    @classmethod
    def test(cls, *, noassert: bool = ...): ...

class RulesRoot(SequenceApi[Rule]):
    groups: RuleGroups
    root: RulesRoot
    locked: bool
    tableau: Tableau
    def __init__(self, tab: Tableau) -> None: ...
    def append(self, rule: type[Rule]): ...
    def extend(self, rules: Iterable[type[Rule]], name: Optional[str] = ...): ...
    def clear(self) -> None: ...
    @overload
    def get(self, ref: type[_RuleT], default=...) -> _RuleT: ...
    @overload
    def get(self, ref: str, default=...) -> Rule: ...
    def names(self) -> Set[str]: ...
    @overload
    def __getitem__(self, i: SupportsIndex) -> Rule: ...
    @overload
    def __getitem__(self, s: slice) -> Sequence[Rule]: ...

class RuleGroup(SequenceApi[Rule]):
    root: RulesRoot
    name: Optional[str]
    def __init__(self, name: Optional[str], root: RulesRoot) -> None: ...
    def append(self, value: type[Rule]): ...
    def extend(self, values: Iterable[type[Rule]]): ...
    def clear(self) -> None: ...
    @overload
    def get(self, ref: type[_RuleT], default=...) -> _RuleT: ...
    @overload
    def get(self, ref: str, default=...) -> Rule: ...
    def names(self) -> Set[str]: ...
    @overload
    def __getitem__(self, i: SupportsIndex) -> Rule: ...
    @overload
    def __getitem__(self, s: slice) -> Sequence[Rule]: ...

class RuleGroups(SequenceApi[RuleGroup]):
    root: RulesRoot
    def __init__(self, root: RulesRoot) -> None: ...
    def create(self, name: Optional[str] = ...) -> RuleGroup: ...
    def append(self, Rules: Iterable[type[Rule]], name: Optional[str] = ...) -> None: ...
    def extend(self, groups: Iterable[Iterable[type[Rule]]]) -> None: ...
    def clear(self) -> None: ...
    def get(self, name: str, default=...) -> RuleGroup: ...
    def names(self) -> Set[str]: ...

class Tableau(Sequence[Branch], EventEmitter):
    history: Sequence[StepEntry]
    models: frozenset[BaseModel]
    open: Sequence[Branch]
    opts: Mapping[str, Optional[bool|int]]
    rules: RulesRoot
    stats: dict[str, Any]
    timers: TabTimers
    tree: TreeStruct
    def __init__(self, logic: Optional[_LogicLookupKey] = ..., argument: Optional[Argument] = ..., **opts) -> None: ...
    @property
    def id(self) -> int: ...
    @property
    def flag(self) -> TabFlag: ...
    @property
    def argument(self) -> Optional[Argument]: ...
    @property
    def logic(self) -> Optional[LogicType]: ...
    @property
    def System(self) -> Optional[TableauxSystem]: ...
    @argument.setter
    def argument(self, argument: Argument): ...
    @logic.setter
    def logic(self, logic: _LogicLookupKey): ...
    @property
    def finished(self) -> bool: ...
    @property
    def completed(self) -> bool: ...
    @property
    def premature(self) -> bool: ...
    @property
    def valid(self) -> Optional[bool]: ...
    @property
    def invalid(self) -> Optional[bool]: ...
    @property
    def current_step(self) -> int: ...
    def add(self: _Self, branch: Branch) -> _Self: ...
    def branch(self, parent: Optional[Branch] = ...) -> Branch: ...
    def branching_complexity(self, node: Node) -> int: ...
    def build(self: _Self) -> _Self: ...
    def finish(self: _Self) -> _Self: ...
    def next(self) -> Optional[StepEntry]: ...
    def stat(self, branch: Branch, *keys: Node|TabStatKey) -> Any: ...
    def step(self) -> Optional[StepEntry|Literal[False]]: ...
    @overload
    def __getitem__(self, s: slice) -> list[Branch]: ...
    @overload
    def __getitem__(self, i: SupportsIndex) -> Branch: ...

class TreeStruct(dictns):
    root: bool
    nodes: list[Node]
    ticksteps: list[int|None]
    children: list[TreeStruct]
    leaf: bool
    closed: bool
    open: bool
    left: int
    right: int
    descendant_node_count: int
    structure_node_count: int
    depth: int
    has_open: bool
    has_closed: bool
    closed_step: Optional[int]
    step: int
    width: int
    balanced_line_width: float
    balanced_line_margin: float
    branch_id: Optional[int]
    model_id: Optional[int]
    is_only_branch: bool
    branch_step: int
    id: int
    def __init__(self) -> None: ...
