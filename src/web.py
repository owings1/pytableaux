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

import logic, json

available_module_names = {
    'logics'    : ['cfol', 'k3', 'l3', 'lp', 'go', 'fde', 'k', 'd', 't', 's4'],
    'notations' : ['polish'],
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
    notation_user_predicate_symbols[notation_name] = list(notation.Parser.upchars)
        
import os.path
current_dir = os.path.dirname(os.path.abspath(__file__))
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
            'operators_list'    : logic.operators_list,
            'logic_modules'     : available_module_names['logics'],
            'logics'            : modules['logics'],
            'writer_modules'    : available_module_names['writers'],
            'writers'           : modules['writers'],
            'notation_modules'  : available_module_names['notations'],
            'notations'         : modules['notations'],
            'form_data'         : kw,
            'system_predicates' : logic.system_predicates,
            'quantifiers'       : logic.quantifiers_list,
            'app' : json.dumps({
                'notation_user_predicate_symbols' : notation_user_predicate_symbols,
                'num_predicate_symbols'           : logic.num_predicate_symbols
            }),
            'version'           : logic.version,
            'copyright'         : logic.copyright
        }
        vocabulary = logic.Vocabulary()
        view = 'argument'
        if len(kw) and ('errors' not in kw or not len(kw['errors'])):
            notation = modules['notations'][kw['notation']]
            writer = modules['writers'][kw['writer']]
            
            errors = {}
            App.declare_user_predicates(kw, vocabulary, errors)
            parser = notation.Parser(vocabulary)
                       
            try:
                premiseStrs = [premise for premise in kw['premises[]'] if len(premise) > 0]
            except:
                premiseStrs = None
            kw['premises[]'] = premiseStrs
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
                data.update({
                    'tableaux' : tableaux,
                    'notation' : notation,
                    'writer'   : writer,
                    'argument' : {
                        'premises'   : [notation.write(premise) for premise in argument.premises],
                        'conclusion' : notation.write(argument.conclusion)
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
    server.quickstart(App(), '/', config)

if  __name__ =='__main__':main()