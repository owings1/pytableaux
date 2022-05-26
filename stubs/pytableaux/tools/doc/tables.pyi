import reprlib
from _typeshed import Incomplete
from pytableaux.tools import abcs
from pytableaux.tools.doc.directives import TableGenerator
from typing import Callable, Sequence
from sphinx.application import Sphinx

def setup(app: Sphinx) -> None:...

class Reprer(reprlib.Repr, dict, metaclass=abcs.AbcMeta):
    defaults: Incomplete
    attropts: Incomplete
    lw: Callable
    instmap: Incomplete
    instconds: Incomplete
    opts: Incomplete
    def __init__(self, **opts) -> None: ...
    __call__: Incomplete
    def repr1(self, x, level): ...
    def repr_lexclass(self, obj, level): ...
    def repr_lexical(self, obj, level): ...

def oper_sym_table(): ...

class OperSymTable(TableGenerator):
    def gentable(self): ...

def lex_eg_table(columns: list[str], *, notn: str = ..., charset: str = ...): ...

class LexEgTable(TableGenerator):
    required_arguments: int
    optional_arguments: Incomplete
    def gentable(self): ...

def member_table(owner: Sequence, columns: list[str], *, getitem: bool = ...): ...

class MemberTable(TableGenerator):
    required_arguments: int
    optional_arguments: Incomplete
    def gentable(self): ...
