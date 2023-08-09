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
pytableaux.web.views
^^^^^^^^^^^^^^^^^^^^

"""
from __future__ import annotations

import logging
from collections import deque
from datetime import datetime
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from types import MappingProxyType as MapProxy
from typing import TYPE_CHECKING, Any, Mapping

import cherrypy
import cherrypy._cpdispatch
import simplejson as json
from cherrypy import HTTPError, NotFound
from cherrypy._cprequest import Request, Response

from .. import logics, package
from ..errors import ProofTimeoutError
from ..lang import Argument, Notation, Predicates, TriCoords
from ..proof import Tableau, writers
from ..tools import EMPTY_MAP, PathedDict, dmerged
from ..tools.timing import StopWatch
from .mail import is_valid_email
from .util import errstr, fix_uri_req_data, tojson

if TYPE_CHECKING:
    from .application import WebApp

EMPTY = ()
NOARG = object()

class View:

    exposed = True
    minargs = 0
    maxargs = 0

    @property
    def request(self) -> Request:
        return cherrypy.request

    @property
    def response(self) -> Response:
        return cherrypy.response

    @property
    def status(self) -> int:
        return self.response.status
    
    @status.setter
    def status(self, status: int) -> None:
        self.response.status = status

    @property
    def app(self) -> WebApp:
        return self.request.app.root

    @property
    def config(self) -> dict:
        return self.app.config

    @property
    def is_debug(self) -> bool:
        return self.app.is_debug

    @property
    def logger(self) -> logging.Logger:
        return self.app.logger
    
    def __call__(self, *args, **kw):
        self.args = args
        self.errors = {}
        handler = self.get_handler(*self.args)
        self.kw = fix_uri_req_data(kw)
        if not callable(handler):
            raise NotFound()
        self.setup()
        return handler(*args)

    def get_handler(self, *args):
        if not (self.minargs <= len(args) <= self.maxargs):
            raise NotFound()
        handler = getattr(self, self.request.method, None)
        if not callable(handler):
            raise HTTPError(405)
        return handler

    def setup(self):
        pass
        # self.errors = {}


@cherrypy.tools.json_in()
class JsonView(View):

    Payload = PathedDict
    payload_defaults: Mapping[str, Any] = EMPTY_MAP
    indent = None

    def __call__(self, *args, **kw):
        self.response.headers['Content-Type'] = 'application/json'
        try:
            reply = self.get_reply(*args, **kw)
        except HTTPError as err:
            self.status = err.status
            reply = dict(message=err.reason, status=self.status)
        return self.encode(reply)

    get_reply = View.__call__

    def tojson(self, *args, **kw) -> str:
        if kw.get('indent', NOARG) is NOARG:
            kw['indent'] = self.indent
        return self.app.tojson(*args, **kw)

    def encode(self, *args, **kw) -> bytes:
        return self.tojson(*args, **kw).encode()

    def setup(self, payload=NOARG):
        super().setup()
        if payload is NOARG:
            payload = getattr(self.request, 'json', None)
        if payload is None:
            payload = EMPTY_MAP
        self.payload = self.Payload(dmerged(self.payload_defaults, payload))

class HealthView(JsonView):

    def GET(self):
        return dict(status=self.status)

class ApiView(JsonView):

    def get_reply(self, *args, **kw) -> dict:
        reply = {}
        try:
            try:
                result = super().get_reply(*args, **kw)
                if result is None:
                    raise HTTPError(400)
                reply['message'] = 'OK'
                reply['result'] = result
            except ProofTimeoutError as err:
                self.status = 408
                raise
            except HTTPError as err:
                self.status = err.status
                reply['message'] = err.reason
                raise
            except Exception as err:
                self.status = 500
                raise
        except Exception as err:
            reply['error'] = type(err).__name__
            self.logger.error(err, exc_info=err)
            if 'message' not in reply:
                reply['message'] = str(err)
        if self.errors:
            reply['errors'] = self.errors
        reply['status'] = self.status
        return reply

    def parse_preds(self, key: str = 'predicates') -> Predicates|None:
        specs = self.payload[key]
        if not specs:
            return
        errors = self.errors
        preds = Predicates()
        for i, spec in enumerate(specs):
            try:
                preds.add(TriCoords.make(spec))
            except Exception as err:
                errors[f'{key}:{i}'] = err
        if preds and not errors:
            return preds

class ApiParseView(ApiView):

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
        errors = self.errors
        payload = self.payload
        try:
            notn = Notation[payload['notation']]
        except KeyError as err:
            errors['notation'] = f"Invalid notation: {err}"
        preds = self.parse_preds('predicates')
        if errors:
            return
        parser = notn.Parser(preds)
        try:
            sentence = parser(payload['input'])
        except Exception as err:
            errors['input'] = err
            return
        return dict(
            type = sentence.TYPE.name,
            rendered = {
                notn.name: {
                    charset: notn.DefaultWriter(charset)(sentence)
                    for charset in notn.charsets}
                for notn in Notation})

class ApiProveView(ApiView):

    payload_defaults: Mapping[str, Any] = MapProxy(dict(
        logic=None,
        argument=MapProxy(dict(
            notation=Notation.polish.name,
            premises=EMPTY,
            predicates=EMPTY)),
        build_models=False,
        max_steps=None,
        rank_optimizations=True,
        group_optimizations=True,
        writer_registry='default',
        output=MapProxy(dict(
            notation=Notation.polish.name,
            format='html',
            charset=None,
            options=EMPTY_MAP))))

    def setup(self, *args, **kw):
        super().setup(*args, **kw)
        self.payload['output:options:debug'] = self.is_debug
        self.logic = None
        self.argument = None
        self.tabopts = None
        self.tableau = None
        self.pw = None

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
        self.argument = self.get_argument()
        self.logic = self.get_logic()
        self.pw = self.get_pw()
        self.tabopts = self.get_tabopts()
        if self.errors:
            return
        self.tableau = self.build()
        return dict(
            tableau = dict(
                logic = self.logic.name,
                argument = dict(
                    premises   = tuple(map(self.pw.lw, self.argument.premises)),
                    conclusion = self.pw.lw(self.argument.conclusion)),
                valid  = self.tableau.valid,
                body   = self.pw(self.tableau),
                stats  = self.tableau.stats,
                result = self.tableau.stats['result']),
            attachments = self.pw.attachments(),
            writer = dict(
                format  = self.pw.format,
                charset = self.pw.lw.charset,
                options = self.pw.opts))

    def build(self):
        metrics = self.app.metrics
        logic = self.logic
        with StopWatch() as timer:
            metrics.proofs_inprogress_count(logic.name).inc()
            tab = Tableau(logic, self.argument, **self.tabopts)
            try:
                tab.build()
                metrics.proofs_completed_count(logic.name, tab.stats['result']).inc()
            finally:
                metrics.proofs_inprogress_count(logic.name).dec()
                metrics.proofs_execution_time(logic.name).observe(timer.elapsed_secs())
        return tab

    def get_logic(self):
        try:
            return logics.registry(self.payload['logic'])
        except Exception as err:
            self.errors['logic'] = err

    def get_tabopts(self):
        payload = self.payload
        if payload['max_steps'] is not None:
            try:
                payload['max_steps'] = int(payload['max_steps'])
            except ValueError as err:
                self.errors['max_steps'] = f"Invalid int value: {err}"
        return dict(
            is_rank_optim   = bool(payload['rank_optimizations']),
            is_group_optim  = bool(payload['group_optimizations']),
            is_build_models = bool(payload['build_models']),
            max_steps       = payload['max_steps'],
            build_timeout   = self.config['maxtimeout'])

    def get_argument(self):
        errors = self.errors
        payload = self.payload
        try:
            notn = Notation[payload['argument:notation']]
        except KeyError as err:
            errors['argument:notation'] = f"Invalid parser notation: {err}"
            return
        preds = self.parse_preds('argument:predicates')
        parser = notn.Parser(preds)
        premises = deque()
        for i, premise in enumerate(payload['argument:premises']):
            try:
                premises.append(parser(premise))
            except Exception as err:
                premises.append(None)
                errors[f'argument:premises:{i}'] = err
        try:
            conclusion = parser(payload['argument:conclusion'])
        except Exception as err:
            errors['argument:conclusion'] = err
        if errors:
            return
        return Argument(conclusion, premises)

    def get_pw(self):
        errors = self.errors
        payload = self.payload
        try:
            reg = writers.registries[payload['writer_registry']]
        except KeyError as err:
            errors['writer_registry'] = f'Invalid registry: {err}'
            return
        try:
            WriterClass = reg[payload['output:format']]
        except KeyError as err:
            errors['output:format'] = f"Invalid writer: {err}"
            return
        try:
            notn = Notation[payload['output:notation']]
        except KeyError as err:
            errors['output:notation'] = f"Invalid notation: {err}"
            return
        try:
            charset = payload['output:charset'] or WriterClass.default_charsets[notn]
            lw = notn.DefaultWriter(charset)
        except (KeyError, ValueError) as err:
            errors['output:charset'] = f"Unsupported charset: {err}"
            return
        return WriterClass(lw = lw, **payload['output:options'])

class TemplateView(View):

    template: str = ''

    def setup(self):
        super().setup()
        self.warns  = {}
        self.debugs = []
        self.context = dict(
            debugs = self.debugs,
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
        self.context['errors'] = {key: errstr(value) for key, value in self.errors.items()}
        pass

    def GET(self):
        pass

class FormView(TemplateView):

    form_defaults: Mapping[str, Any] = EMPTY_MAP

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
    
    def validate_form(self, form):
        return self.errors or True

class ProveView(FormView):

    form_defaults: Mapping[str, Any] = MapProxy(dict(
        input_notation = Notation.standard.name,
        output_format = 'html',
        output_notation = Notation.standard.name,
        output_charset = 'html',
        show_controls = True,
        build_models = True,
        color_open = True,
        writer_registry = 'default',
        rank_optimizations = True,
        group_optimizations = True))

    @property
    def api(self) -> ApiProveView:
        return self.app.api.prove

    @property
    def errors(self) -> dict:
        return self.api.errors

    @errors.setter
    def errors(self, errors: dict):
        self.api.errors = errors

    @property
    def tableau(self):
        return self.api.tableau

    @property
    def is_proof(self) -> bool:
        return not self.errors and bool(self.resp_data)

    @property
    def pw(self):
        return self.api.pw

    def setup(self):
        super().setup()
        self.template = f'v2/main'
        self.resp_data = None
        self.is_controls = False
        self.is_models = False
        self.is_color = False
        self.selected_tab = 'input'
        self.api_payload = None

    def validate_form(self, form_data):
        try:
            self.api_payload = json.loads(form_data['api-json'])
        except Exception as err:
            return {'api-json': err}
        return True

    def GET(self):
        self.api.setup(None)
        return super().GET()

    def POST(self):
        if not self.validate():
            return
        self.api.setup(self.api_payload)
        try:
            self.resp_data = self.api.POST()
        except Exception as err:
            self.errors['tableau'] = err
        if not self.is_proof:
            return
        if self.pw.format == 'html':
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
                resp_data = self.trim_resp_debug(self.resp_data),
                page_data = page_data).items())
        self.context.update(page_data,
            tableau = self.tableau,
            lw = self.pw and self.pw.lw,
            page_json = self.app.tojson(page_data),
            form_data = self.form_data,
            resp_data = self.resp_data)

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

class FeedbackView(FormView):

    @property
    def exposed(self) -> bool:
        return self.config['feedback_enabled'] and self.mailroom.enabled

    @property
    def mailroom(self):
        return self.app.mailroom

    def setup(self):
        super().setup()
        self.template = 'feedback'
        self.is_submitted = False

    def GET(self):
        if not self.mailroom.last_was_success:
            self.warns['mailroom'] = (
                'The most recent email was unsuccessful. '
                'You might want to send an email instead.')

    def validate_form(self, form):
        "Validate `name`, `email`, and `message` keys."
        errs = {}
        if not is_valid_email(form['email']):
            errs['email'] = 'Invalid email address'
        if not form['name']:
            errs['name'] = 'Please enter your name'
        if not form['message']:
            errs['message'] = 'Please enter a message'
        return errs or True
    
    def POST(self):
        if not self.validate():
            return
        date = datetime.now()
        context = dict(
            date = str(date),
            ip = self.request.remote.ip,
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
       


