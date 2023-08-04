import logging
from typing import Any, ClassVar, Collection, Mapping, Sequence

import cherrypy as chpy
import jinja2
from cherrypy._cprequest import Request
from pytableaux.logics import LogicType
from pytableaux.lang import Argument, LexWriter, Notation, Predicates
from pytableaux.proof import Tableau
from pytableaux.tools.events import EventEmitter
from pytableaux.web.mail import Mailroom
from pytableaux.web.metrics import AppMetrics

from pytableaux.tools.hybrids import qsetf


class WebApp(EventEmitter):
    api_defaults: Mapping[str, Any]
    jsapp_data: Mapping[str, Any]

    config: dict[str, Any]
    default_context: dict[str, Any]
    logics_map: Mapping[str, LogicType]
    example_args: Mapping[str, Mapping[str, Mapping[str, Any]]]
    lexwriters: Mapping[Notation, Mapping[str, LexWriter]]
    jenv: jinja2.Environment
    logger: logging.Logger
    mailroom: Mailroom
    metrics: AppMetrics
    static_res: dict[str, bytes]
    template_cache: dict[str, jinja2.Template]
    def __init__(self, opts: Mapping[str, Any] = ..., **kw) -> None: ...
    def routes(self) -> dict[str, dict[str, Any]]: ...
    def init_events(self): ...
    def start(self) -> None: ...
    def static(self, *respath, **req_data): ...
    def index(self, **req_data): ...
    def feedback(self, **form_data) -> str: ...
    def api(self, action: str = ...) -> dict[str, Any]: ...
    def api_parse(self, body: Mapping) -> dict[str, Any]: ...
    def api_prove(self, body: Mapping) -> tuple[dict, Tableau, LexWriter]: ...
    def get_template(self, view: str) -> jinja2.Template: ...
    def render(self, view: str, *args, **kw) -> str: ...
    def get_remote_ip(req: Request) -> str: ...
    @classmethod
    def setup_class_data(cls) -> None: ...
    @staticmethod
    def trim_resp_debug(resp_data: dict) -> dict: ...
    @staticmethod
    def _parse_preds(pspecs: Collection[Mapping|Sequence]) -> Predicates|None:...
    @classmethod
    def _parse_argument(cls, adata: Mapping) -> Argument:...

class AppDispatcher(chpy._cpdispatch.Dispatcher):
    def __call__(self, path_info: str): ...
    def webapp(self) -> WebApp: ...
    def before_dispatch(self, *args) -> None: ...
