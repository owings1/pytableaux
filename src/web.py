# pytableaux, a multi-logic proof generator.
# Copyright (C) 2014-2021 Doug Owings.
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

from errors import TimeoutError
from tools.decorators import static
from tools.misc import errstr, get_logic

import examples, fixed
from fixed import issues_href, source_href, version
import lexicals
from lexicals import Argument, Predicate, Predicates, LexWriter, RenderSet, \
    Operator, Quantifier, Notation, LexType
from parsers import create_parser
from proof.tableaux import Tableau
from proof.writers import create_tabwriter, formats as tabwriter_formats


import cherrypy as server
from functools import partial
import json, re, time, traceback
import operator as opr
import prometheus_client as prom

from cherrypy._cpdispatch import Dispatcher
from datetime import datetime
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from www.mailroom import Mailroom

from www.conf import available, consts, cp_global_config, jenv, \
    logger, logic_categories, Metric, modules, example_arguments, \
    nups, opts, re_email, parser_tables

mailroom = Mailroom(opts)

##############################
## Cherrypy Server Config   ##
##############################

class AppDispatcher(Dispatcher):
    def __call__(self, path_info):
        Metric.app_requests_count(path_info).inc()
        return super().__call__(path_info.split('?')[0])

cp_config = {
    '/' : {
        'request.dispatch': AppDispatcher(),
    },
    '/static' : {
        'tools.staticdir.on'  : True,
        'tools.staticdir.dir' : consts['static_dir'],
    },
    '/doc': {
        'tools.staticdir.on'    : True,
        'tools.staticdir.dir'   : consts['static_dir_doc'],
        'tools.staticdir.index' : consts['index_filename'],
    },
    '/favicon.ico': {
        'tools.staticfile.on': True,
        'tools.staticfile.filename': consts['favicon_file'],
    },
    '/robots.txt': {
        'tools.staticfile.on': True,
        'tools.staticfile.filename': consts['robotstxt_file'],
    },
}

#####################
## Static Data     ##
#####################
# For notn, only include those common to all, until UI suports
# notn-specific choice.
lexwriter_encodings = {
    notn.name: RenderSet.available(notn.name)
    for notn in Notation
}
_enc = set(enc for encs in lexwriter_encodings.values() for enc in encs)
for notn in Notation:
    _enc = _enc.intersection(RenderSet.available(notn.name))
lexwriter_encodings_common = sorted(_enc)
del(_enc)

########################
## Static LexWriters  ##
########################
lexwriters = {
    notn.name: {
        enc: LexWriter(notn, enc=enc)
        for enc in RenderSet.available(notn.name)
    }
    for notn in Notation 
}

#####################
## Form Defaults   ##
#####################
form_defaults = {
    'input_notation'  : 'standard',
    'format'          : 'html',
    'output_notation' : 'standard',
    'symbol_enc'      : 'html',
    'show_controls'   : True,

    # 'options.controls': True,
    'options.group_optimizations': True,
    'options.models': True,
    'options.rank_optimizations': True,

}

###############
## JS Data   ##
###############
base_browser_data = {
    'example_predicates'    : tuple(p.spec for p in examples.preds),
    # nups: "notation-user-predicate-symbols"
    'nups'                  : nups,
    'num_predicate_symbols' : Predicate.TYPE.maxi + 1,
    'example_arguments'     : example_arguments,
    'is_debug'              : opts['is_debug'],
}

#################
## View Data   ##
#################
base_view_data = {
    'app_name'            : opts['app_name'],
    'copyright'           : fixed.copyright,
    'example_args_list'   : examples.titles,
    'feedback_to_address' : opts['feedback_to_address'],
    'form_defaults'       : form_defaults,
    'google_analytics_id' : opts['google_analytics_id'],
    'is_debug'            : opts['is_debug'],
    'is_feedback'         : opts['feedback_enabled'],
    'is_google_analytics' : bool(opts['google_analytics_id']),
    'issues_href'         : issues_href,
    'lexwriter_notations' : Notation.names,
    'lexwriter_encodings' : lexwriter_encodings_common,
    'lwstdhtm'            : lexwriters['standard']['html'],
    'logic_categories'    : logic_categories,
    'logic_modules'       : available['logics'],
    'logics'              : modules['logics'],
    'parser_tables'       : parser_tables,
    'operators_list'      : list(Operator),
    'quantifiers'         : list(Quantifier),
    'lexicals'            : lexicals,
    'LexType'             : LexType,
    'source_href'         : source_href,
    'tabwriter_formats'   : tabwriter_formats,
    'version'             : version,
    'view_version'        : 'v2',
}

###################
## Templates     ##
###################

template_cache = dict()

def get_template(view):
    if '.' not in view:
        view = '.'.join((view, 'jinja2'))
    if opts['is_debug'] or (view not in template_cache):
        template_cache[view] = jenv.get_template(view)
    return template_cache[view]

def render(view, data = {}):
    return get_template(view).render(data)

#####################
## Miscellaneous   ##
#####################

def fix_form_data(form_data):
    form_data = dict(form_data)
    if len(form_data):
        for param in form_data:
            if param.endswith('[]'):
                if isinstance(form_data[param], str):
                    form_data[param] = [form_data[param]]
    return form_data

def debug_result(result):
    if result:
        result = dict(result)
        if 'tableau' in result and 'body' in result['tableau']:
            if len(result['tableau']['body']) > 255:
                result['tableau'] = dict(result['tableau'])
                result['tableau']['body'] = '{0}...'.format(
                    result['tableau']['body'][0:255]
                )
    return result

def is_valid_email(value):
    return re.fullmatch(re_email, value)

def validate_feedback_form(form_data):
    errors = dict()
    if not is_valid_email(form_data['email']):
        errors['Email'] = 'Invalid email address'
    if not len(form_data['name']):
        errors['Name'] = 'Please enter your name'
    if not len(form_data['message']):
        errors['Message'] = 'Please enter a message'
    if errors:
        raise RequestDataError(errors)

def get_remote_ip(req):
    # TODO: use proxy forward header
    return req.remote.ip

class RequestDataError(Exception):
    def __init__(self, errors):
        self.errors = errors

###################
## Webapp        ##
###################

class App(object):

    @server.expose
    def index(self, *args, **req_data):

        req = server.request

        errors = dict()
        warns  = dict()
        debugs = list()

        data = dict(base_view_data)
        browser_data = dict(base_browser_data)

        if req_data.get('v') in ('v1', 'v2'):
            view_version = req_data['v']
        else:
            view_version = 'v2'
        view = '/'.join((view_version, 'main'))

        if req_data.get('debug') == 'false':
            is_debug = False
        else:
            is_debug = opts['is_debug']

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
                    # arg, vocab = self.parse_argument_data(api_data['argument'])
                    self.parse_argument_data(api_data['argument'])
                except RequestDataError as err:
                    errors.update(err.errors)
                resp_data, tableau, lw = self.api_prove(api_data)
            except RequestDataError as err:
                errors.update(err.errors)
            except TimeoutError as err: # pragma: no cover
                errors['Tableau'] = errstr(err)

            if not errors:
                is_proof = True
                if form_data.get('format') == 'html':
                    is_controls = bool(form_data.get('show_controls'))
                    is_models = bool(
                        form_data.get('options.models') and
                        tableau.invalid
                    )
                    selected_tab = 'view'
                else:
                    selected_tab = 'stats'
                data.update({
                    'tableau' : tableau,
                    'lw'      : lw,
                })

        if errors:
            data['errors'] = errors

        browser_data.update({
            'is_debug'     : is_debug,
            'is_proof'     : is_proof,
            'is_controls'  : is_controls,
            'is_models'    : is_models,
            'selected_tab' : selected_tab,
        })

        if is_debug:
            debugs.extend([
                ('api_data', api_data),
                ('req_data', req_data),
                ('form_data', form_data),
                ('resp_data', debug_result(resp_data)),
                ('browser_data', browser_data),
            ])
            data['debugs'] = debugs

        data.update({
            'browser_json' : json.dumps(browser_data, indent = 2),
            'is_proof'     : is_proof,
            'is_controls'  : is_controls,
            'is_models'    : is_models,
            'selected_tab' : selected_tab,
            'view_version' : view_version,
            'form_data'    : form_data,
            'resp_data'    : resp_data,
            'warns'        : warns,
        })

        return render(view, data)

    def feedback(self, **form_data):

        errors = dict()
        warns  = dict()
        debugs = list()

        data = dict(base_view_data)

        is_submitted = False

        view = 'feedback'
        
        data.update({
            'form_data' : form_data,
        })

        req = server.request

        if req.method == 'POST':

            try:
                validate_feedback_form(form_data)
            except RequestDataError as err:
                errors.update(err.errors)

            if len(errors) == 0:
                date = datetime.now()
                data.update({
                    'date'    : str(date),
                    'ip'      : get_remote_ip(req),
                    'headers' : req.headers,
                })
                msg = MIMEMultipart('alternative')
                msg['From'] = '{0} Feedback <{1}>'.format(
                    opts['app_name'],
                    opts['feedback_from_address'],
                )
                msg['To'] = opts['feedback_to_address']
                msg['Subject'] = 'Feedback from {0}'.format(form_data['name'])
                msg_txt = render('feedback-email.txt', data)
                msg_html = render('feedback-email', data)
                msg.attach(MIMEText(msg_txt, 'plain'))
                msg.attach(MIMEText(msg_html, 'html'))
                mailroom.enqueue(
                    opts['feedback_from_address'],
                    (opts['feedback_to_address'],),
                    msg.as_string(),
                )
                is_submitted = True

        else:
            if not mailroom.last_was_success:
                warns['Mailroom'] = ' '.join((
                    'The most recent email was unsuccessful.',
                    'You might want to send an email instead.',
                ))

        debugs.extend([
            ('form_data', form_data),
        ])
        data.update({
            'errors'       : errors,
            'warns'        : warns,
            'is_submitted' : is_submitted,
        })
        return render(view, data)

    feedback.exposed = opts['feedback_enabled'] and bool(opts['smtp_host'])

    @server.expose
    @server.tools.json_in()
    @server.tools.json_out()
    def api(self, action=None):

        req = server.request
        res = server.response

        if req.method == 'POST':
            try:
                result = None
                if action == 'parse':
                    result = self.api_parse(req.json)
                elif action == 'prove':
                    result, _t, _lw = self.api_prove(req.json)
                if result:
                    return {
                        'status'  : 200,
                        'message' : 'OK',
                        'result'  : result,
                    }
            except TimeoutError as err: # pragma: no cover
                res.status = 408
                return {
                    'status'  : 408,
                    'message' : errstr(err),
                    'error'   : err.__class__.__name__,
                }
            except RequestDataError as err:
                res.status = 400
                return {
                    'status'  : 400,
                    'message' : 'Request data errors',
                    'error'   : err.__class__.__name__,
                    'errors'  : err.errors,
                }
            except Exception as err: # pragma: no cover
                res.status = 500
                return {
                    'status'  : 500,
                    'message' : errstr(err),
                    'error'   : err.__class__.__name__,
                }
                #traceback.print_exc()
        res.status = 404
        return {'message': 'Not found', 'status': 404}

    def api_parse(self, body):
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

        body = dict(body)

        # defaults
        if 'notation' not in body:
            body['notation'] = 'polish'
        if 'predicates' not in body:
            body['predicates'] = list()
        if 'input' not in body:
            body['input'] = ''

        errors = dict()
        if body['notation'] not in Notation:
            errors['Notation'] = 'Invalid notation'

        try:
            preds = self.parse_predicates_data(body['predicates'])
        except RequestDataError as err:
            errors.update(err.errors)
            preds = Predicates()

        if len(errors) == 0:
            parser = create_parser(body['notation'], preds)
            try:
                sentence = parser.parse(body['input'])
            except Exception as err:
                errors['Sentence'] = errstr(err)

        if len(errors) > 0:
            raise RequestDataError(errors)

        return {
            'type'     : sentence.TYPE.name,
            'rendered' : {
                notn: {
                    fmt: lexwriters[notn][fmt].write(sentence)
                    for fmt in lexwriters[notn]
                }
                for notn in lexwriters
            },
        }

    def api_prove(self, body):
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

        body = dict(body)

        # defaults
        body['argument'] = body.get('argument', {})
        body['output'] = body.get('output', {})
        odata = body['output']
        odata['notation'] = odata.get('notation', 'standard')
        odata['format'] = odata.get('format', 'html')
        if 'symbol_enc' not in odata:
            if odata['format'] == 'html':
                odata['symbol_enc'] = 'html'
            else:
                odata['symbol_enc'] = 'ascii'
        odata['options'] = odata.get('options', {})
        body['build_models'] = bool(body.get('build_models'))
        body['max_steps'] = body.get('max_steps', None)
        body['rank_optimizations'] = body.get('rank_optimizations', True)
        body['group_optimizations'] = body.get('group_optimizations', True)

        odata['options']['debug'] = opts['is_debug']

        errors = dict()
        try:
            logic = get_logic(body['logic'])
        except Exception as err:
            errors['Logic'] = errstr(err)
        try:
            arg, v = self.parse_argument_data(body['argument'])
        except RequestDataError as err:
            errors.update(err.errors)
        try:
            lwmap = lexwriters[odata['notation']]
            try:
                lw = lwmap[odata['symbol_enc']]
            except KeyError as err:
                errors['Symbol Encoding'] = 'Unsupported encoding: {0}'.format(str(odata['symbol_enc']))
            except Exception as err:
                if opts['is_debug']:
                    traceback.print_exc()
                errors['Symbol Encoding'] = errstr(err)
        except Exception as err:
            errors['Output notation'] = errstr(err)
            if opts['is_debug']:
                traceback.print_exc()
        try:
            tabwriter = create_tabwriter(
                notn=odata['notation'],
                format=odata['format'],
                # lw=lw,
                enc=odata['symbol_enc'],
                **odata['options'],
            )
        except Exception as err:
            errors['Output format'] = errstr(err)

        if body['max_steps'] != None:
            try:
                body['max_steps'] = int(body['max_steps'])
            except Exception as err:
                errors['Max steps'] = errstr(err)

        if errors:
            raise RequestDataError(errors)

        proof_start_time = time.time()

        Metric.proofs_inprogress_count(logic.name).inc()

        proof_opts = {
            'is_rank_optim'  : body['rank_optimizations'],
            'is_group_optim' : body['group_optimizations'],
            'build_timeout'  : opts['maxtimeout'],
            'is_build_models': body['build_models'],
            'max_steps'      : body['max_steps'],
        }

        proof = Tableau(logic, arg, **proof_opts)

        try:
            proof.build()
            Metric.proofs_completed_count(logic.name, proof.stats['result'])
        finally:
            proof_time = time.time() - proof_start_time
            Metric.proofs_inprogress_count(logic.name).dec()
            Metric.proofs_execution_time(logic.name).observe(proof_time)

        # actually we return a tuple (resp, tableau, lw) because the
        # web ui needs the tableau object to write the controls.
        return ({
            'tableau': {
                'logic' : logic.name,
                'argument': {
                    'premises'   : [
                        lw.write(premise)
                        for premise in arg.premises
                    ],
                    'conclusion' : lw.write(arg.conclusion),
                },
                'valid'  : proof.valid,
                'header' : tabwriter.document_header(),
                'footer' : tabwriter.document_footer(),
                'body'   : tabwriter.write(proof),
                'stats'  : proof.stats,
                'result' : proof.stats['result'],
            },
            'attachments' : tabwriter.attachments(proof),
            'writer' : {
                'name'       : tabwriter.name,
                'format'     : odata['format'],
                'symbol_enc' : odata['symbol_enc'],
                'options'    : tabwriter.opts,
            }
        }, proof, lw)

    def parse_argument_data(self, adata):

        adata = dict(adata)

        # defaults
        if 'notation' not in adata:
            adata['notation'] = 'polish'
        if 'predicates' not in adata:
            adata['predicates'] = list()
        if 'premises' not in adata:
            adata['premises'] = list()

        preds = Predicates()

        errors = dict()

        try:
            if adata['notation'] not in Notation:
                raise ValueError('Invalid parser notation')
        except Exception as e:
            errors['Notation'] = str(e)

        if not errors:
            try:
                preds = self.parse_predicates_data(adata['predicates'])
            except RequestDataError as err:
                errors.update(err.errors)
            parser = create_parser(adata['notation'], preds)
            i = 1
            premises = []
            for premise in adata['premises']:
                try:
                    premises.append(parser.parse(premise))
                except Exception as e:
                    premises.append(None)
                    errors['Premise {0}'.format(str(i))] = errstr(e)
                i += 1
            try:
                conclusion = parser.parse(adata['conclusion'])
            except Exception as e:
                errors['Conclusion'] = errstr(e)

        if errors:
            raise RequestDataError(errors)

        return (Argument(conclusion, premises), preds)

    def parse_predicates_data(self, predicates) -> Predicates:
        preds = Predicates()
        errors = dict()
        Coords = Predicate.Coords
        fields = Coords._fields
        for i, pdata in enumerate(predicates, start = 1):
            try:
                if isinstance(pdata, dict):
                    keys = fields
                else:
                    keys = range(len(fields))
                coords = Coords(*map(partial(opr.getitem, pdata), keys))
                preds.add(coords)
            except Exception as e:
                errors['Predicate {0}'.format(str(i))] = errstr(e)
        if errors:
            raise RequestDataError(errors)
        return preds

#############
## Main    ##
#############

def main(): # pragma: no cover
    logger.info(
        'Staring metrics on port {0}'.format(str(opts['metrics_port']))
    )
    mailroom.start()
    prom.start_http_server(opts['metrics_port'])
    server.config.update(cp_global_config)
    server.quickstart(App(), '/', cp_config)

if  __name__ == '__main__': # pragma: no cover
    main()