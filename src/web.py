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

import examples, logic
import json, re, time

import cherrypy as server
import prometheus_client as prom

from cherrypy._cpdispatch import Dispatcher
from datetime import datetime
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from past.builtins import basestring
from www.mailroom import Mailroom

from www.conf import available, consts, cp_global_config, jenv
from www.conf import logger, logic_categories, metrics, modules
from www.conf import nups, opts, re_email

ProofTimeoutError = logic.TableauxSystem.ProofTimeoutError
# shorthand
ntmods = modules['notations']

mailroom = Mailroom(opts)

##############################
## Cherrypy Server Config   ##
##############################

class AppDispatcher(Dispatcher):
    def __call__(self, path_info):
        metrics['app_requests_count'].labels(opts['app_name'], path_info).inc()
        logger.debug('path_info:', path_info)
        return Dispatcher.__call__(self, path_info.split('?')[0])

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

browser_data = {
    'example_predicates'    : examples.test_pred_data,
    # nups: "notation-user-predicate-symbols"
    'nups'                  : nups,
    'num_predicate_symbols' : logic.num_predicate_symbols,
    'example_arguments' : {
        arg.title : {
            nt: {
                'premises'   : [
                    ntmods[nt].write(premise)
                    for premise in arg.premises
                ],
                'conclusion' : ntmods[nt].write(
                    arg.conclusion
                ),
            }
            for nt in available['notations']
        }
        for arg in examples.arguments()
    }
}

base_view_data = {
    'app_name'            : opts['app_name'],
    'browser_json'        : json.dumps(browser_data, indent = 2),
    'copyright'           : logic.copyright,
    'example_args_list'   : examples.args_list,
    'feedback_to_address' : opts['feedback_to_address'],
    'google_analytics_id' : opts['google_analytics_id'],
    'is_debug'            : opts['is_debug'],
    'is_feedback'         : opts['feedback_enabled'],
    'is_google_analytics' : bool(opts['google_analytics_id']),
    'issues_href'         : logic.issues_href,
    'logic_categories'    : logic_categories,
    'logic_modules'       : available['logics'],
    'logics'              : modules['logics'],
    'notation_modules'    : available['notations'],
    'notations'           : ntmods,
    'operators_list'      : logic.operators_list,
    'quantifiers'         : logic.quantifiers_list,
    'source_href'         : logic.source_href,
    'system_predicates'   : logic.system_predicates,
    'version'             : logic.version,
    'writer_modules'      : available['writers'],
    'writers'             : modules['writers'],
}

###################
## Templates     ##
###################

template_cache = dict()

def get_template(view):
    if '.' not in view:
        view = '.'.join((view, 'html'))
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
                # http://python-future.org/compatible_idioms.html#basestring
                if isinstance(form_data[param], basestring):
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
    def index(self, *args, **form_data):

        errors = dict()
        warns  = dict()
        debugs = list()

        data = dict(base_view_data)

        vocab = logic.Vocabulary()

        view = 'argument'

        form_data = fix_form_data(form_data)
        api_data = None
        result = None

        if len(form_data):

            try:
                try:
                    api_data = json.loads(form_data['api-json'])
                except Exception as err:
                    raise RequestDataError({'api-data': str(err)})
                try:
                    arg, vocab = self.parse_argument_data(api_data['argument'])
                except RequestDataError as err:
                    errors.update(err.errors)
                result = self.api_prove(api_data)
            except RequestDataError as err:
                errors.update(err.errors)
            except ProofTimeoutError as err: # pragma: no cover
                errors['Tableau'] = str(err)

            if len(errors) == 0:
                view = 'prove'
                data.update({
                    'is_proof' : True,
                    'result'   : result,
                })

        if len(errors) > 0:
            data['errors'] = errors

        debugs.extend([
            ('api_data', api_data),
            ('form_data', form_data),
            ('result', debug_result(result)),
        ])

        data.update({
            'form_data'            : form_data,
            'user_predicates'      : vocab.user_predicates,
            'user_predicates_list' : vocab.user_predicates_list,
            'debugs'               : debugs,
            'warns'                : warns,
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

        if len(form_data):

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
                    result = self.api_prove(req.json)
                if result:
                    return {
                        'status'  : 200,
                        'message' : 'OK',
                        'result'  : result,
                    }
            except ProofTimeoutError as err: # pragma: no cover
                res.status = 408
                return {
                    'status'  : 408,
                    'message' : str(err),
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
                    'message' : str(err),
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
               "type": "PredicatedSentence",
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
        try:
            input_notation = ntmods[body['notation']]
        except KeyError:
            errors['Notation'] = 'Invalid notation'

        try:
            vocab = self.parse_predicates_data(body['predicates'])
        except RequestDataError as err:
            errors.update(err.errors)
            vocab = logic.Vocabulary()

        if len(errors) == 0:
            parser = input_notation.Parser(vocabulary = vocab)
            try:
                sentence = parser.parse(body['input'])
            except Exception as err:
                errors['Sentence'] = str(err)

        if len(errors) > 0:
            raise RequestDataError(errors)

        return {
            'type'     : sentence.type,
            'rendered' : {
                nt: {
                    'default': ntmods[nt].write(sentence),
                    'html'   : ntmods[nt].write(sentence, 'html'),
                }
                for nt in available['notations']
            }
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
                    "symbol_set": "default",
                    "options": {
                        "color_open": true,
                        "controls": true,
                        "models": false
                    }
                },
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
                    "writer": {
                        "name": "HTML",
                        "format": "html,
                        "symbol_set": "default",
                        "options": {}
                    },
                    "max_steps" : null
                }
            }
        """

        body = dict(body)

        # defaults
        if 'argument' not in body:
            body['argument'] = dict()
        if 'output' not in body:
            body['output'] = dict()
        odata = body['output']
        if 'notation' not in odata:
            odata['notation'] = 'standard'
        if 'format' not in odata:
            odata['format'] = 'html'
        if 'symbol_set' not in odata:
            if odata['format'] == 'html':
                odata['symbol_set'] = 'html'
            else:
                odata['symbol_set'] = 'default'
        if 'options' not in odata:
            odata['options'] = dict()
        if 'color_open' not in odata['options']:
            odata['options']['color_open'] = True
        if 'controls' not in odata['options']:
            odata['options']['controls'] = True
        if 'models' not in odata['options']:
            odata['options']['models'] = False
        if 'max_steps' not in body:
            body['max_steps'] = None
        if 'rank_optimizations' not in body:
            body['rank_optimizations'] = True
        if 'group_optimizations' not in body:
            body['group_optimizations'] = True

        odata['options']['debug'] = opts['is_debug']

        errors = dict()
        try:
            selected_logic = logic.get_logic(body['logic'])
        except Exception as err:
            errors['Logic'] = str(err)
        try:
            arg, v = self.parse_argument_data(body['argument'])
        except RequestDataError as err:
            errors.update(err.errors)
        try:
            output_notation = modules['notations'][odata['notation']]
            try:
                sw = output_notation.Writer(odata['symbol_set'])
            except Exception as err:
                errors['Symbol Set'] = str(err)
        except Exception as err:
            errors['Output notation'] = str(err)
        try:
            pwmod = modules['writers'][odata['format']]
            proof_writer = pwmod.Writer(**odata['options'])
        except Exception as err:
            errors['Output format'] = str(err)

        if body['max_steps'] != None:
            try:
                body['max_steps'] = int(body['max_steps'])
            except Exception as err:
                errors['Max steps'] = str(err)

        if len(errors) > 0:
            raise RequestDataError(errors)

        proof_start_time = time.time()

        metrics['proofs_inprogress_count'].labels(
            opts['app_name'], selected_logic.name
        ).inc()

        proof_opts = {
            'is_rank_optim'  : body['rank_optimizations'],
            'is_group_optim' : body['group_optimizations'],
            'build_timeout'  : opts['maxtimeout'],
            'is_build_models': odata['options']['models'],
            'max_steps'      : body['max_steps'],
        }

        proof = logic.tableau(selected_logic, arg, **proof_opts)

        try:

            proof.build()

        except:

            metrics['proofs_inprogress_count'].labels(
                opts['app_name'], selected_logic.name
            ).dec()

            proof_time = time.time() - proof_start_time

            metrics['proofs_execution_time'].labels(
                opts['app_name'], selected_logic.name
            ).observe(proof_time)

            raise

        proof_time = time.time() - proof_start_time

        metrics['proofs_inprogress_count'].labels(
            opts['app_name'], selected_logic.name
        ).dec()

        metrics['proofs_execution_time'].labels(
            opts['app_name'], selected_logic.name
        ).observe(proof_time)

        metrics['proofs_completed_count'].labels(
            opts['app_name'], selected_logic.name, proof.stats['result']
        ).inc()

        return {
            'tableau': {
                'logic' : selected_logic.name,
                'argument': {
                    'premises'   : [
                        sw.write(premise)
                        for premise in arg.premises
                    ],
                    'conclusion' : sw.write(arg.conclusion),
                },
                'valid'  : proof.valid,
                'header' : proof_writer.document_header(),
                'footer' : proof_writer.document_footer(),
                'body'   : proof_writer.write(proof, sw=sw),
                'stats'  : proof.stats,
                'result' : proof.stats['result'],
                'writer' : {
                    'name'       : proof_writer.name,
                    'format'     : odata['format'],
                    'symbol_set' : odata['symbol_set'],
                    'options'    : proof_writer.defaults,
                }
            }
        }

    def parse_argument_data(self, adata):

        adata = dict(adata)

        # defaults
        if 'notation' not in adata:
            adata['notation'] = 'polish'
        if 'predicates' not in adata:
            adata['predicates'] = list()
        if 'premises' not in adata:
            adata['premises'] = list()

        vocab = logic.Vocabulary()

        errors = dict()

        try:
            notation = ntmods[adata['notation']]
        except Exception as e:
            errors['Notation'] = str(e)

        if len(errors) == 0:
            try:
                vocab = self.parse_predicates_data(adata['predicates'])
            except RequestDataError as err:
                errors.update(err.errors)
            parser = notation.Parser(vocabulary = vocab)
            i = 1
            premises = []
            for premise in adata['premises']:
                try:
                    premises.append(parser.parse(premise))
                except Exception as e:
                    premises.append(None)
                    errors['Premise {0}'.format(str(i))] = str(e)
                i += 1
            try:
                conclusion = parser.parse(adata['conclusion'])
            except Exception as e:
                errors['Conclusion'] = str(e)

        if len(errors) > 0:
            raise RequestDataError(errors)

        return (logic.argument(conclusion, premises), vocab)

    def parse_predicates_data(self, predicates):
        vocab = logic.Vocabulary()
        errors = dict()
        i = 1
        for pdata in predicates:
            try:
                vocab.declare_predicate(**pdata)
            except Exception as e:
                errors['Predicate {0}'.format(str(i))] = str(e)
            i += 1
        if len(errors) > 0:
            raise RequestDataError(errors)
        return vocab

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