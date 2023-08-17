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

import re
import logging
from typing import Any, Mapping, Sequence

import simplejson as json

from ..errors import Emsg
from ..lang import Lexical

re_email = re.compile(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b')
'Email regex.'

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

def is_valid_email(value: str) -> bool:
    "Whether a string is a valid email address."
    return re_email.fullmatch(value) is not None

def cp_staticdir_conf(path, index='index.html'):
    conf = {
        'tools.staticdir.on': True,
        'tools.staticdir.dir': path,
        'tools.etags.on': True,
        'tools.etags.autotags': True}
    if index:
        conf['tools.staticdir.index'] = index
    return conf

def get_logger(name: str|Any, conf: Mapping[str, Any] = None) -> logging.Logger:
    "Get a logger and configure it for web format."
    if not isinstance(name, str):
        if not isinstance(name, type):
            name = type(name)
        name = name.__qualname__
    logger = logging.Logger(name)
    ch = logging.StreamHandler()
    formatter = logging.Formatter(
        # Similar to cherrypy's format for consistency.
        '[%(asctime)s] %(name)s.%(levelname)s %(message)s',
        datefmt = '%d/%b/%Y:%H:%M:%S')
    ch.setFormatter(formatter)
    logger.addHandler(ch)
    if conf is not None:
        set_conf_loglevel(logger, conf)
    return logger

def set_conf_loglevel(logger: logging.Logger, conf: Mapping[str, Any]):
    "Update a logger's loglevel based on the config."
    if conf['is_debug']:
        logger.setLevel(10)
        logger.info(f'Setting debug loglevel {logger.getEffectiveLevel()}')
        return
    leveluc = conf['loglevel'].upper()
    if not hasattr(logging, leveluc):
        logger.warn(f"Ignoring invalid loglevel '{leveluc}'")
        leveluc = 'INFO'
    levelnum = getattr(logging, leveluc)
    logger.setLevel(levelnum)


def fromjson_hook(obj):
    if isinstance(obj, list):
        return tuple(map(fromjson_hook, obj))
    if isinstance(obj, dict):
        return {key: fromjson_hook(value) for key, value in obj.items()}
    return obj