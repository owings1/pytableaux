import logic

available_module_names = {
    'logics': ['cfol', 'k3', 'lp', 'go', 'fde', 'k', 'd', 't', 's4'],
    'notations': ['polish'],
    'writers': ['html', 'ascii']
}

import importlib
modules = {}
for package in available_module_names:
    modules[package] = {}
    for name in available_module_names[package]:
        modules[package][name] = importlib.import_module(package + '.' + name)
        
import os.path
current_dir = os.path.dirname(os.path.abspath(__file__))
config = {
    '/static' : {
        'tools.staticdir.on': True,
        'tools.staticdir.dir': os.path.join(current_dir, 'www', 'static')
    }
}

from jinja2 import Environment, PackageLoader
env = Environment(loader=PackageLoader('logic', 'www/views'))

logic.declare_predicate('Predicate 1', 0, 0, 1)
logic.declare_predicate('Predicate 2', 1, 0, 1)
logic.declare_predicate('Predicate 3', 2, 0, 1)
logic.declare_predicate('Predicate 4', 0, 1, 2)
logic.declare_predicate('Predicate 5', 1, 1, 2)
logic.declare_predicate('Predicate 6', 2, 1, 2)

print logic.Vocabulary.predicates
import cherrypy as server

class App:
    
    @server.expose
    def index(self, *args, **kw):
        data = {
            'operators_list': logic.operators_list,
            'logic_modules': available_module_names['logics'],
            'logics': modules['logics'],
            'writer_modules': available_module_names['writers'],
            'writers': modules['writers'],
            'notation_modules': available_module_names['notations'],
            'notations': modules['notations'],
            'form_data': kw,
            'predicates': logic.Vocabulary.predicates
        }
        if len(kw) and ('errors' not in kw or not len(kw['errors'])):
            view = 'prove'
            notation = modules['notations'][kw['notation']]
            writer = modules['writers'][kw['writer']]
            
            try:
                premiseStrs = [premise for premise in kw['premises[]'] if len(premise) > 0]
            except:
                premiseStrs = None
            kw['premises[]'] = premiseStrs
            
            # declare predicates
            
            parser = notation.Parser()
            errors = {}
            premises = []
            i = 1
            for premiseStr in premiseStrs:
                try:
                    premises.append(parser.parse(premiseStr))
                except Exception as e:
                    errors['Premise ' + str(i)] = e
                i += 1
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
                return self.index(*args, **kw)
            
            argument = logic.argument(conclusion, premises)
            tableaux = [logic.tableau(modules['logics'][chosen_logic], argument).build() for chosen_logic in kw['logic']]

            data.update({
                'tableaux': tableaux,
                'notation': notation,
                'writer': writer,
                'argument': {
                    'premises': [notation.write(premise) for premise in argument.premises],
                    'conclusion': notation.write(argument.conclusion)
                }
            })
        else:
            view = 'argument'
        data.update({
            'predicates': logic.Vocabulary.predicates,
            'predicates_list': logic.Vocabulary.predicates_list
        })
        if 'errors' in kw:
            data['errors'] = kw['errors']
        return self.render(view, data)
    
    @server.expose
    def parse(self, *args, **kw):
        notation = modules['notations'][kw['notation']]
        try:
            sentence = notation.Parser().parse(kw['sentence'])
        except logic.Parser.ParseError as e:
            return self.render('error', { 'error': e })
        return ''
        
    def render(self, view, data={}):
        return env.get_template(view + '.html').render(data)
        
def main():
    server.quickstart(App(), '/', config)

if  __name__ =='__main__':main()