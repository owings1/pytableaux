# pytableaux, a multi-logic proof generator.
# Copyright (C) 2014-2022 Doug Owings.
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
#
# ------------------
#
# pytableaux - Web Application
from __future__ import annotations

__all__ = ()

from errors import RequestDataError, TimeoutError, errstr
from tools.abcs import KT, VT
from tools.mappings import MapCover, MapProxy, dmap
from tools.misc import get_logic
from tools.timing import StopWatch

import examples, fixed
import lexicals
from lexicals import (
    Argument,
    LexType,
    LexWriter,
    Notation,
    Predicate,
    Predicates,
)
from parsers import create_parser
from proof.tableaux import Tableau
from proof.writers import TabWriter

from www.mailroom import Mailroom
from www.conf import (
    APP_ENVCONF,
    APP_JENV,

    api_defaults,
    app_modules,
    cp_config,
    cp_global_config,
    example_arguments,
    form_defaults,
    lexwriter_encodings,
    lexwriters,
    logger,
    logic_categories,
    Metric,
    parser_nups,
    parser_tables,
    re_email,
)

import cherrypy as chpy
from cherrypy._cprequest import Request, Response
from datetime import datetime
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from jinja2 import Template
import json
import prometheus_client as prom
import re
import traceback
from typing import Any, Mapping, Sequence


mailroom = Mailroom(APP_ENVCONF)

###############
## JS Data   ##
###############
base_browser_data = MapCover(dict(
    example_arguments     = example_arguments,
    example_predicates    = tuple(p.spec for p in examples.preds),
    nups                  = parser_nups,
    num_predicate_symbols = Predicate.TYPE.maxi + 1,
))

#################
## View Data   ##
#################
base_view_data = MapCover(dict(

    example_args_list   = examples.titles,
    form_defaults       = form_defaults,
    lexicals            = lexicals,
    LexType             = LexType,
    lexwriter_encodings = lexwriter_encodings,
    lwstdhtm            = lexwriters['standard']['html'],
    logic_categories    = logic_categories,
    logics              = app_modules['logics'],
    Notation            = Notation,
    parser_tables       = parser_tables,
    tabwriter_formats   = TabWriter.Registry.keys(),
    view_version        = 'v2',
))


###################
## Webapp        ##
###################

_EMPTY_MAP = MapProxy()
_TEMPLATE_CACHE: dict[str, Template] = {}

class App:

    config = dict(APP_ENVCONF,
        copyright   = fixed.copyright,
        issues_href = fixed.issues_href,
        source_href = fixed.source_href,
        version     = fixed.version,
    )

    @chpy.expose
    def index(self, **req_data):

        req: Request = chpy.request

        errors = {}
        warns  = {}
        debugs = []

        view_data = dict(base_view_data)
        browser_data = dict(base_browser_data)

        if req_data.get('v') in ('v1', 'v2'):
            view_version = req_data['v']
        else:
            view_version = 'v2'
        view = '/'.join((view_version, 'main'))

        if req_data.get('debug') == 'false':
            is_debug = False
        else:
            is_debug = self.config['is_debug']

        form_data = fix_form_data(req_data)
        api_data = resp_data = None
        is_proof = is_controls = is_models = False
        selected_tab = 'argument'

        if req.method == 'POST':
            
            try:
                try:
                    api_data = json.loads(form_data['api-json'])
                except Exception as err:
                    raise RequestDataError({'api-data': errstr(err)})
                try:
                    self._parse_argument(api_data['argument'])
                    # test:
                    # raise RequestDataError({'test': 'error'})
                except RequestDataError as err:
                    errors.update(err.errors)
                resp_data, tableau, lw = self.api_prove(api_data)
            except RequestDataError as err:
                errors.update(err.errors)
            except TimeoutError as err: # pragma: no cover
                errors['Tableau'] = errstr(err)

            if not errors:
                is_proof = True
                if resp_data['writer']['format'] == 'html':
                    is_controls = bool(form_data.get('show_controls'))
                    is_models = bool(
                        form_data.get('options.models') and
                        tableau.invalid
                    )
                    selected_tab = 'view'
                else:
                    selected_tab = 'stats'
                view_data.update(
                    tableau = tableau,
                    lw      = lw,
                )

        if errors:
            view_data['errors'] = errors

        browser_data.update(
            is_debug     = is_debug,
            is_proof     = is_proof,
            is_controls  = is_controls,
            is_models    = is_models,
            selected_tab = selected_tab,
        )

        if is_debug:
            debugs.extend(dict(
                api_data = api_data,
                req_data = req_data,
                form_data = form_data,
                resp_data = resp_data and debug_resp_data(resp_data),
                browser_data = browser_data,
            ).items())
            view_data['debugs'] = debugs

        view_data.update(
            browser_json = json.dumps(browser_data, indent = 2),
            config       = self.config,
            is_debug     = is_debug,
            is_proof     = is_proof,
            is_controls  = is_controls,
            is_models    = is_models,
            selected_tab = selected_tab,
            view_version = view_version,
            form_data    = form_data,
            resp_data    = resp_data,
            warns        = warns,
        )

        return self._render(view, view_data)

    def feedback(self, **form_data) -> str:

        req: Request = chpy.request

        errors = {}
        warns  = {}
        debugs = []

        view = 'feedback'
        view_data = dict(base_view_data,
            form_data = form_data
        )

        config = self.config
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
                    date    = str(date),
                    ip      = get_remote_ip(req),
                    headers = req.headers,
                )
                fromaddr = config['feedback_from_address']
                toaddr = config['feedback_to_address']
                msg = MIMEMultipart('alternative')
                msg['To'] = toaddr
                msg['From'] = '%s Feedback <%s>' % (config['app_name'], fromaddr)
                msg['Subject'] = 'Feedback from %s' % form_data['name']
                msg_txt = self._render('feedback-email.txt', view_data)
                msg_html = self._render('feedback-email', view_data)
                msg.attach(MIMEText(msg_txt, 'plain'))
                msg.attach(MIMEText(msg_html, 'html'))
                mailroom.enqueue(fromaddr, (toaddr,), msg.as_string())
                is_submitted = True

        else:
            if not mailroom.last_was_success:
                warns['Mailroom'] = (
                    'The most recent email was unsuccessful. '
                    'You might want to send an email instead.'
                )

        if is_debug:
            debugs.extend(dict(
                form_data = form_data,
            ).items())
            view_data['debugs'] = debugs

        view_data.update(
            config       = self.config,
            errors       = errors,
            warns        = warns,
            is_debug     = is_debug,
            is_submitted = is_submitted,
        )

        return self._render(view, view_data)

    feedback.exposed = APP_ENVCONF['feedback_enabled'] and bool(APP_ENVCONF['smtp_host'])

    @chpy.expose
    @chpy.tools.json_in()
    @chpy.tools.json_out()
    def api(self, action: str = None) -> dict[str, Any]:

        req: Request = chpy.request
        res: Response = chpy.response

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
                        result  = result,
                    )
            except TimeoutError as err: # pragma: no cover
                res.status = 408
                return dict(
                    status  = 408,
                    message = errstr(err),
                    error   = type(err).__name__,
                )
            except RequestDataError as err:
                res.status = 400
                return dict(
                    status  = 400,
                    message = 'Request data errors',
                    error   = type(err).__name__,
                    errors  = err.errors,
                )
            except Exception as err: # pragma: no cover
                res.status = 500
                return dict(
                    status  = 500,
                    message = errstr(err),
                    error   = type(err).__name__,
                )
                #traceback.print_exc()
        res.status = 404
        return dict(message = 'Not found', status = 404)

    def api_parse(self, body: Mapping) -> dict[str, Any]:
        """
        Example request body::

            {
               "notation": "polish",
               "input": "Fm",
               "predicates" : [
                  {
                     "name": "is F",
                     "index": 0,
                     "subscript": 0,
                     "arity": 1
                  }
               ]
            }

        Example success result::

            {
               "type": "Predicated",
               "rendered": {
                    "standard": {
                        "default": "Fa",
                        "html": "Fa"
                    },
                    "polish": {
                        "default": "Fm",
                        "html": "Fm"
                    }
                }
            }
        """
        errors = {}

        body = dict(body)

        # defaults
        if 'notation' not in body:
            body['notation'] = api_defaults['input_notation']
        if 'predicates' not in body:
            body['predicates'] = []
        if 'input' not in body:
            body['input'] = ''

        try:
            preds = self._parse_preds(body['predicates'])
        except RequestDataError as err:
            errors.update(err.errors)
            preds = None

        elabel = 'Notation'
        if body['notation'] not in Notation:
            errors[elabel] = "Invalid notation: '%s'" % body['notation']

        if not errors:
            parser = create_parser(body['notation'], preds)
            elabel = 'Input'
            try:
                sentence = parser(body['input'])
            except Exception as err:
                errors[elabel] = errstr(err)

        if errors:
            raise RequestDataError(errors)

        return dict(
            type     = sentence.TYPE.name,
            rendered = {
                notn: {
                    fmt: lexwriters[notn][fmt](sentence)
                    for fmt in lexwriters[notn]
                }
                for notn in lexwriters
            },
        )

    def api_prove(self, body: Mapping) -> tuple[dict, Tableau, LexWriter]:
        """
        Example request body::

            {
                "argument": {
                    "premises": ["KFmFn"],
                    "conclusion": "Fm",
                    "notation": "polish",
                    "predicates": [
                        {
                            "name": "is F",
                            "index": 0,
                            "subscript": 0,
                            "arity": 1
                        }
                    ]
                },
                "logic": "FDE",
                "output": {
                    "notation": "standard",
                    "format": "html",
                    "symbol_enc": "default",
                    "options": {
                        
                    }
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
                    "name": "HTML",
                    "format": "html,
                    "symbol_enc": "html",
                    "options": {}
                },
            }
        """
        is_debug = self.config['is_debug']
        errors = {}

        body = dmap(
            output       = {},
            argument     = _EMPTY_MAP,
            build_models = False,
            max_steps    = None,
            rank_optimizations  = True,
            group_optimizations = True,
        ) | body

        odata: dmap
        odata = body['output'] = dmap(
            options = {},
            notation = api_defaults['output_notation'],
            format   = api_defaults['output_format'],
        ) | body['output']

        if 'symbol_enc' not in odata:
            if odata['format'] == 'html':
                odata['symbol_enc'] = 'html'
            else:
                odata['symbol_enc'] = 'ascii'

        odata['options']['debug'] = is_debug

        if body['max_steps'] is not None:
            elabel = 'Max steps'
            try:
                body['max_steps'] = int(body['max_steps'])
            except Exception as err:
                errors[elabel] = errstr(err)
                body['max_steps'] = None

        proof_opts = dict(
            is_rank_optim   = bool(body['rank_optimizations']),
            is_group_optim  = bool(body['group_optimizations']),
            is_build_models = bool(body['build_models']),
            max_steps       = body['max_steps'],
            build_timeout   = self.config['maxtimeout'],
        )

        try:
            arg = self._parse_argument(body['argument'])
        except RequestDataError as err:
            errors.update(err.errors)

        elabel = 'Logic'
        try:
            logic = get_logic(body['logic'])
        except Exception as err:
            errors[elabel] = errstr(err)

        elabel = 'Output notation'
        try:
            lwmap = lexwriters[odata['notation']]
        except KeyError:
            errors[elabel] = "Invalid notation: '%s'" % odata['notation']
        except Exception as err:
            errors[elabel] = errstr(err)
            if is_debug:
                traceback.print_exc()

        else:
            elabel = 'Symbol encoding'
            try:
                lw = lwmap[odata['symbol_enc']]
            except KeyError:
                errors[elabel] = "Unsupported encoding: '%s'" % odata['symbol_enc']
            except Exception as err:
                if is_debug:
                    traceback.print_exc()
                errors[elabel] = errstr(err)

            else:
                elabel = 'Output format'
                try:
                    tabwriter = TabWriter(odata['format'],
                        lw  = lw,
                        enc = odata['symbol_enc'],
                        **odata['options'],
                    )
                except Exception as err:
                    errors[elabel] = errstr(err)
                    if is_debug:
                        traceback.print_exc()

        if errors:
            raise RequestDataError(errors)

        logicname: str = logic.name
        with StopWatch() as timer:
            Metric.proofs_inprogress_count(logicname).inc()
            proof = Tableau(logic, arg, **proof_opts)

            try:
                proof.build()
                Metric.proofs_completed_count(logicname, proof.stats['result'])
            finally:
                Metric.proofs_inprogress_count(logicname).dec()
                Metric.proofs_execution_time(logicname).observe(timer.elapsed_secs())

        # Return a tuple (resp, tableau, lw) because the web ui needs the
        # tableau object to write the controls.
        return (dict(
            tableau = dict(
                logic = logicname,
                argument = dict(
                    premises   = tuple(map(lw, arg.premises)),
                    conclusion = lw(arg.conclusion),
                ),
                valid  = proof.valid,
                header = tabwriter.document_header(),
                footer = tabwriter.document_footer(),
                body   = tabwriter.write(proof),
                stats  = proof.stats,
                result = proof.stats['result'],
            ),
            attachments = tabwriter.attachments(proof),
            writer = dict(
                name       = tabwriter.name,
                format     = odata['format'],
                symbol_enc = odata['symbol_enc'],
                options    = tabwriter.opts,
            )
        ), proof, lw)

    @classmethod
    def _parse_argument(cls, adata: Mapping[str, Any]) -> Argument:

        errors = {}
        adata = dict(adata)

        # defaults
        if 'notation' not in adata:
            adata['notation'] = api_defaults['input_notation']
        if 'predicates' not in adata:
            adata['predicates'] = []
        if 'premises' not in adata:
            adata['premises'] = []

        elabel = 'Notation'
        try:
            if adata['notation'] not in Notation:
                raise ValueError('Invalid parser notation')
        except Exception as e:
            errors[elabel] = str(e)

        if not errors:
            try:
                preds = cls._parse_preds(adata['predicates'])
            except RequestDataError as err:
                errors.update(err.errors)
                preds = None
            parser = create_parser(adata['notation'], preds)
            premises = []
            for i, premise in enumerate(adata['premises'], start = 1):
                elabel = 'Premise %d' % i
                try:
                    premises.append(parser.parse(premise))
                except Exception as e:
                    premises.append(None)
                    errors[elabel] = errstr(e)
            elabel = 'Conclusion'
            try:
                conclusion = parser.parse(adata['conclusion'])
            except Exception as e:
                errors[elabel] = errstr(e)

        if errors:
            raise RequestDataError(errors)

        return Argument(conclusion, premises)

    @staticmethod
    def _parse_preds(pspecs: Sequence[Mapping|Sequence]) -> Predicates|None:
        if not len(pspecs):
            return None
        errors = {}
        preds = Predicates()
        Coords = Predicate.Coords
        fields = Coords._fields
        for i, specdata in enumerate(pspecs, start = 1):
            elabel = 'Predicate %d' % i
            try:
                if isinstance(specdata, dict):
                    keys = fields
                else:
                    keys = range(len(fields))
                coords = Coords(*map(specdata.__getitem__, keys))
                preds.add(coords)
            except Exception as e:
                errors[elabel] = errstr(e)
        if errors:
            raise RequestDataError(errors)
        return preds

    def _get_template(self, view: str) -> Template:
        if '.' not in view:
            view = '.'.join((view, 'jinja2'))
        if self.config['is_debug'] or (view not in _TEMPLATE_CACHE):
            _TEMPLATE_CACHE[view] = APP_JENV.get_template(view)
        return _TEMPLATE_CACHE[view]

    def _render(self, view: str, data: dict = {}) -> str:
        return self._get_template(view).render(data)

#####################
## Miscellaneous   ##
#####################

def fix_form_data(form_data: dict[str, VT]) -> dict[str, VT]:
    form_data = dict(form_data)
    if len(form_data):
        for param in form_data:
            if param.endswith('[]'):
                if isinstance(form_data[param], str):
                    form_data[param] = [form_data[param]]
    return form_data

def debug_resp_data(resp_data: dict[KT, VT]) -> dict[KT, VT]:
    result = dict(resp_data)
    if 'tableau' in result and 'body' in result['tableau']:
        if len(result['tableau']['body']) > 255:
            result['tableau'] = dict(result['tableau'])
            result['tableau']['body'] = '{0}...'.format(
                result['tableau']['body'][0:255]
            )
    return result

def is_valid_email(value: str) -> bool:
    return re.fullmatch(re_email, value) is not None

def validate_feedback_form(form_data: dict[str, str]) -> None:
    errors = {}
    if not is_valid_email(form_data['email']):
        errors['Email'] = 'Invalid email address'
    if not len(form_data['name']):
        errors['Name'] = 'Please enter your name'
    if not len(form_data['message']):
        errors['Message'] = 'Please enter a message'
    if errors:
        raise RequestDataError(errors)

def get_remote_ip(req: Request) -> str:
    # TODO: use proxy forward header
    return req.remote.ip


#############
## Main    ##
#############

def main(): # pragma: no cover
    app = App()
    logger.info('Staring metrics on port %d' % APP_ENVCONF['metrics_port'])
    mailroom.start()
    prom.start_http_server(APP_ENVCONF['metrics_port'])
    chpy.config.update(cp_global_config)
    chpy.quickstart(app, '/', cp_config)

if  __name__ == '__main__': # pragma: no cover
    main()