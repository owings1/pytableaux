# pytableaux, a multi-logic proof generator.
# Copyright (C) 2014-2017 Doug Owings.
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

available_module_names = {
    'logics'    : ['cpl', 'cfol', 'k3', 'k3w', 'l3', 'lp', 'go', 'fde', 'k', 'd', 't', 's4'],
    'notations' : ['standard', 'polish'],
    'writers'   : ['html', 'ascii']
}

import importlib
modules = {}
for package in available_module_names:
    modules[package] = {}
    for name in available_module_names[package]:
        modules[package][name] = importlib.import_module(package + '.' + name)
        
notation_user_predicate_symbols = {}
for notation_name in modules['notations']:
    notation = modules['notations'][notation_name]
    notation_user_predicate_symbols[notation_name] = list(notation.symbol_sets['default'].chars('user_predicate'))

import os.path
current_dir = os.path.dirname(os.path.abspath(__file__))
global_config = {
    'global': {
        'server.socket_host': os.environ['PY_HOST'] if 'PY_HOST' in os.environ else '127.0.0.1',
        'server.socket_port': int(os.environ['PY_PORT']) if 'PY_PORT' in os.environ else 8080
    }
}
config = {
    '/static' : {
        'tools.staticdir.on'  : True,
        'tools.staticdir.dir' : os.path.join(current_dir, 'www', 'static')
    }
}

config['/doc'] = {
    'tools.staticdir.on'    : True,
    'tools.staticdir.dir'   : os.path.join(current_dir, '..', 'doc', '_build', 'html'),
    'tools.staticdir.index' : 'index.html'
}

from jinja2 import Environment, PackageLoader
env = Environment(loader=PackageLoader('logic', 'www/views'))

import cherrypy as server

class App:
                
    @server.expose
    def index(self, *args, **kw):
        App.fix_kw(kw)
        print kw
        data = {
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
        vocabulary = logic.Vocabulary()
        view = 'argument'
        if len(kw) and ('errors' not in kw or not len(kw['errors'])):
            notation = modules['notations'][kw['notation']]
            writer = modules['writers'][kw['writer']].Writer()
            
            errors = {}
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

            try:
                if not isinstance(kw['logic'], list):
                    kw['logic'] = [kw['logic']]
            except:
                errors['Logic'] = Exception('Please select a logic')
                
            if len(errors) > 0:
                kw['errors'] = errors
            else:
                view = 'prove'
                argument = logic.argument(conclusion, premises)
                tableaux = [logic.tableau(modules['logics'][chosen_logic], argument).build() for chosen_logic in kw['logic']]
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
        return env.get_template(view + '.html').render(data)

    # this is a work in progress
    def prove(self, data):
        input_data = {
            'parser' : '',         # standard, polish
            'output' : {
                'formats'    : [], # list of logic names (fde, cfol, etc.)
                'notation'   : '', # optional, default is parser.notation
            },
            'predicates' : {
                'name' : {
                    'index'     : 0,
                    'subscript' : 0,
                    'arity'     : 1
                }
            },
            'argument' : {
                'premises'   : [], # None or missing is allowed
                'conclusion' : ''
            },
            'logics' : []
        }
        output_data = {
            'argument' : {
                'symbol_set' : {
                    'premises'   : [],
                    'conclusion' : ''
                }
            },
            'predicate_strings' : {     # includes system predicates
                'symbol_set' : {
                    'name' : ''
                }
            },
            'predicate_defs' : {            # includes system predicates
                'name' : {
                    'index'     : 0,
                    'subscript' : 0,
                    'arity'     : 1
                }
            },
            'headers' : {
                'format' : ''
            },
            'footers' : {
                'format' : ''
            },
            'proofs' : {
                'logicName' : {
                    'valid' : None,
                    'output' : {
                        'format' : ''
                    }
                }
            }
        }
        return output_data

    @staticmethod
    def fix_kw(kw):
        if len(kw):
            for param in kw:
                if param.endswith('[]'):
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
        
def main():
    server.config.update(global_config)
    server.quickstart(App(), '/', config)

if  __name__ =='__main__':main()