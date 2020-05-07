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
# pytableaux - web server test cases
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
            'input_notation'  : 'polish',
            'output_notation' : 'polish',
            'format'          : 'ascii',
            'logic'           : 'cpl',
            'conclusion'      : 'a'
        }
        app = web.App()
        res = app.index(**kw)
