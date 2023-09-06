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
pytableaux.web.api
^^^^^^^^^^^^^^^^^^

"""
from __future__ import annotations

from cherrypy import HTTPError

from ...errors import ProofTimeoutError
from ...lang import Predicates, TriCoords
from ..views import JsonView

__all__ = (
    'app',
    'App')

class View(JsonView):

    def get_reply(self, *args, **kw) -> dict:
        reply = {}
        try:
            try:
                result = super().get_reply(*args, **kw)
                if result is None:
                    raise HTTPError(400)
                reply['message'] = 'OK'
                reply['result'] = result
            except ProofTimeoutError as err:
                self.status = 408
                raise
            except HTTPError as err:
                self.status = err.status
                reply['message'] = err.reason
                raise
            except Exception as err:
                self.status = 500
                raise
        except Exception as err:
            reply['error'] = type(err).__name__
            self.logger.error(err, exc_info=err)
            if 'message' not in reply:
                reply['message'] = str(err)
        if self.errors:
            reply['errors'] = self.errors
        reply['status'] = self.status
        return reply

    def parse_preds(self, key: str = 'predicates') -> Predicates|None:
        specs = self.payload[key]
        preds = Predicates()
        if not specs:
            return preds
        errors = self.errors
        for i, spec in enumerate(specs):
            try:
                preds.add(TriCoords.make(spec))
            except Exception as err:
                errors[f'{key}:{i}'] = err
        if not errors:
            return preds

from . import views

class App:
    parse = views.ParseView()
    prove = views.ProveView()
    default = View()

app = App()