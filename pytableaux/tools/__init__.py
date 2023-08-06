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
pytableaux.tools
----------------

"""
from __future__ import annotations

import builtins
import functools
import itertools
import keyword
import re
import sys
from abc import abstractmethod as abstract
from collections import defaultdict
from collections.abc import Mapping, Sequence, Set
from enum import Enum
from operator import gt, lt, truth
from types import DynamicClassAttribute, FunctionType
from types import MappingProxyType as MapProxy
from typing import TYPE_CHECKING, Any, Callable, Generic, TypeVar

__all__ = (
    'absindex',
    'abstract',
    'closure',
    'dictattr',
    'dictns',
    'dund',
    'dxopy',
    'EMPTY_MAP',
    'EMPTY_SEQ',
    'EMPTY_SET',
    'for_defaults',
    'getitem',
    'isattrstr',
    'isdund',
    'isint',
    'isstr',
    'itemsiter',
    'key0',
    'lazy',
    'MapCover',
    'maxceil',
    'membr',
    'minfloor',
    'NoSetAttr',
    'sbool',
    'select_fget',
    'SeqCover',
    'SetView',
    'slicerange',
    'substitute',
    'thru',
    'true',
    'undund',
    'wraps')

EMPTY_MAP = MapProxy({})
EMPTY_SEQ = ()
EMPTY_SET = frozenset()
NOARG = object()
WRASS_SET = frozenset(functools.WRAPPER_ASSIGNMENTS)
_Self = TypeVar('_Self')
_T = TypeVar('_T')

if TYPE_CHECKING:
    from typing import overload
    class property(builtins.property, Generic[_Self, _T]):
        fget: Callable[[_Self], Any] | None
        fset: Callable[[_Self, Any], None] | None
        fdel: Callable[[_Self], None] | None
        @overload
        def __init__(
            self,
            fget: Callable[[_Self], _T] | None = ...,
            fset: Callable[[_Self, Any], None] | None = ...,
            fdel: Callable[[_Self], None] | None = ...,
            doc: str | None = ...,
        ) -> None: ...
        def getter(self, __fget: Callable[[_Self], _T]) -> property[_Self, _T]: ...
        def setter(self, __fset: Callable[[_Self, Any], None]) -> property[_Self, _T]: ...
        def deleter(self, __fdel: Callable[[_Self], None]) -> property[_Self, _T]: ...
        def __get__(self, __obj: _Self, __type: type | None = ...) -> _T: ...
        def __set__(self, __obj: _Self, __value: Any) -> None: ...
        def __delete__(self, __obj: _Self) -> None: ...

def closure(func: Callable[..., _T]) -> _T:
    """Closure decorator calls the argument and returns its return value.
    If the return value is a function, updates its wrapper.
    """
    ret = func()
    if type(ret) is FunctionType:
        functools.update_wrapper(ret, func)
    return ret

def thru(obj):
    'Return the argument.'
    return obj

def true(_):
    'Always returns ``True``.'
    return True

def key0(obj):
    'Get key/subscript ``0``.'
    return obj[0]

def dund(name:str) -> str:
    "Convert name to dunder format."
    return name if isdund(name) else f'__{name}__'

def isdund(name: str) -> bool:
    'Whether the string is a dunder name string.'
    return (
        len(name) > 4 and
        name[:2] == name[-2:] == '__' and
        name[2] != '_' and
        name[-3] != '_')

def undund(name: str) -> str:
    "Remove dunder from the name."
    if isdund(name):
        return name[2:-2]
    return name

def isint(obj) -> bool:
    'Whether the argument is an :obj:`int` instance'
    return isinstance(obj, int)

def isattrstr(obj) -> bool:
    "Whether the argument is a non-keyword identifier string"
    return (
        isinstance(obj, str) and
        obj.isidentifier() and
        not keyword.iskeyword(obj))

def isstr(obj) -> bool:
    'Whether the argument is an :obj:`str` instance'
    return isinstance(obj, str)

re_boolyes = re.compile(r'^(true|yes|1)$', re.I)
'Regex for string boolean `yes`.'

def sbool(arg: str, /) -> bool:
    "Cast string to boolean, leans toward ``False``."
    return bool(re_boolyes.match(arg))

def getitem(obj, key, default = NOARG, /):
    "Get by subscript similar to :func:`getattr`."
    try:
        return obj[key]
    except (KeyError, IndexError):
        if default is NOARG:
            raise
        return default

def select_fget(obj):
    if callable(getattr(obj, '__getitem__', None)):
        return getitem
    return getattr

def minfloor(floor, it, default=None):
    return _limit_best(lt, floor, it, default, 'minfloor')

def maxceil(ceil, it, default=None):
    return _limit_best(gt, ceil, it, default, 'maxceil')

def _limit_best(better, limit, it, default, _name, /):
    it = iter(it)
    if default is not None:
        best = default
    else:
        try:
            best = next(it)
        except StopIteration:
            raise ValueError(
                f"{_name}() arg is an empty sequence") from None
    for val in it:
        if val == limit:
            return val
        if better(val, best):
            best = val
    return best

def substitute(coll, old_value, new_value):
    return type(coll)(new_value if x == old_value else x for x in coll)

def for_defaults(defaults: Mapping, override: Mapping, /) -> dict:
    if not override:
        return dict(defaults)
    return {key: override.get(key, defval) for key, defval in defaults.items()}

def absindex(seqlen: int, index: int, /, strict = True):
    'Normalize to positive/absolute index.'
    if index < 0:
        index = seqlen + index
    if strict and (index >= seqlen or index < 0):
        raise Emsg.IndexOutOfRange(index)
    return index

def slicerange(seqlen: int, slice_: slice, values, /, strict = True):
    'Get a range of indexes from a slice and new values, and perform checks.'
    range_ = range(*slice_.indices(seqlen))
    if len(range_) != len(values):
        if strict:
            raise Emsg.MismatchSliceSize(values, range_)
        if abs(slice_.step or 1) != 1:
            raise Emsg.MismatchExtSliceSize(values, range_)
    return range_

@closure
def itemsiter():

    def api(obj, /, *, vget = None, kpred = true, vpred = true, koper = truth, voper = truth):
        if vget:
            return gen1(obj.__iter__, vget, kpred, vpred, koper, voper)
        try:
            return gen1(obj.keys, obj.__getitem__, kpred, vpred, koper, voper)
        except AttributeError:
            return gen2(obj, kpred, vpred, koper, voper)

    def gen1(getkeys, vget, kpred, vpred, koper, voper):
        for k in getkeys():
            if koper(kpred(k)):
                v = vget(k)
                if voper(vpred(v)):
                    yield k, v

    def gen2(items, kpred, vpred, koper, voper):
        for k, v in items:
            if koper(kpred(k)) and voper(vpred(v)):
                yield k, v

    return api

@closure
def dxopy():

    def api(a, proxy = False, /, ):
        """Deep map copy, recursive for mapping values.
        Safe for circular reference. Second arg supports
        deep proxy.
        """
        return runner(a, {}, MapProxy if proxy else thru)

    def runner(a: Mapping, memo, wrap):
        if (i := id(a)) in memo:
            return a
        memo[i] = True
        m = wrap({
            key: runner(value, memo, wrap)
                if isinstance(value, Mapping)
                else value
            for key, value in a.items()})
        memo[id(m)] = True
        return m

    return api

@closure
def dmerged():


    # TODO: memoize ...

    def merger(a: Mapping, b: Mapping, /) -> dict:
        'Basic dict merge copy, recursive for dict value.'
        c = {}
        for key, value in b.items():
            if isinstance(value, Mapping):
                avalue = a.get(key)
                if isinstance(avalue, Mapping):
                    c[key] = merger(a[key], value)
                else:
                    c[key] = dcopy(value)
            else:
                c[key] = value
        for key, value in a.items():
            if key not in c:
                if isinstance(value, Mapping):
                    c[key] = dcopy(value)
                else:
                    c[key] = value
        return c

    def dcopy(a: Mapping, /) -> dict:
        'Basic dict copy of a mapping, recursive for mapping values.'
        return {
            key: dcopy(value)
                if isinstance(value, Mapping)
                else value
            for key, value in a.items()}

    return merger

from . import abcs

pass
from ..errors import Emsg, check


class BaseMember:

    __slots__ = ('__name__', '__qualname__', '__owner')

    def __set_name__(self, owner, name):
        self.__owner = owner
        self.__name__ = name
        self.__qualname__ = f'{owner.__name__}.{name}'
        self.sethook(owner, name)

    def sethook(self, owner, name):
        pass

    @property
    def owner(self):
        try:
            return self.__owner
        except AttributeError:
            pass

    @property
    def name(self) -> str:
        try:
            return self.__name__
        except AttributeError:
            return type(self).__name__

    def __repr__(self) -> str:
        if not hasattr(self, '__qualname__') or not callable(self):
            return object.__repr__(self)
        return '<callable %s at %s>' % (self.__qualname__, hex(id(self)))

class membr(BaseMember):

    __slots__ = ('cbak',)

    owner: object
    cbak: tuple

    def __init__(self, cb, *args, **kw):
        self.cbak = cb, args, kw

    def sethook(self, owner, name):
        setattr(owner, name, self())

    def __call__(self):
        cb, args, kw = self.cbak
        return cb(self, *args, **kw)

    @classmethod
    def defer(cls, fdefer):
        def fd(member, *args, **kw):
            return fdefer(member, *args, **kw)
        def f(*args, **kw):
            return cls(fd, *args, **kw)
        return f

def _prevmodule(thisname = __name__, /):
    f = sys._getframe()
    while (f := f.f_back) is not None:
        val = f.f_globals.get('__name__', '__main__')
        if val != thisname:
            return val

class wraps(dict):

    __slots__ = ('only', 'original')

    def __init__(self, original = None, /, only = WRASS_SET, exclude = EMPTY_SET, **kw):
        'Initialize argument, initial input function that will be decorated.'
        self.original = original
        only = set(map(dund, only))
        only.difference_update(map(dund, exclude))
        only.intersection_update(WRASS_SET)
        self.only = only
        if kw:
            self.update(kw)
        if original:
            self.update(original)
            if (k := '__module__') in only and k not in self:
                if (v := getattr(original, '__objclass__', None)):
                    self.setdefault(k, v)
                else:
                    self.setdefault(k, _prevmodule())

    def __call__(self, fout):
        'Decorate function. Receives the wrapper function and updates its attributes.'
        self.update(fout)
        if isinstance(fout, (classmethod, staticmethod)):
            self.write(fout.__func__)
        else:
            self.write(fout)
        return fout

    def read(self, obj):
        "Read relevant attributes from object/mapping."
        get = select_fget(obj)
        for name in self.only:
            if (value := get(obj, name, None)):
                yield name, value
            elif (value := get(obj, undund(name), None)):
                yield name, value

    def write(self, obj):
        "Write wrapped attributes to a wrapper."
        for attr, val in self.items():
            setattr(obj, attr, val)
        if callable(self.original):
            obj.__wrapped__ = self.original
        return obj

    def update(self, obj = None, /, **kw):
        """Read from an object/mapping and update relevant values. Any attributes
        already present are ignored. Returns self.
        """
        for o in obj, kw:
            if o is not None:
                for attr, val in self.read(o):
                    if attr not in self:
                        self[attr] = val
        return self

    def setdefault(self, key, value):
        "Override value if key is relevant and value is not empty."
        if key in self.only:
            if value:
                self[key] = value
                return value
            return self[key]
            
    def __setitem__(self, key, value):
        if key in self or key not in self.only:
            raise KeyError(key)
        super().__setitem__(key, value)

    def __repr__(self):
        return f'{type(self).__name__}({dict(self)})'

class lazy:

    __slots__ = EMPTY_SET

    def __new__(cls, *args, **kw):
        return cls.get(*args, **kw)

    class get(BaseMember):

        __slots__ = ('key', 'method')
        format = '_{}'.format

        def __new__(cls, key = None, /, method = None):
            """If only argument to constructor is callable, construct and call the
            instance. Otherwise create normally.
            """
            inst = object.__new__(cls)
            inst.method = method
            if not callable(key) or method is not None:
                inst.key = check.inst(key, str)
                if method is not None:
                    check.callable(method)
                return inst
            inst.key = None
            return inst(check.callable(key))

        def __call__(self, method):
            key = self.key or self.format(method.__name__)
            @wraps(method)
            def fget(self):
                try:
                    return getattr(self, key)
                except AttributeError:
                    pass
                setattr(self, key, value := method(self))
                return value
            return fget

        def sethook(self, owner, name):
            if self.key is None:
                self.key = self.format(name)
            setattr(owner, name, self(self.method))

    class prop(get):
        """Return a property with the getter. NB: a setter/deleter should be
        sure to use the correct attribute.
        """

        __slots__ = EMPTY_SET

        @property
        def propclass(self) -> type[property]:
            return property

        if TYPE_CHECKING:
            def __new__(cls, func: Callable[[_Self], _T]) -> property[_Self, _T]: ...

        def __call__(self, method: Callable[[_Self], _T]) -> property[_Self, _T]:
            fget = super().__call__(method)
            return self.propclass(fget, doc = method.__doc__)

    class dynca(prop):
        """Return a DynamicClassAttribute with the getter. NB: a setter/deleter
        should be sure to use the correct attribute.
        """

        @property
        def propclass(self):
            return DynamicClassAttribute

        __slots__ = EMPTY_SET

class NoSetAttr(BaseMember):
    'Lame thing that does a lame thing.'

    enabled: bool
    "Whether raising is enabled."

    _defaults = MapProxy(dict(
        efmt = (
            "Attribute '{0}' of '{1.__class__.__name__}' "
            "objects is readonly").format,
        # Control attribute name to check on the object,
        # e.g. '_readonly', in addition to this object's
        # `enabled` setting.
        attr = None,
        # If `True`: Check `attr` on the object's class;
        # If set to a `type`, check the `attr` on that class;
        # If Falsy, only check for this object's `enabled` setting.
        cls = None))

    __slots__ =  ('cache', 'defaults', 'enabled')

    defaults: dict
    cache: dict[tuple, dict]

    def __init__(self, /, *, enabled = True, **defaults):
        self.enabled = bool(enabled)
        self.defaults = self._defaults | defaults
        self.cache = defaultdict(dict)

    def __call__(self, base: type, **opts):
        return self._make(base.__setattr__, **(self.defaults | opts))

    def _make(self, sa, /, efmt, attr, cls):
        if attr:
            if cls is True:
                check = self._clschecker(attr)
            elif cls:
                check = self._fixedchecker(attr, cls)
            else:
                check = self._selfchecker(attr)
            def f(obj, name, value, /):
                if self.enabled and check(obj):
                    raise AttributeError(efmt(name, obj))
                sa(obj, name, value)
        else:
            def f(obj, name, value, /):
                if self.enabled:
                    raise AttributeError(efmt(name, obj))
                sa(obj, name, value)
        return wraps(sa)(f)

    def cached(func):
        @wraps(func)
        def f(self: NoSetAttr, *args):
            cache = self.cache[func]
            try:
                return cache[args]
            except KeyError:
                return cache.setdefault(args, func(self, *args))
        return f

    @cached
    def _fixedchecker(self, attr, obj):
        return lambda _: getattr(obj, attr, False)

    @cached
    def _callchecker(self, attr, fget):
        return lambda obj: getattr(fget(obj), attr, False)

    @cached
    def _clschecker(self, attr):
        return self._callchecker(type, attr)

    @cached
    def _selfchecker(self, attr):
        return lambda obj: getattr(obj, attr, False)

    del(cached)

    def sethook(self, owner, name):
        func = self(owner.__bases__[0])
        func.__name__ = name
        func.__qualname__ = self.__qualname__
        setattr(owner, name, func)


class SetView(Set, abcs.Copyable, immutcopy = True):
    'Set cover.'

    __slots__ = ('__contains__', '__iter__', '__len__')

    def __new__(cls, set_, /,):
        check.inst(set_, Set)
        self = object.__new__(cls)
        self.__len__ = set_.__len__
        self.__iter__ = set_.__iter__
        self.__contains__ = set_.__contains__
        return self

    def __repr__(self):
        prefix = type(self).__name__
        if len(self):
            return f'{prefix}{set(self)}'
        return f'{prefix}''{}'

class SeqCoverAttr(frozenset, Enum):
    REQUIRED = {'__len__', '__getitem__', '__contains__', '__iter__',
                'count', 'index',}
    OPTIONAL = {'__reversed__'}
    ALL = REQUIRED | OPTIONAL

# class SeqCover(Sequence, abcs.Copyable, immutcopy = True):
class SeqCover(Sequence):

    __slots__ = SeqCoverAttr.ALL

    def __new__(cls, seq: Sequence, /):
        self = object.__new__(cls)
        sa = object.__setattr__
        for name in SeqCoverAttr.REQUIRED:
            sa(self, name, getattr(seq, name))
        for name in SeqCoverAttr.OPTIONAL:
            value = getattr(seq, name, NOARG)
            if value is not NOARG:
                sa(self, name, value)
        return self

    def __repr__(self):
        return f'{type(self).__name__}({list(self)})'

class KeySetAttr:
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

    def update(self, it = None, /, **kw):
        if it is None:
            it = iter(EMPTY_SET)
        else:
            it = itemsiter(it)
        if len(kw):
            it = itertools.chain(it, itemsiter(kw))
        setitem = self.__setitem__
        for key, value in it:
            setitem(key, value)

    @classmethod
    def _keyattr_ok(cls, name: str) -> bool:
        'Return whether it is ok to set the attribute name.'
        return not hasattr(cls, name)

# class MapCover(Mapping, abcs.Copyable, immutcopy = True):
class MapCover(Mapping):
    'Mapping reference.'

    __slots__ = ('__getitem__', '_cov_mapping')
    _cov_mapping: Mapping

    def __init__(self, mapping, /):
        if type(mapping) is not MapProxy:
            mapping = MapProxy(mapping)
        self._cov_mapping = mapping
        self.__getitem__ = mapping.__getitem__

    def __reversed__(self):
        return reversed(self._cov_mapping)

    def __len__(self):
        return len(self._cov_mapping)

    def __iter__(self):
        return iter(self._cov_mapping)

    def __repr__(self):
        return repr(self._asdict())

    def __or__(self, other):
        return dict(self) | other

    def __ror__(self, other):
        return other | dict(self)

    def _asdict(self):
        'Compatibility for JSON serialization.'
        return dict(self)

class dictattr(KeySetAttr, dict):
    "Dict attr base class."

    __slots__ = EMPTY_SET

    def __init__(self, it = None, /, **kw):
        if it is not None:
            self.update(it)
        if len(kw):
            self.update(kw)

class dictns(dictattr):
    "Dict attr namespace with __dict__ slot and liberal key approval."

    @classmethod
    def _keyattr_ok(cls, name):
        return len(name) and name[0] != '_'

class PathedDict(dict):

    separator: str = ':'

    __slots__ = EMPTY_SET

    def __getitem__(self, key):
        try:
            return super().__getitem__(key)
        except KeyError:
            if not isinstance(key, str):
                raise
        key, *keys = key.split(self.separator)
        obj = super().__getitem__(key)
        for key in keys:
            obj = obj[key]
        return obj

    def __setitem__(self, key, value):
        if not isinstance(key, str) or self.separator not in key:
            return super().__setitem__(key, value)
        keys = key.split(self.separator)
        last = keys.pop()
        obj = self
        for key in keys:
            obj = obj.setdefault(key, {})
        obj[last] = value

from .hybrids import EMPTY_QSET as EMPTY_QSET
from .hybrids import qset as qset
from .hybrids import qsetf as qsetf
