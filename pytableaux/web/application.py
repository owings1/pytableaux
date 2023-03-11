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
import mimetypes
import os.path
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
from pytableaux.proof import Tableau, writers
from pytableaux.tools import EMPTY_MAP, qsetf
from pytableaux.tools.events import EventEmitter
from pytableaux.tools.timing import StopWatch
from pytableaux.web import Wevent, fix_uri_req_data, tojson
from pytableaux.web.mail import Mailroom, validate_feedback_form
from pytableaux.web.metrics import AppMetrics

EMPTY = ()

class WebApp(EventEmitter):

    config: dict[str, Any]
    "Instance config."

    static_res: dict[str, bytes]
    "Compiled in-memory static resources."

    metrics: AppMetrics
    "Prometheus metrics helper."

    routes: dict[str, dict[str, Any]]
    "Cherrypy routing config."

    logger: logging.Logger
    "Logger instance."

    template_cache: dict[str, jinja2.Template]
    "Instance jinja2 template cache."

    jenv: jinja2.Environment
    "Instance jinja2 template environment."

    base_view_data: Mapping[str, Any]
    "Instance base view data, merged with class defaults."

    api_defaults: ClassVar[Mapping]
    config_defaults: ClassVar[Mapping]
    form_defaults: ClassVar[Mapping]
    is_class_setup: ClassVar[bool] = False
    jsapp_data: ClassVar[Mapping]
    lw_cache: ClassVar[Mapping[Notation, Mapping[str, LexWriter]]]
    routes_defaults: ClassVar[Mapping[str, Mapping]]
    view_data_defaults: ClassVar[Mapping]
    view_version_default = 'v2'
    view_versions: ClassVar[qsetf[str]] = qsetf({'v2'})

    @classmethod
    def setup_class_data(cls):
        if cls.is_class_setup:
            return
        static_dir = f'{package.root}/web/static'
        doc_dir = os.path.abspath(f'{package.root}/../doc/_build/html')
        cls.routes_defaults = MapProxy({
            '/': {
                'request.dispatch': AppDispatcher()},
            '/static': {
                'tools.staticdir.on'  : True,
                'tools.staticdir.dir' : static_dir},
            '/doc': {
                'tools.staticdir.on'    : True,
                'tools.staticdir.dir'   : doc_dir,
                'tools.staticdir.index' : 'index.html'},
            '/favicon.ico': {
                'tools.staticfile.on'       : True,
                'tools.staticfile.filename' : f'{static_dir}/img/favicon-60x60.png'},
            '/robots.txt': {
                'tools.staticfile.on'       : True,
                'tools.staticfile.filename' : f'{static_dir}/robots.txt'}})
        cls.config_defaults = MapProxy(dict(web.EnvConfig.env_config(),
            copyright = package.copyright,
            issues_href = package.issues.url,
            source_href = package.repository.url,
            version = package.version.display,
            view_path = f'{package.root}/web/views',
            view_version = cls.view_version_default))
        cls.api_defaults = MapProxy(dict(
            input_notation = Notation.polish.name,
            output_notation = Notation.polish.name,
            output_format = 'html'))
        cls.form_defaults = MapProxy(dict(
            input_notation = Notation.standard.name,
            output_format = 'html',
            output_notation = Notation.standard.name,
            output_charset = 'html',
            show_controls = True,
            build_models = True,
            color_open = True,
            rank_optimizations = True,
            group_optimizations = True))
        cls.lw_cache = MapProxy({
            notn: MapProxy({
                charset: LexWriter(notn, charset)
                for charset in notn.charsets})
            for notn in Notation})
        # Rendered example arguments
        example_args = MapProxy({
            arg.title: MapProxy({
                notn.name: MapProxy(dict(
                    premises = tuple(map(lw, arg.premises)),
                    conclusion = lw(arg.conclusion)))
                    for notn, lw in (
                        (notn, LexWriter(notn, charset = 'ascii'))
                        for notn in Notation)} | {
                '@Predicates': (
                    arg.predicates(sort=True) - Predicate.System).specs()})
                        for arg in examples.arguments()})
        cls.jsapp_data = MapProxy(dict(
            example_args = example_args,
            example_preds = examples.preds.specs(),#tuple(p.spec for p in examples.preds),
            nups = MapProxy({
                notn.name: ParseTable.fetch(notn).chars[LexType.Predicate]
                for notn in Notation})))
        logics_map = {key: logics.registry(key) for key in logics.__all__}
        cls.view_data_defaults = MapProxy(dict(
            LexType = LexType,
            Notation = Notation,
            Operator = Operator,
            Quantifier = Quantifier,
            Predicate = Predicate,
            ParseTable = ParseTable,
            toJson = tojson,
            logics = logics_map,
            example_args = example_args,
            form_defaults = cls.form_defaults,
            view_versions = cls.view_versions,
            output_formats = writers.registry.keys(),
            output_charsets = Notation.get_common_charsets(),
            logic_categories = logics.registry.grouped(logics_map),
            lwh = cls.lw_cache[Notation.standard]['html']))
        cls.is_class_setup = True

    def __init__(self, opts = None, **kw):
        super().__init__(*Wevent)
        self.setup_class_data()
        self.config = dict(self.config_defaults)
        config = self.config
        if opts is not None:
            config.update(opts)
        config.update(kw)
        self.logger = web.get_logger(self, config)
        self.metrics = AppMetrics(config)
        self.routes = dict({
            key: dict(value)
            for key, value in self.routes_defaults.items()})
        self.template_cache = {}
        self.jenv = jinja2.Environment(
            loader = jinja2.FileSystemLoader(config['view_path']))
        app_json = tojson(self.jsapp_data, indent = 2 * config['is_debug'])
        self.static_res = {
            'js/appdata.json': app_json.encode('utf-8'),
            'js/appdata.js': f';window.AppData = {app_json};'.encode('utf-8')}
        self.base_view_data = dict(self.view_data_defaults)
        self.mailroom = Mailroom(config)
        self.init_events()

    def init_events(self):
        EventEmitter.__init__(self, *Wevent)
        m = self.metrics
        self.on(Wevent.before_dispatch,
            lambda path: m.app_requests_count(path).inc())
        self.on(Wevent.after_dispatch,
            lambda path: self.logger.info(self.get_remote_ip(cherrypy.request)))

    def start(self):
        """Start the web server."""
        config = self.config
        logger = self.logger
        metrics_port = config['metrics_port']
        self.mailroom.start()
        cherrypy.config.update({
            'global': {
                'server.socket_host'   : config['host'],
                'server.socket_port'   : config['port'],
                'engine.autoreload.on' : config['is_debug']}})
        logger.info(f'Starting metrics on port {metrics_port}')
        prom.start_http_server(metrics_port)
        cherrypy.quickstart(self, '/', self.routes)

    @expose
    def static(self, *respath, **req_data):
        req: Request = cherrypy.request
        res: Response = cherrypy.response
        resource = '/'.join(respath)
        try:
            content = self.static_res[resource]
        except KeyError:
            raise NotFound()
        if req.method != 'GET':
            raise HTTPError(405)
        res.headers['Content-Type'] = mimetypes.guess_type(resource)[0]
        return content

    @expose
    def index(self, **req_data):
        req: Request = cherrypy.request
        errors = {}
        warns  = {}
        debugs = []
        config = self.config
        view_data = dict(self.base_view_data)
        form_data = fix_uri_req_data(req_data)
        view_version = form_data.get('v')
        if view_version not in self.view_versions:
            view_version = config['view_version']
        view = f'{view_version}/main'
        if 'debug' in form_data and config['is_debug']:
            is_debug = form_data['debug'] not in ('', '0', 'false')
        else:
            is_debug = config['is_debug']
        api_data = resp_data = None
        is_proof = is_controls = is_models = is_color = False
        selected_tab = 'input'
        if req.method == 'POST':
            try:
                try:
                    api_data = json.loads(form_data['api-json'])
                except Exception as err:
                    raise RequestDataError({'api-data': errstr(err)})
                resp_data, tableau, lw = self.api_prove(api_data)
            except RequestDataError as err:
                errors.update(err.errors)
            except ProofTimeoutError as err: # pragma: no cover
                errors['Tableau'] = errstr(err)
            else:
                is_proof = True
                if resp_data['writer']['format'] == 'html':
                    is_controls = bool(form_data.get('show_controls'))
                    is_models = bool(
                        form_data.get('build_models') and
                        tableau.invalid)
                    is_color = bool(form_data.get('color_open'))
                    selected_tab = 'view'
                else:
                    selected_tab = 'stats'
                view_data.update(
                    tableau = tableau,
                    lw = lw)
        else:
            form_data = dict(self.form_defaults)
        if errors:
            view_data['errors'] = errors
        page_data = dict(
            is_debug     = is_debug,
            is_proof     = is_proof,
            is_controls  = is_controls,
            is_models    = is_models,
            is_color     = is_color,
            selected_tab = selected_tab)
        if is_debug:
            debugs.extend(dict(
                req_data  = req_data,
                form_data = form_data,
                api_data  = api_data,
                resp_data = self.trim_resp_debug(resp_data),
                page_data = page_data).items())
            view_data['debugs'] = debugs
        view_data.update(page_data,
            page_json = tojson(page_data, indent = 2 * is_debug),
            config       = self.config,
            view_version = view_version,
            form_data    = form_data,
            resp_data    = resp_data,
            warns        = warns)
        return self.render(view, view_data)

    @expose
    def feedback(self, **form_data):
        config = self.config
        if not (config['feedback_enabled'] and config['smtp_host']):
            raise NotFound()
        mailroom = self.mailroom
        req: Request = cherrypy.request
        errors = {}
        warns  = {}
        debugs = []
        view_version = form_data.get('v')
        if view_version not in self.view_versions:
            view_version = config['view_version']
        view = 'feedback'
        view_data = dict(self.base_view_data,
            form_data = form_data,
            view_version = view_version)
        is_submitted = False
        is_debug = config['is_debug']
        if req.method == 'POST':
            try:
                validate_feedback_form(form_data)
            except RequestDataError as err:
                errors.update(err.errors)
            else:
                date = datetime.now()
                view_data.update(
                    date = str(date),
                    ip = self.get_remote_ip(req),
                    headers = req.headers)
                from_addr = config['feedback_from_address']
                from_name = form_data['name']
                to_addr = config['feedback_to_address']
                app_name = config['app_name']
                msg = MIMEMultipart('alternative')
                msg['To'] = to_addr
                msg['From'] = f'{app_name} Feedback <{from_addr}>'
                msg['Subject'] = f'Feedback from {from_name}'
                msg_txt = self.render('feedback-email.txt', view_data)
                msg_html = self.render('feedback-email', view_data)
                msg.attach(MIMEText(msg_txt, 'plain'))
                msg.attach(MIMEText(msg_html, 'html'))
                mailroom.enqueue(from_addr, (to_addr,), msg.as_string())
                is_submitted = True
        else:
            if not mailroom.last_was_success:
                warns['Mailroom'] = (
                    'The most recent email was unsuccessful. '
                    'You might want to send an email instead.')
        page_data = dict(
            is_debug = is_debug,
            is_submitted = is_submitted)
        if is_debug:
            debugs.extend(dict(
                form_data = form_data).items())
            view_data['debugs'] = debugs
        view_data.update(page_data,
            page_json = tojson(page_data, indent = 2 * is_debug),
            config = config,
            errors = errors,
            warns = warns)
        return self.render(view, view_data)

    @expose
    @cherrypy.tools.json_in()
    @cherrypy.tools.json_out()
    def api(self, action = None):
        req: Request = cherrypy.request
        res: Response = cherrypy.response
        if req.method == 'POST':
            try:
                result = None
                if action == 'parse':
                    result = self.api_parse(req.json)
                elif action == 'prove':
                    result, *_ = self.api_prove(req.json)
                if result:
                    return dict(
                        status  = 200,
                        message = 'OK',
                        result  = result)
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
        res.status = 404
        return dict(message = 'Not found', status = 404)

    def api_parse(self, body: dict):
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
        # defaults
        body = dict(
            notation = self.api_defaults['input_notation'],
            predicates = EMPTY,
            input = '') | body
        try:
            preds = self._parse_preds(body['predicates'])
        except RequestDataError as err:
            errors.update(err.errors)
            preds = None
        elabel = 'Notation'
        try:
            notn = Notation[body['notation']]
        except KeyError as err:
            errors[elabel] = f"Invalid notation: {err}"
        if not errors:
            parser = notn.Parser(preds)
            elabel = 'Input'
            try:
                sentence = parser(body['input'])
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
                for notn, lwmap in self.lw_cache.items()})

    def api_prove(self, body: dict) -> tuple[dict, Tableau, LexWriter]:
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
        body = dict(
            logic        = None,
            argument     = EMPTY_MAP,
            build_models = False,
            max_steps    = None,
            rank_optimizations  = True,
            group_optimizations = True) | body
        odata = dict(
            notation = self.api_defaults['output_notation'],
            format   = self.api_defaults['output_format'],
            charset  = None,
            options  = {}) | body.get('output', EMPTY_MAP)
        odata['options']['debug'] = config['is_debug']
        if body['max_steps'] is not None:
            elabel = 'Max steps'
            try:
                body['max_steps'] = int(body['max_steps'])
            except ValueError as err:
                errors[elabel] = f"Invalid int value: {err}"
        tableau_opts = dict(
            is_rank_optim   = bool(body['rank_optimizations']),
            is_group_optim  = bool(body['group_optimizations']),
            is_build_models = bool(body['build_models']),
            max_steps       = body['max_steps'],
            build_timeout   = config['maxtimeout'])
        try:
            arg = self._parse_argument(body['argument'])
        except RequestDataError as err:
            errors.update(err.errors)
        elabel = 'Logic'
        try:
            logic = logics.registry(body['logic'])
        except Exception as err:
            errors[elabel] = errstr(err)
        elabel = 'Output Format'
        try:
            WriterClass = writers.registry[odata['format']]
        except KeyError as err:
            errors[elabel] = f"Invalid writer: {err}"
        else:
            elabel = 'Output Notation'
            try:
                onotn = Notation[odata['notation']]
            except KeyError as err:
                errors[elabel] = f"Invalid notation: {err}"
            else:
                elabel = 'Output Charset'
                try:
                    lwkey = odata['charset'] or WriterClass.default_charsets[onotn]
                    lw = self.lw_cache[onotn][lwkey]
                except KeyError as err:
                    errors[elabel] = f"Unsupported charset: {err}"
                else:
                    pw = WriterClass(lw = lw, **odata['options'])
        if errors:
            raise RequestDataError(errors)
        metrics = self.metrics
        with StopWatch() as timer:
            metrics.proofs_inprogress_count(logic.name).inc()
            tableau = proof.Tableau(logic, arg, **tableau_opts)
            try:
                tableau.build()
                metrics.proofs_completed_count(logic.name, tableau.stats['result']).inc()
            finally:
                metrics.proofs_inprogress_count(logic.name).dec()
                metrics.proofs_execution_time(logic.name).observe(timer.elapsed_secs())
        resp_data = dict(
            tableau = dict(
                logic = logic.name,
                argument = dict(
                    premises   = tuple(map(lw, arg.premises)),
                    conclusion = lw(arg.conclusion)),
                valid  = tableau.valid,
                body   = pw(tableau),
                stats  = tableau.stats,
                result = tableau.stats['result']),
            attachments = pw.attachments(),
            writer = dict(
                format  = pw.format,
                charset = lw.charset,
                options = pw.opts))
        # Return a tuple (resp, tableau, lw) because the web ui needs the
        # tableau object to write the controls.
        return resp_data, tableau, lw

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

    def get_template(self, view):
        cache = self.template_cache
        if '.' not in view:
            view = f'{view}.jinja2'
        if self.config['is_debug'] or (view not in cache):
            cache[view] = self.jenv.get_template(view)
        return cache[view]

    def render(self, view, *args, **kw):
        return self.get_template(view).render(*args, **kw)

    @staticmethod
    def get_remote_ip(req: Request):
        return req.headers.get('X-Forwarded-For', req.remote.ip)

    @staticmethod
    def _parse_preds(pspecs):
        if not pspecs:
            return None
        errors = {}
        preds = Predicates()
        fields = TriCoords._fields
        for i, specdata in enumerate(pspecs, start = 1):
            elabel = f'Predicate {i}'
            try:
                if isinstance(specdata, dict):
                    keys = fields
                else:
                    keys = range(len(fields))
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

class AppDispatcher(cherrypy._cpdispatch.Dispatcher):

    def __call__(self, path_info: str):
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
