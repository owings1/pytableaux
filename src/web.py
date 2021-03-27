# pytableaux, a multi-logic proof generator.
# Copyright (C) 2014-2020 Doug Owings.
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

import examples, logic, json, os
import importlib
import traceback
import os.path
import cherrypy as server
from jinja2 import Environment, PackageLoader
import prometheus_client

ProofTimeoutError = logic.TableauxSystem.ProofTimeoutError
# http://python-future.org/compatible_idioms.html#basestring
from past.builtins import basestring

default_host = '127.0.0.1'
default_port = 8080
default_metrics_port = 8181
envvar_host = 'PT_HOST'
envvar_port = 'PT_PORT'
envvar_debug = 'PT_DEBUG'
envvar_maxtimeout = 'PT_MAXTIMEOUT'
envvar_ganalytics_id = 'PT_GOOGLE_ANALYTICS_ID'
envvar_metrics_port = 'PT_METRICS_PORT'
index_filename = 'index.html'
default_maxtimeout = 30000

def is_envvar(envvar):
    return envvar in os.environ and len(os.environ[envvar]) > 0

is_debug = is_envvar(envvar_debug)
is_google_analytics = is_envvar(envvar_ganalytics_id)
maxtimeout = int(os.environ[envvar_maxtimeout]) if is_envvar(envvar_maxtimeout) else default_maxtimeout
google_analytics_id = os.environ[envvar_ganalytics_id] if is_google_analytics else None
metrics_port = int(os.environ[envvar_metrics_port]) if is_envvar(envvar_metrics_port) else default_metrics_port

current_dir = os.path.dirname(os.path.abspath(__file__))
static_dir = os.path.join(current_dir, 'www', 'static')
static_dir_doc = os.path.join(current_dir, '..', 'doc', '_build', 'html')
favicon_file = os.path.join(static_dir, 'img/favicon-60x60.png')
view_path = 'www/views'
template_cache = dict()

jinja_env = Environment(loader=PackageLoader('logic', view_path))

available_module_names = {
    'logics'    : ['cpl', 'cfol', 'fde', 'k3', 'k3w', 'k3wq', 'b3e', 'go', 'l3', 'g3', 'p3', 'lp', 'rm3', 'k', 'd', 't', 's4', 's5'],
    'notations' : ['standard', 'polish'],
    'writers'   : ['html', 'ascii']
}

modules = dict()
notation_user_predicate_symbols = dict()
logic_categories = dict()

for package in available_module_names:
    modules[package] = {}
    for name in available_module_names[package]:
        modules[package][name] = importlib.import_module(package + '.' + name)

for notation_name in modules['notations']:
    notation = modules['notations'][notation_name]
    notation_user_predicate_symbols[notation_name] = list(notation.symbol_sets['default'].chars('user_predicate'))

def get_category_order(name):
    return logic.get_logic(name).Meta.category_display_order

for name in modules['logics']:
    lgc = modules['logics'][name]
    if lgc.Meta.category not in logic_categories:
        logic_categories[lgc.Meta.category] = list()
    logic_categories[lgc.Meta.category].append(name)

for category in logic_categories.keys():
    logic_categories[category].sort(key=get_category_order)

global_config = {
    'global': {
        'server.socket_host'   : os.environ[envvar_host] if is_envvar(envvar_host) else default_host,
        'server.socket_port'   : int(os.environ[envvar_port]) if is_envvar(envvar_port) else default_port,
        'engine.autoreload.on' : is_debug
    }
}
config = {
    '/static' : {
        'tools.staticdir.on'  : True,
        'tools.staticdir.dir' : static_dir
    },
    '/doc': {
        'tools.staticdir.on'    : True,
        'tools.staticdir.dir'   : static_dir_doc,
        'tools.staticdir.index' : index_filename
    },
    '/favicon.ico': {
        'tools.staticfile.on': True,
        'tools.staticfile.filename': favicon_file
    }
}

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
    'is_debug'            : is_debug,
    'is_google_analytics' : is_google_analytics,
    'google_analytics_id' : google_analytics_id,
}

def get_template(view):
    if is_debug or (view not in template_cache):
        template_cache[view] = jinja_env.get_template(view + '.html')
    return template_cache[view]

def render(view, data={}):
    raw_html = get_template(view).render(data)
    return raw_html

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

        odata['options']['debug'] = is_debug

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

        proof_opts = {
            'is_rank_optim'  : body['rank_optimizations'],
            'is_group_optim' : body['group_optimizations'],
            'build_timeout'  : maxtimeout,
            'is_build_models': odata['options']['models'],
            'max_steps'      : body['max_steps'],
        }
        proof = logic.tableau(selected_logic, arg, **proof_opts)
        proof.build()

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

def main(): # pragma: no cover
    print("Staring metrics on port", metrics_port)
    prometheus_client.start_http_server(metrics_port)
    server.config.update(global_config)
    server.quickstart(App(), '/', config)

if  __name__ == '__main__': # pragma: no cover
    main()