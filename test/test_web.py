# pytableaux, a multi-logic proof generator.
# Copyright (C) 2014-2021 Doug Owings.
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
import json
from cherrypy.test import helper
from urllib.parse import urlencode
def test_instantiate():
    app = web.App()

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
        cherrypy.tree.mount(web.App(), '/', {})

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
        assert 'tableau-wrapper' in res

    def test_index_fail_bad_api_data_1(self):
        kw = {
            'api-json': 'badjson'
        }
        res = self.post_form('/', kw)
        assert 'correct the following errors' in res

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
        assert 'correct the following errors' in res

    def test_api_parse_1(self):
        app = web.App()
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
        assert res['type'] in ('Predicated',)

    def test_api_parse_2(self):
        app = web.App()
        body = {
            'input': 'a'
        }
        res = app.api_parse(body)
        assert res['type'] in ('Atomic',)

    def test_api_parse_invalid_notation(self):
        app = web.App()
        body = {
            'notation': 'nonexistent',
            'input': 'a'
        }
        with pytest.raises(web.RequestDataError) as exc_info:
            app.api_parse(body)
            assert 'Notation' in exc_info.value.errors

    def test_api_parse_missing_input(self):
        app = web.App()
        body = {}
        with pytest.raises(web.RequestDataError) as exc_info:
            app.api_parse(body)
            assert 'Sentence' in exc_info.value.errors

    def test_api_parse_bad_predicate_data(self):
        app = web.App()
        body = {
            'input': 'a',
            'predicates': [
                {'arity': 'asdf'}
            ]
        }
        with pytest.raises(web.RequestDataError) as exc_info:
            app.api_parse(body)
            assert 'Predicate 1' in exc_info.value.errors

    def test_api_prove_cpl_addition(self):
        app = web.App()
        body = {
            'argument': {
                'premises': ['a'],
                'conclusion': 'Aab'
            },
            'logic': 'cpl'
        }
        res = app.api_prove(body)
        assert res[0]['tableau']['valid']

    def test_api_errors_various(self):
        app = web.App()
        with pytest.raises(web.RequestDataError) as exc_info:
            app.api_prove({'logic': 'bunky'})
            assert 'Logic' in exc_info.value.errors
        with pytest.raises(web.RequestDataError) as exc_info:
            app.api_prove({'output': {'symbol_enc': 'bunky'}})
            assert 'Symbol Set' in exc_info.value.errors
        with pytest.raises(web.RequestDataError) as exc_info:
            app.api_prove({'output': {'notation': 'bunky'}})
            assert 'Output notation' in exc_info.value.errors
        with pytest.raises(web.RequestDataError) as exc_info:
            app.api_prove({'output': {'format': 'bunky'}})
            assert 'Output format' in exc_info.value.errors
        with pytest.raises(web.RequestDataError) as exc_info:
            app.api_prove({'max_steps': 'bunky'})
            assert 'Max steps' in exc_info.value.errors
        with pytest.raises(web.RequestDataError) as exc_info:
            app.api_prove({'argument': {'notation': 'bunky'}})
            assert 'Notation' in exc_info.value.errors
        with pytest.raises(web.RequestDataError) as exc_info:
            app.api_prove({'argument': {'predicates': [{'arity': 'bunky'}]}})
            assert 'Predicate 1' in exc_info.value.errors
        with pytest.raises(web.RequestDataError) as exc_info:
            app.api_prove({'argument': {'premises': ['bunky']}})
            assert 'Premise 1' in exc_info.value.errors
        with pytest.raises(web.RequestDataError) as exc_info:
            app.api_prove({'argument': {'conclusion': 'bunky'}})
            assert 'Conclusion' in exc_info.value.errors

    def test_post_api_prove_1(self):
        body = {
            'argument': {
                'premises': ['a'],
                'conclusion': 'Aab'
            },
            'logic': 'cpl'
        }
        res = self.post_json('/api/prove', body)
        assert res['message'] == 'OK'

    def test_post_api_prove_400_1(self):
        body = {
            'argument': {
                'conclusion': 'bunky'
            },
            'logic': 'cpl'
        }
        res = self.post_json('/api/prove', body)
        assert res['status'] == 400

    def test_post_api_parse_1(self):
        body = {
            'input': 'a'
        }
        res = self.post_json('/api/parse', body)
        assert res['result']['type'] in ('Atomic',)

    def test_post_api_404_1(self):
        body = {}
        res = self.post_json('/api/bunky', body)
        assert res['status'] == 404

    def test_fix_form_data_braces_1(self):
        form_data = {
            'test[]': 'a'
        }
        res = web.fix_form_data(form_data)
        assert isinstance(res['test[]'], list)