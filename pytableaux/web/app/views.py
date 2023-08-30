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
"""
pytableaux.web.app.views
^^^^^^^^^^^^^^^^^^^^^^^^

"""
from __future__ import annotations

from datetime import datetime
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from types import MappingProxyType as MapProxy
from typing import Any, Mapping

import simplejson as json

from ... import package
from ...lang import LexWriter, Notation
from .. import api
from ..mail import is_valid_email
from ..util import tojson
from ..views import FormView, JsonView

__all__ = (
    'FeedbackView',
    'HealthView',
    'ProveView')

class HealthView(JsonView):

    def GET(self):
        return dict(status=self.status)

class ProveView(FormView):

    form_defaults: Mapping[str, Any] = MapProxy(dict(
        input_notation = Notation.standard.name,
        output_format = 'html',
        output_notation = Notation.standard.name,
        show_controls = True,
        build_models = True,
        color_open = True,
        writer_registry = 'default',
        rank_optimizations = True,
        group_optimizations = True))

    @property
    def api(self) -> api.ProveView:
        return self.app.api.prove

    @property
    def errors(self) -> dict:
        return self.api.errors

    @errors.setter
    def errors(self, errors: dict):
        self.api.errors = errors

    @property
    def tableau(self):
        return self.api.tableau

    @property
    def is_proof(self) -> bool:
        return not self.errors and bool(self.resp_data)

    @property
    def pw(self):
        return self.api.pw
    
    @property
    def lw(self):
        return self.pw and self.pw.lw

    def setup(self):
        super().setup()
        self.template = f'prove/main'
        self.resp_data = None
        self.is_controls = False
        self.is_models = False
        self.is_color = False
        self.selected_tab = 'input'
        self.api_payload = None
        self.lw_for_argument = None

    def validate_form(self, form_data):
        try:
            self.api_payload = self.api.Payload(json.loads(form_data['api-json']))
        except Exception as err:
            return {'api-json': err}
        return True

    def GET(self):
        self.api.setup(None)
        return super().GET()

    def POST(self):
        if not self.validate():
            return
        self.api_payload['output:attachments'] = True
        if self.api_payload.get('output:format') == 'latex':
            self.api_payload.setdefault('output:options:fulldoc', True)
        self.api.setup(self.api_payload)
        try:
            self.resp_data = self.api.POST()
        except Exception as err:
            self.errors['tableau'] = err
        if not self.is_proof:
            return
        try:
            argtitle = self.app.example_args_rev[self.tableau.argument]
        except KeyError:
            pass
        else:
            self.form_data['example_argument'] = argtitle
        if self.pw.format == 'html':
            self.is_controls = bool(self.kw.get('show_controls'))
            self.is_models = bool(
                self.kw.get('build_models') and
                self.tableau.invalid)
            self.is_color = bool(self.kw.get('color_open'))
            self.selected_tab = 'view'
        else:
            self.selected_tab = False # 'stats'
        if self.lw.format in ('html', 'text') and self.lw.strings.dialect in ('html', 'ascii', 'unicode'):
            self.lw_for_argument = self.lw
        else:
            # For the argument display, so we don't end up writing latex sequences.
            self.lw_for_argument = LexWriter(self.lw.notation, 'html', **self.lw.opts)

    def finish_context(self):
        super().finish_context()
        page_data = dict(
            is_debug     = self.is_debug,
            is_proof     = self.is_proof,
            is_controls  = self.is_controls,
            is_models    = self.is_models,
            is_color     = self.is_color,
            selected_tab = self.selected_tab)
        if self.is_debug:
            self.debugs.extend(dict(
                req_data  = self.kw,
                form_data = self.form_data,
                api_payload = self.api_payload,
                resp_data = self.trim_resp_debug(self.resp_data),
                page_data = page_data).items())
        self.context.update(page_data,
            tableau = self.tableau,
            lw = self.lw,
            lw_for_argument = self.lw_for_argument,
            page_json = self.app.tojson(page_data),
            form_data = self.form_data,
            resp_data = self.resp_data)

    @staticmethod
    def trim_resp_debug(resp_data: dict) -> dict:
        "Trim data for debug logging."
        if not resp_data:
            return resp_data
        result = dict(resp_data)
        if 'tableau' in result and 'body' in result['tableau']:
            if len(result['tableau']['body']) > 255:
                result['tableau'] = dict(result['tableau'])
                result['tableau']['body'] = '{0}...'.format(
                    result['tableau']['body'][0:255])
        return result

class FeedbackView(FormView):

    @property
    def exposed(self) -> bool:
        return self.config['feedback_enabled'] and self.mailroom.enabled

    @property
    def mailroom(self):
        return self.app.mailroom

    def setup(self):
        super().setup()
        self.template = 'feedback'
        self.is_submitted = False

    def GET(self):
        if not self.mailroom.last_was_success:
            self.warns['mailroom'] = (
                'The most recent email was unsuccessful. '
                'You might want to send an email instead.')

    def validate_form(self, form):
        "Validate `name`, `email`, and `message` keys."
        errs = {}
        if not is_valid_email(form['email']):
            errs['email'] = 'Invalid email address'
        if not form['name']:
            errs['name'] = 'Please enter your name'
        if not form['message']:
            errs['message'] = 'Please enter a message'
        return errs or True
    
    def POST(self):
        if not self.validate():
            return
        date = datetime.now()
        context = dict(
            date = str(date),
            ip = self.request.remote.ip,
            headers = self.request.headers,
            form_data = self.form_data)
        from_addr = self.config['feedback_from_address']
        from_name = self.form_data['name']
        to_addr = self.config['feedback_to_address']
        msg = MIMEMultipart('alternative')
        msg['To'] = to_addr
        msg['From'] = f"{package.name} Feedback <{from_addr}>"
        msg['Subject'] = f'Feedback from {from_name}'
        msg_txt = self.app.render('email/feedback.txt', context)
        msg_html = self.app.render('email/feedback.jinja2', context)
        msg.attach(MIMEText(msg_txt, 'plain'))
        msg.attach(MIMEText(msg_html, 'html'))
        self.mailroom.enqueue(from_addr, (to_addr,), msg.as_string())
        self.is_submitted = True

    def finish_context(self):
        super().finish_context()
        page_data = dict(
            is_debug = self.is_debug,
            is_submitted = self.is_submitted)
        if self.is_debug:
            self.debugs.extend(dict(
                form_data = self.form_data).items())
        self.context.update(page_data,
            form_data = self.form_data,
            page_json = tojson(page_data, indent = self.app.json_indent))
