available_module_names = {
    'logics': ['cpl', 'fde', 'k', 'd', 't', 's4'],
    'notations': ['polish'],
    'writers': ['ascii']
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

import cherrypy as server
class App:
    
    @server.expose
    def index(self, *args, **kw):
        data = {
            'logic_modules': available_module_names['logics'],
            'logics': modules['logics'],
            'writer_modules': available_module_names['writers'],
            'writers': modules['writers'],
            'notation_modules': available_module_names['notations'],
            'notations': modules['notations'],
            'form_data': kw
        }
        if len(kw) and ('errors' not in kw or not len(kw['errors'])):
            import logic
        
            ParseError = logic.Parser.ParseError
        
            notation = modules['notations'][kw['notation']]
            writer = modules['writers'][kw['writer']]
            chosen_logic = modules['logics'][kw['logic']]
        
            try:
                premiseStrs = [premise for premise in kw['premises[]'] if len(premise) > 0]
            except:
                premiseStrs = None
            data['form_data']['premises[]'] = premiseStrs
            parser = notation.Parser()
        
            errors = {}
            premises = []
            i = 1
            for premiseStr in premiseStrs:
                try:
                    premises.append(parser.parse(premiseStr))
                except ParseError as e:
                    errors['Premise ' + str(i)] = e
                i += 1
            try:
                conclusion = parser.parse(kw['conclusion'])
            except ParseError as e:
                errors['Conclusion'] = e
            if len(errors) > 0:
                kw['errors'] = errors
                return self.index(*args, **kw)
            
            argument = logic.argument(conclusion, premises)
            tableau = logic.tableau(chosen_logic, argument).build()

            data.update({
                'tableau': tableau,
                'logic': chosen_logic,
                'notation': notation,
                'writer': writer,
                'argument': {
                    'premises': [notation.write(premise) for premise in argument.premises],
                    'conclusion': notation.write(argument.conclusion)
                }
            })
        
            return self.render('prove', data)
        
        if 'errors' in kw:
            data['errors'] = kw['errors']
        return self.render('argument', data)
            
    def render(self, view, data={}):
        return env.get_template(view + '.html').render(data)
        
def main():
    server.quickstart(App(), '/', config)

if  __name__ =='__main__':main()