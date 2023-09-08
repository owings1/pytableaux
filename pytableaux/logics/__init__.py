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

import enum
import itertools
import operator as opr
import sys
from collections import defaultdict
from collections.abc import Mapping, Set
from importlib import import_module
from types import FunctionType
from types import MappingProxyType as MapProxy
from types import MethodType, ModuleType
from typing import TYPE_CHECKING, Any, Iterator, TypeVar

from ..errors import Emsg, check
from ..lang import Operator
from ..tools import EMPTY_SET, abcs, closure, qset, qsetf, SequenceSet, membr, wraps
from ..tools.hybrids import QsetView

if TYPE_CHECKING:
    from ..models import BaseModel, Mval
    from ..proof import Rule, ClosingRule

_T = TypeVar('_T')

__all__ = (
    'b3e',
    'cfol',
    'cpl',
    'd',
    'fde',
    'g3',
    'go',
    'k',
    'k3',
    'k3w',
    'k3wq',
    'kfde',
    'kk3',
    'kl3',
    'klp',
    'krm3',
    'l3',
    'lp',
    'mh',
    'nh',
    'p3',
    'rm3',
    's4',
    's4fde',
    's4k3',
    's4l3',
    's4lp',
    's5',
    's5fde',
    's5k3',
    's5l3',
    's5lp',
    't',
    'tfde',
    'tk3',
    'tl3',
    'tlp',
    'trm3')

NOARG = object()

class Registry(Mapping[Any, 'LogicType'], abcs.Copyable):
    """Logic module registry."""

    packages: qset[str]
    "Packages containing logic modules to load from."

    modules: QsetView[str]
    "The set of loaded module names."

    index: Mapping
    """Mapping to ``module.__name__`` for each of its keys. See :meth:`get()`."""

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
        return type(self)(source=self)

    def clear(self):
        "Clear the registry."
        for logic in set(self.values()):
            self.remove(logic)

    def __call__(self, key: str|ModuleType, /) -> LogicType:
        """Get a logic from the registry, importing if needed. See :meth:`get()`"""
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

    def get(self, ref, default = NOARG, /) -> LogicType:
        """Get a logic from the registry, importing if needed.

        Args:
            key: One of the following:

                - Full ``module.__name__``
                - local ID (lowercase last part of ``module.__name__``)
                - The module's ``Meta.name`` attribute
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

    def locate(self, ref, default = NOARG, /) -> LogicType:
        """Like :meth:`get()` but also searches the ``__module__`` attribute of
        classes, methods, and functions to locate the logic in which it was defined.

        Args:
            ref: A key accepted by :meth:`get()`, or a class, method, or function
                defined in a logic module.
            default: A default value to suppress not found error.
        
        Returns:
            The logic module
        
        Raises:
            ValueError: if not found.
            TypeError: on bad key argument.
        """
        try:
            if isinstance(ref, (str, ModuleType)):
                return self(ref)
            check.inst(ref, (type, MethodType, FunctionType))
            return self(ref.__module__.lower())
        except ValueError:
            if default is NOARG:
                raise
            return default

    def all(self):
        for package in self.packages:
            yield from self.package_all(package)

    def package_all(self, package: str|ModuleType, /):
        """Yield the package's declared logic modules from its ``__all__``
        attribute.
        """
        package = self._check_package(package)
        return map(
            f'{package.__name__}.%s'.__mod__,
            package.__all__)

    def import_all(self) -> None:
        """Import all logics for all registry packages. See :meth:`import_package()`.
        """
        for _ in map(self.import_package, self.packages): pass

    def import_package(self, package: str|ModuleType, /) -> None:
        """Import all logic modules for a package. Uses the ``__all__`` attribute
        to list the logic names.

        Raises:
            ValueError: if the package is not in the registry packages.
        """
        for modname in self.package_all(package):
            if modname not in self.modules:
                self.add(import_module(modname))

    def grouped(self, keys=None, /, *, sort=True, key=None, reverse=False) -> dict[LogicType.Meta.Category, list[LogicType]]:
        """Group logics by category.

        Args:
            keys: Iterable of keys accepted by :meth:`get()`.
            sort: Whether to sort each group. Default ``True``.
            key: The sort key for the groups. Default is ``.Meta.category_order``.
            reverse: Whether to reverse sort each group.

        Returns:
            A dict from each category name to the list of logic modules.

        Raises:
            ValueError: if any not found.
        """
        if keys is None:
            keys = self.all()
        groups = defaultdict(list)
        for logic in map(self, keys):
            groups[logic.Meta.category].append(logic)
        if not sort:
            return dict(groups)
        if key is None:
            key = key_category_order
        for group in groups.values():
            group.sort(key=key, reverse=reverse)
        return {
            category: groups[category]
            for category in sorted(groups, reverse=reverse)}

    def get_extends(self, logic) -> qsetf[LogicType]:
        result = LogicSet(registry=self)
        todo = LogicSet((logic,), registry=self)
        while len(todo):
            extends = LogicSet(registry=self)
            for other in todo:
                extends |= other.Meta.extension_of
            extends -= result
            todo.clear()
            todo |= extends
            result |= extends
        result.discard(logic)
        result.sort()
        return qsetf(result)

    def get_extensions(self, logic) -> qsetf[LogicType]:
        result = LogicSet((logic,), registry=self)
        while True:
            length = len(result)
            for other in map(self, self.all()):
                extension_of = LogicSet(other.Meta.extension_of)
                if len(result & extension_of):
                    result.add(other)
            if len(result) == length:
                break
        result.remove(logic)
        result.sort()
        return qsetf(result)

    def _check_package(self, pkgref: str|ModuleType, /) -> ModuleType:
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

    def __iter__(self) -> Iterator[str]:
        yield from self.modules

    def __reversed__(self) -> Iterator[str]:
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


class LogicTypeMeta(type):

    __call__ = None

    @staticmethod
    def __instancecheck__(obj):
        return instancecheck(obj)

    _metamap = {}

    @staticmethod
    @closure
    def new_meta(metamap = _metamap):
        def new(meta):
            metamap[meta.__module__] = check.subcls(meta, LogicType.Meta)
        return new

    @staticmethod
    @closure
    def meta_for_module(metamap: dict = _metamap):
        def get(name: str) -> type[LogicType.Meta]|None:
            return metamap.get(name)
        return get

    _metamap = MapProxy(_metamap)

class LogicType(metaclass=LogicTypeMeta):
    "Stub class definition for a logic interface."
    class Meta:
        name: str
        modal: bool = False
        quantified: bool = False
        values: type[Mval]
        designated_values: Set[Mval]
        unassigned_value: Mval
        many_valued: bool
        category: LogicType.Meta.Category
        title: str
        description: str = ''
        category_order: int = 0
        tags = SequenceSet[str]
        native_operators: SequenceSet[Operator] = qsetf()
        modal_operators: SequenceSet[Operator] = qsetf(sorted((
            Operator.Possibility,
            Operator.Necessity)))
        truth_functional_operators: SequenceSet[Operator] = qsetf(sorted((
            Operator.Assertion,
            Operator.Negation,
            Operator.Conjunction,
            Operator.Disjunction,
            Operator.MaterialConditional,
            Operator.MaterialBiconditional,
            Operator.Conditional,
            Operator.Biconditional)))
        extension_of: Set[str] = EMPTY_SET

        class Category(enum.Enum):

            Bivalent = 0, 'Bivalent'
            BivalentModal = 1, 'Bivalent Modal'
            ManyValued = 2, 'Many-valued'
            ManyValuedModal = 3, 'Many-valued Modal'

            def __init__(self, order: int, title: str):
                self.order = order
                self.title = title

            @membr.defer
            def wrapper(member: membr):
                @wraps(oper := getattr(opr, member.name))
                def wrapped(self: LogicType.Meta.Category, other, /):
                    cls = type(self)
                    if isinstance(other, str):
                        other = cls(other)
                    elif not isinstance(other, cls):
                        return NotImplemented
                    return oper(self.order, other.order)
                return wrapped

            __lt__ = __gt__ = __le__ = __ge__ = wrapper()

            del(wrapper)

            def __eq__(self, other):
                if isinstance(other, str):
                    return self.name == other or self.title == other
                if not isinstance(other, type(self)):
                    return NotImplemented
                return self is other

            def __hash__(self):
                return hash(self.title)
                
            def __str__(self):
                return self.title

        def __init_subclass__(cls):
            super().__init_subclass__()
            LogicTypeMeta.new_meta(cls)
            for name in ('native_operators', 'modal_operators', 'truth_functional_operators'):
                setattr(cls, name, qsetf(sorted(getattr(cls, name))))
            tags = []
            if cls.quantified:
                tags.append('quantified')
            if len(cls.values) == 2:
                cls.many_valued = False
                tags.append('bivalent')
                category = 'Bivalent'
            else:
                cls.many_valued = True
                tags.append('many-valued')
                category = 'ManyValued'
                if len(cls.values) - len(cls.designated_values):
                    tags.append('gappy')
                if len(cls.designated_values) > 1:
                    tags.append('glutty')
            if cls.modal:
                tags.append('modal')
                category += 'Modal'
            cls.tags = qsetf(tags)
            cls.category = getattr(cls.Category, category)
            extension_of = cls.__dict__.get('extension_of', EMPTY_SET)
            if isinstance(extension_of, str):
                extension_of = extension_of,
            cls.extension_of = qsetf(sorted(extension_of))

    if TYPE_CHECKING:
        from ..proof import System
        class Model(BaseModel[_T]): ...

    class Rules:
        closure: tuple[type[ClosingRule], ...]
        groups: tuple[tuple[type[Rule], ...], ...]

        @classmethod
        def all(cls):
            yield from cls.closure
            for group in cls.groups:
                yield from group

        @classmethod
        def _check_groups(cls):
            pass



class LogicSet(qset[LogicType]):

    __slots__ = ('_hook_cast')

    def __init__(self, *args, registry:Registry=registry):
        self._hook_cast = registry
        super().__init__(*args)

    def _default_sort_key(self, value):
        return (value.Meta.category, value.Meta.category_order)
        # return value.Meta.name

@closure
def instancecheck():

    from ..proof import System
    from ..models import BaseModel

    LogicType.__new__ = None
    LogicTypeMeta.__new__ = None

    LogicType.System = System
    LogicType.Model = BaseModel

    def validate(obj: LogicType):
        check.inst(obj, ModuleType)
        check.subcls(obj.Rules, LogicType.Rules)
        check.subcls(obj.Meta, LogicType.Meta)
        check.subcls(obj.System, LogicType.System)
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

    return instancecheck