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
"""
pytableaux.logics
^^^^^^^^^^^^^^^^^

"""

from __future__ import annotations

__docformat__ = 'google'
__all__ = (
    'b3e', 'cfol', 'cpl', 'd', 'fde', 'g3', 'go', 'k', 'k3', 'k3w', 'k3wq',
    'l3', 'lp', 'mh', 'nh', 'p3', 'rm3', 's4', 's5', 't',
)

import itertools
import sys
from collections import defaultdict
from importlib import import_module
from types import ModuleType
from typing import (Any, Callable, ClassVar, Collection, Iterable, Mapping,
                    Protocol, Set, overload)

from pytableaux import models
from pytableaux.errors import Emsg, check
from pytableaux.proof import tableaux
from pytableaux.tools import MapProxy, abcs, closure, hybrids, mappings
from pytableaux.tools.sets import EMPTY_SET, SetView


class Registry(abcs.Abc):

    packages: hybrids.qset[str]
    "Packages that contain logic modules."

    modules: Set[str]
    "``module.__name__`` value set."

    index: Mapping[LogicLookupKey, str]
    """Mapping to ``module.__name__`` for all of the following keys:
    
    - Full ``module.__name__``
    - local ID (lowercase last part of ``module.__name__``)
    - The module's ``.name`` attribute
    - Module object
    """

    __slots__ = 'packages', 'modules', 'index', 'add_logic', 'remove_logic'

    def __init__(self):
        modules = set()
        index = RegIndex()

        self.packages = hybrids.qset()
        self.modules = SetView(modules)
        self.index = MapProxy(index)

        def add_logic(logic: LogicModule):
            modname = logic.__name__
            index.update(
                zip(self._index_keys(logic), itertools.repeat(modname))
            )
            modules.add(modname)

        def remove_logic(logic: LogicModule):
            self.index -= self._index_keys(logic)
            self.modules.discard(logic.__name__)

        self.add_logic = add_logic
        self.remove_logic = remove_logic

    @overload
    def add_logic(self, logic: LogicModule):...
    @overload
    def remove_logic(self, logic: LogicModule):...
    del(add_logic, remove_logic)

    def get(self, key: LogicLookupKey) -> LogicModule:
        """Get a logic from the registry, importing if needed.
        """
        try:
            modname = self.index[key]
        except KeyError:
            pass
        else:
            return sys.modules[modname]

        check.inst(key, LogicLookupKey)

        if isinstance(key, ModuleType):
            moduleobj = key
            if moduleobj.__package__ not in self.packages:
                raise Emsg.NotLogicsPackage(moduleobj.__package__)
        else:

            if '.' in key:
                pkgstr = key.split('.')[0:-1]
                if pkgstr not in self.packages:
                    raise Emsg.NotLogicsPackage(pkgstr)
                searchit = key,
            else:
                searchit = (f'{pkgname}.{key}' for pkgname in self.packages)

            tried = []
            for srchname in searchit:
                tried.append(srchname)
                try:
                    moduleobj = import_module(srchname)
                except ModuleNotFoundError:
                    continue
                break
            else:
                raise ModuleNotFoundError(f'tried: {tried}')

        if not isinstance(moduleobj, LogicModule):
            raise Emsg.BadLogicModule(moduleobj.__name__)

        self.add_logic(moduleobj)
        return moduleobj

    def sync(self):
        """Sync all registry packages by calling ``.sync_package()``.
        """
        added = set()
        for pkgname in self.packages:
            added.update(self.sync_package(pkgname))
        return added

    def sync_package(self, pkgname: str) -> set[str]:
        """Attempt to find and add any logics that are already loaded (imported)
        but not in the registry. Tries the package's ``__all__`` and ``__dict__``
        attributes.
        """
        if pkgname not in self.packages:
            raise Emsg.NotLogicsPackage(pkgname)
        pkgmod = sys.modules.get(pkgname)
        if pkgmod is None:
            return

        fmt = f'{pkgname}''.%s'.__mod__

        tosync = set()

        it1 = (modname
            for modname in map(fmt, (val
                # In the package's __all__ attribute
                for val in getattr(pkgmod, '__all__', EMPTY_SET)
                    # Would be a module of the package (if a module)
                    if '.' not in val
                    # Not in the package dict (handled below)
                    and val not in pkgmod.__dict__
                ))
                # Not already in the registry
                if modname not in self.modules
                # Is imported
                and modname in sys.modules
                # And is a logic
                and isinstance(sys.modules[modname], LogicModule)
        )
        tosync.update(it1)

        it2 = (fmt(name)
            # In the package dict
            for name, val in pkgmod.__dict__.items()
                # A module of the package
                if type(val) is ModuleType and val.__package__ == pkgname
                # Not already in the registry
                and val.__name__ not in self.modules
                # And is a logic
                and isinstance(val, LogicModule)
        )
        tosync.update(it2)

        synced = set()
        for modname in tosync:
            module = sys.modules[modname]
            if module.__package__ != pkgmod.__name__:
                raise Emsg.NotLogicsPackage(pkgmod.__name__)
            if not isinstance(module, LogicModule):
                raise Emsg.BadLogicModule(module.__name__) 
            self.add_logic(module)
            synced.add(module)

        return synced

    def import_all(self):
        """Import all logics for all registry packages. See ``.import_package()``.
        """
        for pkgname in self.packages:
            self.import_package(pkgname)

    def import_package(self, pkgname: str):
        """Import all logic modules for a package. Uses the ``__all__`` attribute
        to list the logic names.
        """
        if pkgname not in self.packages:
            raise Emsg.NotLogicsPackage(pkgname)
        pkgmod = import_module(pkgname)
        for val in getattr(pkgmod, '__all__', EMPTY_SET):
            modname = f'{pkgname}.{val}'
            if modname not in self.modules:
                module = import_module(modname)
                if isinstance(module, LogicModule):
                    self.get(module)

    def _index_keys(self, logic: LogicModule) -> set[str|ModuleType]:
        return {
            logic,
            logic.name,
            logic.__name__,
            logic.__name__.split('.')[-1].lower(),
        }

class LogicMeta(abcs.AbcMeta):

    _modcache = set()

    def __instancecheck__(self, obj):
        if obj in self._modcache:
            return True
        result, err = self.is_logic(obj)
        if result:
            self._modcache.add(obj)
        else:
            pass
            print(err)
        return result

    @closure
    def is_logic():

        def validate(self, obj):
            check.inst(obj, (type, ModuleType))
            check.inst(obj.name, str)
            check.inst(obj.TableauxSystem, type)
            check.inst(obj.TabRules, type)
            check.inst(obj.Model, type)
            check.subcls(obj.TableauxSystem, tableaux.TableauxSystem)
            check.subcls(obj.Model, models.BaseModel)
            for attr in self.Meta.__annotations__.keys():
                getattr(obj.Meta, attr)

        def geterr(self, obj):
            try:
                validate(self, obj)
            except Exception as err:
                return False, err
            return True, None
        return geterr

class RegIndex(mappings.dmap):
    __slots__ = EMPTY_SET

    def __setitem__(self, key, value):
        if key in self:
            raise Emsg.DuplicateKey(key)
        super().__setitem__(key, value)

    def update(self, mapping = None, **kw):
        'Check all keys before updating.'
        if mapping is None:
            upd = kw
        elif len(kw):
            upd = dict(mapping, **kw)
        else:
            upd = dict(mapping)
        for key in upd:
            if key in self:
                raise Emsg.DuplicateKey(key)
        super().update(upd)

class LogicType(metaclass = LogicMeta):
    name: str
    class Meta:
        category: str
        description: str
        category_order: int
        tags: Collection[str]   
    TableauxSystem: ClassVar[type[tableaux.TableauxSystem]]
    Model: ClassVar[type[models.BaseModel]]
    TabRules: ClassVar[type]

LogicModule = LogicType | ModuleType

LogicLookupKey = ModuleType | str
"""Logic registry key. Either the module object, ``module.__name__``,
``module.name``, identifier.
"""


registry = Registry()
registry.packages.add(__package__)

# ----------------------------------------------------------------------
# ----------------------------------------------------------------------


class SupportsModule(Protocol):
    __module__: str

LogicId = ModuleType | str
LogicRef = LogicId | SupportsModule


_lookup: Mapping[LogicId, ModuleType]
"Index of loaded logics."

@closure
def getlogic():

    global _lookup
    lookup: dict[LogicId, ModuleType] = {}
    _lookup = MapProxy(lookup)

    from pytableaux import logics as myself

    def add_to_index(logic, key):
        idx = lookup
        keys = dict(
            name = logic.name,
            name_lower = logic.name.lower(),
            key = key,
        )
        from pprint import pp
        pp(keys)
        for k in keys.values():
            idx[k] = logic
        setattr(myself, logic.name, logic)
        return logic

    def get(ref: LogicRef) -> ModuleType:
        """Get the logic module from the specified reference.

        Each of following examples returns the L{FDE} logic module::

            getlogic('fde')
            getlogic('FDE')
            getlogic('logics.fde')
            getlogic(getlogic('FDE'))

        Args:
            ref: The logic reference.
        
        Returns:
            The logic module.

        Raises:
            ValueError: if the module is not a logic.
            ModuleNotFoundError: if the module is not found.
            TypeError: if no module name can be determined from ``ref``.
        """
        idx = _lookup
        try:
            return idx[ref]
        except KeyError:
            pass
        try:
            return idx[ref.__module__.lower()]
        except AttributeError:
            pass
        except KeyError:
            ref = import_module(ref.__module__)
        if isinstance(ref, ModuleType):
            if ref.__package__ != __package__ or ref.__name__ == __name__:
                raise ValueError(f'{ref} is not a logic module')
            key = ref.__name__.lower()
            try:
                logic = idx[key]
            except KeyError:
                pass
            else:
                if logic is not ref:
                    raise ValueError(f'{ref} does not match stored {logic}')

            return add_to_index(ref, key)

        if not isinstance(ref, str):
            raise TypeError("ref must be string or module, or have __module__ attribute")
        key = ref.lower()
        try:
            logic = idx[key]
        except KeyError:
            pass
        else:
            return logic
        if key == __name__:
            raise ValueError(f'{ref} is not a logic module')
        if '.' not in key:
            key = f'{__name__}.{key}'
        elif not key.startswith(__name__ + '.'):
            raise ValueError(f'{key} is not in package {__package__}')
        cand = import_module(key)
        if cand.__package__ != __package__:
            raise ValueError(f'{cand} is not in package {__package__}')

        return add_to_index(cand, key)

    return get

def key_category_order(logic: ModuleType) -> int:
    "Returns the category order from the logic, e.g. for sorting."
    return logic.Meta.category_order

def group_logics(logics: Iterable[LogicId], /, *,
    sort: bool = True,
    reverse: bool = False,
    key: Callable[[ModuleType], Any] = key_category_order,
) -> dict[str, list[ModuleType]]:
    "Group logics by category."
    groups: dict[str, list[ModuleType]] = defaultdict(list)
    for logic in map(getlogic, logics):
        groups[logic.Meta.category].append(logic)
    if sort:
        for group in groups.values():
            group.sort(key = key, reverse = reverse)
    return dict(groups)
