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
view_path = 'www/views'

jinja_env = Environment(loader=PackageLoader('logic', view_path))

available_module_names = {
    'logics'    : ['cpl', 'cfol', 'k3', 'k3w', 'b3e', 'l3', 'lp', 'go', 'fde', 'k', 'd', 't', 's4'],
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
    }
}

config['/doc'] = {
    'tools.staticdir.on'    : True,
    'tools.staticdir.dir'   : static_dir_doc,
    'tools.staticdir.index' : index_filename
}

class App(object):
                
    @server.expose
    def index(self, *args, **kw):

        App.fix_kw(kw)

        print(args)
        print(kw)

        data = App.get_base_data(kw)

        vocabulary = logic.Vocabulary()

        view = 'argument'

        if len(kw) and ('errors' not in kw or not len(kw['errors'])):

            notation = modules['notations'][kw['notation']]
            writer = modules['writers'][kw['writer']].Writer()
            
            errors = {}
            if 'user_predicate_arities[]' in kw:
                App.declare_user_predicates(kw, vocabulary, errors)
            parser = notation.Parser(vocabulary)

            try:
                premiseStrs = [premise for premise in kw['premises[]'] if len(premise) > 0]
            except:
                premiseStrs = []

            premises = []
            for i, premiseStr in enumerate(premiseStrs):
                try:
                    premises.append(parser.parse(premiseStr))
                except Exception as e:
                    errors['Premise ' + str(i + 1)] = e
            try:
                conclusion = parser.parse(kw['conclusion'])
            except Exception as e:
                errors['Conclusion'] = e

            if 'symbol_set' in kw:
                symbol_set = kw['symbol_set']
            else:
                if kw['writer'] == 'html' and 'html' in notation.symbol_sets:
                    symbol_set = 'html'
                else:
                    symbol_set = 'default'

            if len(kw['logic']) < 1:
                errors['Logic'] = Exception('Please select a logic')
                
            if len(errors) > 0:
                kw['errors'] = errors
            else:
                view = 'prove'
                argument = logic.argument(conclusion, premises)
                tableaux = [logic.tableau(modules['logics'][kw['logic']], argument).build()]
                sw = notation.Writer(symbol_set)
                data.update({
                    'tableaux'   : tableaux,
                    'notation'   : notation,
                    'sw'         : sw,
                    'writer'     : writer,
                    'argument' : {
                        'premises'   : [sw.write(premise) for premise in argument.premises],
                        'conclusion' : sw.write(argument.conclusion)
                    }
                })
        data.update({
            'user_predicates'      : vocabulary.user_predicates,
            'user_predicates_list' : vocabulary.user_predicates_list
        })
        if 'errors' in kw:
            data['errors'] = kw['errors']
        return self.render(view, data)

    @server.expose
    def parse(self, *args, **kw):
        notation = modules['notations'][kw['notation']]
        vocabulary = logic.Vocabulary()
        errors = {}
        App.declare_user_predicates(kw, vocabulary, errors)
        try:
            logic.parse(kw['sentence'], vocabulary, notation)
        except logic.Parser.ParseError as e:
            return self.render('error', { 'error': e })
        return ''
        
    def render(self, view, data={}):
        return jinja_env.get_template(view + '.html').render(data)

    @staticmethod
    def fix_kw(kw):
        if len(kw):
            for param in kw:
                if param.endswith('[]'):
                    # http://python-future.org/compatible_idioms.html#basestring
                    if isinstance(kw[param], basestring):
                        kw[param] = [kw[param]]

    @staticmethod
    def declare_user_predicates(kw, vocabulary, errors={}):
        App.fix_kw(kw)
        arities = kw['user_predicate_arities[]']
        for i, name in enumerate(kw['user_predicate_names[]']):
            if i < len(arities) and len(arities[i]):
                if len(name):
                    index, subscript = kw['user_predicate_symbols[]'][i].split('.')
                    try:
                        vocabulary.declare_predicate(name, int(index), int(subscript), int(arities[i]))
                    except Exception as e:
                        errors['Predicate ' + str(i + 1)] = e
                else:
                    errors['Predicate ' + str(i + 1)] = Exception('Name cannot be empty')

    @staticmethod
    def get_base_data(kw):
        return {
            'operators_list'     : logic.operators_list,
            'logic_modules'      : available_module_names['logics'],
            'logics'             : modules['logics'],
            'writer_modules'     : available_module_names['writers'],
            'writers'            : modules['writers'],
            'notation_modules'   : available_module_names['notations'],
            'notations'          : modules['notations'],
            'form_data'          : kw,
            'system_predicates'  : logic.system_predicates,
            'quantifiers'        : logic.quantifiers_list,
            'example_args_list'  : examples.args_list,
            'app' : json.dumps({
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
            }, indent=2),
            'version'           : logic.version,
            'copyright'         : logic.copyright,
            'source_href'       : logic.source_href
        }
        
        
def main():
    server.config.update(global_config)
    server.quickstart(App(), '/', config)

if  __name__ == '__main__':
    main()