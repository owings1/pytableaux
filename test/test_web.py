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
import json
from cherrypy.test import helper

from pytableaux.errors import *
from pytableaux.web.app import App
from pytableaux.web.util import fix_uri_req_data


# see https://docs.cherrypy.org/en/latest/tutorials.html#tutorial-12-using-pytest-and-code-coverage
class AppTest(helper.CPWebCase):

    def post_json(self, page, data):
        self.app
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

    @classmethod
    def setup_server(cls):
        cls.app = App(metrics_enabled=True, feedback_enabled=True)
        cherrypy.tree.mount(cls.app, '/', cls.app.cp_config)

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
        res = self.post_json('/api/parse', body)
        self.assertIn(res['result']['type'], ('Predicated',))

    def test_api_parse_2(self):
        body = {
            'input': 'a'
        }
        res = self.post_json('/api/parse', body)
        self.assertIn(res['result']['type'], ('Atomic',))

    def test_api_parse_invalid_notation(self):
        body = {
            'notation': 'nonexistent',
            'input': 'a'
        }
        res = self.post_json('/api/parse', body)
        self.assertStatus(400)
        self.assertIn('notation', res['errors'])

    def test_api_parse_missing_input(self):
        res = self.post_json('/api/parse', {})
        self.assertStatus(400)
        self.assertIn('input', res['errors'])

    def test_api_parse_bad_predicate_data(self):
        body = {
            'input': 'a',
            'predicates': [
                {'arity': 'asdf'}
            ]
        }
        res = self.post_json('/api/parse', body)
        self.assertStatus(400)
        self.assertIn('predicates:0', res['errors'])

    def test_api_prove_cpl_addition(self):
        body = {
            'argument': {
                'premises': ['a'],
                'conclusion': 'Aab'
            },
            'logic': 'cpl'
        }
        res = self.post_json('/api/prove', body)
        self.assertStatus(200)
        self.assertTrue(res['result']['tableau']['valid'])

    def test_api_errors_various(self):
        res = self.post_json('/api/prove', {'logic': 'bunky'})
        self.assertStatus(400)
        self.assertIn('logic', res['errors'])
        res = self.post_json('/api/prove', {'output': {'format': 'bunky'}})
        self.assertStatus(400)
        self.assertIn('output:format', res['errors'])
        res = self.post_json('/api/prove', {'max_steps': 'bunky'})
        self.assertStatus(400)
        self.assertIn('max_steps', res['errors'])
        res = self.post_json('/api/prove', {'argument': {'notation': 'bunky'}})
        self.assertStatus(400)
        self.assertIn('argument:notation', res['errors'])
        res = self.post_json('/api/prove', {'argument': {'predicates': [{'arity': 'bunky'}]}})
        self.assertStatus(400)
        self.assertIn('argument:predicates:0', res['errors'])
        res = self.post_json('/api/prove', {'argument': {'premises': ['bunky']}})
        self.assertStatus(400)
        self.assertIn('argument:premises:0', res['errors'])
        res = self.post_json('/api/prove', {'argument': {'conclusion': 'bunky'}})
        self.assertStatus(400)
        self.assertIn('argument:conclusion', res['errors'])


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

    def test_post_api_prove_argstr_ok(self):
        body = {
            'argument': 'VxCFxHx:VxCFxGx:VxCGxHx|0.0.1,1.0.1,2.0.1',
            'logic': 'cfol',
        }
        res = self.post_json('/api/prove', body)
        self.assertEqual(res['status'], 200)

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
        res = fix_uri_req_data(form_data)
        self.assertEqual(res['test[]'], ['a'])
