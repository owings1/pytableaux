from __future__ import annotations

__all__ = ()

import prometheus_client as prom
import cherrypy as chpy
import os.path
import sys

def start():

    from pytableaux import web

    metrics_port = web.APP_ENVCONF['metrics_port']

    web.mailroom.start()

    web.logger.info(f'Starting metrics on port {metrics_port}')
    prom.start_http_server(metrics_port)

    chpy.config.update(web.cp_global_config)
    chpy.quickstart(web.App(), '/', web.cp_config)

if  __name__ == '__main__':

    # print(f'__main__.py, __name__={__name__}, __package__={__package__}')
    if '.' not in __package__:
        addpath = os.path.abspath(
            os.path.join(os.path.dirname(__file__), '..', '..')
        )
        if addpath not in sys.path:
            sys.path.insert(1, addpath)

    start()
