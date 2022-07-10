from pytableaux.lang import Constant, Sentence
from pytableaux.proof import Access, Branch, Node, Rule, RuleHelper, Target, ClosingRule, Tableau
from pytableaux.tools import abcs
from pytableaux.tools.mappings import dmap
from pytableaux.tools.sets import setm
from pytableaux.typing import _FiltersDict, _KT, _NodePredFunc, _T, _VT, _NodeTargetsGen, _NodeTargetsFn
from typing import Any, overload

class AdzHelper(RuleHelper):
    rule: Rule
    closure_rules: tuple[ClosingRule, ...]
    def __init__(self, rule: Rule) -> None: ...
    def closure_score(self, target: Target) -> float: ...
    def _apply(self, target: Target) -> None:...

class BranchCache(dmap[Branch, _T], abcs.Copyable, RuleHelper):
    def __init__(self, rule: Rule) -> None: ...
    def copy(self:_T, *, listeners: bool = ...) ->_T: ...
    def listen_on(self, rule: Rule, tableau: Tableau): ...
    def listen_off(self, rule: Rule, tableau: Tableau): ...

class BranchDictCache(BranchCache[dmap[_KT, _VT]]):...

class QuitFlag(BranchCache[bool]):
    def __call__(self, target: Target) -> None: ...

class BranchValueHook(BranchCache[_VT]):
    hook_method_name: str
    def hook(self, node: Node, branch: Branch) -> _VT|None: ...
    def __call__(self, node: Node, branch: Branch) -> None: ...

class BranchTarget(BranchValueHook[Target]):...

class AplSentCount(BranchCache[dmap[Sentence, int]]):
    def __call__(self, target: Target): ...

class NodeCount(BranchCache[dmap[Node, int]]):
    def min(self, branch: Branch) -> int: ...
    def isleast(self, node: Node, branch: Branch) -> bool: ...
    def __call__(self, target: Target): ...

class NodesWorlds(BranchCache[setm[tuple[Node, int]]]):
    def __call__(self, target: Target): ...

class UnserialWorlds(BranchCache[setm[int]]):
    def __call__(self, node: Node, branch: Branch): ...

class WorldIndex(BranchDictCache[int, setm[int]]):
    class Nodes(BranchCache[dmap[Access, Node]]):
        def __call__(self, node: Node, branch: Branch): ...
    nodes: WorldIndex.Nodes
    def has(self, branch: Branch, access: Access) -> bool: ...
    def intransitives(self, branch: Branch, w1: int, w2: int) -> set[int]: ...
    def __call__(self, node: Node, branch: Branch): ...

class FilterNodeCache(BranchCache[set[Node]]):
    ignore_ticked: bool
    def __call__(self, node: Node, branch: Branch) -> bool: ...

class PredNodes(FilterNodeCache):
    def __call__(self, node: Node, _): ...

class FilterHelper(FilterNodeCache):
    filters: _FiltersDict
    pred: _NodePredFunc
    def filter(self, node: Node, branch: Branch) -> bool: ...
    def __call__(self, node: Node, branch: Branch) -> bool: ...
    def example_node(self) -> dict[str, Any]: ...
    def release(self, node: Node, branch: Branch) -> None: ...
    def gc(self) -> None: ...
    @staticmethod
    def build_filters_pred(rule: Rule) -> tuple[_FiltersDict, _NodePredFunc]: ...
    @classmethod
    def node_targets(cls, node_targets_fn: _NodeTargetsFn) -> _NodeTargetsGen: ...

class NodeConsts(BranchDictCache[Node, set[Constant]]):
    class Consts(BranchCache[set[Constant]]): ...
    def filter(self, node: Node, branch: Branch) -> bool: ...
    consts: NodeConsts.Consts
    def __call__(self, node: Node, branch: Branch): ...

class WorldConsts(BranchDictCache[int, set[Constant]]):
    def __call__(self, node: Node, branch: Branch): ...

class MaxConsts(dict[Branch, int], RuleHelper):
    world_consts: WorldConsts
    def is_reached(self, branch: Branch, world: int = ...) -> bool: ...
    def is_exceeded(self, branch: Branch, world: int = ...) -> bool: ...
    def quit_flag(self, branch: Branch) -> dict: ...
    def __call__(self, tableau: Tableau) -> None: ...

class MaxWorlds(dict[Branch, int], RuleHelper):
    def is_reached(self, branch: Branch) -> bool: ...
    def is_exceeded(self, branch: Branch) -> bool: ...
    def modals(self, s: Sentence) -> int: ...
    def quit_flag(self, branch: Branch) -> dict[str, Any]: ...
    def __call__(self, tableau: Tableau) -> None: ...
    def configure_rule(cls, rulecls: type[Rule], config, **kw): ...