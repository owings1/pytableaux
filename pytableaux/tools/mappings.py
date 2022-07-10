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
pytableaux.tools.mappings
^^^^^^^^^^^^^^^^^^^^^^^^^

"""
from __future__ import annotations

from collections import defaultdict, deque
from collections.abc import (Callable, Iterable, Iterator, Mapping,
                             MutableMapping, Reversible, Set)
from itertools import chain, filterfalse
from operator import not_, truth
from types import MappingProxyType as MapProxy

from pytableaux import __docformat__
from pytableaux.errors import Emsg
from pytableaux.tools import (EMPTY_MAP, abcs, closure, isattrstr, membr, thru,
                              true, wraps)
from pytableaux.tools.sets import EMPTY_SET, setf

__all__ = (
    'defaultdmap',
    'DequeCache',
    'dmap',
    'dmapattr',
    'dmapns',
    'EMPTY_MAP',
    'ItemMapEnum',
    'ItemsIterator',
    'KeySetAttr',
    'MapCover',
    'MappingApi',
    'MapProxy',
    'MutableMappingApi',
)

class MappingApi(Mapping, Reversible, abcs.Copyable):
    "Extended mapping api with fine-grained operator support."

    __slots__ = EMPTY_SET

    @abcs.abcf.temp
    @membr.defer
    def oper(member: membr):
        opname = member.name
        @wraps(member)
        def f(self, other, /):
            return _opcache.resolve(self, opname, other)
        return f

    __or__ = __ror__ = __and__ = __rand__ = __sub__ = __rsub__ = \
         __rxor__ = __mod__ = __rmod__ = oper()

    def __or__op__(self, other):
        'Mapping | Mapping -> Mapping'
        return chain(ItemsIterator(self), ItemsIterator(other))

    def __ror__op__(self, other):
        'Set     | Mapping --> Set'
        if isinstance(other, Set): return chain(other, self)
        'Mapping | Mapping --> Mapping'
        return chain(ItemsIterator(other), ItemsIterator(self))

    def __mod__op__(self, other):
        'Mapping | Mapping -> Mapping'
        return chain(ItemsIterator(self), ItemsIterator(other, 
            kpred = self.__contains__, koper = not_
        ))

    def __rmod__op__(self, other):
        'Mapping | Mapping -> Mapping'
        if not isinstance(other, Mapping):
            return NotImplemented
        return chain(ItemsIterator(other), ItemsIterator(self,
            kpred = other.__contains__, koper = not_
        ))

    def __and__op__(self, other):
        if not isinstance(other, Set):
            return NotImplemented
        'Mapping & Set --> Mapping'
        return ItemsIterator(self, kpred = other.__contains__)

    def __rand__op__(self, other):
        if not isinstance(other, Set):
            return NotImplemented
        'Set & Mapping --> Set'
        return filter(self.__contains__, other)

    def __sub__op__(self, other):
        if not isinstance(other, Set):
            return NotImplemented
        'Mapping - Set --> Mapping'
        return ItemsIterator(self, kpred = other.__contains__, koper = not_)

    def __rsub__op__(self, other):
        if not isinstance(other, Set):
            return NotImplemented
        'Set - Mapping --> Set'
        return filterfalse(other, self.__contains__)

    def __rxor__op__(self, other):
        if not isinstance(other, Set):
            return NotImplemented
        'Set ^ Mapping --> Set'
        return chain(
            filterfalse(self.__contains__, other),
            filterfalse(other.__contains__, self),
        )

    def copy(self):
        return self._from_mapping(self)

    def _asdict(self):
        'Compatibility for JSON serialization.'
        return dict(self)

    @classmethod
    def _from_mapping(cls, mapping):
        'Construct a new instance from a mapping.'
        return cls(mapping)

    @classmethod
    def _from_iterable(cls, it, /):
        'Construct a new instance from an iterable of item tuples.'
        return NotImplemented

    @classmethod
    def _oper_res_type(cls, othrtype, /):
        '''Return the type (or callable) to construct a new instance from the result
        of an arithmetic operator expression for objects of type cls on the left hand
        side, and of othrtype on the right hand side.'''
        return cls

    @classmethod
    def _roper_res_type(cls, othrtype,/):
        '''Return the type (or callable) to construct a new instance from the result
        of an arithmetic operator expression for objects of type cls on the right hand
        side, and of othrtype on the left hand side.'''
        if issubclass(othrtype, Set):
            return othrtype
        return cls._oper_res_type(othrtype)


class MapCover(MappingApi):
    'Mapping reference.'

    __slots__ = ('__getitem__', '_cov_mapping')
    _cov_mapping: Mapping

    @closure
    def __init__():
        sa = object.__setattr__
        def init(self, mapping: Mapping, /):
            if type(mapping) is not MapProxy:
                mapping = MapProxy(mapping)
            sa(self, '_cov_mapping', mapping)
            sa(self, '__getitem__', mapping.__getitem__)
        return init

    def copy(self):
        return self._from_mapping(self._asdict())

    def __reversed__(self):
        return reversed(self._cov_mapping)

    def __len__(self):
        return len(self._cov_mapping)

    def __iter__(self):
        return iter(self._cov_mapping)

    def __delattr__(self, name: str, /):
        if name in __class__.__slots__:
            raise Emsg.ReadOnly(self, name)
        super().__delattr__(name)

    def __setattr__(self, name, value, /, *, _sa = object.__setattr__):
        if hasattr(self, name) and name in __class__.__slots__:
            raise Emsg.ReadOnly(self, name)
        _sa(self, name, value)

    def __repr__(self):
        return repr(self._asdict())

    @classmethod
    def _from_iterable(cls, it):
        return cls._from_mapping(dict(it))


class MutableMappingApi(MappingApi, MutableMapping, abcs.Copyable):

    __slots__ = EMPTY_SET

    def __or__op__(self, other):
        if self._oper_res_type(type(other)) is type(self):
            inst = self.copy()
            inst.update(other)
            return inst
        return super().__or__op__(other)

    def __ror__op__(self, other):
        if self._roper_res_type(type(other)) is type(self):
            inst = self.copy()
            inst.update(other)
            return inst
        return super().__ror__op__(other)

    def __ior__(self, other):
        if not isinstance(other, Iterable):
            return NotImplemented
        self.update(other)
        return self

    def __imod__(self, other):
        if not isinstance(other, Iterable):
            return NotImplemented
        self.update(ItemsIterator(other, kpred = self.__contains__, koper = not_))
        return self

    def __iand__(self, other):
        if not isinstance(other, Set):
            return NotImplemented
        for _ in map(self.__delitem__,
            tuple(filterfalse(other.__contains__, self))
        ): pass
        return self

    def __isub__(self, other):
        if not isinstance(other, Set):
            return NotImplemented
        for _ in map(self.__delitem__,
            tuple(filter(self.__contains__, other))
        ): pass
        return self

    @closure
    def _setitem_update():
        EMPTY_ITER = iter(())
        def update(self, it = None, /, **kw):
            """Alternate `.update()` implementation for classes that need more 
            setitem/delitem control.
            """
            if it is None:
                it = EMPTY_ITER
            else:
                it = ItemsIterator(it)
            if len(kw):
                it = chain(it, ItemsIterator(kw))
            setitem = self.__setitem__
            for key, value in it:
                setitem(key, value)
        return update

    @classmethod
    def _from_iterable(cls, it, /):
        return cls(it)

class dmap(dict, MutableMappingApi):
    'Mutable mapping api from dict.'

    __slots__ = EMPTY_SET

    copy    = MutableMappingApi.copy
    __or__  = MutableMappingApi.__or__
    __ror__ = MutableMappingApi.__ror__

class defaultdmap(defaultdict, MutableMappingApi):
    'Mutable mapping api from defaultdict.'

    __slots__ = EMPTY_SET

    copy    = MutableMappingApi.copy
    __or__  = MutableMappingApi.__or__
    __ror__ = MutableMappingApi.__ror__

    @classmethod
    def _from_mapping(cls, mapping, /):
        if isinstance(mapping, defaultdict):
            return cls(mapping.default_factory, mapping)
        return cls(None, mapping)

    @classmethod
    def _from_iterable(cls, it, /):
        return cls(None, it)

    @classmethod
    def _roper_res_type(cls, othrtype, /):
        if issubclass(othrtype, Mapping):
            return dmap
        return super()._roper_res_type(othrtype)

class KeySetAttr(metaclass = abcs.AbcMeta):
    "Mixin class for read-write attribute-key gate."

    __slots__ = EMPTY_SET

    def __setitem__(self, key, value, /):
        super().__setitem__(key, value)
        if isattrstr(key) and self._keyattr_ok(key):
            super().__setattr__(key, value)

    def __setattr__(self, name, value):
        super().__setattr__(name, value)
        if self._keyattr_ok(name):
            super().__setitem__(name, value)

    def __delitem__(self, key, /):
        super().__delitem__(key)
        if isattrstr(key) and self._keyattr_ok(key):
            super().__delattr__(key)

    def __delattr__(self, name):
        super().__delattr__(name)
        if self._keyattr_ok(name) and name in self:
            super().__delitem__(name)

    update = MutableMappingApi._setitem_update

    @classmethod
    def _keyattr_ok(cls, name: str) -> bool:
        'Return whether it is ok to set the attribute name.'
        return not hasattr(cls, name)

class dmapattr(KeySetAttr, dmap):
    "Dict attr dmap base class."

    __slots__ = EMPTY_SET

    def __init__(self, it = None, /, **kw):
        if it is not None:
            self.update(it)
        if len(kw):
            self.update(kw)

class dmapns(dmapattr):
    "Dict attr namespace with __dict__ slot and liberal key approval."

    @classmethod
    def _keyattr_ok(cls, name):
        return len(name) and name[0] != '_'

class ItemMapEnum(abcs.Ebc):
    """Fixed mapping enum based on item tuples.

    If a member value is defined as a mapping, the member's ``_value_`` attribute
    is converted to a tuple of item tuples during ``__init__()``.

    Implementations should always call ``super().__init__()`` if it is overridden.

    Math operators ``|``, ``&``, ``-``, ``%``, and ``^`` are implemented like
    ``MappingApi``, including right-hand operators. Mapping operators ``|`` and
    ``^`` return a ``dict`` instance by default, which can be overridden via the
    ``_oper_res_type()`` class method.

    The methods ``_from_mapping()`` and ``_from_iterable()`` are **not** added.
    These methods would not be called internally by operator methods, since we
    always resolve to a ``dict`` (not our own class).

    Note that ``.get()`` is implemented as ``.mget()``, since ``AbcEnumMeta``
    uses ``'get'`` as a class method to lookup enum members.
    """

    __slots__ = (
        '__iter__', '__getitem__', '__len__', '__reversed__',
        'name', 'value', '_value_'
    )

    def __init__(self, *args):
        if len(args) == 1 and isinstance(args[0], Mapping):
            self._value_ = args = tuple(args[0].items())
        m = dict(args)
        self.__len__ = m.__len__
        self.__iter__ = m.__iter__
        self.__getitem__ = m.__getitem__
        self.__reversed__ = m.__reversed__

    keys = MappingApi.keys
    items = MappingApi.items
    values = MappingApi.values
    mget = MappingApi.get # get() is not allowed for Ebc

    _asdict = MappingApi._asdict

    __or__ = MappingApi.__or__
    __ror__ = MappingApi.__ror__
    __or__op__ = MappingApi.__or__op__
    __ror__op__ = MappingApi.__ror__op__

    __mod__ = MappingApi.__mod__
    __rmod__ = MappingApi.__rmod__
    __mod__op__ = MappingApi.__mod__op__
    __rmod__op__ = MappingApi.__rmod__op__

    __and__ = MappingApi.__and__
    __rand__ = MappingApi.__rand__
    __and__op__ = MappingApi.__and__op__
    __rand__op__ = MappingApi.__rand__op__

    __sub__ = MappingApi.__sub__
    __rsub__ = MappingApi.__rsub__
    __sub__op__ = MappingApi.__sub__op__
    __rsub__op__ = MappingApi.__rsub__op__

    __rxor__ = MappingApi.__rxor__
    __rxor__op__ = MappingApi.__rxor__op__

    _roper_res_type = classmethod(MappingApi._roper_res_type.__func__)

    @classmethod
    def _oper_res_type(cls, othrtype, /):
        return dict

class DequeCache(abcs.Abc):

    __slots__ = ('__getitem__', '__setitem__', '_maxlen')

    @property
    def maxlen(self) -> int:
        return self._maxlen()

    def __init__(self, maxlen = 10):

        idx   = {}
        rev   = {}
        deck  = deque(maxlen = maxlen)

        self._maxlen = lambda: deck.maxlen

        self.__getitem__ = idx.__getitem__

        def setitem(key, item, /):
            if item in rev:
                item = idx[item]
            else:
                if len(deck) == deck.maxlen:
                    old = deck.popleft()
                    for k in rev.pop(old):
                        del(idx[k])
                idx[item] = item
                rev[item] = {item}
                deck.append(item)
            idx[key] = item
            rev[item].add(key)

        self.__setitem__ = setitem


class ItemsIterator(Iterator[tuple]):
    'Mapping items iterator.'

    __slots__ = '_gen_',

    def __new__(cls, obj, /, *args, **kw):
        if type(obj) is cls and not len(args) and not len(kw):
            return obj
        return super().__new__(cls)

    def __init__(self, obj, /, *, vget = None, kpred = true,
        vpred = true, koper = truth, voper = truth):
        if vget is None:
            if hasattr(obj, 'keys'):
                self._gen_ = self._gen1(
                    obj.keys, obj.__getitem__, kpred, vpred, koper, voper
                )
            else:
                self._gen_ = self._gen2(
                    obj, kpred, vpred, koper, voper
                )
        else:
            self._gen_ = self._gen1(
                obj.__iter__, vget, kpred, vpred, koper, voper
            )

    def __iter__(self):
        return self

    def __next__(self) -> tuple:
        return self._gen_.__next__()

    @staticmethod
    def _gen1(getkeys, vget, kpred, vpred, koper, voper):
        for k in getkeys():
            if koper(kpred(k)):
                v = vget(k)
                if voper(vpred(v)):
                    yield k, v

    @staticmethod
    def _gen2(items, kpred, vpred, koper, voper):
        for k, v in items:
            if koper(kpred(k)) and voper(vpred(v)):
                yield k, v


@closure
def _opcache():

    class CacheResolversType(dict):

        __slots__ = EMPTY_SET

        def __missing__(self, pair, /):
            while checklimit(len(self)):
                self.pop(next(iter(self)))
            res_create, get_res_iter = pair
            def cached_resolver(mapi, other):
                return res_create(get_res_iter(mapi, other))
            cached_resolver.__qualname__ = cached_resolver.__name__
            return self.setdefault(pair, cached_resolver)

    class FuncCache(dict):

        __slots__ = setf(('get_res_iter', 'get_res_type'))

        get_res_iter: Callable
        get_res_type: Callable

        def __init__(self, mapitype: type[MappingApi], opname: str, /):
            self.get_res_iter = getattr(mapitype, opname + 'op__')
            if opname.startswith('__r'):
                self.get_res_type = mapitype._roper_res_type
            else:
                self.get_res_type = mapitype._oper_res_type

        def __missing__(self, othrtype: type[Iterable], /):
            while checklimit(len(self)):
                self.pop(next(iter(self)))
            return self.setdefault(othrtype, self.resolve)

        def resolve(self, mapi, other, /, *, FTHRU = thru):
            othrtype = type(other)
            if not issubclass(othrtype, Iterable):
                return self.reject(othrtype)
            res_type = self.get_res_type(othrtype)
            if res_type is NotImplemented:
                return self.reject(othrtype)
            get_res_iter = self.get_res_iter
            it = get_res_iter(mapi, other)
            if (
                it is not self and it is not other and
                isinstance(res_type, type) and isinstance(it, res_type)
            ):
                res_create = FTHRU
            elif isinstance(it, Mapping):
                res_create = getattr(res_type, '_from_mapping', res_type)
            elif isinstance(it, Iterable):
                res_create = getattr(res_type, '_from_iterable', res_type)
            elif it is NotImplemented:
                return self.reject(othrtype)
            else:
                raise Emsg.InstCheck(it, Iterable)
            res = res_create(it)
            self[othrtype] = resolve_cache[res_create, get_res_iter]
            return res

        @closure
        def reject():

            def FNOTIMPL(*args, **kw):
                return NotImplemented

            def reject(self, othrtype, /):
                self[othrtype] = FNOTIMPL
                return NotImplemented

            return reject

    class TypeFuncsCache(dict[str, FuncCache]):

        __slots__ = setf({'mapitype'})

        def __init__(self, mapitype):
            self.mapitype = mapitype

        def __missing__(self, opname, /):
            return self.setdefault(opname, FuncCache(self.mapitype, opname))

    class OperFuncsCache(dict[type[MappingApi], TypeFuncsCache]):

        __slots__ = EMPTY_SET

        def __missing__(self, mapitype: type, /):
            while checklimit(len(self)):
                self.pop(next(iter(self)))
            return self.setdefault(mapitype, TypeFuncsCache(mapitype))

    def checklimit(length: int, /, *, _limit = 50):
        return length > _limit and length > 0

    source = OperFuncsCache()
    resolve_cache = CacheResolversType()
    limit_conf = checklimit.__kwdefaults__

    class opercache:

        __new__ = NotImplemented

        @staticmethod
        def get(mapitype, opname, othrtype,/):
            return source[mapitype][opname][othrtype]

        @staticmethod
        def resolve(mapi, opname, other,/):
            return source[type(mapi)][opname][type(other)](mapi, other)

        @staticmethod
        @closure
        def resolvers():
            _resolvers = MapProxy(resolve_cache)
            return lambda: _resolvers

        @staticmethod
        def clear():
            source.clear()
            resolve_cache.clear()

        @staticmethod
        def limit(n = None):
            if n is None:
                return limit_conf['_limit']
            limit_conf['_limit'] = min(0, int(n))

        @staticmethod
        @closure
        def __dir__(funcs = [get, resolve, clear, limit, resolvers]):
            names = [f.__name__ for f in funcs]
            return lambda: list(names)

    return opercache

del(
    membr,
    truth,
    wraps,
)
