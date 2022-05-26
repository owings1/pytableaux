from typing import Any, Callable, Sequence

import sphinx.config
from pytableaux.lang import (Argument, LexWriter, Operator, Predicate,
                             Quantifier, RenderSet)
from pytableaux.proof import Rule, Tableau, TabWriter
from pytableaux.tools.doc import (BaseDirective, DirectiveHelper,
                                  ParserOptionMixin, RenderMixin, Tabler)
from sphinx import addnodes
from sphinx.application import Sphinx


class TableGenerator(DirectiveHelper):
    def gentable(self) -> Tabler: ...
    def run(self): ...

table_generators: dict[str, TableGenerator]

class SentenceBlock(BaseDirective, ParserOptionMixin):
    pass

class TableauDirective(BaseDirective, ParserOptionMixin):
    modes: dict[str, set[str]]
    mode: str
    charset: str
    renderset: RenderSet
    writer: TabWriter
    lwuni: LexWriter
    _trunk_argument: Argument
    def setup(self, force: bool = ...) -> None: ...
    def gettab_rule(self) -> Tableau: ...
    def gettab_argument(self) -> Tableau: ...
    def gettab_trunk(self) -> Tableau: ...
    def getnode_ruledoc_wrapper(self, rulecls: type[Rule], *inserts) -> addnodes.desc: ...
    def getnodes_ruledoc_pair(self, rulecls: type[Rule], *inserts) -> tuple[addnodes.desc, addnodes.desc_content]: ...
    def getnodes_rule_legend(self, rule: Rule|type[Rule]): ...
    def getnodes_trunk_prolog(self): ...
    @classmethod
    def get_trunk_renderset(cls, notn, charset) -> RenderSet:...

class RuleGroupDirective(TableauDirective):
    groupmode: str
    ruleinfo: dict[str, Any]
    title: str|None
    group: list[type[Rule]]|None
    subgroups: dict[Predicate|Quantifier|Operator, list[type[Rule]], None]
    exclude: set[str]
    include: set[str]|None
    groupid: str
    subgroup: list[type[Rule]]|None
    subgroup_type: type[Predicate|Quantifier|Operator]|None
    def setup(self) -> None: ...

class TruthTables(BaseDirective, RenderMixin):
    pass
class CSVTable(sphinx.directives.patches.CSVTable, BaseDirective):
    generator: TableGenerator|None
    def get_csv_data(self) -> Sequence[Sequence[str]]: ...
    class _writeshim:
        def write(self) -> None:...
        def __init__(self, func:Callable) -> None: ...
    @classmethod
    def csvlines(cls, rows: list[list[str]], quoting=..., **kw) -> list[str]: ...

class Include(sphinx.directives.other.Include, BaseDirective):
    class StateMachineProxy:
        pass

def setup(app: Sphinx)-> None:...
