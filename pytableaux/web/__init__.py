# pytableaux, a multi-logic proof generator.
# Copyright (C) 2014-2022 Doug Owings.
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
from typing import Any, Mapping

from pytableaux import package, tools, __docformat__
from enum import auto, Enum
from pytableaux.tools.abcs import ItemMapEnum

__all__ = ()

class Wevent(Enum):
    before_dispatch = auto()

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
        datefmt = '%d/%b/%Y:%H:%M:%S',
    )
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
        leveluc = EnvConfig.loglevel['default'].upper()

    levelnum = getattr(logging, leveluc)
    logger.setLevel(levelnum)

class EnvConfig(ItemMapEnum):

    app_name = dict(
        default = package.name,
        envvar  = 'PT_APPNAME',
        type    = str,
    )
    host = dict(
        default = '127.0.0.1',
        envvar  = 'PT_HOST',
        type    = str,
    )
    port = dict(
        default = 8080,
        envvar  = 'PT_PORT',
        type    = int,
    )
    metrics_port = dict(
        default = 8181,
        envvar  = 'PT_METRICS_PORT',
        type    = int,
    )
    is_debug = dict(
        default = False,
        envvar  = ('PT_DEBUG', 'DEBUG'),
        type    = tools.sbool,
    )
    loglevel = dict(
        default = 'info',
        envvar  = ('PT_LOGLEVEL', 'LOGLEVEL'),
        type    = str,
    )
    maxtimeout = dict(
        default = 30000,
        envvar  = 'PT_MAXTIMEOUT',
        type    = int,
    )
    google_analytics_id = dict(
        default = None,
        envvar  = 'PT_GOOGLE_ANALYTICS_ID',
        type    = str,
    )
    feedback_enabled = dict(
        default = False,
        envvar  = 'PT_FEEDBACK',
        type    = tools.sbool,
    )
    feedback_to_address = dict(
        default = None,
        envvar  = 'PT_FEEDBACK_TOADDRESS',
        type    = str,
    )
    feedback_from_address = dict(
        default = None,
        envvar  = 'PT_FEEDBACK_FROMADDRESS',
        type    = str,
    )
    smtp_host = dict(
        default = None,
        envvar  = ('PT_SMTP_HOST', 'SMTP_HOST'),
        type    = str,
    )
    smtp_port = dict(
        default = 587,
        envvar  = ('PT_SMTP_PORT', 'SMTP_PORT'),
        type    = int,
    )
    smtp_helo = dict(
        default = None,
        envvar  = ('PT_SMTP_HELO', 'SMTP_HELO'),
        type    = str,
    )
    smtp_starttls = dict(
        default = True,
        envvar  = ('PT_SMTP_STARTTLS', 'SMTP_STARTTLS'),
        type    = tools.sbool,
    )
    smtp_tlscertfile = dict(
        default = None,
        envvar  = ('PT_SMTP_TLSCERTFILE', 'SMTP_TLSCERTFILE'),
        type    = str,
    )
    smtp_tlskeyfile = dict(
        default = None,
        envvar  = ('PT_SMTP_TLSKEYFILE', 'SMTP_TLSKEYFILE'),
        type    = str,
    )
    smtp_tlskeypass = dict(
        default = None,
        envvar  = ('PT_SMTP_TLSKEYPASS', 'SMTP_TLSKEYPASS'),
        type    = str,
    )
    smtp_username = dict(
        default = None,
        envvar  = ('PT_SMTP_USERNAME', 'SMTP_USERNAME'),
        type    = str,
    )
    smtp_password = dict(
        default = None,
        envvar  = ('PT_SMTP_PASSWORD', 'SMTP_PASSWORD'),
        type    = str,
    )
    mailroom_interval = dict(
        default = 5,
        envvar  = 'PT_MAILROOM_INTERVAL',
        type    = int,
        min     = 1,
    )
    mailroom_requeue_interval = dict(
        default = 3600,
        envvar  = 'PT_MAILROOM_REQUEUEINTERVAL',
        type    = int,
        min     = 60,
    )

    def __init__(self, m):
        if type(m['envvar']) is str:
            m['envvar'] = m['envvar'],
        super().__init__(m)

    @tools.closure
    def resolve():

        def resolve(self: EnvConfig, env: Mapping[str, Any], /, *, logger = None):
            "Resolve a config value against ``env``."
            if logger is None:
                logger = get_logger(__class__.__qualname__)
            for varname in self['envvar']:
                if varname in env:
                    v = env[varname]
                    break
            else:
                return self['default']

            v = self['type'](v)

            if 'min' in self and v < self['min']:
                v = self['min']
                logger.warning(f'Using min value of {v} for option {self.name}')

            if 'max' in self and v > self['max']:
                v = self['max']
                logger.warning(f'Using max value of {v} for option {self.name}')

            return v

        return resolve

    @classmethod
    def env_config(cls, env: Mapping[str, Any] = None) -> dict[str, Any]:
        "Return a config dict resolve against ``env``."
        if env is None:
            import os
            env = os.environ
        logger = get_logger(__name__)
        return {defn.name: defn.resolve(env, logger = logger) for defn in cls}