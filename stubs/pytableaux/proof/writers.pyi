from typing import Any, ClassVar, Collection, Mapping, TypeVar, overload
import jinja2

from pytableaux.lang import LexWriter, Notation
from pytableaux.proof.tableaux import Tableau
from pytableaux.tools import abcs
from pytableaux.typing import _TT


registry: Mapping[str, type[TabWriter]]

def register(wcls: type[TabWriter],/, *, force: bool = False): ...

class TabWriterMeta(abcs.AbcMeta):
    DefaultFormat: ClassVar[str]
    def __call__(cls, *args, **kw): ...

class TabWriter(metaclass=TabWriterMeta):
    format: ClassVar[str]
    default_charsets: ClassVar[Mapping[Notation, str]]
    defaults: ClassVar[Mapping[str, Any]]
    lw: LexWriter
    opts: dict[str, Any]
    def __init__(self, notn: Notation|str = ..., charset: str = ..., *, lw: LexWriter = ..., **opts) -> None: ...
    def attachments(self) -> Mapping[str, Any]: ...
    def write(self, tableau: Tableau, **kw) -> str: ...
    def __call__(self, tableau: Tableau, **kw) -> str: ...
    @classmethod
    def register(cls, subcls: _TT) -> _TT: ...

class TemplateTabWriter(TabWriter):
    template_dir: ClassVar[str]
    jinja_opts: ClassVar[Mapping[str, Any]]
    _jenv: ClassVar[jinja2.Environment]
    @classmethod
    def render(cls, template: str, *args, **kw) -> str: ...

class HtmlTabWriter(TemplateTabWriter):
    def write(self, tab: Tableau, *, classes: Collection[str] = ...) -> str: ...
    def attachments(self) -> dict[str, str]: ...

class TextTabWriter(TemplateTabWriter):
    def write(self, tab: Tableau) -> str: ...

