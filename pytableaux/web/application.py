# pytableaux, a multi-logic proof generator.
# Copyright (C) 2014-2023 Doug Owings.
# 
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
# 
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Affero General Public License for more details.
# 
# You should have received a copy of the GNU Affero General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.
"""
pytableaux.web.application
^^^^^^^^^^^^^^^^^^^^^^^^^^

"""
from __future__ import annotations

__all__ = ('Api', 'WebApp')

import logging
from types import MappingProxyType as MapProxy
from typing import Any, Mapping

import cherrypy
import cherrypy._cpdispatch
import jinja2
import prometheus_client as prom
from cherrypy import HTTPError, NotFound, expose
from cherrypy._cprequest import Request, Response

from .. import examples, logics, package, web
from ..lang import (LexType, Notation, Operator, ParseTable, Predicate,
                    Quantifier)
from ..logics import LogicType
from ..proof import writers
from ..tools.events import EventEmitter
from ..web import StaticResource, Wevent
from ..web.mail import Mailroom
from ..web.metrics import AppMetrics
from ..web.util import tojson
from . import views

EMPTY = ()
NOARG = object()

class AppDispatcher(cherrypy._cpdispatch.Dispatcher):

    def __call__(self, path_info: str):
        req: Request = cherrypy.request
        req.remote.ip = req.headers.get('X-Forwarded-For', req.remote.ip)
        self.app.emit(Wevent.before_dispatch, path_info)
        try:
            return super().__call__(path_info.split('?')[0])
        finally:
            self.app.emit(Wevent.after_dispatch, path_info)

    @property
    def app(self) -> WebApp:
        return cherrypy.serving.request.app.root

class Api:
    parse = views.ApiParseView()
    prove = views.ApiProveView()
    default = views.ApiView()


class WebApp(EventEmitter):

    config: Mapping[str, Any]
    "Config."

    static_res: Mapping[str, StaticResource]
    "In-memory static resources."

    metrics: AppMetrics
    "Prometheus metrics helper."

    logger: logging.Logger
    "Logger instance."

    template_cache: dict[str, jinja2.Template]
    "Instance jinja2 template cache."

    jenv: jinja2.Environment
    "Instance jinja2 template environment."

    default_context: Mapping[str, Any] = MapProxy(dict(
        package = package,
        LexType = LexType,
        Notation = Notation,
        Operator = Operator,
        Quantifier = Quantifier,
        Predicate = Predicate,
        ParseTable = ParseTable,
        writers = writers))
    "Default template context."

    example_args: Mapping[str, Mapping[str, Mapping[str, Any]]]
    logics_map: Mapping[str, LogicType]
    jsapp_data: Mapping[str, Any]

    dispatcher = AppDispatcher()

    api = Api()
    index = views.ProveView()
    health = views.HealthView()
    feedback = views.FeedbackView()

    @expose
    def static(self, *args, **kw):
        req: Request = cherrypy.request
        res: Response = cherrypy.response
        path = '/'.join(args)
        try:
            resource = self.static_res[path]
        except KeyError:
            raise NotFound()
        if req.method != 'GET' and req.method != 'HEAD':
            raise HTTPError(405)
        res.headers.update(resource.headers)
        if resource.is_modified_since(req.headers.get('If-Modified-Since')):
            return resource.content
        res.status = 304

    @property
    def is_debug(self) -> bool:
        return self.config['is_debug']

    @property
    def json_indent(self) -> int|None:
        return 2 if self.is_debug else None

    def __init__(self, *args, **kw):
        super().__init__(*Wevent)
        self.config = web.EnvConfig.env_config()
        self.config.update(*args, **kw)
        self.logger = web.get_logger(self, self.config)
        self.mailroom = Mailroom(self.config)
        self.metrics = AppMetrics(self.config, prom.CollectorRegistry())
        self.template_cache = {}
        self.jenv = jinja2.Environment(
            loader = jinja2.FileSystemLoader(self.config['templates_path']))
        self.example_args = self._build_example_args()
        self.logics_map = MapProxy({key: logics.registry(key) for key in logics.__all__})
        self.jsapp_data = self._build_jsapp_data()
        self.static_res = self._create_static_res()
        self.default_context = MapProxy(dict(self.default_context,
            config = self.config,
            is_debug = self.is_debug,
            logics = self.logics_map,
            example_args = self.example_args,
            output_charsets = Notation.get_common_charsets(),
            logic_categories = logics.registry.grouped(self.logics_map),
            lwh = Notation.standard.DefaultWriter('html'),
            toJson = self.tojson))
        self.on(Wevent.before_dispatch, self.before_dispatch)

    def start(self):
        """Start the web server."""
        config = self.config
        self.mailroom.start()
        cherrypy.config.update({
            'global': {
                'server.max_request_body_size': 1024 * 1000,
                'server.socket_host'   : config['host'],
                'server.socket_port'   : config['port'],
                'engine.autoreload.on' : config['is_debug']}})
        if config['metrics_enabled']:
            metrics_host = config['metrics_host']
            metrics_port = config['metrics_port']
            self.logger.info(f'Starting metrics on port {metrics_host}:{metrics_port}')
            prom.start_http_server(metrics_port, metrics_host, self.metrics.registry)
        cherrypy.quickstart(self, '/', self._routes())

    def _routes(self) -> dict[str, dict[str, Any]]:
        "Cherrypy routing config."
        config = self.config
        static_dir = config['static_dir']
        return {
            '/': {
                'request.dispatch': self.dispatcher,
                'tools.gzip.on': True,
                'tools.gzip.mime_types': {
                    'text/html',
                    'text/plain',
                    'text/css',
                    'application/javascript',
                    'application/xml'}},
            '/static': {
                'tools.staticdir.on': True,
                'tools.staticdir.dir': static_dir,
                'tools.etags.on': True,
                'tools.etags.autotags': True},
            '/doc': {
                'tools.staticdir.on': True,
                'tools.staticdir.dir': config['doc_dir'],
                'tools.staticdir.index': 'index.html',
                'tools.etags.on': True,
                'tools.etags.autotags': True},
            '/favicon.ico': {
                'tools.staticfile.on': True,
                'tools.staticfile.filename': f'{static_dir}/favicon.ico'},
            '/robots.txt': {
                'tools.staticfile.on': True,
                'tools.staticfile.filename': f'{static_dir}/robots.txt'}}

    def before_dispatch(self, path):
        self.metrics.app_requests_count(path).inc()

    def get_template(self, name: str) -> jinja2.Template:
        cache = self.template_cache
        if '.' not in name:
            name = f'{name}.jinja2'
        if self.is_debug or name not in cache:
            cache[name] = self.jenv.get_template(name)
        return cache[name]

    def render(self, template: str, *args, **kw):
        context = dict(self.default_context)
        context.update(*args, **kw)
        return self.get_template(template).render(context)

    def tojson(self, obj, /, *, indent=None, **kw) -> str:
        if indent is None:
            indent = self.json_indent
        return tojson(obj, indent=indent, **kw)

    def _build_example_args(self):
        return MapProxy({
            arg.title: MapProxy({
                lw.notation.name: MapProxy(dict(
                    premises = tuple(map(lw, arg.premises)),
                    conclusion = lw(arg.conclusion)))
                for lw in (
                    notn.DefaultWriter('ascii')
                    for notn in Notation)} | {
                '@Predicates': tuple(
                    p.spec for p in arg.predicates(sort=True)
                        if not p.is_system)})
            for arg in examples.arguments()})

    def _create_static_res(self):
        app_json = self.tojson(self.jsapp_data)
        return MapProxy({
            resource.path: resource
            for resource in (
                StaticResource('js/appdata.json', app_json),
                StaticResource('js/appdata.js', f';window.AppData={app_json};'))})
    
    def _build_jsapp_data(self):
        return MapProxy(dict(
            example_args = self.example_args,
            example_preds = tuple(p.spec for p in examples.preds),
            nups = MapProxy({
                notn.name: ParseTable.fetch(notn).chars[LexType.Predicate]
                for notn in Notation})))