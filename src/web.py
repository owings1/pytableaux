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
from parsers import ParseTable
from proof.tableaux import Tableau
from proof.writers import TabWriter

from www.mailroom import Mailroom
from www.conf import (
    APP_ENVCONF,
    APP_JENV,
    APP_LOGICS,
    REGEX_EMAIL,

    logger,
    Metric,
    cp_config,
    cp_global_config,

    example_args,
    output_charsets,
    logic_categories,
    parser_nups,
)

import cherrypy as chpy
from cherrypy._cprequest import Request, Response
from datetime import datetime
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from jinja2 import Template
import mimetypes
import prometheus_client as prom
import re
import simplejson as json
from simplejson import JSONEncoderForHTML
# import traceback
from typing import Any, Mapping, Sequence

_LW_CACHE = {
    notn: {
        charset: LexWriter(notn, charset)
        for charset in notn.charsets
    }
    for notn in Notation 
}

mailroom = Mailroom(APP_ENVCONF)

#####################
## Input Defaults  ##
#####################
api_defaults = MapCover(dict(
    input_notation  = 'polish',
    output_notation = 'polish',
    output_format   = 'html',
))
form_defaults = MapCover(dict(
    input_notation  = 'standard',
    output_format   = 'html',
    output_notation = 'standard',
    output_charset  = 'html',
    show_controls   = True,
    build_models    = True,
    color_open      = True,
    rank_optimizations  = True,
    group_optimizations = True,
))


#################
## View Data   ##
#################
base_view_data = MapCover(dict(

    logics              = APP_LOGICS,

    lexicals            = lexicals,
    LexType             = LexType,
    Notation            = Notation,
    ParseTable           = ParseTable,
    Json                = json,

    example_args        = example_args,
    form_defaults       = form_defaults,
    output_formats      = TabWriter.Registry.keys(),
    output_charsets     = output_charsets,
    logic_categories    = logic_categories,

    lwh                 = _LW_CACHE[Notation.standard]['html'],
    view_version        = 'v2',
))


###################
## Webapp        ##
###################
_APP_DATA = MapCover(dict(
    example_args   = example_args,
    example_preds  = tuple(p.spec for p in examples.preds),
    nups           = parser_nups,
))
_APP_JSON = json.dumps(
    dict(_APP_DATA),
    indent = 2 * APP_ENVCONF['is_debug'],
    cls = JSONEncoderForHTML
)
_STATIC = {
    'js/appdata.json': _APP_JSON.encode('utf-8'),
    'js/appdata.js': (';window.AppData = ' + _APP_JSON + ';').encode('utf-8')
}

_EMPTY = ()
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
    def static(self, *respath, **req_data):
        req: Request = chpy.request
        res: Response = chpy.response
        resource = '/'.join(respath)
        try:
            content = _STATIC[resource]
        except KeyError:
            raise chpy.NotFound()
        if req.method != 'GET':
            raise chpy.HTTPError(405)
        res.headers['Content-Type'] = mimetypes.guess_type(resource)[0]
        return content

    @chpy.expose
    def index(self, **req_data):

        req: Request = chpy.request

        errors = {}
        warns  = {}
        debugs = []

        view_data = dict(base_view_data)

        config = self.config

        form_data = fix_uri_req_data(req_data)

        if form_data.get('v') in ('v1', 'v2'):
            view_version = form_data['v']
        else:
            view_version = 'v2'
        view = '/'.join((view_version, 'main'))

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
            except TimeoutError as err: # pragma: no cover
                errors['Tableau'] = errstr(err)
            else:
                is_proof = True
                if resp_data['writer']['format'] == 'html':
                    is_controls = bool(form_data.get('show_controls'))
                    is_models = bool(
                        form_data.get('build_models') and
                        tableau.invalid
                    )
                    is_color = bool(form_data.get('color_open'))
                    selected_tab = 'view'
                else:
                    selected_tab = 'stats'
                view_data.update(
                    tableau = tableau,
                    lw      = lw,
                )
        else:
            form_data = dict(form_defaults)

        if errors:
            view_data['errors'] = errors

        page_data = dict(
            is_debug     = is_debug,
            is_proof     = is_proof,
            is_controls  = is_controls,
            is_models    = is_models,
            is_color     = is_color,
            selected_tab = selected_tab,
        )

        if is_debug:
            debugs.extend(dict(
                req_data  = req_data,
                form_data = form_data,
                api_data  = api_data,
                resp_data = resp_data and debug_resp_data(resp_data),
                page_data = page_data,
            ).items())
            view_data['debugs'] = debugs

        view_data.update(page_data,
            page_json = json.dumps(
                page_data,
                indent = 2 * is_debug,
                cls = JSONEncoderForHTML
            ),
            config       = self.config,
            view_version = view_version,
            form_data    = form_data,
            resp_data    = resp_data,
            warns        = warns,
        )

        return self._render(view, view_data)

    @chpy.expose
    def feedback(self, **form_data) -> str:

        config = self.config
        if not (config['feedback_enabled'] and config['smtp_host']):
            raise chpy.NotFound()

        req: Request = chpy.request

        errors = {}
        warns  = {}
        debugs = []

        view = 'feedback'
        view_data = dict(base_view_data,
            form_data = form_data
        )

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

        page_data = dict(
            is_debug     = is_debug,
            is_submitted = is_submitted,
        )

        if is_debug:
            debugs.extend(dict(
                form_data = form_data,
            ).items())
            view_data['debugs'] = debugs

        view_data.update(page_data,
            page_json = json.dumps(
                page_data,
                indent = 2 * is_debug,
                cls = JSONEncoderForHTML
            ),
            config       = self.config,
            errors       = errors,
            warns        = warns,
        )

        return self._render(view, view_data)

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
                        "ascii": "Fa",
                        "unicode": "Fa",
                        "html": "Fa"
                    },
                    "polish": {
                        "ascii": "Fm",
                        "unicode": "Fm",
                        "html": "Fm"
                    }
                }
            }
        """
        errors = {}

        # defaults
        body = dict(
            notation   = api_defaults['input_notation'],
            predicates = _EMPTY,
            input      = '',
        ) | body

        try:
            preds = self._parse_preds(body['predicates'])
        except RequestDataError as err:
            errors.update(err.errors)
            preds = None

        elabel = 'Notation'
        try:
            notn = Notation[body['notation']]
        except KeyError as err:
            errors[elabel] = "Invalid notation: '%s'" % err

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
            type     = sentence.TYPE.name,
            rendered = {
                notn.name: {
                    charset: lw(sentence)
                    for charset, lw in lwmap.items()
                }
                for notn, lwmap in _LW_CACHE.items()
            },
        )

    def api_prove(self, body: Mapping[str, Any]) -> tuple[dict, Tableau, LexWriter]:
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
                    "charset": "html",
                    "options": {}
                },
            }
        """
        config = self.config
        errors = {}

        body = dmap(
            logic        = None,
            argument     = _EMPTY_MAP,
            build_models = False,
            max_steps    = None,
            rank_optimizations  = True,
            group_optimizations = True,
        ) | body

        odata = dmap(
            notation = api_defaults['output_notation'],
            format   = api_defaults['output_format'],
            charset  = None,
            options  = {},
        ) | body.get('output', _EMPTY_MAP)

        odata['options']['debug'] = config['is_debug']

        if body['max_steps'] is not None:
            elabel = 'Max steps'
            try:
                body['max_steps'] = int(body['max_steps'])
            except ValueError as err:
                errors[elabel] = "Invalid int value: %s" % err

        tableau_opts = dict(
            is_rank_optim   = bool(body['rank_optimizations']),
            is_group_optim  = bool(body['group_optimizations']),
            is_build_models = bool(body['build_models']),
            max_steps       = body['max_steps'],
            build_timeout   = config['maxtimeout'],
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
        else:
            logicname: str = logic.name

        elabel = 'Output Format'
        try:
            WriterClass = TabWriter.Registry[odata['format']]
        except KeyError:
            errors[elabel] = "Invalid writer: '%s'" % odata['format']
        else:

            elabel = 'Output Notation'
            try:
                onotn = Notation[odata['notation']]
            except KeyError as err:
                errors[elabel] = "Invalid notation: '%s'" % err
            else:

                elabel = 'Output Charset'
                try:
                    lw = _LW_CACHE[onotn][
                        odata['charset'] or WriterClass.default_charsets[onotn]
                    ]
                except KeyError as err:
                    errors[elabel] = "Unsupported charset: '%s'" % err
                else:
                    tw = WriterClass(lw = lw, **odata['options'])

        if errors:
            raise RequestDataError(errors)

        with StopWatch() as timer:
            Metric.proofs_inprogress_count(logicname).inc()
            tableau = Tableau(logic, arg, **tableau_opts)

            try:
                tableau.build()
                Metric.proofs_completed_count(logicname, tableau.stats['result'])
            finally:
                Metric.proofs_inprogress_count(logicname).dec()
                Metric.proofs_execution_time(logicname).observe(timer.elapsed_secs())

        resp_data = dict(
            tableau = dict(
                logic = logicname,
                argument = dict(
                    premises   = tuple(map(lw, arg.premises)),
                    conclusion = lw(arg.conclusion),
                ),
                valid  = tableau.valid,
                header = tw.document_header(),
                footer = tw.document_footer(),
                body   = tw(tableau),
                stats  = tableau.stats,
                result = tableau.stats['result'],
            ),
            attachments = tw.attachments(tableau),
            writer = dict(
                name    = tw.name,
                format  = tw.format,
                charset = lw.charset,
                options = tw.opts,
            )
        )
        # Return a tuple (resp, tableau, lw) because the web ui needs the
        # tableau object to write the controls.
        return resp_data, tableau, lw

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
            notn = Notation[adata['notation']]
        except KeyError as err:
            errors[elabel] = "Invalid parser notation: '%s'" % err
        else:
            try:
                preds = cls._parse_preds(adata['predicates'])
            except RequestDataError as err:
                errors.update(err.errors)
                preds = None
            parser = notn.Parser(preds)
            premises = []
            for i, premise in enumerate(adata['premises'], start = 1):
                elabel = 'Premise %d' % i
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

def fix_uri_req_data(form_data: dict[str, VT]) -> dict[str, VT]:
    form_data = dict(form_data)
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
    return re.fullmatch(REGEX_EMAIL, value) is not None

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