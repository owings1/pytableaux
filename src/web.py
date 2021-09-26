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
# pytableaux - Web Interface

import examples, logic, json, os, time
import importlib
import logging
import os.path
import re
import smtplib
import ssl
import traceback
import cherrypy as server
from cherrypy._cpdispatch import Dispatcher
from datetime import datetime
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from jinja2 import Environment, FileSystemLoader
import prometheus_client as prom

ProofTimeoutError = logic.TableauxSystem.ProofTimeoutError
# http://python-future.org/compatible_idioms.html#basestring
from past.builtins import basestring

re_email = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'

app_dir = os.path.dirname(os.path.abspath(__file__))

consts = {
    'index_filename' : 'index.html',
    'view_path'      : os.path.join(app_dir, 'www/views'),
    'static_dir'     : os.path.join(app_dir, 'www/static'),
    'favicon_file'   : os.path.join(app_dir, 'www/static/img/favicon-60x60.png'),
    'static_dir_doc' : os.path.join(app_dir, '..', 'doc/_build/html'),
}

optdefs = {
    'app_name' : {
        'default' : 'pytableaux',
        'envvar'  : 'PT_APPNAME',
        'type'    : 'string',
    },
    'host' : {
        'default' : '127.0.0.1',
        'envvar'  : 'PT_HOST',
        'type'    : 'string'
    },
    'port' : {
        'default' : 8080,
        'envvar'  : 'PT_PORT',
        'type'    : 'int',
    },
    'metrics_port' : {
        'default' : 8181,
        'envvar'  : 'PT_METRICS_PORT',
        'type'    : 'int',
    },
    'is_debug' : {
        'default' : False,
        'envvar'  : ('PT_DEBUG', 'DEBUG'),
        'type'    : 'boolean',
    },
    'loglevel': {
        'default' : 'info',
        'envvar'  : ('PT_LOGLEVEL', 'LOGLEVEL'),
        'type'    : 'string',
    },
    'maxtimeout' : {
        'default' : 30000,
        'envvar'  : 'PT_MAXTIMEOUT',
        'type'    : 'int',
    },
    'google_analytics_id' : {
        'default' : None,
        'envvar'  : 'PT_GOOGLE_ANALYTICS_ID',
        'type'    : 'string',
    },
    'feedback_enabled': {
        'default' : False,
        'envvar'  : 'PT_FEEDBACK',
        'type'    : 'boolean',
    },
    'feedback_to_address': {
        'default'  : None,
        'envvar'  : 'PT_FEEDBACK_TOADDRESS',
        'type'    : 'string',
    },
    'feedback_from_address': {
        'default'  : None,
        'envvar'  : 'PT_FEEDBACK_FROMADDRESS',
        'type'    : 'string',
    },
    'smtp_host': {
        'default' : None,
        'envvar'  : ('PT_SMTP_HOST', 'SMTP_HOST'),
        'type'    : 'string',
    },
    'smtp_port': {
        'default' : 587,
        'envvar'  : ('PT_SMTP_PORT', 'SMTP_PORT'),
        'type'    : 'int',
    },
    'smtp_helo': {
        'default' : None,
        'envvar'  : ('PT_SMTP_HELO', 'SMTP_HELO'),
        'type'    : 'string',
    },
    'smtp_starttls': {
        'default' : True,
        'envvar'  : ('PT_SMTP_STARTTLS', 'SMTP_STARTTLS'),
        'type'    : 'boolean',
    },
    'smtp_tlscertfile': {
        'default' : None,
        'envvar'  : ('PT_SMTP_TLSCERTFILE', 'SMTP_TLSCERTFILE'),
        'type'    : 'string',
    },
    'smtp_tlskeyfile': {
        'default' : None,
        'envvar'  : ('PT_SMTP_TLSKEYFILE', 'SMTP_TLSKEYFILE'),
        'type'    : 'string',
    },
    'smtp_tlskeypass': {
        'default' : None,
        'envvar'  : ('PT_SMTP_TLSKEYPASS', 'SMTP_TLSKEYPASS'),
        'type'    : 'string',
    },
    'smtp_username': {
        'default' : None,
        'envvar'  : ('PT_SMTP_USERNAME', 'SMTP_USERNAME'),
        'type'    : 'string',
    },
    'smtp_password': {
        'default' : None,
        'envvar'  : ('PT_SMTP_PASSWORD', 'SMTP_PASSWORD'),
        'type'    : 'string',
    },
}

#####################################################
#                                                   #
# Metrics                                           #
#                                                   #
#####################################################

metrics = {
    'app_requests_count' : prom.Counter(
        'app_requests_count',
        'total app http requests',
        ['app_name', 'endpoint'],
    ),
    'proofs_completed_count' : prom.Counter(
        'proofs_completed_count',
        'total proofs completed',
        ['app_name', 'logic', 'result'],
    ),
    'proofs_inprogress_count' : prom.Gauge(
        'proofs_inprogress_count',
        'total proofs in progress',
        ['app_name', 'logic'],
    ),
    'proofs_execution_time' : prom.Summary(
        'proofs_execution_time',
        'total proof execution time',
        ['app_name', 'logic'],
    )
}

#####################################################
#                                                   #
# Modules Info                                      #
#                                                   #
#####################################################

modules = dict()
logic_categories = dict()
notation_user_predicate_symbols = dict()

available_module_names = {
    'logics'    : [
        'cpl', 'cfol', 'fde', 'k3', 'k3w', 'k3wq', 'b3e', 'go',
        'l3', 'g3', 'p3', 'lp', 'rm3', 'k', 'd', 't', 's4', 's5'
    ],
    'notations' : ['standard', 'polish'],
    'writers'   : ['html', 'ascii'],
}

def populate_modules_info():
    
    for package in available_module_names:
        modules[package] = {}
        for name in available_module_names[package]:
            modules[package][name] = importlib.import_module(
                '.'.join((package, name))
            )

    for notation_name in modules['notations']:
        notation = modules['notations'][notation_name]
        notation_user_predicate_symbols[notation_name] = list(
            notation.symbol_sets['default'].chars('user_predicate')
        )

    for name in modules['logics']:
        lgc = modules['logics'][name]
        if lgc.Meta.category not in logic_categories:
            logic_categories[lgc.Meta.category] = list()
        logic_categories[lgc.Meta.category].append(name)

    def get_category_order(name):
        return logic.get_logic(name).Meta.category_display_order

    for category in logic_categories.keys():
        logic_categories[category].sort(key = get_category_order)

populate_modules_info()

#####################################################
#                                                   #
# Options                                           #
#                                                   #
#####################################################

def get_opt_value(name, defn):
    evtype = type(defn['envvar'])
    if evtype == str:
        envvars = (defn['envvar'],)
    else:
        envvars = defn['envvar']
    for varname in envvars:
        if varname in os.environ:
            v = os.environ[varname]
            if defn['type'] == 'int':
                v = int(v)
            elif defn['type'] == 'boolean':
                v = str(v).lower() in ('true', 'yes', '1')
            else:
                # string
                v = str(v)
            return v
    return defn['default']

opts = {
    name: get_opt_value(name, optdefs[name]) for name in optdefs.keys()
}

# Logger
def init_logger(logger):
    ch = logging.StreamHandler()
    formatter = logging.Formatter(
        # Similar to cherrypy's format for consistency.
        '[%(asctime)s] %(name)s.%(levelname)s %(message)s',
        datefmt='%d/%b/%Y:%H:%M:%S',
    )
    ch.setFormatter(formatter)
    logger.addHandler(ch)
    if hasattr(logging, opts['loglevel'].upper()):
        logger.setLevel(getattr(logging, opts['loglevel'].upper()))
    else:
        logger.setLevel(getattr(logging, optdefs['loglevel']['default'].upper()))
        logger.warn('Ingoring invalid loglevel: {0}'.format(opts['loglevel']))
        opts['loglevel'] = optdefs['loglevel']['default'].upper()
logger = logging.Logger('APP')
init_logger(logger)


#####################################################
#                                                   #
# Server Config                                     #
#                                                   #
#####################################################

class AppDispatcher(Dispatcher):
    def __call__(self, path_info):
        metrics['app_requests_count'].labels(opts['app_name'], path_info).inc()
        logger.debug('path_info:', path_info)
        return Dispatcher.__call__(self, path_info.split('?')[0])

global_config = {
    'global': {
        'server.socket_host'   : opts['host'],
        'server.socket_port'   : opts['port'],
        'engine.autoreload.on' : opts['is_debug'],
    },
}

config = {
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
}

#####################################################
#                                                   #
# Static Data                                       #
#                                                   #
#####################################################

browser_data = {
    'example_predicates'              : examples.test_pred_data,
    'notation_user_predicate_symbols' : notation_user_predicate_symbols,
    'num_predicate_symbols'           : logic.num_predicate_symbols,
    'example_arguments' : {
        arg.title : {
            notation: {
                'premises'   : [modules['notations'][notation].write(premise) for premise in arg.premises],
                'conclusion' : modules['notations'][notation].write(arg.conclusion),
            }
            for notation in available_module_names['notations']
        }
        for arg in examples.arguments()
    }
}

base_view_data = {
    'app_name'            : opts['app_name'],
    'browser_json'        : json.dumps(browser_data, indent = 2),
    'copyright'           : logic.copyright,
    'example_args_list'   : examples.args_list,
    'google_analytics_id' : opts['google_analytics_id'],
    'is_debug'            : opts['is_debug'],
    'is_feedback'         : opts['feedback_enabled'],
    'is_google_analytics' : bool(opts['google_analytics_id']),
    'logic_categories'    : logic_categories,
    'logic_modules'       : available_module_names['logics'],
    'logics'              : modules['logics'],
    'notation_modules'    : available_module_names['notations'],
    'notations'           : modules['notations'],
    'operators_list'      : logic.operators_list,
    'quantifiers'         : logic.quantifiers_list,
    'source_href'         : logic.source_href,
    'system_predicates'   : logic.system_predicates,
    'version'             : logic.version,
    'writer_modules'      : available_module_names['writers'],
    'writers'             : modules['writers'],
}

#####################################################
#                                                   #
# Templates                                         #
#                                                   #
#####################################################

jenv = Environment(loader = FileSystemLoader(consts['view_path']))
template_cache = dict()

def get_template(view):
    if '.' not in view:
        view = '.'.join((view, 'html'))
    if opts['is_debug'] or (view not in template_cache):
        template_cache[view] = jenv.get_template(view)
    return template_cache[view]

def render(view, data={}):
    return get_template(view).render(data)

#####################################################
#                                                   #
# Generic                                           #
#                                                   #
#####################################################

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
                result['tableau']['body'] = '{0}...'.format(result['tableau']['body'][0:255])
    return result

def is_valid_email(value):
    return re.fullmatch(re_email, value)

def validate_feedback_form(form_data):
    errors = {}
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

class InternalError(Exception):
    pass

class ConfigError(Exception):
    pass

#####################################################
#                                                   #
# SMTP                                              #
#                                                   #
#####################################################

if opts['smtp_host']:
    logger.info('Intializing SMTP settings')
    if opts['feedback_enabled']:
        if not opts['feedback_to_address']:
            raise ConfigError('Feedback is enabled but to address is not set')
        if not opts['feedback_from_address']:
            raise ConfigError('Feedback is enabled but from address is not set')
        if not is_valid_email(opts['feedback_to_address']):
            raise ConfigError('Invalid feedback to address:', str(opts['feedback_to_address']))
        if not is_valid_email(opts['feedback_from_address']):
            raise ConfigError('Invalid feedback from address:', str(opts['feedback_from_address']))
    if opts['smtp_starttls']:
        smtp_tlscontext = ssl.SSLContext()
        if opts['smtp_tlscertfile']:
            logger.info('Loading TLS certificate for SMTP')
            smtp_tlscontext.load_cert_chain(
                opts['smtp_tlscertfile'],
                keyfile = opts['smtp_tlskeyfile'],
                password = opts['smtp_tlskeypass'],
            )
    else:
        logger.warn('TLS disabled for SMTP, messages will NOT be encrypted')

mailqueue = []
def queue_email(from_addr, to_addrs, msg):
    if not opts['smtp_host']:
        raise InternalError('SMTP not configured')
    mailqueue.append({
        'from_addr' : from_addr,
        'to_addrs'  : to_addrs,
        'msg'       : msg,
    })

def smtp_mailroom():
    if not mailqueue:
        return
    logger.info(
        'Connecting to SMTP server {0}:{1}'.format(
            opts['smtp_host'], str(opts['smtp_port'])
        )
    )
    smtp = smtplib.SMTP(
        host=opts['smtp_host'],
        port=opts['smtp_port'],
        local_hostname=opts['smtp_helo'],
    )
    try:
        smtp.ehlo()
        if opts['smtp_starttls']:
            logger.info('Starting SMTP TLS session')
            resp = smtp.starttls(context = smtp_tlscontext)
            logger.debug('Starttls response: {0}'.format(str(resp)))
        else:
            logger.warn('TLS disabled, not encrypting email')
        if (opts['smtp_username']):
            logger.debug('Logging into SMTP server with {0}'.format(opts['smtp_username']))
            smtp.login(opts['smtp_username'], opts['smtp_password'])
        i, total = (0, len(mailqueue))
        requeue = []
        while mailqueue:
            job = mailqueue.pop(0)
            try:
                logger.info('Sending message {0} of {1}'.format(str(i + 1), str(total)))
                smtp.sendmail(**job)
            except Exception as merr:
                traceback.print_exc()
                logger.error('Sendmail failed with error: {0}'.format(str(merr)))
                requeue.append(job)
            i += 1
        logger.info('Disconnecting from SMTP server')
        smtp.quit()
    except Exception as err:
        logger.error('SMTP failed with error {0}'.format(str(err)))
        try:
            smtp.quit()
        except Exception as err:
            logger.warn('Failed to quit SMTP connection: {0}'.format(str(err)))
    if requeue:
        logger.info('Requeuing {0} failed messages'.format(len(requeue)))
        mailqueue.extend(requeue)

#####################################################
#                                                   #
# Webapp                                            #
#                                                   #
#####################################################

class App(object):

    @server.expose
    def index(self, *args, **form_data):

        errors = {}
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
        })

        return render(view, data)

    def feedback(self, **form_data):
        view = 'feedback'
        data = dict(base_view_data)
        is_submitted = False
        errors = {}
        if len(form_data):
            try:
                validate_feedback_form(form_data)
            except RequestDataError as err:
                errors.update(err.errors)
            if len(errors) == 0:
                try:
                    date = datetime.now()
                    data.update({
                        'date'      : str(date),
                        'ip'        : get_remote_ip(server.request),
                        'form_data' : form_data,
                    })
                    msg_txt = render('feedback-email.txt', data)
                    msg_html = render('feedback-email', data)
                    msg = MIMEMultipart('alternative')
                    msg['From'] = '{0} Feedback <{1}>'.format(
                        opts['app_name'],
                        opts['feedback_from_address'],
                    )
                    msg['To'] = opts['feedback_to_address']
                    msg['Subject'] = 'Feedback from {0}'.format(form_data['name'])
                    msg.attach(MIMEText(msg_txt, 'plain'))
                    msg.attach(MIMEText(msg_html, 'html'))
                    queue_email(
                        opts['feedback_from_address'],
                        (opts['feedback_to_address'],),
                        msg.as_string(),
                    )
                    # TODO: move to independent thead.
                    smtp_mailroom()
                    is_submitted = True
                except:
                    raise
        data.update({
            'errors'       : errors,
            'is_submitted' : is_submitted,
        })
        return render(view, data)
    feedback.exposed = opts['feedback_enabled'] and bool(opts['smtp_host'])

    @server.expose
    @server.tools.json_in()
    @server.tools.json_out()
    def api(self, action=None):

        if server.request.method == 'POST':
            try:
                result = None
                if action == 'parse':
                    result = self.api_parse(server.request.json)
                elif action == 'prove':
                    result = self.api_prove(server.request.json)
                if result:
                    return {
                        'status'  : 200,
                        'message' : 'OK',
                        'result'  : result,
                    }
            except ProofTimeoutError as err: # pragma: no cover
                server.response.statis = 408
                return {
                    'status'  : 408,
                    'message' : str(err),
                    'error'   : err.__class__.__name__,
                }
            except RequestDataError as err:
                server.response.status = 400
                return {
                    'status'  : 400,
                    'message' : 'Request data errors',
                    'error'   : err.__class__.__name__,
                    'errors'  : err.errors,
                }
            except Exception as err: # pragma: no cover
                server.response.status = 500
                return {
                    'status'  : 500,
                    'message' : str(err),
                    'error'   : err.__class__.__name__,
                }
                #traceback.print_exc()
        server.response.status = 404
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

        errors = {}
        try:
            input_notation = modules['notations'][body['notation']]
        except KeyError:
            errors['Notation'] = 'Invalid notation'

        try:
            vocab = self.parse_predicates_data(body['predicates'])
        except RequestDataError as err:
            errors.update(err.errors)
            vocab = logic.Vocabulary()

        if len(errors) == 0:
            parser = input_notation.Parser(vocabulary=vocab)
            try:
                sentence = parser.parse(body['input'])
            except Exception as err:
                errors['Sentence'] = str(err)

        if len(errors) > 0:
            raise RequestDataError(errors)

        return {
            'type'     : sentence.type,
            'rendered' : {
                notation: {
                    'default': modules['notations'][notation].write(sentence),
                    'html'   : modules['notations'][notation].write(sentence, 'html'),
                }
                for notation in available_module_names['notations']
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

        errors = {}
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
            proof_writer = modules['writers'][odata['format']].Writer(**odata['options'])
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
                    'premises'   : [sw.write(premise) for premise in arg.premises],
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
            notation = modules['notations'][adata['notation']]
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
        errors = {}
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

#####################################################
#                                                   #
# Main                                              #
#                                                   #
#####################################################

def main(): # pragma: no cover
    logger.info('Staring metrics on port {0}'.format(str(opts['metrics_port'])))
    prom.start_http_server(opts['metrics_port'])
    server.config.update(global_config)
    server.quickstart(App(), '/', config)

if  __name__ == '__main__': # pragma: no cover
    main()