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
pytableaux.web
^^^^^^^^^^^^^^

"""
from __future__ import annotations

import logging
from typing import TYPE_CHECKING, Any, Mapping

import cherrypy
import cherrypy._cpdispatch
from cherrypy import HTTPError, NotFound
from cherrypy._cprequest import Request, Response

from ..tools import EMPTY_MAP, PathedDict, dmerged
from .util import errstr, fix_uri_req_data

if TYPE_CHECKING:
    from .app import App

__all__ = (
    'FormView',
    'JsonView',
    'TemplateView',
    'View')

NOARG = object()

class View:

    exposed = True
    minargs = 0
    maxargs = 0

    @property
    def request(self) -> Request:
        return cherrypy.request

    @property
    def response(self) -> Response:
        return cherrypy.response

    @property
    def status(self) -> int:
        return self.response.status
    
    @status.setter
    def status(self, status: int) -> None:
        self.response.status = status

    @property
    def app(self) -> App:
        return self.request.app.root

    @property
    def config(self) -> dict:
        return self.app.config

    @property
    def is_debug(self) -> bool:
        return self.app.is_debug

    @property
    def logger(self) -> logging.Logger:
        return self.app.logger
    
    def __call__(self, *args, **kw):
        self.args = args
        self.errors = {}
        handler = self.get_handler(*self.args)
        self.kw = fix_uri_req_data(kw)
        if not callable(handler):
            raise NotFound()
        self.setup()
        return handler(*args)

    def get_handler(self, *args):
        if not (self.minargs <= len(args) <= self.maxargs):
            raise NotFound()
        handler = getattr(self, self.request.method, None)
        if not callable(handler):
            raise HTTPError(405)
        return handler

    def setup(self):
        pass
        # self.errors = {}

@cherrypy.tools.json_in()
class JsonView(View):

    Payload = PathedDict
    payload_defaults: Mapping[str, Any] = EMPTY_MAP
    indent = None

    def __call__(self, *args, **kw):
        self.response.headers['Content-Type'] = 'application/json'
        try:
            reply = self.get_reply(*args, **kw)
        except HTTPError as err:
            self.status = err.status
            reply = dict(message=err.reason, status=self.status)
        return self.encode(reply)

    get_reply = View.__call__

    def tojson(self, *args, **kw) -> str:
        if kw.get('indent', NOARG) is NOARG:
            kw['indent'] = self.indent
        return self.app.tojson(*args, **kw)

    def encode(self, *args, **kw) -> bytes:
        return self.tojson(*args, **kw).encode()

    def setup(self, payload=NOARG):
        super().setup()
        self.status = 200
        if payload is NOARG:
            payload = getattr(self.request, 'json', None)
        if payload is None:
            payload = EMPTY_MAP
        self.payload = self.Payload(dmerged(self.payload_defaults, payload))

class TemplateView(View):

    template: str = ''

    def setup(self):
        super().setup()
        self.warns  = {}
        self.debugs = []
        self.context = dict(
            debugs = self.debugs,
            warns = self.warns)

    def __call__(self, *args, **kw):
        content = super().__call__(*args, **kw)
        if content is None:
            content = self.render()
        return content

    def render(self):
        self.finish_context()
        return self.app.render(self.template, self.context)

    def finish_context(self):
        self.context['errors'] = {key: errstr(value) for key, value in self.errors.items()}
        pass

    def GET(self):
        pass

class FormView(TemplateView):

    form_defaults: Mapping[str, Any] = EMPTY_MAP

    def setup(self):
        super().setup()
        self.form_data = dict(self.form_defaults)
        self.form_data.update(self.kw)

    def validate(self):
        errs = self.validate_form(self.form_data)
        if errs is True:
            return True
        self.errors.update(errs)
        return False
    
    def validate_form(self, form):
        return self.errors or True
