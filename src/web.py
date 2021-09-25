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
import traceback
import os.path
import cherrypy as server
from cherrypy._cpdispatch import Dispatcher
from jinja2 import Environment, FileSystemLoader
import prometheus_client as prom

ProofTimeoutError = logic.TableauxSystem.ProofTimeoutError
# http://python-future.org/compatible_idioms.html#basestring
from past.builtins import basestring

CWD = os.path.dirname(os.path.abspath(__file__))

consts = {
    'index_filename' : 'index.html',
    'view_path'      : os.path.join(CWD, 'www/views'),
    'static_dir'     : os.path.join(CWD, 'www/static'),
    'favicon_file'   : os.path.join(CWD, 'www/static/img/favicon-60x60.png'),
    'static_dir_doc' : os.path.join(CWD, '..', 'doc/_build/html')
}

optdefs = {
    'app_name' : {
        'default' : 'pytableaux',
        'envvar'  : 'PT_APPNAME',
        'type'    : 'string'
    },
    'host' : {
        'default' : '127.0.0.1',
        'envvar'  : 'PT_HOST',
        'type'    : 'string'
    },
    'port' : {
        'default' : 8080,
        'envvar'  : 'PT_PORT',
        'type'    : 'int'
    },
    'metrics_port' : {
        'default' : 8181,
        'envvar'  : 'PT_METRICS_PORT',
        'type'    : 'int'
    },
    'is_debug' : {
        'default' : False,
        'envvar'  : 'PT_DEBUG',
        'type'    : 'boolean'
    },
    'maxtimeout' : {
        'default' : 30000,
        'envvar'  : 'PT_MAXTIMEOUT',
        'type'    : 'int'
    },
    'google_analytics_id' : {
        'default' : None,
        'envvar'  : 'PT_GOOGLE_ANALYTICS_ID',
        'type'    : 'string'
    }
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
        ['app_name', 'endpoint']
    ),
    'proofs_completed_count' : prom.Counter(
        'proofs_completed_count',
        'total proofs completed',
        ['app_name', 'logic', 'result']
    ),
    'proofs_inprogress_count' : prom.Gauge(
        'proofs_inprogress_count',
        'total proofs in progress',
        ['app_name', 'logic']
    ),
    'proofs_execution_time' : prom.Summary(
        'proofs_execution_time',
        'total proof execution time',
        ['app_name', 'logic']
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
    'logics'    : ['cpl', 'cfol', 'fde', 'k3', 'k3w', 'k3wq', 'b3e', 'go', 'l3', 'g3', 'p3', 'lp', 'rm3', 'k', 'd', 't', 's4', 's5'],
    'notations' : ['standard', 'polish'],
    'writers'   : ['html', 'ascii']
}

def get_category_order(name):
    return logic.get_logic(name).Meta.category_display_order

def populate_modules_info():
    
    for package in available_module_names:
        modules[package] = {}
        for name in available_module_names[package]:
            modules[package][name] = importlib.import_module(package + '.' + name)

    for notation_name in modules['notations']:
        notation = modules['notations'][notation_name]
        notation_user_predicate_symbols[notation_name] = list(notation.symbol_sets['default'].chars('user_predicate'))

    for name in modules['logics']:
        lgc = modules['logics'][name]
        if lgc.Meta.category not in logic_categories:
            logic_categories[lgc.Meta.category] = list()
        logic_categories[lgc.Meta.category].append(name)

    for category in logic_categories.keys():
        logic_categories[category].sort(key=get_category_order)

populate_modules_info()

#####################################################
#                                                   #
# Options                                           #
#                                                   #
#####################################################

def get_opt_value(name, defn):
    if defn['envvar'] in os.environ:
        v = os.environ[defn['envvar']]
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

#####################################################
#                                                   #
# Server Config                                     #
#                                                   #
#####################################################

class AppDispatcher(Dispatcher):
    def __call__(self, path_info):
        metrics['app_requests_count'].labels(opts['app_name'], path_info).inc()
        print(path_info)
        return Dispatcher.__call__(self, path_info.split('?')[0])

global_config = {
    'global': {
        'server.socket_host'   : opts['host'],
        'server.socket_port'   : opts['port'],
        'engine.autoreload.on' : opts['is_debug']
    }
}

config = {
    '/' : {
        'request.dispatch': AppDispatcher()
    },
    '/static' : {
        'tools.staticdir.on'  : True,
        'tools.staticdir.dir' : consts['static_dir']
    },
    '/doc': {
        'tools.staticdir.on'    : True,
        'tools.staticdir.dir'   : consts['static_dir_doc'],
        'tools.staticdir.index' : consts['index_filename']
    },
    '/favicon.ico': {
        'tools.staticfile.on': True,
        'tools.staticfile.filename': consts['favicon_file']
    }
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
                'conclusion' : modules['notations'][notation].write(arg.conclusion)
            }
            for notation in available_module_names['notations']
        }
        for arg in examples.arguments()
    }
}

base_view_data = {
    'operators_list'      : logic.operators_list,
    'logic_modules'       : available_module_names['logics'],
    'logics'              : modules['logics'],
    'logic_categories'    : logic_categories,
    'writer_modules'      : available_module_names['writers'],
    'writers'             : modules['writers'],
    'notation_modules'    : available_module_names['notations'],
    'notations'           : modules['notations'],
    'system_predicates'   : logic.system_predicates,
    'quantifiers'         : logic.quantifiers_list,
    'example_args_list'   : examples.args_list,
    'browser_json'        : json.dumps(browser_data, indent=2),
    'version'             : logic.version,
    'copyright'           : logic.copyright,
    'source_href'         : logic.source_href,
    'is_debug'            : opts['is_debug'],
    'is_google_analytics' : not not opts['google_analytics_id'],
    'google_analytics_id' : opts['google_analytics_id'],
}

#####################################################
#                                                   #
# Templates                                         #
#                                                   #
#####################################################

jinja_env = Environment(loader=FileSystemLoader(consts['view_path']))
template_cache = dict()

def get_template(view):
    if opts['is_debug'] or (view not in template_cache):
        template_cache[view] = jinja_env.get_template(view + '.html')
    return template_cache[view]

def render(view, data={}):
    raw_html = get_template(view).render(data)
    return raw_html

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
                result['tableau']['body'] = result['tableau']['body'][0:255] + '...'
    return result

class RequestDataError(Exception):

    def __init__(self, errors):
        self.errors = errors

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
                        'result'  : result
                    }
            except ProofTimeoutError as err: # pragma: no cover
                server.response.statis = 408
                return {
                    'status'  : 408,
                    'message' : str(err),
                    'error'   : err.__class__.__name__
                }
            except RequestDataError as err:
                server.response.status = 400
                return {
                    'status'  : 400,
                    'message' : 'Request data errors',
                    'error'   : err.__class__.__name__,
                    'errors'  : err.errors
                }
            except Exception as err: # pragma: no cover
                server.response.status = 500
                return {
                    'status'  : 500,
                    'message' : str(err),
                    'error'   : err.__class__.__name__
                }
                traceback.print_exc()
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
                    'html'   : modules['notations'][notation].write(sentence, 'html')
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
                    'premises': [sw.write(premise) for premise in arg.premises],
                    'conclusion': sw.write(arg.conclusion)
                },
                'valid': proof.valid,
                'header': proof_writer.document_header(),
                'footer': proof_writer.document_footer(),
                'body': proof_writer.write(proof, sw=sw),
                'stats': proof.stats,
                'result': proof.stats['result'],
                'writer': {
                    'name': proof_writer.name,
                    'format': odata['format'],
                    'symbol_set': odata['symbol_set'],
                    'options': proof_writer.defaults
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
            parser = notation.Parser(vocabulary=vocab)
            i = 1
            premises = []
            for premise in adata['premises']:
                try:
                    premises.append(parser.parse(premise))
                except Exception as e:
                    premises.append(None)
                    errors['Premise ' + str(i)] = str(e)
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
                errors['Predicate ' + str(i)] = str(e)
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
    print("Staring metrics on port", opts['metrics_port'])
    prom.start_http_server(opts['metrics_port'])
    server.config.update(global_config)
    server.quickstart(App(), '/', config)

if  __name__ == '__main__': # pragma: no cover
    main()