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
pytableaux.web.app
^^^^^^^^^^^^^^^^^^

"""
from __future__ import annotations

import logging
from types import MappingProxyType as MapProxy
from typing import TYPE_CHECKING, Any, Mapping

import cherrypy
import cherrypy._cpdispatch
import jinja2
from cherrypy import HTTPError, NotFound, expose
from cherrypy._cprequest import Request, Response

from ... import examples, logics, package
from ...lang import (Argument, LexType, LexWriter, Notation, Operator,
                     ParseTable, Predicate, Quantifier)
from ...logics import LogicType
from ...proof import writers
from ...tools import inflect
from ...tools.events import EventEmitter
from .. import EnvConfig, StaticResource, Wevent, api
from ..util import cp_staticdir_conf, get_logger, tojson
from . import views

if TYPE_CHECKING:
    from ..metrics import AppMetrics

EMPTY = ()
NOARG = object()

all = (
    'App',
    'Dispatcher',
    'Helper')

class Dispatcher(cherrypy._cpdispatch.Dispatcher):

    def __call__(self, path_info: str):
        req: Request = cherrypy.request
        req.remote.ip = req.headers.get('X-Forwarded-For', req.remote.ip)
        self.app.emit(Wevent.before_dispatch, path_info)
        try:
            return super().__call__(path_info.split('?')[0])
        finally:
            self.app.emit(Wevent.after_dispatch, path_info)

    @property
    def app(self) -> App:
        return cherrypy.serving.request.app.root

class App(EventEmitter):

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

    jinja: jinja2.Environment
    "Instance jinja2 template environment."

    default_context: Mapping[str, Any] = MapProxy(dict(
        package = package,
        inflect = inflect,
        LexType = LexType,
        Notation = Notation,
        Operator = Operator,
        Quantifier = Quantifier,
        Predicate = Predicate,
        ParseTable = ParseTable,
        writers = writers))
    "Default template context."

    cp_config: Mapping[str, Any]
    example_args: Mapping[str, Mapping[str, Mapping[str, Any]]]
    example_args_rev: Mapping[Argument, str]
    logics_map: Mapping[str, LogicType]
    jsapp_data: Mapping[str, Any]

    dispatcher = Dispatcher()

    api = api.app

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
            raise NotFound() from None
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
        self.config = EnvConfig.env_config()
        self.config.update(*args, **kw)
        self.logger = get_logger(self, self.config)
        self.cp_config = self._build_cp_config()
        if self.config['feedback_enabled']:
            from ..mail import Mailroom
            self.mailroom = Mailroom(self.config)
        if self.config['metrics_enabled']:
            from prometheus_client import CollectorRegistry

            from ..metrics import AppMetrics
            self.metrics = AppMetrics(self.config, CollectorRegistry())
        self.template_cache = {}
        self.jinja = jinja2.Environment(
            loader = jinja2.FileSystemLoader(self.config['templates_path']))
        self.example_args = self._build_example_args()
        self.example_args_rev = MapProxy(dict(map(reversed, examples.args.items())))
        logics.registry.import_all()
        self.logics_map = MapProxy({
            logic.Meta.name.lower(): logic
            for logic in logics.registry.values()})
        self.jsapp_data = self._build_jsapp_data()
        self.static_res = self._create_static_res()
        self.helper = Helper(self)
        self.default_context = MapProxy(dict(self.default_context,
            h = self.helper,
            config = self.config,
            is_debug = self.is_debug,
            logics = self.logics_map,
            example_args = self.example_args,
            output_formats = sorted(set(Notation.get_common_formats()).intersection(writers.registry)),
            logic_categories = logics.registry.grouped(),
            lw_html_ref = LexWriter(notation=Notation.standard, format='html'),
            toJson = self.tojson))
        self.on(Wevent.before_dispatch, self.before_dispatch)

    def start(self):
        """Start the web server."""
        cherrypy.config.update({
            'global': {
                'server.max_request_body_size': 1024 * 1000,
                'server.socket_host'   : self.config['host'],
                'server.socket_port'   : self.config['port'],
                'engine.autoreload.on' : self.config['is_debug']}})
        if self.config['feedback_enabled']:
            self.mailroom.start()
        if self.config['metrics_enabled']:
            self._start_metrics_server()
        cherrypy.quickstart(self, '/', self.cp_config)

    def before_dispatch(self, path):
        if self.config['metrics_enabled']:
            self.metrics.app_requests_count(path).inc()

    def get_template(self, name: str) -> jinja2.Template:
        cache = self.template_cache
        if '.' not in name:
            name = f'{name}.jinja2'
        if self.is_debug or name not in cache:
            cache[name] = self.jinja.get_template(name)
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
                    LexWriter(notation=notn, format='text', dialect='ascii')
                    for notn in Notation)})
            for arg in examples.args.values()})

    def _create_static_res(self):
        app_json = self.tojson(self.jsapp_data)
        return MapProxy({
            resource.path: resource
            for resource in (
                StaticResource('js/appdata.json', app_json),
                StaticResource('js/appdata.js', f';window.AppData={app_json};'))})
    
    def _build_jsapp_data(self):
        stdtbl = ParseTable.fetch(Notation.standard)
        stdlw = LexWriter(notation=Notation.standard, format='text', dialect='unicode')
        return MapProxy(dict(
            example_args = self.example_args,
            display_trans = MapProxy({
                'standard': MapProxy({
                    stdtbl.reversed[oper]: stdlw(oper)
                        for oper in Operator} | {
                    stdtbl.reversed[quant]: stdlw(quant)
                        for quant in Quantifier})}),
            parse_trans = MapProxy({
                'standard': MapProxy({
                    stdlw(oper): stdtbl.reversed[oper]
                        for oper in Operator} | {
                    stdlw(quant): stdtbl.reversed[quant]
                        for quant in Quantifier})})))

    def _build_cp_config(self):
        cp_config = {
            '/': {
                'tools.gzip.on': True,
                'tools.gzip.mime_types': {
                    'text/html',
                    'text/plain',
                    'text/css',
                    'application/javascript',
                    'application/xml'}}}
        cp_config['/']['request.dispatch'] = self.dispatcher
        cp_config.update({
            '/static': cp_staticdir_conf(self.config['static_dir'], index=None),
            '/favicon.ico': {
                'tools.staticfile.on': True,
                'tools.staticfile.filename': f"{self.config['static_dir']}/favicon.ico"},
            '/robots.txt': {
                'tools.staticfile.on': True,
                'tools.staticfile.filename': f"{self.config['static_dir']}/robots.txt"}})
        if self.config['doc_dir']:
            cp_config['/doc'] = cp_staticdir_conf(self.config['doc_dir'])
        if self.config['test_dir']:
            cp_config['/test'] = {
                'tools.redirect.on': True,
                'tools.redirect.url': '/test/coverage/index.html',
                'tools.redirect.internal': False}
            cp_config['/test/coverage'] = {
                **cp_staticdir_conf(self.config['test_dir'], index=None),
                'tools.redirect.on': False}
        return cp_config
    
    def _start_metrics_server(self):
        metrics_host = self.config['metrics_host']
        metrics_port = self.config['metrics_port']
        self.logger.info(f'Starting metrics on port {metrics_host}:{metrics_port}')
        from prometheus_client import start_http_server
        start_http_server(metrics_port, metrics_host, self.metrics.registry)


class Helper:
    def __init__(self, app: App):
        self.app = app
    def logic_doc_href(self, logic):
        return f'/doc/logics/{logics.registry(logic).Meta.name.lower()}.html'
