import cherrypy as server

class App:
    
    from jinja2 import Environment, PackageLoader
    env = Environment(loader=PackageLoader('logic', 'www/views'))
    
    @server.expose
    def index(self):
        return self.render('index')
    
    @server.expose
    def prove(self, conclusion=None, premise=None, logic_module=None):
        import logic, importlib
        import notations.polish, writers.ascii
        parser = notations.polish.Parser()
        chosen_logic = importlib.import_module('logics.' + logic_module)
        argument = parser.argument(conclusion, [premise])
        tableau = logic.tableau(chosen_logic, argument).build()
        data = {
            'tableau': tableau,
            'logic': chosen_logic,
            'tableau_ascii': writers.ascii.write(tableau, notations.polish)
        }
        return self.render('prove', data)
        
    def render(self, view, data={}):
        return env.get_template(view + '.html').render(data)
        
def main():
    server.quickstart(App())

if  __name__ =='__main__':main()