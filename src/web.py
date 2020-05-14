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
import os.path
import cherrypy as server
from jinja2 import Environment, PackageLoader

# http://python-future.org/compatible_idioms.html#basestring
from past.builtins import basestring

default_host = '127.0.0.1'
default_port = 8080
envvar_host = 'PY_HOST'
envvar_port = 'PY_PORT'
index_filename = 'index.html'

current_dir = os.path.dirname(os.path.abspath(__file__))
static_dir = os.path.join(current_dir, 'www', 'static')
static_dir_doc = os.path.join(current_dir, '..', 'doc', '_build', 'html')
favicon_file = os.path.join(static_dir, 'img/favicon-96x96.png')
view_path = 'www/views'

jinja_env = Environment(loader=PackageLoader('logic', view_path))

available_module_names = {
    'logics'    : ['cpl', 'cfol', 'k3', 'k3w', 'b3e', 'l3', 'lp', 'rm3', 'go', 'fde', 'k', 'd', 't', 's4'],
    'notations' : ['standard', 'polish'],
    'writers'   : ['html', 'ascii']
}

modules = {}
for package in available_module_names:
    modules[package] = {}
    for name in available_module_names[package]:
        modules[package][name] = importlib.import_module(package + '.' + name)
        
notation_user_predicate_symbols = {}
for notation_name in modules['notations']:
    notation = modules['notations'][notation_name]
    notation_user_predicate_symbols[notation_name] = list(notation.symbol_sets['default'].chars('user_predicate'))

global_config = {
    'global': {
        'server.socket_host': os.environ[envvar_host] if envvar_host in os.environ else default_host,
        'server.socket_port': int(os.environ[envvar_port]) if envvar_port in os.environ else default_port
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
    'operators_list'    : logic.operators_list,
    'logic_modules'     : available_module_names['logics'],
    'logics'            : modules['logics'],
    'writer_modules'    : available_module_names['writers'],
    'writers'           : modules['writers'],
    'notation_modules'  : available_module_names['notations'],
    'notations'         : modules['notations'],
    'system_predicates' : logic.system_predicates,
    'quantifiers'       : logic.quantifiers_list,
    'example_args_list' : examples.args_list,
    'browser_json'      : json.dumps(browser_data, indent=2),
    'version'           : logic.version,
    'copyright'         : logic.copyright,
    'source_href'       : logic.source_href
}

def render(view, data={}):
    raw_html = jinja_env.get_template(view + '.html').render(data)
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

class App(object):
                
    @server.expose
    def index(self, *args, **form_data):

        form_data = fix_form_data(form_data)

        data = dict()

        errors = {}

        vocabulary = logic.Vocabulary()

        view = 'argument'

        if len(form_data):

            input_notation = modules['notations'][form_data['input_notation']]
            output_notation = modules['notations'][form_data['output_notation']]
            writer = modules['writers'][form_data['format']].Writer()

            if 'user_predicate_arities[]' in form_data:
                App.declare_user_predicates(form_data, vocabulary, errors)
            parser = input_notation.Parser(vocabulary)

            try:
                premise_strs = [premise for premise in form_data['premises[]'] if len(premise) > 0]
            except:
                premise_strs = list()

            premises = []
            for i, premise_str in enumerate(premise_strs):
                try:
                    premises.append(parser.parse(premise_str))
                except Exception as e:
                    errors['Premise ' + str(i + 1)] = str(e)
            try:
                conclusion = parser.parse(form_data['conclusion'])
            except Exception as e:
                errors['Conclusion'] = str(e)

            if 'symbol_set' in form_data:
                symbol_set = form_data['symbol_set']
            else:
                if writer.name == 'HTML' and 'html' in output_notation.symbol_sets:
                    symbol_set = 'html'
                else:
                    symbol_set = 'default'

            try:
                sw = output_notation.Writer(symbol_set)
            except Exception as e:
                errors['Symbol Set'] = str(e)

            if len(form_data['logic']) < 1:
                errors['Logic'] = str(Exception('Please select a logic'))
            elif form_data['logic'] not in modules['logics']:
                errors['Logic'] = str(Exception('Invalid logic'))
            else:
                selected_logic = modules['logics'][form_data['logic']]

            if len(errors) == 0:
                view = 'prove'
                argument = logic.argument(conclusion, premises)
                proof = logic.tableau(selected_logic, argument).build()
                data.update({
                    'is_proof'   : True,
                    'tableau'    : proof,
                    'notation'   : notation,
                    'sw'         : sw,
                    'writer'     : writer,
                    'argument' : {
                        'premises'   : [sw.write(premise) for premise in argument.premises],
                        'conclusion' : sw.write(argument.conclusion)
                    }
                })

        data.update(base_view_data)
        data.update({
            'form_data'            : form_data,
            'user_predicates'      : vocabulary.user_predicates,
            'user_predicates_list' : vocabulary.user_predicates_list
        })

        if len(errors) > 0:
            data['errors'] = errors

        return render(view, data)

    @staticmethod
    def declare_user_predicates(form_data, vocabulary, errors={}):
        arities = form_data['user_predicate_arities[]']
        for i, name in enumerate(form_data['user_predicate_names[]']):
            if i < len(arities) and len(arities[i]):
                if len(name):
                    index, subscript = form_data['user_predicate_symbols[]'][i].split('.')
                    try:
                        vocabulary.declare_predicate(name, int(index), int(subscript), int(arities[i]))
                    except Exception as e:
                        errors['Predicate ' + str(i + 1)] = e
                else:
                    errors['Predicate ' + str(i + 1)] = Exception('Name cannot be empty')

    @server.expose
    @server.tools.json_in()
    @server.tools.json_out()
    def api(self, action=None):
        if server.request.method == 'POST':
            try:
                if action == 'parse':
                    result = self.api_parse(server.request.json)
                elif action == 'prove':
                    result = self.api_prove(server.request.json)
                return {
                    'status'  : 200,
                    'message' : 'OK',
                    'result'  : result
                }
            except Exception as err:
                server.response.status = 400
                return {
                    'status'  : 400,
                    'message' : str(err),
                    'error'   : err.__class__.__name__
                }
        server.response.status = 404
        return {'message': 'Not found', 'status': 404}

    def api_parse(self, body):
        """
        Example request body::

            {
               "notation": "polish",
               "input": "Fm",
               "predicates : [
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
               "type": "AtomicSentence",
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
        if 'notation' not in body:
            body['notation'] = 'polish'
        if 'predicates' not in body:
            body['predicates'] = list()
        if 'input' not in body:
            body['input'] = ''
        input_notation = modules['notations'][body['notation']]
        vocab = logic.Vocabulary()
        for pdata in body['predicates']:
            vocab.declare_predicate(**pdata)
        sentence = logic.parse(body['input'], vocab, input_notation)
        return {
            'type'     : sentence.__class__.__name__,
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
                    "options": {}
                }
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
                    "footer": "..."
                }
            }
        """
        body = dict(body)
        if 'output' not in body:
            body['output'] = dict()
        odata = body['output']
        if 'notation' not in odata:
            odata['notation'] = 'standard'
        if 'format' not in odata:
            odata['format'] = 'html'
        if 'symset' not in odata:
            if odata['format'] == 'html':
                odata['symset'] = 'html'
            else:
                odata['symset'] = 'default'
        if 'options' not in odata:
            odata['options'] = dict()
        arg = self.parse_argument_data(body['argument'])
        proof = logic.tableau(body['logic'], arg).build()
        output_notation = modules['notations'][odata['notation']]
        sw = output_notation.Writer(odata['symset'])
        proof_writer = modules['writers'][odata['format']].Writer()
        return {
            'tableau': {
                'logic' : logic.get_logic(body['logic']).name,
                'argument': {
                    'premises': [sw.write(premise) for premise in arg.premises],
                    'conclusion': sw.write(arg.conclusion)
                },
                'valid': proof.valid,
                'header': proof_writer.document_header(),
                'footer': proof_writer.document_footer(),
                'body': proof_writer.write(proof, writer=sw, **odata['options'])
            }
        }

    def parse_argument_data(self, adata):
        adata = dict(adata)
        if 'notation' not in adata:
            adata['notation'] = 'polish'
        if 'predicates' not in adata:
            adata['predicates'] = list()
        if 'premises' not in adata:
            adata['premises'] = list()
        vocab = logic.Vocabulary()
        for pdata in adata['predicates']:
            vocab.declare_predicate(**pdata)
        return logic.argument(vocabulary=vocab, notation=adata['notation'], premises=adata['premises'], conclusion=adata['conclusion'])

def main():
    server.config.update(global_config)
    server.quickstart(App(), '/', config)

if  __name__ == '__main__':
    main()