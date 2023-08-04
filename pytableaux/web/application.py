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

__all__ = ('WebApp',)

import logging
from datetime import datetime
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from types import MappingProxyType as MapProxy
from typing import Any, ClassVar, Mapping

import cherrypy
import cherrypy._cpdispatch
import jinja2
import prometheus_client as prom
import simplejson as json
from cherrypy import HTTPError, NotFound, expose
from cherrypy._cprequest import Request, Response

from pytableaux import examples, logics, package, proof, web
from pytableaux.errors import ProofTimeoutError, RequestDataError
from pytableaux.lang import (Argument, LexType, LexWriter, Notation, Operator,
                             ParseTable, Predicate, Predicates, Quantifier,
                             TriCoords)
from pytableaux.logics import LogicType
from pytableaux.proof import Tableau, writers
from pytableaux.tools import EMPTY_MAP, dmerged
from pytableaux.tools.events import EventEmitter
from pytableaux.tools.timing import StopWatch
from pytableaux.web import StaticResource, Wevent, tojson
from pytableaux.web.mail import Mailroom, is_valid_email
from pytableaux.web.metrics import AppMetrics
from pytableaux.web.util import fix_uri_req_data

EMPTY = ()
NOARG = object()

class WebApp(EventEmitter):

    config: dict[str, Any]
    "Config."

    static_res: dict[str, StaticResource]
    "In-memory static resources."

    metrics: AppMetrics
    "Prometheus metrics helper."

    logger: logging.Logger
    "Logger instance."

    template_cache: dict[str, jinja2.Template]
    "Instance jinja2 template cache."

    jenv: jinja2.Environment
    "Instance jinja2 template environment."

    default_context: Mapping[str, Any]
    "Default template context."

    allowed_methods = frozenset(('GET', 'POST', 'HEAD'))
    example_args: Mapping[str, Mapping[str, Mapping[str, Any]]]
    logics_map: Mapping[str, LogicType]
    api_defaults: Mapping[str, Any] = MapProxy(dict(
        input_notation = Notation.polish.name,
        output_notation = Notation.polish.name,
        output_format = 'html'))
    jsapp_data: ClassVar[Mapping]
    lexwriters: Mapping[Notation, Mapping[str, LexWriter]]

    @property
    def json_indent(self) -> int|None:
        return 2 if self.config['is_debug'] else None

    def __init__(self, *args, **kw):
        super().__init__(*Wevent)
        self.config = web.EnvConfig.env_config()
        self.config.update(*args, **kw)
        self.logger = web.get_logger(self, self.config)
        # self.metrics = AppMetrics(config, prom.REGISTRY)
        self.metrics = AppMetrics(self.config, prom.CollectorRegistry())
        self.template_cache = {}
        self.jenv = jinja2.Environment(
            loader = jinja2.FileSystemLoader(self.config['templates_path']))
        self.example_args = {
            arg.title: {
                notn.name: dict(
                    premises = tuple(map(lw, arg.premises)),
                    conclusion = lw(arg.conclusion))
                for notn, lw in (
                    (notn, LexWriter(notn, charset='ascii'))
                    for notn in Notation)} | {
                '@Predicates': (
                    arg.predicates(sort=True) - Predicate.System).specs()}
                        for arg in examples.arguments()}
        self.logics_map = {key: logics.registry(key) for key in logics.__all__}
        self.jsapp_data = dict(
            example_args = self.example_args,
            example_preds = examples.preds.specs(),
            nups = {
                notn.name: ParseTable.fetch(notn).chars[LexType.Predicate]
                for notn in Notation})
        app_json = tojson(self.jsapp_data, indent = self.json_indent)
        self.static_res = {
            resource.path: resource
            for resource in (
                StaticResource('js/appdata.json', app_json),
                StaticResource('js/appdata.js', f';window.AppData={app_json};'))}
        self.lexwriters = {
            notn: {
                charset: LexWriter(notn, charset)
                for charset in notn.charsets}
            for notn in Notation}
        self.default_context = MapProxy(dict(
            config = self.config,
            is_debug = self.config['is_debug'],
            package = package,
            LexType = LexType,
            Notation = Notation,
            Operator = Operator,
            Quantifier = Quantifier,
            Predicate = Predicate,
            ParseTable = ParseTable,
            toJson = tojson,
            logics = self.logics_map,
            example_args = self.example_args,
            output_formats = writers.registry.keys(),
            output_charsets = Notation.get_common_charsets(),
            logic_categories = logics.registry.grouped(self.logics_map),
            lwh = self.lexwriters[Notation.standard]['html']))
        self.mailroom = Mailroom(self.config)
        self.dispatcher = AppDispatcher()
        self.init_events()
        self._api = Api()

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

    def init_events(self):
        EventEmitter.__init__(self, *Wevent)
        self.on(Wevent.before_dispatch,
            lambda path: self.metrics.app_requests_count(path).inc())

    def start(self):
        """Start the web server."""
        config = self.config
        logger = self.logger
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
            logger.info(f'Starting metrics on port {metrics_host}:{metrics_port}')
            prom.start_http_server(metrics_port, metrics_host, self.metrics.registry)
        cherrypy.quickstart(self, '/', self._routes())

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

    @expose
    def index(self, **kw):
        return ProveView()(**kw)

    @expose
    def feedback(self, **kw):
        if not self.config['feedback_enabled'] or not self.mailroom.enabled:
            raise NotFound()
        return FeedbackView()(**kw)

    @expose
    @cherrypy.tools.json_out()
    def health(self):
        return dict(status=200)

    @expose
    @cherrypy.tools.json_in()
    @cherrypy.tools.json_out()
    def api(self, action = None):
        req: Request = cherrypy.request
        res: Response = cherrypy.response
        if action not in ('parse', 'prove'):
            res.status = 404
            return dict(message = 'Not found', status = 404)
        if req.method != 'POST':
            res.status = 405
            return dict(message = 'Method not allowed', status = 405)
        result = None
        try:
            if action == 'parse':
                result = self._api.parse()
            elif action == 'prove':
                result = self._api.prove()
        except ProofTimeoutError as err: # pragma: no cover
            res.status = 408
            return dict(
                status  = 408,
                message = errstr(err),
                error   = type(err).__name__)
        except RequestDataError as err:
            res.status = 400
            return dict(
                status  = 400,
                message = 'Request data errors',
                error   = type(err).__name__,
                errors  = err.errors)
        except Exception as err: # pragma: no cover
            res.status = 500
            return dict(
                status  = 500,
                message = errstr(err),
                error   = type(err).__name__)
            #traceback.print_exc()
        return dict(
            status  = 200,
            message = 'OK',
            result  = result)

    @classmethod
    def _parse_argument(cls, adata: Mapping):
        errors = {}
        elabel = 'Notation'
        try:
            notn = Notation[
                adata.get('notation') or
                cls.api_defaults['input_notation']
            ]
        except KeyError as err:
            errors[elabel] = f"Invalid parser notation: {err}"
        else:
            try:
                preds = cls._parse_preds(adata.get('predicates', EMPTY))
            except RequestDataError as err:
                errors.update(err.errors)
                preds = None
            parser = notn.Parser(preds)
            premises = []
            for i, premise in enumerate(adata.get('premises', EMPTY), start = 1):
                elabel = f'Premise {i}'
                try:
                    premises.append(parser(premise))
                except Exception as e:
                    premises.append(None)
                    errors[elabel] = errstr(e)
            elabel = 'Conclusion'
            try:
                conclusion = parser(adata['conclusion'])
            except Exception as e:
                errors[elabel] = errstr(e)
        if errors:
            raise RequestDataError(errors)
        return Argument(conclusion, premises)

    def get_template(self, name):
        cache = self.template_cache
        if '.' not in name:
            name = f'{name}.jinja2'
        if self.config['is_debug'] or name not in cache:
            cache[name] = self.jenv.get_template(name)
        return cache[name]

    def render(self, template, *args, **kw):
        context = dict(self.default_context)
        context.update(*args, **kw)
        return self.get_template(template).render(context)

    @staticmethod
    def get_remote_ip(req: Request):
        return req.headers.get('X-Forwarded-For', req.remote.ip)

    @staticmethod
    def _parse_preds(pspecs):
        if not pspecs:
            return None
        errors = {}
        preds = Predicates()
        for i, specdata in enumerate(pspecs, start = 1):
            elabel = f'Predicate {i}'
            keys = TriCoords._fields
            try:
                if not isinstance(specdata, Mapping):
                    keys = range(len(keys))
                spec = TriCoords(*map(specdata.__getitem__, keys))
                preds.add(spec)
            except Exception as e:
                errors[elabel] = errstr(e)
        if errors:
            raise RequestDataError(errors)
        return preds

    @staticmethod
    def trim_resp_debug(resp_data: dict) -> dict:
        "Trim data for debug logging."
        if not resp_data:
            return resp_data
        result = dict(resp_data)
        if 'tableau' in result and 'body' in result['tableau']:
            if len(result['tableau']['body']) > 255:
                result['tableau'] = dict(result['tableau'])
                result['tableau']['body'] = '{0}...'.format(
                    result['tableau']['body'][0:255])
        return result

class ApiProveResponse(dict):

    def __init__(self, tab: Tableau, lw: LexWriter, /, *args, **kw):
        super().__init__(*args, **kw)
        self._tab = tab
        self._lw = lw

class AppDispatcher(cherrypy._cpdispatch.Dispatcher):

# class AppDispatcher(cherrypy._cpdispatch.RoutesDispatcher):

    def __call__(self, path_info: str):
        req: Request = cherrypy.request
        req.remote.ip = req.headers.get('X-Forwarded-For', req.remote.ip)
        self.before_dispatch(path_info)
        try:
            return super().__call__(path_info.split('?')[0])
        finally:
            self.after_dispatch(path_info)

    def webapp(self) -> WebApp:
        "Get the WebApp instance from cherrypy env."
        return cherrypy.serving.request.app.root

    def before_dispatch(self, *args):
        "Forward event to webapp"
        self.webapp().emit(Wevent.before_dispatch, *args)

    def after_dispatch(self, *args):
        "Forward event to webapp"
        self.webapp().emit(Wevent.after_dispatch, *args)

def errstr(err: Exception) -> str:
    return f'{type(err).__name__}: {err}'


class AppHandler:

    @property
    def config(self):
        return self.app.config

    @property
    def is_debug(self) -> bool:
        return self.config['is_debug']

    @property
    def request(self) -> Request:
        return cherrypy.request

    @property
    def response(self) -> Response:
        return cherrypy.response

    @property
    def app(self) -> WebApp:
        return self.request.app.root

    def __call__(self, *args, **kw):
        handler = self.get_handler(*args, **kw)
        if not callable(handler):
            raise NotFound()
        return handler(*args, **kw)

    def get_handler(self, *args, **kw):
        ...

class Api(AppHandler):

    def parse(self):
        return ApiParseView()()

    def prove(self):
        return ApiProveView()()

class View(AppHandler):

    def __call__(self, *args, **kw):
        handler = self.get_handler()
        if not callable(handler):
            raise NotFound()
        self.args = args
        self.kw = fix_uri_req_data(kw)
        self.setup()
        return handler(*args)

    def get_handler(self):
        handler = getattr(self, self.request.method, None)
        if not callable(handler):
            raise HTTPError(405)
        return handler

    def setup(self):
        pass

class JsonView(View):

    payload_defaults: Mapping[str, Any] = MapProxy({})

    def setup(self, payload=NOARG):
        super().setup()
        if payload is NOARG:
            payload = self.request.json
        if payload is None:
            payload = EMPTY_MAP
        self.payload = dmerged(self.payload_defaults, payload)

class ApiParseView(JsonView):

    payload_defaults: Mapping[str, Any] = MapProxy(dict(
        notation = Notation.polish.name,
        predicates = EMPTY,
        input = ''))

    def POST(self):
        """
        Request example::

            {
               notation: "polish",
               input: "Fm",
               predicates : [ [0, 0, 1] ]
            }

        Response Example::

            {
              type: "Predicated",
              rendered: {
                standard: {
                  ascii: "Fa", unicode: "Fa", html: "Fa"
                },
                polish: {
                  ascii: "Fm", unicode": "Fm", html: "Fm"
                }
              }
            }
        """
        errors = {}
        payload = self.payload
        # defaults
        try:
            preds = self.app._parse_preds(payload['predicates'])
        except RequestDataError as err:
            errors.update(err.errors)
            preds = None
        elabel = 'Notation'
        try:
            notn = Notation[payload['notation']]
        except KeyError as err:
            errors[elabel] = f"Invalid notation: {err}"
        if not errors:
            parser = notn.Parser(preds)
            elabel = 'Input'
            try:
                sentence = parser(payload['input'])
            except Exception as err:
                errors[elabel] = errstr(err)
        if errors:
            raise RequestDataError(errors)
        return dict(
            type = sentence.TYPE.name,
            rendered = {
                notn.name: {
                    charset: lw(sentence)
                    for charset, lw in lwmap.items()}
                for notn, lwmap in self.app.lexwriters.items()})

class ApiProveView(JsonView):

    payload_defaults: Mapping[str, Any] = MapProxy(dict(
        logic        = None,
        argument     = EMPTY_MAP,
        build_models = False,
        max_steps    = None,
        rank_optimizations  = True,
        group_optimizations = True,
        output = dict(
            notation = Notation.polish.name,
            format   = 'html',
            charset  = None,
            options  = {})))

    def setup(self, *args, **kw):
        super().setup(*args, **kw)
        self.payload['output']['options']['debug'] = self.config['is_debug']

    def POST(self):
        """
        Example request body::

            {
                "logic": "FDE",
                "argument": {
                    "conclusion": "Fm",
                    "premises": ["KFmFn"],
                    "notation": "polish",
                    "predicates": [ [0, 0, 1] ]
                },
                "output": {
                    "format": "html",
                    "notation": "standard",
                    "charset": "html",
                    "options": {}
                },
                "build_models": false,
                "max_steps": null,
                "rank_optimizations": true,
                "group_optimizations": true
            }

        Example success result::

            {
                "tableau": {
                    "logic": "FDE",
                    "argument": {
                        "premises": ["Fa &and; Fb"],
                        "conclusion": "Fb"
                    },
                    "valid": true,
                    "body": "...html...",
                    "header": "...",
                    "footer": "...",
                    "max_steps" : null
                },
                "writer": {
                    "format": "html,
                    "charset": "html",
                    "options": {}
                },
            }
        """
        config = self.config
        errors = {}
        payload = self.payload
        if payload['max_steps'] is not None:
            elabel = 'Max steps'
            try:
                payload['max_steps'] = int(payload['max_steps'])
            except ValueError as err:
                errors[elabel] = f"Invalid int value: {err}"
        tableau_opts = dict(
            is_rank_optim   = bool(payload['rank_optimizations']),
            is_group_optim  = bool(payload['group_optimizations']),
            is_build_models = bool(payload['build_models']),
            max_steps       = payload['max_steps'],
            build_timeout   = config['maxtimeout'])
        try:
            arg = self.app._parse_argument(payload['argument'])
        except RequestDataError as err:
            errors.update(err.errors)
        elabel = 'Logic'
        try:
            logic = logics.registry(payload['logic'])
        except Exception as err:
            errors[elabel] = errstr(err)
        elabel = 'Output Format'
        try:
            WriterClass = writers.registry[payload['output']['format']]
        except KeyError as err:
            errors[elabel] = f"Invalid writer: {err}"
        else:
            elabel = 'Output Notation'
            try:
                onotn = Notation[payload['output']['notation']]
            except KeyError as err:
                errors[elabel] = f"Invalid notation: {err}"
            else:
                elabel = 'Output Charset'
                try:
                    lwkey = payload['output']['charset'] or WriterClass.default_charsets[onotn]
                    lw = self.app.lexwriters[onotn][lwkey]
                except KeyError as err:
                    errors[elabel] = f"Unsupported charset: {err}"
                else:
                    pw = WriterClass(lw = lw, **payload['output']['options'])
        if errors:
            raise RequestDataError(errors)
        metrics = self.app.metrics
        with StopWatch() as timer:
            metrics.proofs_inprogress_count(logic.name).inc()
            tab = Tableau(logic, arg, **tableau_opts)
            try:
                tab.build()
                metrics.proofs_completed_count(logic.name, tab.stats['result']).inc()
            finally:
                metrics.proofs_inprogress_count(logic.name).dec()
                metrics.proofs_execution_time(logic.name).observe(timer.elapsed_secs())
        return ApiProveResponse(tab, lw,
            tableau = dict(
                logic = logic.name,
                argument = dict(
                    premises   = tuple(map(lw, arg.premises)),
                    conclusion = lw(arg.conclusion)),
                valid  = tab.valid,
                body   = pw(tab),
                stats  = tab.stats,
                result = tab.stats['result']),
            attachments = pw.attachments(),
            writer = dict(
                format  = pw.format,
                charset = lw.charset,
                options = pw.opts))

class TemplateView(View):

    template: str = ''

    def setup(self):
        super().setup()
        self.errors = {}
        self.warns  = {}
        self.debugs = []
        self.context = dict(
            debugs = self.debugs,
            errors = self.errors,
            warns = self.warns)

    def __call__(self, *args, **kw):
        content = super().__call__(*args, **kw)
        if content is None:
            content = self.render()
        return content

    def render(self):
        self.finish_context()
        return self.app.render(self.template, self.context)

    def finish_context(self):
        pass

    def GET(self):
        pass

class FormView(TemplateView):

    form_defaults: Mapping[str, Any] = MapProxy({})

    def setup(self):
        super().setup()
        self.form_data = dict(self.form_defaults)
        self.form_data.update(self.kw)

    def validate(self):
        errs = self.validate_form(self.form_data)
        if errs is True:
            return True
        self.errors.update(errs)
        return False
    
    def validate_form(self):
        return True

class ProveView(FormView):

    form_defaults: Mapping[str, Any] = MapProxy(dict(
        input_notation = Notation.standard.name,
        output_format = 'html',
        output_notation = Notation.standard.name,
        output_charset = 'html',
        show_controls = True,
        build_models = True,
        color_open = True,
        rank_optimizations = True,
        group_optimizations = True))

    def setup(self):
        super().setup()
        self.template = f'v2/main'
        self.resp_data = None
        self.tableau = None
        self.lw = None
        self.is_proof = False
        self.is_controls = False
        self.is_models = False
        self.is_color = False
        self.selected_tab = 'input'

    def POST(self):
        try:
            api_data = json.loads(self.kw['api-json'])
        except Exception as err:
            self.errors['api-json'] = errstr(err)
            return
        prove = ApiProveView()
        try:
            prove.setup(api_data)
            self.resp_data = prove.POST()
        except RequestDataError as err:
            self.errors.update(err.errors)
            return
        except ProofTimeoutError as err: # pragma: no cover
            self.errors['Tableau'] = errstr(err)
            return
        self.tableau = self.resp_data._tab
        self.lw = self.resp_data._lw
        self.is_proof = True
        if self.resp_data['writer']['format'] == 'html':
            self.is_controls = bool(self.kw.get('show_controls'))
            self.is_models = bool(
                self.kw.get('build_models') and
                self.tableau.invalid)
            self.is_color = bool(self.kw.get('color_open'))
            self.selected_tab = 'view'
        else:
            self.selected_tab = 'stats'

    def finish_context(self):
        super().finish_context()
        page_data = dict(
            is_proof     = self.is_proof,
            is_controls  = self.is_controls,
            is_models    = self.is_models,
            is_color     = self.is_color,
            selected_tab = self.selected_tab)
        if self.is_debug:
            self.debugs.extend(dict(
                req_data  = self.kw,
                form_data = self.form_data,
                resp_data = trim_resp_debug(self.resp_data),
                page_data = page_data).items())
        self.context.update(page_data,
            tableau = self.tableau,
            lw = self.lw,
            page_json = tojson(page_data, indent = self.app.json_indent),
            form_data = self.form_data,
            resp_data = self.resp_data)

class FeedbackView(FormView):

    @property
    def mailroom(self):
        return self.app.mailroom

    def setup(self):
        super().setup()
        self.template = 'feedback'
        self.is_submitted = False

    def GET(self):
        if not self.mailroom.last_was_success:
            self.warns['Mailroom'] = (
                'The most recent email was unsuccessful. '
                'You might want to send an email instead.')

    def validate_form(self, form):
        "Validate `name`, `email`, and `message` keys."
        errs = {}
        if not is_valid_email(form['email']):
            errs['Email'] = 'Invalid email address'
        if not form['name']:
            errs['Name'] = 'Please enter your name'
        if not form['message']:
            errs['Message'] = 'Please enter a message'
        return errs or True
    
    def POST(self):
        if not self.validate():
            return
        date = datetime.now()
        context = dict(
            date = str(date),
            ip = self.app.get_remote_ip(self.request),
            headers = self.request.headers,
            form_data = self.form_data)
        from_addr = self.config['feedback_from_address']
        from_name = self.form_data['name']
        to_addr = self.config['feedback_to_address']
        msg = MIMEMultipart('alternative')
        msg['To'] = to_addr
        msg['From'] = f"{package.name} Feedback <{from_addr}>"
        msg['Subject'] = f'Feedback from {from_name}'
        msg_txt = self.app.render('feedback-email.txt', context)
        msg_html = self.app.render('feedback-email', context)
        msg.attach(MIMEText(msg_txt, 'plain'))
        msg.attach(MIMEText(msg_html, 'html'))
        self.mailroom.enqueue(from_addr, (to_addr,), msg.as_string())
        self.is_submitted = True

    def finish_context(self):
        super().finish_context()
        page_data = dict(
            is_debug = self.is_debug,
            is_submitted = self.is_submitted)
        if self.is_debug:
            self.debugs.extend(dict(
                form_data = self.form_data).items())
        self.context.update(page_data,
            form_data = self.form_data,
            page_json = tojson(page_data, indent = self.app.json_indent))
       

def trim_resp_debug(resp_data: dict) -> dict:
    "Trim data for debug logging."
    if not resp_data:
        return resp_data
    result = dict(resp_data)
    if 'tableau' in result and 'body' in result['tableau']:
        if len(result['tableau']['body']) > 255:
            result['tableau'] = dict(result['tableau'])
            result['tableau']['body'] = '{0}...'.format(
                result['tableau']['body'][0:255])
    return result