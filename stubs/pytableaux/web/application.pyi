import logging
from typing import Any, Mapping

import cherrypy as chpy
import jinja2
from pytableaux.logics import LogicType
from pytableaux.tools.events import EventEmitter
from pytableaux.web.mail import Mailroom
from pytableaux.web.metrics import AppMetrics



class WebApp(EventEmitter):
    jsapp_data: Mapping[str, Any]

    config: dict[str, Any]
    default_context: dict[str, Any]
    logics_map: Mapping[str, LogicType]
    example_args: Mapping[str, Mapping[str, Mapping[str, Any]]]
    jenv: jinja2.Environment
    logger: logging.Logger
    mailroom: Mailroom
    metrics: AppMetrics
    static_res: dict[str, bytes]
    template_cache: dict[str, jinja2.Template]
    def __init__(self, opts: Mapping[str, Any] = ..., **kw) -> None: ...
    def init_events(self): ...
    def start(self) -> None: ...
    def static(self, *respath, **req_data): ...
    def get_template(self, view: str) -> jinja2.Template: ...
    def render(self, view: str, *args, **kw) -> str: ...

class AppDispatcher(chpy._cpdispatch.Dispatcher): ...
