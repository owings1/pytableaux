from typing import Any, ClassVar, Iterable, Mapping, overload

from pytableaux.lang import (Operated, Operator, Predicate, Predicated,
                             Quantified, Quantifier, Sentence)
from pytableaux.proof import Branch, Node, Target, filters


class ClosingRule(Rule):
    def nodes_will_close_branch(self, nodes: Iterable[Node], branch: Branch) -> bool: ...

class NoopRule(Rule):
    @staticmethod
    def example_nodes(): ...

class BaseClosureRule(ClosingRule):
    def nodes_will_close_branch(self, nodes: Iterable[Node], branch: Branch) -> bool: ...
    def node_will_close_branch(self, node: Node, branch: Branch) -> bool: ...

class BaseSimpleRule(Rule):
    def score_candidate(self, target: Target) -> float: ...

class BaseNodeRule(BaseSimpleRule):
    ignore_ticked: ClassVar[bool]
    def example_nodes(self) -> tuple[dict]: ...

class BaseSentenceRule(BaseNodeRule):
    NodeFilters: ClassVar[Mapping[type[filters.NodeCompare], Any]]
    negated: ClassVar[bool|None]
    operator: ClassVar[Operator|None]
    quantifier: ClassVar[Quantifier|None]
    predicate: ClassVar[Predicate|None]
    def sentence(self, node: Node) -> Sentence: ...

class PredicatedSentenceRule(BaseSentenceRule):
    @overload
    def sentence(self, node: Node) -> Predicated: ...

class QuantifiedSentenceRule(BaseSentenceRule):
    @overload
    def sentence(self, node: Node) -> Quantified: ...

class OperatedSentenceRule(BaseSentenceRule):
    @overload
    def sentence(self, node: Node) -> Operated: ...

class NarrowQuantifierRule(QuantifiedSentenceRule):
    def _get_node_targets(self, node: Node, branch: Branch, /) -> Iterable[Target]:...
class ExtendedQuantifierRule(NarrowQuantifierRule):...
class GetNodeTargetsRule(BaseNodeRule):
    def _get_node_targets(self, node: Node, branch: Branch, /) -> Iterable[Target]:...

from pytableaux.proof.tableaux import Rule as Rule
