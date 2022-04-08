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
#
# ------------------
#
# pytableaux - Web App Configuration
from __future__ import annotations

__all__ = (
    'APP_ENVCONF',
    'APP_JENV',
    'APP_LOGICS',
    'REGEX_EMAIL',

    'Metric',

    'cp_config',
    'cp_global_config',
    'example_args',
    'output_charsets',
    'logger',
    'logic_categories',
    'parser_nups',
)

import examples
from lexicals import LexType, Notation, LexWriter
from parsers import ParseTable
from tools import closure
from tools.abcs import AbcEnum
from tools.misc import get_logic

from cherrypy._cpdispatch import Dispatcher
from jinja2 import Environment, FileSystemLoader
import logging
import os
import prometheus_client as prom


def _app_path(*args,
    _appdir = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..')
):
    return os.path.join(_appdir, *args)

def _static_path(*args):
    return _app_path('www/static', *args)

_PATHS = dict(
    favicon_file   = _static_path('img/favicon-60x60.png'),
    robotstxt_file = _static_path('robots.txt'),
    static_dir     = _static_path(),
    doc_static_dir = _app_path('..', 'doc/_build/html'),
    view_path      = _app_path('www/views'),
)

# Enabled logics.
APP_LOGICS = {
    k: get_logic(k) for k in (
        'cpl',
        'cfol',
        'fde',
        'k3',
        'k3w',
        'k3wq',
        'b3e',
        'go',
        'mh',
        'l3',
        'g3',
        'p3',
        'lp',
        'nh',
        'rm3',
        'k',
        'd',
        't',
        's4',
        's5',
    )
}

# Web Template path.
APP_JENV = Environment(loader = FileSystemLoader(_PATHS['view_path']))

# Email validation
REGEX_EMAIL = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'

## Option definitions

_OPTDEFS = dict(
    app_name = dict(
        default = 'pytableaux',
        envvar  = 'PT_APPNAME',
        type    = 'string',
    ),
    host = dict(
        default = '127.0.0.1',
        envvar  = 'PT_HOST',
        type    = 'string'
    ),
    port = dict(
        default = 8080,
        envvar  = 'PT_PORT',
        type    = 'int',
    ),
    metrics_port = dict(
        default = 8181,
        envvar  = 'PT_METRICS_PORT',
        type    = 'int',
    ),
    is_debug = dict(
        default = False,
        envvar  = ('PT_DEBUG', 'DEBUG'),
        type    = 'boolean',
    ),
    loglevel = dict(
        default = 'info',
        envvar  = ('PT_LOGLEVEL', 'LOGLEVEL'),
        type    = 'string',
    ),
    maxtimeout = dict(
        default = 30000,
        envvar  = 'PT_MAXTIMEOUT',
        type    = 'int',
    ),
    google_analytics_id = dict(
        default = None,
        envvar  = 'PT_GOOGLE_ANALYTICS_ID',
        type    = 'string',
    ),
    feedback_enabled = dict(
        default = False,
        envvar  = 'PT_FEEDBACK',
        type    = 'boolean',
    ),
    feedback_to_address = dict(
        default = None,
        envvar  = 'PT_FEEDBACK_TOADDRESS',
        type    = 'string',
    ),
    feedback_from_address = dict(
        default = None,
        envvar  = 'PT_FEEDBACK_FROMADDRESS',
        type    = 'string',
    ),
    smtp_host = dict(
        default = None,
        envvar  = ('PT_SMTP_HOST', 'SMTP_HOST'),
        type    = 'string',
    ),
    smtp_port = dict(
        default = 587,
        envvar  = ('PT_SMTP_PORT', 'SMTP_PORT'),
        type    = 'int',
    ),
    smtp_helo = dict(
        default = None,
        envvar  = ('PT_SMTP_HELO', 'SMTP_HELO'),
        type    = 'string',
    ),
    smtp_starttls = dict(
        default = True,
        envvar  = ('PT_SMTP_STARTTLS', 'SMTP_STARTTLS'),
        type    = 'boolean',
    ),
    smtp_tlscertfile = dict(
        default = None,
        envvar  = ('PT_SMTP_TLSCERTFILE', 'SMTP_TLSCERTFILE'),
        type    = 'string',
    ),
    smtp_tlskeyfile = dict(
        default = None,
        envvar  = ('PT_SMTP_TLSKEYFILE', 'SMTP_TLSKEYFILE'),
        type    = 'string',
    ),
    smtp_tlskeypass = dict(
        default = None,
        envvar  = ('PT_SMTP_TLSKEYPASS', 'SMTP_TLSKEYPASS'),
        type    = 'string',
    ),
    smtp_username = dict(
        default = None,
        envvar  = ('PT_SMTP_USERNAME', 'SMTP_USERNAME'),
        type    = 'string',
    ),
    smtp_password = dict(
        default = None,
        envvar  = ('PT_SMTP_PASSWORD', 'SMTP_PASSWORD'),
        type    = 'string',
    ),
    mailroom_interval = dict(
        default = 5,
        envvar  = 'PT_MAILROOM_INTERVAL',
        type    = 'int',
        min     = 1,
    ),
    mailroom_requeue_interval = dict(
        default = 3600,
        envvar  = 'PT_MAILROOM_REQUEUEINTERVAL',
        type    = 'int',
        min     = 60,
    ),
)

## Logging

def _init_logger(logger: logging.Logger):
    ch = logging.StreamHandler()
    formatter = logging.Formatter(
        # Similar to cherrypy's format for consistency.
        '[%(asctime)s] %(name)s.%(levelname)s %(message)s',
        datefmt = '%d/%b/%Y:%H:%M:%S',
    )
    ch.setFormatter(formatter)
    logger.addHandler(ch)
    return logger

logger = _init_logger(logging.Logger('APP'))

## Env Config

def _getoptval(name: str, defn: dict):
    envvars = defn['envvar']
    if type(envvars) is str:
        envvars = envvars,
    for varname in envvars:
        if varname in os.environ:
            v = os.environ[varname]
            break
    else:
        return defn['default']

    defntype = defn.get('type', 'string')

    if defntype == 'int':
        v = int(v)
    elif defntype == 'boolean':
        v = str(v).lower() in ('true', 'yes', '1')
    elif defntype == 'string':
        v = str(v)
    else:
        raise NotImplementedError(defntype)

    if 'min' in defn and v < defn['min']:
        v = defn['min']
        logger.warn(
            'Using min value of %s for option %s' % (v, name)
        )
    if 'max' in defn and v > defn['max']:
        v = defn['max']
        logger.warn(
            'Using max value of %s for option %s' % (v, name)
        )

    return v

APP_ENVCONF = {
    name: _getoptval(name, defn)
    for name, defn in _OPTDEFS.items()
}

@closure
def _():

    # Set loglevel from APP_ENVCONF

    if APP_ENVCONF['is_debug']:
        logger.setLevel(10)
        logger.info('Setting debug loglevel %d' % logger.getEffectiveLevel())
        return

    leveluc = APP_ENVCONF['loglevel'].upper()

    if not hasattr(logging, leveluc):
        logger.warn("Ignoring invalid loglevel '%s'" % leveluc)
        APP_ENVCONF['loglevel'] = _OPTDEFS['loglevel']['default']
        leveluc = APP_ENVCONF['loglevel'].upper()

    levelnum = getattr(logging, leveluc)
    logger.setLevel(levelnum)

## Prometheus Metrics

class Metric(AbcEnum):

    value: prom.metrics.MetricWrapperBase

    app_requests_count = prom.Counter(
        'app_requests_count',
        'total app http requests',
        ['app_name', 'endpoint'],
    )
    proofs_completed_count = prom.Counter(
        'proofs_completed_count',
        'total proofs completed',
        ['app_name', 'logic', 'result'],
    )
    proofs_inprogress_count = prom.Gauge(
        'proofs_inprogress_count',
        'total proofs in progress',
        ['app_name', 'logic'],
    )
    proofs_execution_time = prom.Summary(
        'proofs_execution_time',
        'total proof execution time',
        ['app_name', 'logic'],
    )

    def __call__(self, *labels: str) -> prom.metrics.MetricWrapperBase:
        return self.value.labels(APP_ENVCONF['app_name'], *labels)

## Cherrypy config

cp_global_config = {
    'global': {
        'server.socket_host'   : APP_ENVCONF['host'],
        'server.socket_port'   : APP_ENVCONF['port'],
        'engine.autoreload.on' : APP_ENVCONF['is_debug'],
    },
}

class _AppDispatcher(Dispatcher):
    def __call__(self, path_info: str):
        Metric.app_requests_count(path_info).inc()
        return super().__call__(path_info.split('?')[0])

cp_config = {
    '/': {
        'request.dispatch': _AppDispatcher(),
    },
    '/static': {
        'tools.staticdir.on'  : True,
        'tools.staticdir.dir' : _PATHS['static_dir'],
    },
    '/doc': {
        'tools.staticdir.on'    : True,
        'tools.staticdir.dir'   : _PATHS['doc_static_dir'],
        'tools.staticdir.index' : 'index.html',
    },
    '/favicon.ico': {
        'tools.staticfile.on'       : True,
        'tools.staticfile.filename' : _PATHS['favicon_file'],
    },
    '/robots.txt': {
        'tools.staticfile.on'       : True,
        'tools.staticfile.filename' : _PATHS['robotstxt_file'],
    },
}

## Static Data

# Rendered example arguments
example_args = {
    arg.title : {
        notn.name: dict(
            premises = tuple(map(lw, arg.premises)),
            conclusion = lw(arg.conclusion),
        )
        for notn, lw in (
            (notn, LexWriter(notn, charset = 'ascii'))
            for notn in Notation
        )
    }
    for arg in examples.arguments()
}

# Predicate symbols
parser_nups = {
    notn.name: ParseTable.fetch(notn).chars[LexType.Predicate]
    for notn in Notation
}

# Logic category groupings.
logic_categories: dict[str, list[str]] = {}

@closure
def _():

    for modname, logic in APP_LOGICS.items():
        category = logic.Meta.category
        if category not in logic_categories:
            logic_categories[category] = []
        logic_categories[category].append(modname)

    def get_category_order(modname: str) -> int:
        return APP_LOGICS[modname].Meta.category_order

    for group in logic_categories.values():
        group.sort(key = get_category_order)

# For notn, only include those common to all, until UI suports
# notn-specific choice.

def _get_common_charsets():
    charsets: set[str] = set(
        charset
        for notn in Notation
            for charset in notn.charsets
    )
    for notn in Notation:
        charsets = charsets.intersection(notn.charsets)
    return sorted(charsets)

output_charsets = _get_common_charsets()

## Cleanup

del(
    _OPTDEFS,
    _PATHS,
    _,
    _app_path,
    _init_logger,
    _getoptval,
    _get_common_charsets,
    _static_path,
    get_logic,
    closure,

    _AppDispatcher,
    AbcEnum,
    Dispatcher,
    Environment,
    FileSystemLoader,
    Notation,

    examples,
    logging,
    os,
)