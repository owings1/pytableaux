# pytableaux, a multi-logic proof generator.
# Copyright (C) 2014-2023 Doug Owings.
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
from __future__ import annotations

from urllib.parse import urlencode

import cherrypy
import pytest
import simplejson as json
from cherrypy.test import helper

from pytableaux.errors import *
from pytableaux.web import util
from pytableaux.web.application import WebApp


def test_instantiate():
    app = WebApp()

# see https://docs.cherrypy.org/en/latest/tutorials.html#tutorial-12-using-pytest-and-code-coverage
class AppTest(helper.CPWebCase):

    def post_json(self, page, data):
        body = json.dumps(data)
        headers = [
            ('Content-type', 'application/json'),
            ('Content-Length', str(len(body)))
        ]
        res_raw = self.getPage(page, headers, 'POST', body)
        res_list = list(res_raw)
        return json.loads(res_list[2])

    def post_form(self, page, data):
        body = urlencode(data)
        headers = [
            ('Content-type', 'application/x-www-form-urlencoded'),
            ('Content-Length', str(len(body)))
        ]
        res_raw = self.getPage(page, headers, 'POST', body)
        res_list = list(res_raw)
        return str(res_list[2])

    @staticmethod
    def setup_server():
        cherrypy.tree.mount(WebApp(), '/', {})

    def test_index_get(self):
        self.getPage('/')
        self.assertStatus('200 OK')

    def test_index_ok_1(self):
        kw = {
            'api-json': json.dumps({
                'argument': {
                    'conclusion': 'a'
                },
                'logic': 'cpl'
            })
        }
        res = self.post_form('/', kw)
        self.assertIn('tableau-wrapper', res)

    def test_index_fail_bad_api_data_1(self):
        kw = {
            'api-json': 'badjson'
        }
        res = self.post_form('/', kw)
        self.assertIn('correct the following errors', res)

    def test_index_fail_bad_arg_1(self):
        kw = {
            'api-json': json.dumps({
                'argument': {
                    'conclusion' : 'asdf'
                },
                'logic': 'cpl'
            })
        }
        res = self.post_form('/', kw)
        self.assertIn('correct the following errors', res)

    def test_api_parse_1(self):
        app = WebApp()
        body = {
            'notation': 'polish',
            'input'   : 'Fm',
            'predicates' : [
               {
                  'name'      : 'is F',
                  'index'     : 0,
                  'subscript' : 0,
                  'arity'     : 1
               }
            ]
        }
        res = app.api_parse(body)
        self.assertIn(res['type'], ('Predicated',))

    def test_api_parse_2(self):
        app = WebApp()
        body = {
            'input': 'a'
        }
        res = app.api_parse(body)
        self.assertIn(res['type'], ('Atomic',))

    def test_api_parse_invalid_notation(self):
        app = WebApp()
        body = {
            'notation': 'nonexistent',
            'input': 'a'
        }
        with pytest.raises(RequestDataError) as exc_info:
            app.api_parse(body)
            self.assertIn('Notation', exc_info.value.errors)

    def test_api_parse_missing_input(self):
        app = WebApp()
        body = {}
        with pytest.raises(RequestDataError) as exc_info:
            app.api_parse(body)
            self.assertIn('Sentence', exc_info.value.errors)

    def test_api_parse_bad_predicate_data(self):
        app = WebApp()
        body = {
            'input': 'a',
            'predicates': [
                {'arity': 'asdf'}
            ]
        }
        with pytest.raises(RequestDataError) as exc_info:
            app.api_parse(body)
            self.assertIn('Predicate 1', exc_info.value.errors)

    def test_api_prove_cpl_addition(self):
        app = WebApp()
        body = {
            'argument': {
                'premises': ['a'],
                'conclusion': 'Aab'
            },
            'logic': 'cpl'
        }
        res = app.api_prove(body)
        self.assertTrue(res[0]['tableau']['valid'])

    def test_api_errors_various(self):
        app = WebApp()
        with pytest.raises(RequestDataError) as exc_info:
            app.api_prove({'logic': 'bunky'})
            self.assertIn('Logic', exc_info.value.errors)
        with pytest.raises(RequestDataError) as exc_info:
            app.api_prove({'output': {'charset': 'bunky'}})
            self.assertIn('Symbol Set', exc_info.value.errors)
        with pytest.raises(RequestDataError) as exc_info:
            app.api_prove({'output': {'notation': 'bunky'}})
            self.assertIn('Output notation', exc_info.value.errors)
        with pytest.raises(RequestDataError) as exc_info:
            app.api_prove({'output': {'format': 'bunky'}})
            self.assertIn('Output format', exc_info.value.errors)
        with pytest.raises(RequestDataError) as exc_info:
            app.api_prove({'max_steps': 'bunky'})
            self.assertIn('Max steps', exc_info.value.errors)
        with pytest.raises(RequestDataError) as exc_info:
            app.api_prove({'argument': {'notation': 'bunky'}})
            self.assertIn('Notation', exc_info.value.errors)
        with pytest.raises(RequestDataError) as exc_info:
            app.api_prove({'argument': {'predicates': [{'arity': 'bunky'}]}})
            self.assertIn('Predicate 1', exc_info.value.errors)
        with pytest.raises(RequestDataError) as exc_info:
            app.api_prove({'argument': {'premises': ['bunky']}})
            self.assertIn('Premise 1', exc_info.value.errors)
        with pytest.raises(RequestDataError) as exc_info:
            app.api_prove({'argument': {'conclusion': 'bunky'}})
            self.assertIn('Conclusion', exc_info.value.errors)

    def test_post_api_prove_1(self):
        body = {
            'argument': {
                'premises': ['a'],
                'conclusion': 'Aab'
            },
            'logic': 'cpl'
        }
        res = self.post_json('/api/prove', body)
        self.assertEqual(res['message'], 'OK')

    def test_post_api_prove_400_1(self):
        body = {
            'argument': {
                'conclusion': 'bunky'
            },
            'logic': 'cpl'
        }
        res = self.post_json('/api/prove', body)
        self.assertEqual(res['status'], 400)

    def test_post_api_parse_1(self):
        body = {
            'input': 'a'
        }
        res = self.post_json('/api/parse', body)
        self.assertIn(res['result']['type'], ('Atomic',))

    def test_post_api_404_1(self):
        body = {}
        res = self.post_json('/api/bunky', body)
        self.assertEqual(res['status'], 404)

    def test_fix_form_data_braces_1(self):
        form_data = {
            'test[]': 'a'
        }
        res = util.fix_uri_req_data(form_data)
        self.assertIsInstance(res['test[]'], list)
