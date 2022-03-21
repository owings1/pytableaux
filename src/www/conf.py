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
    'api_defaults',
    'app_modules',
    'cp_config',
    'cp_global_config',
    'example_arguments',
    'form_defaults',
    'lexwriter_encodings',
    'lexwriters',
    'logger',
    'logic_categories',
    'Metric',
    'parser_nups',
    'parser_tables',
    're_email',
)

from tools.abcs import AbcEnum
from tools.decorators import closure
from tools.mappings import MapCover
from tools.misc import get_logic
from parsers import CharTable
from lexicals import LexType, Notation, LexWriter, RenderSet
import examples

import logging, os, os.path
import prometheus_client as prom
from cherrypy._cpdispatch import Dispatcher
from jinja2 import Environment, FileSystemLoader

# Enabled logics.
_LOGICS = (
    'cpl', 'cfol', 'fde', 'k3', 'k3w', 'k3wq', 'b3e', 'go', 'mh',
    'l3', 'g3', 'p3', 'lp', 'nh', 'rm3', 'k', 'd', 't', 's4', 's5'
)

#  Path info
_APP_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..')

def _apath(*args):
    return os.path.join(_APP_DIR, *args)

_PATHS = dict(
    favicon_file   = _apath('www/static/img/favicon-60x60.png'),
    index_filename = 'index.html',
    robotstxt_file = _apath('www/static/robots.txt'),
    static_dir     = _apath('www/static'),
    static_dir_doc = _apath('..', 'doc/_build/html'),
    view_path      = _apath('www/views'),
)

## Option definitions

_OPTDEFS = {
    'app_name' : {
        'default' : 'pytableaux',
        'envvar'  : 'PT_APPNAME',
        'type'    : 'string',
    },
    'host' : {
        'default' : '127.0.0.1',
        'envvar'  : 'PT_HOST',
        'type'    : 'string'
    },
    'port' : {
        'default' : 8080,
        'envvar'  : 'PT_PORT',
        'type'    : 'int',
    },
    'metrics_port' : {
        'default' : 8181,
        'envvar'  : 'PT_METRICS_PORT',
        'type'    : 'int',
    },
    'is_debug' : {
        'default' : False,
        'envvar'  : ('PT_DEBUG', 'DEBUG'),
        'type'    : 'boolean',
    },
    'loglevel': {
        'default' : 'info',
        'envvar'  : ('PT_LOGLEVEL', 'LOGLEVEL'),
        'type'    : 'string',
    },
    'maxtimeout' : {
        'default' : 30000,
        'envvar'  : 'PT_MAXTIMEOUT',
        'type'    : 'int',
    },
    'google_analytics_id' : {
        'default' : None,
        'envvar'  : 'PT_GOOGLE_ANALYTICS_ID',
        'type'    : 'string',
    },
    'feedback_enabled': {
        'default' : False,
        'envvar'  : 'PT_FEEDBACK',
        'type'    : 'boolean',
    },
    'feedback_to_address': {
        'default' : None,
        'envvar'  : 'PT_FEEDBACK_TOADDRESS',
        'type'    : 'string',
    },
    'feedback_from_address': {
        'default'  : None,
        'envvar'  : 'PT_FEEDBACK_FROMADDRESS',
        'type'    : 'string',
    },
    'smtp_host': {
        'default' : None,
        'envvar'  : ('PT_SMTP_HOST', 'SMTP_HOST'),
        'type'    : 'string',
    },
    'smtp_port': {
        'default' : 587,
        'envvar'  : ('PT_SMTP_PORT', 'SMTP_PORT'),
        'type'    : 'int',
    },
    'smtp_helo': {
        'default' : None,
        'envvar'  : ('PT_SMTP_HELO', 'SMTP_HELO'),
        'type'    : 'string',
    },
    'smtp_starttls': {
        'default' : True,
        'envvar'  : ('PT_SMTP_STARTTLS', 'SMTP_STARTTLS'),
        'type'    : 'boolean',
    },
    'smtp_tlscertfile': {
        'default' : None,
        'envvar'  : ('PT_SMTP_TLSCERTFILE', 'SMTP_TLSCERTFILE'),
        'type'    : 'string',
    },
    'smtp_tlskeyfile': {
        'default' : None,
        'envvar'  : ('PT_SMTP_TLSKEYFILE', 'SMTP_TLSKEYFILE'),
        'type'    : 'string',
    },
    'smtp_tlskeypass': {
        'default' : None,
        'envvar'  : ('PT_SMTP_TLSKEYPASS', 'SMTP_TLSKEYPASS'),
        'type'    : 'string',
    },
    'smtp_username': {
        'default' : None,
        'envvar'  : ('PT_SMTP_USERNAME', 'SMTP_USERNAME'),
        'type'    : 'string',
    },
    'smtp_password': {
        'default' : None,
        'envvar'  : ('PT_SMTP_PASSWORD', 'SMTP_PASSWORD'),
        'type'    : 'string',
    },
    'mailroom_interval': {
        'default' : 5,
        'envvar'  : 'PT_MAILROOM_INTERVAL',
        'type'    : 'int',
        'min'     : 1,
    },
    'mailroom_requeue_interval': {
        'default' : 3600,
        'envvar'  : 'PT_MAILROOM_REQUEUEINTERVAL',
        'type'    : 'int',
        'min'     : 60,
    },
}


logic_categories: dict[str, list[str]] = dict()

app_modules = dict(
    logics = {k: get_logic(k) for k in _LOGICS}
)

# 'nups' means "notation-user-predicate-symbols"
parser_nups = {}
parser_tables = {}
example_arguments = {}

@closure
def _():
    
    exargs = examples.arguments()
    for arg in exargs:
        example_arguments[arg.title] = {}
    for notn in Notation:
        # Build rendered example arguments
        lw = LexWriter(notn, enc = 'ascii')
        for arg in exargs:
            example_arguments[arg.title][notn.name] = dict(
                premises = tuple(map(lw, arg.premises)),
                conclusion = lw(arg.conclusion),
            )
        parser_tables[notn.name] = table = CharTable.fetch(notn)
        parser_nups[notn.name] = table.chars[LexType.Predicate]

    for modname, logic in app_modules['logics'].items():
        category = logic.Meta.category
        if category not in logic_categories:
            logic_categories[category] = []
        logic_categories[category].append(modname)

    def get_category_order(modname: str) -> int:
        return app_modules['logics'][modname].Meta.category_display_order

    for group in logic_categories.values():
        group.sort(key = get_category_order)


## Logging

def _init_logger(logger: logging.Logger):
    ch = logging.StreamHandler()
    formatter = logging.Formatter(
        # Similar to cherrypy's format for consistency.
        '[%(asctime)s] %(name)s.%(levelname)s %(message)s',
        datefmt='%d/%b/%Y:%H:%M:%S',
    )
    ch.setFormatter(formatter)
    logger.addHandler(ch)
    return logger

logger = _init_logger(logging.Logger('APP'))

## Env Config

def _getoptval(name):
    defn = _OPTDEFS[name]
    evtype = type(defn['envvar'])
    if evtype == str:
        envvars = (defn['envvar'],)
    else:
        envvars = defn['envvar']
    for varname in envvars:
        if varname in os.environ:
            v = os.environ[varname]
            if defn['type'] == 'int':
                v = int(v)
                if 'min' in defn and v < defn['min']:
                    logger.warn(
                        'Using min value of {0} for option {1}'.format(
                            str(defn['min']), name
                        )
                    )
                    v = defn['min']
                if 'max' in defn and v > defn['max']:
                    logger.warn(
                        'Using max value of {0} for option {1}'.format(
                            str(defn['max']), name
                        )
                    )
                        
            elif defn['type'] == 'boolean':
                v = str(v).lower() in ('true', 'yes', '1')
            else:
                # string
                v = str(v)
            return v
    return defn['default']

APP_ENVCONF = {
    name: _getoptval(name) for name in _OPTDEFS.keys()
}

# Set loglevel from APP_ENVCONF
if APP_ENVCONF['is_debug']:
    logger.setLevel(10)
    logger.info('Setting debug loglevel {0}'.format(str(logger.getEffectiveLevel())))
elif hasattr(logging, APP_ENVCONF['loglevel'].upper()):
    logger.setLevel(getattr(logging, APP_ENVCONF['loglevel'].upper()))
else:
    logger.setLevel(getattr(logging, _OPTDEFS['loglevel']['default'].upper()))
    logger.warn('Ingoring invalid loglevel: {0}'.format(APP_ENVCONF['loglevel']))
    APP_ENVCONF['loglevel'] = _OPTDEFS['loglevel']['default'].upper()

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

# Util

re_email = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'

## cherrypy global config
cp_global_config = {
    'global': {
        'server.socket_host'   : APP_ENVCONF['host'],
        'server.socket_port'   : APP_ENVCONF['port'],
        'engine.autoreload.on' : APP_ENVCONF['is_debug'],
    },
}



# Jinja2

APP_JENV = Environment(loader = FileSystemLoader(_PATHS['view_path']))

##############################
## Cherrypy Server Config   ##
##############################

class _AppDispatcher(Dispatcher):
    def __call__(self, path_info: str):
        Metric.app_requests_count(path_info).inc()
        return super().__call__(path_info.split('?')[0])

cp_config = {
    '/' : {
        'request.dispatch': _AppDispatcher(),
    },
    '/static' : {
        'tools.staticdir.on'  : True,
        'tools.staticdir.dir' : _PATHS['static_dir'],
    },
    '/doc': {
        'tools.staticdir.on'    : True,
        'tools.staticdir.dir'   : _PATHS['static_dir_doc'],
        'tools.staticdir.index' : _PATHS['index_filename'],
    },
    '/favicon.ico': {
        'tools.staticfile.on': True,
        'tools.staticfile.filename': _PATHS['favicon_file'],
    },
    '/robots.txt': {
        'tools.staticfile.on': True,
        'tools.staticfile.filename': _PATHS['robotstxt_file'],
    },
}

#####################
## Static Data     ##
#####################
# For notn, only include those common to all, until UI suports
# notn-specific choice.
def _():
    encs_map = {
        notn.name: RenderSet.available(notn)
        for notn in Notation
    }
    enc = set(enc for encs in encs_map.values() for enc in encs)
    for notn in Notation:
        enc = enc.intersection(RenderSet.available(notn))
    return sorted(enc)

lexwriter_encodings = _()

########################
## Static LexWriters  ##
########################
lexwriters = {
    notn.name: {
        enc: LexWriter(notn, enc=enc)
        for enc in RenderSet.available(notn)
    }
    for notn in Notation 
}

#####################
## Input Defaults  ##
#####################
api_defaults = MapCover(dict(
    input_notation  = 'polish',
    output_notation = 'polish',
    output_format   = 'html',
))
form_defaults = MapCover({
    'input_notation'  : 'standard',
    'format'          : 'html',
    'output_notation' : 'standard',
    'symbol_enc'      : 'html',
    'show_controls'   : True,

    # 'options.controls': True,
    'options.group_optimizations': True,
    'options.models': True,
    'options.rank_optimizations': True,
})

del(
    _APP_DIR,
    _LOGICS,
    _OPTDEFS,
    _PATHS,
    _,
    _apath,
    _init_logger,
    _getoptval,
    get_logic,
    closure,

    _AppDispatcher,
    AbcEnum,
    Dispatcher,
    Environment,
    FileSystemLoader,
    Notation,
    RenderSet,
)