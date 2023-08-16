# -*- coding: utf-8 -*-
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
pytableaux.logics
^^^^^^^^^^^^^^^^^

"""
from __future__ import annotations

import itertools
import sys
from collections import defaultdict
from collections.abc import Mapping
from importlib import import_module
from types import FunctionType
from types import MappingProxyType as MapProxy
from types import MethodType, ModuleType
from typing import TYPE_CHECKING, Any

from ..errors import Emsg, check
from ..lang import Operator
from ..tools import EMPTY_SET, abcs, closure, qset
from ..tools.hybrids import QsetView

if TYPE_CHECKING:
    from ..models import BaseModel
    from ..proof import Rule, ClosingRule, TableauxSystem

__all__ = (
    'b3e', 'cfol', 'cpl', 'd', 'fde', 'g3', 'go', 'k', 'k3', 'k3w', 'k3wq',
    'l3', 'lp', 'mh', 'nh', 'p3', 'rm3', 's4', 's5', 't')

NOARG = object()


_metamap = {}
_metamap_setdefault = _metamap.setdefault
_metamap: Mapping[str, type[LogicType.Meta]] = MapProxy(_metamap)

class GetLogicMetaMixinMetaType(type):
    @property
    def Meta(self) -> type[LogicType.Meta]|None:
        return _metamap.get(self.__module__)

class LogicType(metaclass = type('LogicTypeMeta', (type,), dict(__call__ = None))):
    "Stub class definition for a logic interface."
    class Meta:
        name: str
        modal: bool|None = None
        category: str
        description: str
        category_order: int
        tags: tuple[str, ...] = ()
        native_operators: tuple[Operator, ...] = ()
        modal_operators: tuple[Operator, ...] = (
            Operator.Possibility,
            Operator.Necessity)
        truth_functional_operators: tuple[Operator, ...] = (
            Operator.Assertion,
            Operator.Negation,
            Operator.Conjunction,
            Operator.Disjunction,
            Operator.MaterialConditional,
            Operator.MaterialBiconditional,
            Operator.Conditional,
            Operator.Biconditional)

        def __init_subclass__(cls):
            super().__init_subclass__()
            _metamap_setdefault(cls.__module__, cls)

    TableauxSystem: type[TableauxSystem]
    Model: type[BaseModel]
    class TabRules:
        Meta: type[LogicType.Meta]
        closure_rules: tuple[type[ClosingRule], ...]
        rule_groups: tuple[tuple[type[Rule], ...], ...]
        all_rules: tuple[type[Rule], ...]


        
class Registry(Mapping[Any, LogicType], abcs.Copyable):
    """Logic module registry.
    """

    packages: qset[str]
    "Packages containing logic modules to load from."

    modules: QsetView[str]
    "The set of loaded module names."

    index: Mapping
    """Mapping to ``module.__name__`` for each of its keys. See ``.get()``."""

    if TYPE_CHECKING:
        def add(self, logic):
            "Add a logic module"
        def remove(self, logic):
            "Remove a logic  module"

    __slots__ = 'packages', 'modules', 'index', 'add', 'remove', 

    def __init__(self, *, source = None):
        self.packages = qset()
        modules = qset()
        index = self.Index()
        if source is not None:
            source = check.inst(source, Registry)
            self.packages.update(source.packages)
            modules.update(source.modules)
            index.update(source.index)
        self.modules = QsetView(modules)
        self.index = MapProxy(index)

        def add(logic):
            check.inst(logic, LogicType)
            modname = logic.__name__
            if modname not in modules:
                index.update(
                    zip(self._module_keys(logic), itertools.repeat(modname)))
                modules.add(modname)

        def remove(logic):
            modules.remove(logic.__name__)
            for key in self._module_keys(logic):
                del(index[key])

        self.add = add
        self.remove = remove

    def discard(self, logic):
        "Discard a logic  module."
        try:
            self.remove(logic)
        except KeyError:
            pass

    def copy(self):
        "Copy the registry."
        return type(self)(source = self)

    def clear(self):
        "Clear the registry."
        for logic in set(self.values()):
            self.remove(logic)

    def __call__(self, key: str|ModuleType, /) -> LogicType:
        """Get a logic from the registry, importing if needed. See ``.get()``"""
        try:
            modname = self.index[key]
        except KeyError:
            pass
        else:
            return sys.modules[modname]

        if isinstance(key, ModuleType):
            module = key
            if module.__package__ not in self.packages:
                raise Emsg.NotLogicsPackage(module.__package__)
        else:
            check.inst(key, str)
            if '.' in key:
                pkgstr = '.'.join(key.split('.')[0:-1])
                if pkgstr not in self.packages:
                    raise Emsg.NotLogicsPackage(pkgstr)
                searchit = key,
            else:
                keylc = key.lower()
                searchit = itertools.chain(
                    (f'{pkgname}.{keylc}' for pkgname in self.packages),
                    (f'{pkgname}.{key}' for pkgname in self.packages))
            tried = []
            for srchname in searchit:
                tried.append(srchname)
                try:
                    module = import_module(srchname)
                except ModuleNotFoundError:
                    continue
                break
            else:
                raise ModuleNotFoundError(f'tried: {tried}')

        if not isinstance(module, LogicType):
            raise Emsg.BadLogicModule(module.__name__)

        self.add(module)
        return module

    def get(self, ref, default = NOARG, /):
        """Get a logic from the registry, importing if needed.

        Args:
            key: One of the following:

                - Full ``module.__name__``
                - local ID (lowercase last part of ``module.__name__``)
                - The module's ``.name`` attribute
                - Module object

            default: A default value to suppress error.
        
        Returns:
            The logic module
        
        Raises:
            ModuleNotFoundError: if not found.
            TypeError: on bad key argument.
        """
        try:
            return self(ref)
        except ModuleNotFoundError:
            if default is NOARG:
                raise
            return default

    def locate(self, ref, default = NOARG, /):
        """Like ``.get()`` but also searches the ``__module__`` attribute of
        classes, methods, and functions to locate the logic in which it was defined.

        Args:
            ref: A ``key`` accepted by ``.get()``, or a class, method, or function
                defined in a logic module.
            default: A default value to suppress not found error.
        
        Returns:
            The logic module
        
        Raises:
            ValueError: if not found.
            TypeError: on bad key argument.
        """
        check.inst(ref, (str, type, ModuleType, MethodType, FunctionType))
        try:
            if isinstance(ref, (str, ModuleType)):
                return self(ref)
            return self(ref.__module__.lower())
        except ValueError:
            if default is NOARG:
                raise
            return default

    def all(self):
        for package in self.packages:
            yield from self._package_all(self._check_package(package))

    def package_all(self, package: str|ModuleType, /):
        """List the package's declared logic modules from its ``__all__``
        attribute.
        """
        return self._package_all(self._check_package(package))

    def sync(self):
        """Sync all registry packages by calling ``.sync_package()``.

        Returns:
            Dict of each package name to its ``sync_package()`` result.
        """
        added = set()
        for pkgname in self.packages:
            added.update(self.sync_package(pkgname))
        return added

    def sync_package(self, package: str|ModuleType, /):
        """Attempt to find and add any logics that are already loaded (imported)
        but not in the registry. Tries the package's ``__all__`` and ``__dict__``
        attributes.

        Args:
            package: The package name or module. Must be in ``registry.packages``.
        
        Returns:
            The module names added to the registry.
        
        Raises:
            ValueError: if package is not in the registry packages.
        """
        added = set()
        for modname in self.package_all(package):
            if modname not in self.modules:
                logic = sys.modules.get(modname) or import_module(modname)
                self.add(logic)
                added.add(logic)
        return added

    def import_all(self):
        """Import all logics for all registry packages. See ``.import_package()``.
        """
        for _ in map(self.import_package, self.packages): pass

    def import_package(self, package: str|ModuleType, /):
        """Import all logic modules for a package. Uses the ``__all__`` attribute
        to list the logic names.

        Raises:
            ValueError: if ``pkgname`` is not in the registry packages.
        """
        package = self._check_package(package)
        for modname in self._package_all(package):
            if modname not in self.modules:
                self.add(import_module(modname))

    def grouped(self, keys, /, *, sort = True, key = None, reverse = False):
        """Group logics by category.

        Args:
            keys: Iterable of keys accepted by ``.get()``.
            sort: Whether to sort each group. Default ``True``.
            key: The sort key for the groups. Default is ``.Meta.category_order``.
            reverse: Whether to reverse sort each group.

        Returns:
            A dict from each category name to the list of logic modules.

        Raises:
            ValueError: if any not found.
        """
        groups = defaultdict(list)
        for logic in map(self, keys):
            groups[logic.Meta.category].append(logic)
        if not sort:
            return dict(groups)
        if key is None:
            key = key_category_order
        for group in groups.values():
            group.sort(key = key, reverse = reverse)
        return {
            category: groups[category]
            for category in sorted(groups)}

    def _check_package(self, pkgref: str|ModuleType, /):
        if pkgref in self.packages:
            return sys.modules.get(pkgref) or import_module(pkgref)
        if isinstance(pkgref, str):
            raise Emsg.NotLogicsPackage(pkgref)
        if check.inst(pkgref, ModuleType).__name__ in self.packages:
            return pkgref
        raise Emsg.NotLogicsPackage(pkgref.__name__)

    @staticmethod
    def _module_keys(logic: LogicType|ModuleType, /):
        """Get the index keys for a logic module.

        Args:
            logic: The logic module.
        
        Returns:
            Generator for the keys, as sepcified in ``.get()``.
        """
        yield logic
        yield logic.Meta.name
        yield logic.__name__
        yield logic.__name__.split('.')[-1].lower()
        
    @staticmethod
    def _package_all(package: ModuleType, /):
        fmt = f'{package.__name__}.%s'.__mod__
        for value in package.__all__:
            yield fmt(value)

    def __contains__(self, key):
        return key in self.index

    def __getitem__(self, key) -> LogicType:
        modname = self.index[key]
        try:
            return sys.modules[modname]
        except KeyError:
            raise RuntimeError

    def __iter__(self):
        yield from self.modules

    def __reversed__(self):
        return reversed(self.modules)

    def __len__(self):
        return len(self.modules)

    def __repr__(self):
        names = (v.Meta.name for v in self.values())
        if self is registry:
            ident = 'default'
        else:
            ident = id(self)
        return f'{type(self).__name__}@{ident}{repr(list(names))}'

    class Index(dict):

        __slots__ = EMPTY_SET

        def __setitem__(self, key, value):
            if key in self:
                raise Emsg.DuplicateKey(key)
            super().__setitem__(key, value)

        def update(self, *args, **kw):
            # Check all keys before updating.
            upd = dict(*args, **kw)
            for key in upd:
                if key in self:
                    raise Emsg.DuplicateKey(key)
            super().update(upd)


def key_category_order(logic: LogicType) -> int:
    "Returns the category order from the logic, e.g. for sorting."
    return logic.Meta.category_order


registry: Registry = Registry()
"The default built-in registry"

registry.packages.add(__package__)


@closure
def instancecheck():

    from ..proof import TableauxSystem
    from ..models import BaseModel

    LogicType.TableauxSystem = TableauxSystem
    LogicType.Model = BaseModel

    def validate(obj):
        check.inst(obj, ModuleType)
        check.subcls(obj.TabRules, LogicType.TabRules)
        check.subcls(obj.Meta, LogicType.Meta)
        check.subcls(obj.TableauxSystem, LogicType.TableauxSystem)
        check.subcls(obj.Model, LogicType.Model)

    cache = set()

    def instancecheck(obj):
        key = id(obj)
        if key not in cache:
            try:
                validate(obj)
            except:
                return False
            cache.add(key)
        return True

    type(LogicType).__instancecheck__ = staticmethod(instancecheck)

    return instancecheck
