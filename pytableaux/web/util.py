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
pytableaux.web.util
^^^^^^^^^^^^^^

"""
from __future__ import annotations

from typing import Any, Mapping, Sequence

import simplejson as json

from pytableaux.errors import Emsg
from pytableaux.lang import Lexical


def json_default(obj: Any):
    if isinstance(obj, Lexical):
        return obj.ident
    if isinstance(obj, Mapping):
        if callable(asdict := getattr(obj, '_asdict', None)):
            return asdict()
        return dict(obj)
    if isinstance(obj, Sequence):
        return list(obj)
    if isinstance(obj, Exception):
        return errstr(obj)
    raise Emsg.CantJsonify(obj)

tojson_defaults = dict(
    cls = json.JSONEncoderForHTML,
    namedtuple_as_object = False,
    for_json = True,
    default = json_default)

def tojson(*args, **kw):
    "Wrapper for ``json.dumps`` with html safe encoder and other defaults."
    return json.dumps(*args, **(tojson_defaults | kw))

def fix_uri_req_data(form_data: Mapping[str, Any]) -> dict[str, Any]:
    "Transform param names ending in ``'[]'`` to lists."
    form_data = dict(form_data)
    for param in form_data:
        if param.endswith('[]'):
            if isinstance(value := form_data[param], str):
                form_data[param] = [value]
    return form_data

def errstr(err: Exception|str) -> str:
    if isinstance(err, Exception):
        return f'{type(err).__name__}: {err}'
    return err