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
# pytableaux - Web App Configuration
import logic
import importlib, logging, os, os.path
import prometheus_client as prom
from jinja2 import Environment, FileSystemLoader

## Option definitions

optdefs = {
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

## Available modules

available = {
    'logics'    : [
        'cpl', 'cfol', 'fde', 'k3', 'k3w', 'k3wq', 'b3e', 'go', 'mh',
        'l3', 'g3', 'p3', 'lp', 'nh', 'rm3', 'k', 'd', 't', 's4', 's5'
    ],
    'notations' : ['standard', 'polish'],
    'writers'   : ['html', 'ascii'],
}
modules = dict()
logic_categories = dict()
# nups: "notation-user-predicate-symbols"
nups = dict()

def populate_modules_info():
    
    for package in available:
        modules[package] = {}
        for name in available[package]:
            modules[package][name] = importlib.import_module(
                '.'.join((package, name))
            )

    for notation_name in modules['notations']:
        notation = modules['notations'][notation_name]
        nups[notation_name] = list(
            notation.symbol_sets['default'].chars('user_predicate')
        )

    for name in modules['logics']:
        lgc = modules['logics'][name]
        if lgc.Meta.category not in logic_categories:
            logic_categories[lgc.Meta.category] = list()
        logic_categories[lgc.Meta.category].append(name)

    def get_category_order(name):
        return logic.get_logic(name).Meta.category_display_order

    for category in logic_categories.keys():
        logic_categories[category].sort(key = get_category_order)

populate_modules_info()

## Logging

logger = logging.Logger('APP')

def init_logger(logger):
    ch = logging.StreamHandler()
    formatter = logging.Formatter(
        # Similar to cherrypy's format for consistency.
        '[%(asctime)s] %(name)s.%(levelname)s %(message)s',
        datefmt='%d/%b/%Y:%H:%M:%S',
    )
    ch.setFormatter(formatter)
    logger.addHandler(ch)

init_logger(logger)

## Options

def getoptval(name):
    defn = optdefs[name]
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

opts = {
    name: getoptval(name) for name in optdefs.keys()
}

# Set loglevel from opts
if hasattr(logging, opts['loglevel'].upper()):
    logger.setLevel(getattr(logging, opts['loglevel'].upper()))
else:
    logger.setLevel(getattr(logging, optdefs['loglevel']['default'].upper()))
    logger.warn('Ingoring invalid loglevel: {0}'.format(opts['loglevel']))
    opts['loglevel'] = optdefs['loglevel']['default'].upper()

## Prometheus Metrics

metrics = {
    'app_requests_count' : prom.Counter(
        'app_requests_count',
        'total app http requests',
        ['app_name', 'endpoint'],
    ),
    'proofs_completed_count' : prom.Counter(
        'proofs_completed_count',
        'total proofs completed',
        ['app_name', 'logic', 'result'],
    ),
    'proofs_inprogress_count' : prom.Gauge(
        'proofs_inprogress_count',
        'total proofs in progress',
        ['app_name', 'logic'],
    ),
    'proofs_execution_time' : prom.Summary(
        'proofs_execution_time',
        'total proof execution time',
        ['app_name', 'logic'],
    )
}

# Util

re_email = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'

## cherrypy global config
cp_global_config = {
    'global': {
        'server.socket_host'   : opts['host'],
        'server.socket_port'   : opts['port'],
        'engine.autoreload.on' : opts['is_debug'],
    },
}

#  Path info

app_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..')

def apath(*args):
    return os.path.join(app_dir, *args)

consts = {
    'index_filename' : 'index.html',
    'view_path'      : apath('www/views'),
    'static_dir'     : apath('www/static'),
    'favicon_file'   : apath('www/static/img/favicon-60x60.png'),
    'robotstxt_file' : apath('www/static/robots.txt'),
    'static_dir_doc' : apath('..', 'doc/_build/html'),
}

# Jinja2

jenv = Environment(loader = FileSystemLoader(consts['view_path']))