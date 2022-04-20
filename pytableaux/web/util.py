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
pytableaux.web._util
^^^^^^^^^^^^^^^^^^^^

"""
from __future__ import annotations

__docformat__ = 'google'
__all__ = ('tojson',)

import functools
from typing import TYPE_CHECKING, Any, Mapping

import simplejson as json
import prometheus_client.metrics as pm
import prometheus_client.metrics_core as pmc
from prometheus_client.registry import CollectorRegistry
from pytableaux.tools import abcs, mappings, typing

if TYPE_CHECKING:
    pass

metric_defs = []
# Decorator for AppMetrics
def mwrap(fn: typing.F) -> typing.F:
    key = fn.__name__
    @functools.wraps(fn)
    def f(self: AppMetrics, *labels):
        return self[key].labels(self.config['app_name'], *labels)
    metcls, desc, tags = fn()
    labels = ['app_name', *tags]
    f.spec = key, desc, labels
    metric_defs.append((key, (metcls, desc, labels)))
    return f

class AppMetrics(mappings.MapCover[str, pmc.Metric|pm.MetricWrapperBase], abcs.Abc):

    @mwrap
    def app_requests_count() -> pm.Counter:
        return pm.Counter, 'total app http requests', ['endpoint']

    @mwrap
    def proofs_completed_count() -> pm.Counter:
        return pm.Counter, 'total proofs completed', ['logic', 'result']

    @mwrap
    def proofs_inprogress_count() -> pm.Gauge:
        return pm.Gauge, 'total proofs in progress', ['logic']

    @mwrap
    def proofs_execution_time() -> pm.Summary:
        return pm.Summary, 'total proof execution time', ['logic']

    config: Mapping[str, Any]
    registry: Any

    def __init__(self, config: Mapping[str, Any], registry: Any = None, /):
        self.config = config
        if registry is None:
            registry = self._new_registry()
        self.registry = registry
        super().__init__( {
            mkey: metrcls(mkey, *spec, registry = registry)
            for mkey, (metrcls, *spec) in metric_defs
        })
        

    @staticmethod
    def _new_registry(*, auto_describe = True, **kw) -> CollectorRegistry:
        return CollectorRegistry(auto_describe = auto_describe, **kw)

    @classmethod
    def _from_mapping(cls, it: Mapping):
        inst = cls.__new__(cls)
        inst.config = {}
        inst.registry = cls._new_registry()
        mappings.MapCover.__init__(inst, it)
        return inst


# ------------------------------------------------------------------

def fix_uri_req_data(form_data: dict[str, Any]) -> dict[str, Any]:
    "Transform param names ending in ``'[]'`` to lists."
    form_data = dict(form_data)
    for param in form_data:
        if param.endswith('[]'):
            if isinstance(form_data[param], str):
                form_data[param] = [form_data[param]]
    return form_data

def tojson(*args, cls = json.JSONEncoderForHTML, **kw):
    "Wrapper for ``json.dumps`` with html safe encoder."
    return json.dumps(*args, cls = cls, **kw)
