import pytest

import web
import cherrypy
from cherrypy.test import helper

def test_instantiate():
    app = web.App()

# see https://docs.cherrypy.org/en/latest/tutorials.html#tutorial-12-using-pytest-and-code-coverage
class AppTest(helper.CPWebCase):

    @staticmethod
    def setup_server():
        cherrypy.tree.mount(web.App(), '/', {})

    def test_index_get(self):
        self.getPage('/')
        self.assertStatus('200 OK')

    def test_index_trivial_invalid_polish_ascii_cpl(self):
        kw = {
            'notation'   : 'polish',
            'writer'     : 'ascii',
            'logic'      : 'cpl',
            'conclusion' : 'a'
        }
        app = web.App()
        res = app.index(**kw)
