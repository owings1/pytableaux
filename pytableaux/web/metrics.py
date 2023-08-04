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
pytableaux.web.metrics
^^^^^^^^^^^^^^^^^^^^^^

"""
from __future__ import annotations

import functools
from collections import deque
from typing import TYPE_CHECKING, Any, Callable, Mapping, TypeVar

import prometheus_client.metrics as pm
import prometheus_client.metrics_core as pmc
from prometheus_client.registry import CollectorRegistry

from pytableaux import __docformat__, package
from pytableaux.tools import MapCover, abcs

if TYPE_CHECKING:
    class HasRegistry:
        registry: CollectorRegistry
    MetricType = pmc.Metric|pm.MetricWrapperBase|HasRegistry
else:
    MetricType = HasRegistry = object

__all__ = ('AppMetrics',)

_F = TypeVar('_F', bound = Callable)
_MetrT = TypeVar('_MetrT', bound = MetricType)

metric_defs: deque[tuple[str, tuple[type[MetricType], str, list[str]]]] = deque()

# Decorator for AppMetrics
def mwrap(fn: _F) -> _F:
    key = fn.__name__
    @functools.wraps(fn)
    def f(self: AppMetrics, *labels):
        return self[key].labels(package.name, *labels)
    metcls, desc, labels = fn()
    labels = ['app_name', *labels]
    f.spec = key, desc, labels
    metric_defs.append((key, (metcls, desc, labels)))
    return f

class AppMetrics(MapCover[str, MetricType], abcs.Abc):

    __slots__ = ('config', 'registry')

    config: Mapping[str, Any]
    registry: CollectorRegistry

    # ------------------------------------------------------------------

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

    # ------------------------------------------------------------------

    def __init__(self, config, registry: CollectorRegistry = None, /):
        self.config = config
        if registry is None:
            registry = self._new_registry()
        self.registry = registry
        mapping: dict[str, MetricType] = {
            name: metrcls(name, *spec, registry = registry)
            for name, (metrcls, *spec) in metric_defs}
        for metric in mapping.values():
            metric.registry = registry
        super().__init__(mapping)

    @staticmethod
    def _new_registry(*, auto_describe = True, **kw) -> CollectorRegistry:
        return CollectorRegistry(auto_describe = auto_describe, **kw)

    @staticmethod
    def _copy_metric(m: _MetrT, registry: CollectorRegistry) -> _MetrT:
        metric = type(m)(m._name,
            documentation = m._documentation,
            labelnames = m._labelnames,
            registry = registry)
        metric.registry = registry
        return metric

    @classmethod
    def _from_mapping(cls, mapping: Mapping):
        inst = cls.__new__(cls)
        inst.config = {}
        inst.registry = cls._new_registry()
        mapping = {
            mkey: cls._copy_metric(m, inst.registry)
            for mkey, m in mapping.items()}
        super().__init__(inst, mapping)
        return inst
