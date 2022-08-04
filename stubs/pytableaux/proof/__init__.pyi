from typing import Any, Mapping, NamedTuple

from pytableaux.lang import Argument, Sentence
from pytableaux.proof.tableaux import RulesRoot
from pytableaux.tools import abcs
from pytableaux.tools.timing import Counter, StopWatch
from pytableaux.typing import _T, _SysRulesT

_Node = dict

def group(*items: _T) -> tuple[_T, ...]:...
def adds(*groups: tuple[dict, ...], **kw) -> dict[str, tuple[dict, ...]|Any]:...

class TableauxSystem(metaclass=abcs.AbcMeta):
    @classmethod
    def build_trunk(cls, tableau: Tableau, argument: Argument) -> None: ...
    @classmethod
    def branching_complexity(cls, node: Node) -> int: ...
    @classmethod
    def add_rules(cls, logic: LogicType, rules: RulesRoot) -> None: ...
    @classmethod
    def initialize(cls, RulesClass: type[_SysRulesT]) -> type[_SysRulesT]: ...

class RuleHelper(metaclass=abcs.AbcMeta):
    rule: Rule
    config: Any
    def __init__(self, rule: Rule) -> None: ...
    def listen_on(self) -> None:...
    def listen_off(self) -> None:...
    @classmethod
    def configure_rule(cls, rulecls: type[Rule], config: Any): ...

class RuleMeta(abcs.AbcMeta):
    @classmethod
    def __prepare__(cls, clsname: str, bases: tuple[type, ...], **kw) -> dict[str, Any]: ...
    def __new__(cls, clsname: str, bases: tuple[type, ...], ns: dict, modal: bool = ..., **kw): ...

class NodeStat(dict[TabStatKey, TabFlag|int]):
    def __init__(self) -> None:...

class BranchStat(dict[TabStatKey, TabFlag|int|dict[Any, NodeStat]]):
    def node(self, node: Node) -> NodeStat:...
    def view(self) -> dict[TabStatKey, TabFlag|int|Any]:...

class TabTimers(NamedTuple):
    build  : StopWatch
    trunk  : StopWatch
    tree   : StopWatch
    models : StopWatch
    @staticmethod
    def create() -> TabTimers:...

class HelperAttr(str, abcs.Ebc):
    InitRuleCls :str

class RuleAttr(str, abcs.Ebc):
    Helpers:str
    Timers:str
    DefaultOpts:str
    Name:str
    NodeFilters :str
    IgnoreTicked:str
    ModalOperators:str
    Modal:str
    Legend:str

class ProofAttr(str, abcs.Ebc):
    pass

class NodeAttr(ProofAttr):
    designation: str
    designated: str
    closure: str
    flag: str
    is_flag: str
    world: str
    world1: str
    w1: str
    world2: str
    w2: str
    info: str
    sentence: str

class PropMap(abcs.ItemMapEnum):
    NodeDefaults:Mapping
    ClosureNode:Mapping
    QuitFlag:Mapping

class BranchEvent(abcs.Ebc):
    AFTER_CLOSE :object
    AFTER_ADD   :object
    AFTER_TICK  :object

class RuleEvent(abcs.Ebc):
    BEFORE_APPLY:object
    AFTER_APPLY :object

class RuleState(abcs.FlagEnum):
    NONE   :int
    INIT   :int
    LOCKED :int

class TabEvent(abcs.Ebc):
    AFTER_BRANCH_ADD    :object
    AFTER_BRANCH_CLOSE  :object
    AFTER_NODE_ADD      :object
    AFTER_NODE_TICK     :object
    AFTER_TRUNK_BUILD   :object
    BEFORE_TRUNK_BUILD  :object
    AFTER_FINISH        :object

class TabStatKey(abcs.Ebc):
    FLAGS       :object
    STEP_ADDED  :object
    STEP_TICKED :object
    STEP_CLOSED :object
    INDEX       :object
    PARENT      :object
    NODES       :object

class TabFlag(abcs.FlagEnum):
    NONE   :int
    TICKED :int
    CLOSED :int
    PREMATURE   :int
    FINISHED    :int
    TIMED_OUT   :int
    TRUNK_BUILT :int
    TIMING_INACCURATE :int

class StepEntry(NamedTuple):
    rule   : Rule
    target : Target
    duration: Counter

class Access(NamedTuple):
    world1: int
    world2: int
    @property
    def w1(self) -> int:...
    @property
    def w2(self) -> int:...
    @classmethod
    def fornode(cls, node: Mapping) -> Access:...
    def reversed(self) -> Access:...
    def tonode(self) -> _Node: ...


def snode(s: Sentence) -> _Node:...
def sdnode(s: Sentence, d:bool) -> _Node:...
def swnode(s: Sentence, w:int) -> _Node:...
def anode(w1:int, w2:int) -> _Node:...


from pytableaux.logics import LogicType as LogicType
from pytableaux.proof.common import Branch as Branch
from pytableaux.proof.common import Node as Node
from pytableaux.proof.common import Target as Target
from pytableaux.proof.rules import ClosingRule as ClosingRule
from pytableaux.proof.tableaux import Rule as Rule
from pytableaux.proof.tableaux import Tableau as Tableau
from pytableaux.proof.tableaux import TreeStruct as TreeStruct
from pytableaux.proof.writers import TabWriter as TabWriter
