from enum import Enum
from types import ModuleType
from typing import (Any, Callable, ClassVar, Collection, Generic, Mapping,
                    NamedTuple, Pattern, overload)

import jinja2
import sphinx.config
import sphinx.directives
from docutils import nodes
from sphinx.application import Sphinx
from sphinx.config import Config
from sphinx.environment import BuildEnvironment
from sphinx.util.docutils import SphinxRole
from sphinx.util.typing import RoleFunction

from pytableaux.lang import Operator, Parser, Predicates
from pytableaux.logics import LogicType
from pytableaux.tools import abcs, dictns, qset
from pytableaux.typing import _T, _DictT

APPSTATE: dict[Sphinx, dict]

class SphinxEvent(str, Enum):
    IncludeRead: str

class ConfKey(str, Enum):
    copy_file_tree: str
    auto_skip_enum_value: str
    wnotn: str
    charset: str
    rset: str
    pnotn: str
    preds: str
    truth_table_template: str
    truth_table_reverse: str
    templates_path: str

class AppEnvMixin(abcs.Abc):
    app: Sphinx
    env: BuildEnvironment
    config: Config
    @property
    def appstate(self) -> dict: ...
    @property
    def jenv(self) -> jinja2.Environment: ...
    def current_module(self) -> ModuleType: ...
    def current_class(self) -> type: ...
    def current_logic(self) -> LogicType: ...
    def viewcode_target(self, obj: Any = ...) -> str: ...

class RenderMixin(AppEnvMixin):
    def render(self, template, *args, **kw): ...

class RoleDirectiveMixin(AppEnvMixin):
    option_spec: ClassVar[Mapping[str, Callable]]
    options: dict[str, Any]
    def set_classes(self, opts=...) -> qset[str]: ...
    def parse_opts(self, rawopts: Mapping[str, Any]) -> dict[str, Any]: ...
    def run(self): ...

class ParserOptionMixin(RoleDirectiveMixin):
    def parser_option(self) -> Parser: ...

class BaseDirective(sphinx.directives.SphinxDirective, RoleDirectiveMixin):
    arguments: list[str]

class DirectiveHelper(RoleDirectiveMixin):
    required_arguments: int
    optional_arguments: int
    @staticmethod
    def arg_parser(arg: str) -> list[str]: ...
    inst: BaseDirective
    arguments: list[str]
    def __init__(self, inst: BaseDirective, rawarg: str) -> None: ...


class BaseRole(SphinxRole, RoleDirectiveMixin):
    patterns: ClassVar[dict[str, str|Pattern]]
    def __init__(self) -> None: ...
    def wrapped(self:_T, name: str, newopts: Mapping, newcontent: list[str] = ...) -> _T: ...

class Processor(AppEnvMixin):
    def run(self) -> None: ...

class AutodocProcessor(Processor):
    lines: list[str]
    record: AutodocProcessor.Record

    class Record(dictns):
        what: str
        name: str
        obj: Any
        options: dict
        lines: list[str]
        def __init__(self, what, name, obj, options, lines) -> None: ...

    def hastext(self, txt: str): ...
    def applies(self): ...
    def __call__(self, app: Sphinx, *args): ...
    def __iadd__(self, other: str|list[str]): ...
    def prepstr(self, s: str|list[str], ignore: int = ..., tabsize: int = ...) -> list[str]: ...

class ReplaceProcessor(Processor):
    event: str
    mode: str
    lines: list[str]
    args: tuple[Any, ...]
    @overload
    def __call__(self, app: Sphinx, docname: str, lines: list[str]): ...
    @overload
    def __call__(self, app: Sphinx, lines: list[str]): ...
    @overload
    def __call__(self, app: Sphinx, what: Any, name: str, obj: Any, options: dict, lines: list[str]): ...

class Tabler(list[list[str]], abcs.Abc):
    header: list[str]
    body: list[list[str]]
    meta: dict[str, Any]
    def __init__(self, body: list[list[str]], header: list[str]|None, **meta) -> None: ...
    def apply_repr(self, reprfunc: Callable) -> Tabler: ...
    def tb(self, tablefmt: str = ..., *, rp: Callable[[Any], Any] = ..., **kw): ...

re_space: Pattern
re_comma: Pattern
re_nonslug_plus: Pattern

def attrsopt(arg: str, /) -> list[str]:...
def boolopt(arg: str, /) -> bool:...
def choice_or_flag(choices: Collection[_T], /,trans: Callable = ...,default = None, **kw):...
def choiceopt(choices: Collection[_T], /, trans: Callable = ...) -> _T:...
def classopt(arg: str) -> list[str]: ...
def cleanws(arg: str) -> str: ...
def flagopt(arg: Any) -> None:...
def nodeopt(arg: str) -> type[nodes.Node]: ...
def opersopt(arg: str) -> tuple[Operator, ...]: ...
def predsopt(arg: str) -> Predicates: ...
def set_classes(opts: _DictT) -> _DictT:...
def snakespace(name):...
def stropt(arg: str, /) -> str:...
def viewcode_target(obj: Any) -> str: ...

class RoleItem(NamedTuple, Generic[_T]):
    name: str
    inst: _T

@overload
def role_entry(rolecls: type[_T]) -> RoleItem[_T]|None: ...
@overload
def role_entry(rolefn: RoleFunction) -> RoleItem[RoleFunction]|None: ...
@overload
def role_entry(roleish: str) -> RoleItem[RoleFunction]|None: ...
def role_instance(roleish: type[_T]) -> _T|None: ...
def role_name(roleish: type|RoleFunction) -> str|None: ...
