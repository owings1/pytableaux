# -*- coding: utf-8 -*-
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
from __future__ import annotations

"""
    pytableaux web server
    ---------------------

"""

__all__ = ()

# import prometheus_client as prom
# import cherrypy as chpy
import os.path
import sys

def start():

    from pytableaux.web.application import WebApp
    WebApp().start()

    # metrics_port = web.APP_ENVCONF['metrics_port']

    # web.mailroom.start()

    # web.logger.info(f'Starting metrics on port {metrics_port}')
    # prom.start_http_server(metrics_port)

    # chpy.config.update(web.cp_global_config)
    # chpy.quickstart(web.App(), '/', web.cp_config)

if  __name__ == '__main__':

    # print(f'__main__.py, __name__={__name__}, __package__={__package__}')

    if '.' not in __package__:
        addpath = os.path.abspath(
            os.path.join(os.path.dirname(__file__), '..', '..')
        )
        if addpath not in sys.path:
            sys.path.insert(1, addpath)

    start()
