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

import functools
import keyword
import re
import sys
from abc import abstractmethod
from collections import defaultdict
from collections.abc import Mapping, MutableMapping, Sequence, Set
from enum import Enum
from operator import gt, lt
from types import FunctionType
from types import MappingProxyType as MapProxy
from typing import (TYPE_CHECKING, Any, Callable, Generic, Iterable, Self,
                    TypeVar)

__all__ = (
    'absindex',
    'closure',
    'dictattr',
    'dictns',
    'dmerged',
    'dund',
    'EMPTY_MAP',
    'EMPTY_SEQ',
    'EMPTY_SET',
    'for_defaults',
    'getitem',
    'group',
    'isattrstr',
    'isdund',
    'isint',
    'ItemMapEnum',
    'KeySetAttr',
    'lazy',
    'MapCover',
    'maxceil',
    'membr',
    'minfloor',
    'NoSetAttr',
    'PathedDict',
    'sbool',
    'select_fget',
    'SeqCover',
    'SequenceSet',
    'SetView',
    'slicerange',
    'substitute',
    'thru',
    'TransMmap',
    'undund',
    'wraps')

EMPTY_MAP = MapProxy({})
EMPTY_SEQ = ()
EMPTY_SET = frozenset()
NOARG = object()
WRASS_SET = frozenset(functools.WRAPPER_ASSIGNMENTS)
_F = TypeVar('_F', bound=Callable)
_KT = TypeVar('_KT')
_T = TypeVar('_T')
_VT = TypeVar('_VT')

if TYPE_CHECKING:
    from typing import overload
    class TypeInstMap(Mapping[type[_VT], _VT]):
        @overload
        def __getitem__(self, key: type[_T]) -> _T: ...
        @overload
        def get(self, key: type[_T]) -> _T: ...
        @overload
        def get(self, key: Any, default: type[_T]) -> _T: ...
        @overload
        def copy(self:_T) -> _T: ...
        @overload
        def setdefault(self, key: type[_T], value: Any) -> _T: ...
        @overload
        def pop(self, key: type[_T]) -> _T: ...
    class TypeTypeMap(Mapping[type[_VT], type[_VT]]):
        @overload
        def __getitem__(self, key: type[_T]) -> type[_T]: ...
        @overload
        def get(self, key: type[_T]) -> type[_T]: ...
        @overload
        def get(self, key: Any, default: type[_T]) -> type[_T]: ...
        @overload
        def copy(self:_T) -> _T: ...
        @overload
        def setdefault(self, key: type[_T], value: Any) -> type[_T]: ...
        @overload
        def pop(self, key: type[_T]) -> type[_T]: ...

def dund(name: str) -> str:
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

def getitem(obj, key, default = NOARG, /):
    "Get by subscript similar to :func:`getattr`."
    try:
        return obj[key]
    except (KeyError, IndexError):
        if default is NOARG:
            raise
        return default

def select_fget(obj):
    """Return :func:`getitem()` if the object has a callable `__getitem__`
    method, else return :func:`getattr()`.
    """
    if callable(getattr(obj, '__getitem__', None)):
        return getitem
    return getattr

def thru(obj: _T) -> _T:
    'Return the argument.'
    return obj

def group(*items):
    """Tuple builder.
    
    Args:
        *items: members.

    Returns:
        The tuple of arguments.
    """
    return items

def isint(obj) -> bool:
    'Whether the argument is an :obj:`int` instance'
    return isinstance(obj, int)

def isattrstr(obj) -> bool:
    "Whether the argument is a non-keyword identifier string"
    return (
        isinstance(obj, str) and
        obj.isidentifier() and
        not keyword.iskeyword(obj))

re_boolyes = re.compile(r'^(true|yes|1)$', re.I)
'Regex for string boolean `yes`.'


def sbool(arg: str, /) -> bool:
    "Cast string to boolean, leans toward ``False``."
    return bool(re_boolyes.match(arg))

def minfloor(floor: _T, it: Iterable[_T], default=None) -> _T:
    """Return the minimum value of ``it``, stopping when a value less than or
    equal to ``floor`` is reached.
    """
    return _limit_best(lt, floor, it, default, 'minfloor')

def maxceil(ceil: _T, it: Iterable[_T], default=None) -> _T:
    """Return the maximum value of ``it``, stopping when a value greater than
    or equal to ``ceil`` is reached.
    """
    return _limit_best(gt, ceil, it, default, 'maxceil')

def limit_best(better: Callable[[_T, _T], bool], limit: _T, it: Iterable[_T], default=None) -> _T:
    """Generic form for :func:`minfloor()` and :func:`maxceil()`.

    Args:
        better: A pairwise comparison function, e.g. :func:`operator.lt`
        limit: The limit, e.g. floor or ceil.
        it: The iterable.
        default: A default value for an empty iterable.
    """
    return _limit_best(better, limit, it, default, 'limit_best')

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
        if val == limit or better(val, limit):
            return val
        if better(val, best):
            best = val
    return best

def substitute(collection: _T, old, new) -> _T:
    """Return a new instance of the collection type with ``new`` substituted
    for ``old``.
    """
    return type(collection)(new if x == old else x for x in collection)

def for_defaults(defaults: Mapping[_KT, _VT], override: Mapping, /) -> dict[_KT, _VT]:
    """Return a dict with keys from ``defaults``, with values from ``override``,
    or ``defaults`` if missing.
    """
    if not override:
        return dict(defaults)
    return {key: override.get(key, defval) for key, defval in defaults.items()}

def absindex(seqlen: int, index: int, /, strict = True) -> int:
    'Normalize to positive/absolute index.'
    if index < 0:
        index = seqlen + index
    if strict and (index >= seqlen or index < 0):
        raise IndexError(f'Index out of range: {index}')
    return index

def slicerange(seqlen: int, slice_: slice, values, /, strict = True) -> range:
    'Get a range of indexes from a slice and new values, and perform checks.'
    range_ = range(*slice_.indices(seqlen))
    if len(range_) != len(values):
        if strict:
            raise ValueError(
                f'Attempt to assign sequence of size {len(values)} '
                f'to slice of size {len(range_)}')
        if abs(slice_.step or 1) != 1:
            raise ValueError(
                f'Attempt to assign sequence of size {len(values)} '
                f'to extended slice of size {len(range_)}')
    return range_

def _prevmodule(thisname = __name__, /):
    f = sys._getframe()
    while (f := f.f_back) is not None:
        val = f.f_globals.get('__name__', '__main__')
        if val != thisname:
            return val

class wraps(dict):
    'Replacement for :func:`functools.wraps`.'

    __slots__ = ('only', 'wrapped')

    def __init__(self, wrapped = None, /, *, only = WRASS_SET, exclude = EMPTY_SET, **kw):
        'Initialize argument, initial input function that will be decorated.'
        self.wrapped = wrapped
        only = set(map(dund, only))
        only.difference_update(map(dund, exclude))
        only.intersection_update(WRASS_SET)
        self.only = only
        self.update(**kw)
        if wrapped:
            self.update(wrapped)
            if (k := '__module__') in only and k not in self:
                if (v := getattr(wrapped, '__objclass__', None)):
                    self.setdefault(k, v)
                else:
                    self.setdefault(k, _prevmodule())

    def __call__(self, wrapper):
        'Decorate function. Receives the wrapper function and updates its attributes.'
        self.update(wrapper)
        if isinstance(wrapper, (classmethod, staticmethod)):
            self.write(wrapper.__func__)
        else:
            self.write(wrapper)
        return wrapper

    def write(self, wrapper):
        "Write wrapped attributes to a wrapper."
        for attr in filter(self.__contains__, self.only):
            setattr(wrapper, attr, self[attr])
        if callable(self.wrapped):
            wrapper.__wrapped__ = self.wrapped
        return wrapper

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

    def read(self, obj):
        "Read relevant attributes from object/mapping."
        get = select_fget(obj)
        for name in self.only:
            if (value := get(obj, name, None)):
                yield name, value
            elif (value := get(obj, undund(name), None)):
                yield name, value

    def setdefault(self, key, value):
        "Override value if key is relevant and value is not empty."
        if key in self.only:
            if value:
                self[key] = value
        return self[key]
            
    def __setitem__(self, key, value):
        if key in self or key not in self.only:
            raise KeyError(key)
        super().__setitem__(key, value)

    def __repr__(self):
        return f'{type(self).__name__}({dict(self)})'


pass

def closure(func: Callable[..., _T]) -> _T:
    """Closure decorator calls the argument and returns its return value.
    If the return value is a function, updates its wrapper.
    """
    ret = func()
    if isinstance(ret, (classmethod, staticmethod, FunctionType)):
    # if type(ret) is FunctionType:
        wraps(func).write(ret)
    return ret

pass

@closure
def dmerged():

    # TODO: memoize ...

    def merger(a: Mapping, b: Mapping, /) -> dict:
        'Basic dict merge copy, recursive for dict value.'
        c = {}
        for key, value in b.items():
            if isinstance(value, Mapping):
                if isinstance(a.get(key), Mapping):
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


class membr:

    __slots__ = ('callable', 'args', 'kwargs', '__name__', '__qualname__')

    callable: Callable
    args: tuple
    kwargs: dict

    @property
    def name(self) -> str:
        try:
            return self.__name__
        except AttributeError:
            return type(self).__name__

    def __init__(self, callable: Callable, *args, **kw):
        self.callable = callable
        self.args = args
        self.kwargs = kw

    def __call__(self):
        return self.callable(self, *self.args, **self.kwargs)

    @classmethod
    def defer(cls, wrapped: Callable[[membr], _F]):
        @wraps(wrapped)
        def wrapper(*args, **kw):
            return cls(wrapped, *args, **kw)
        return wrapper

    def __set_name__(self, owner, name):
        self.__name__ = name
        self.__qualname__ = f'{owner.__name__}.{name}'
        setattr(owner, name, self())

    def __repr__(self) -> str:
        if not hasattr(self, '__qualname__') or not callable(self):
            return object.__repr__(self)
        return '<callable %s at %s>' % (self.__qualname__, hex(id(self)))

class NoSetAttr:
    'Lame thing that does a lame thing.'

    enabled: bool
    "Whether raising is enabled."

    defaults = MapProxy(dict(
        efmt = (
            "Attribute '{0}' of '{1.__class__.__name__}' "
            "objects is readonly").format,
        # Control attribute name to check on the object,
        # e.g. '_readonly', in addition to this object's
        # `enabled` setting.
        attr = '_readonly',
        # If `True`: Check `attr` on the object's class;
        # If set to a `type`, check the `attr` on that class;
        # If Falsy, only check for this object's `enabled` setting.
        cls = None))

    __slots__ =  ('cache', 'opts', 'enabled')

    opts: dict
    cache: dict[tuple, dict]

    def __init__(self, /, *, enabled = True, **opts):
        self.enabled = bool(enabled)
        self.opts = for_defaults(self.defaults, opts)
        self.cache = defaultdict(dict)

    def __call__(self, base: type, **opts):
        return self._make(base.__setattr__, **(self.opts | opts))

    def _make(self, wrapped, /, efmt, attr, cls):
        if cls is True:
            check = self._clschecker(attr)
        elif cls:
            check = self._fixedchecker(attr, cls)
        else:
            check = self._selfchecker(attr)
        @wraps(wrapped)
        def wrapper(obj, name, value, /):
            if self.enabled and check(obj):
                raise AttributeError(efmt(name, obj))
            wrapped(obj, name, value)
        return wrapper

    def cached(wrapped: _F):
        @wraps(wrapped)
        def wrapper(self: NoSetAttr, *args):
            cache = self.cache[wrapped]
            try:
                return cache[args]
            except KeyError:
                return cache.setdefault(args, wrapped(self, *args))
        return wrapper

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


class MapCover(Mapping[_KT, _VT]):
    'Mapping reference.'

    __slots__ = ('__getitem__', '_cov_mapping')
    _cov_mapping: Mapping

    def __init__(self, mapping: Mapping, /):
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

class SeqCover(Sequence):
    'Sequence cover.'

    class CoverAttr(frozenset, Enum):
        REQUIRED = {
            '__len__',
            '__getitem__',
            '__contains__',
            '__iter__',
            'count',
            'index'}
        OPTIONAL = {'__reversed__'}
        ALL = REQUIRED | OPTIONAL

    __slots__ = CoverAttr.ALL

    def __new__(cls, seq: Sequence, /):
        self = object.__new__(cls)
        for name in cls.CoverAttr.ALL:
            value = getattr(seq, name, NOARG)
            if value is NOARG:
                if name in cls.CoverAttr.REQUIRED:
                    raise AttributeError(name)
                continue
            setattr(self, name, value)
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

    @classmethod
    def _keyattr_ok(cls, name: str) -> bool:
        'Return whether it is ok to set the attribute name.'
        return not hasattr(cls, name)

class dictattr(KeySetAttr, dict[_KT, _VT]):
    "Dict attr base class."

    __slots__ = EMPTY_SET

    def __init__(self, *args, **kw):
        self.update(*args, **kw)

    pop = MutableMapping.pop
    popitem = MutableMapping.popitem
    setdefault = MutableMapping.setdefault
    update = MutableMapping.update

class dictns(dictattr[_KT, _VT]):
    "Dict attr namespace with __dict__ slot and liberal key approval."

    @classmethod
    def _keyattr_ok(cls, name):
        return not name.startswith('_') and not hasattr(cls, name)

class TransMmap(MutableMapping[_KT, _VT], MapCover[_KT, _VT]):
    'Mutable mapping with key/value translators'

    __slots__ = (
        '__delitem__',
        '__getitem__',
        '__setitem__')

    kget = kset = vget = vset = staticmethod(thru)

    def __init__(self, *args, **kw):
        self._cov_mapping = MapProxy(mapping := dict(*args, **kw))
        self.__getitem__ = lambda key: self.vget(mapping.__getitem__(self.kget(key)))
        self.__setitem__ = lambda key, value: mapping.__setitem__(self.kset(key), self.vset(value))
        self.__delitem__ = lambda key: mapping.__delitem__(self.kset(key))


class PathedDict(dict[str, _VT]):
    "A nested dict that supports key path expressions like 'a:b:c'."

    separator: str = ':'
    default = dict

    __slots__ = EMPTY_SET

    def __init__(self, *args, **kw):
        self.update(*args, **kw)

    def __getitem__(self, key):
        try:
            return super().__getitem__(key)
        except KeyError:
            if not isinstance(key, str) or self.separator not in key:
                raise
        obj = self
        for key in key.split(self.separator):
            obj = obj[key]
        return obj

    def __setitem__(self, key, value):
        if not isinstance(key, str) or self.separator not in key:
            return super().__setitem__(key, value)
        path = key.split(self.separator)
        last = path.pop()
        obj = self
        for key in path:
            try:
                obj = obj[key]
            except KeyError:
                obj = obj.setdefault(key, self.default())
        obj[last] = value

    def __delitem__(self, key):
        try:
            super().__delitem__(key)
        except KeyError:
            if not isinstance(key, str) or self.separator not in key:
                raise
        path = key.split(self.separator)
        last = path.pop()
        obj = self
        for key in path:
            obj = obj[key]
        del obj[last]

    get = MutableMapping.get
    pop = MutableMapping.pop
    popitem = MutableMapping.popitem
    setdefault = MutableMapping.setdefault
    update = MutableMapping.update

class ForObjectBuilder(Generic[_T]):

    __slots__ = EMPTY_SET

    @classmethod
    def for_object(cls, obj: _T, /) -> Self:
        return cls(
            *cls.get_obj_args(obj),
            **dict(cls.get_obj_kwargs(obj)))

    @classmethod
    @abstractmethod
    def get_obj_args(cls, obj: _T, /) -> Iterable[Any]:
        yield from EMPTY_SET

    @classmethod
    @abstractmethod
    def get_obj_kwargs(cls, obj: _T, /) -> Iterable[tuple[str, Any]]:
        yield from EMPTY_SET

class ItemMapEnum(Enum):
    """Fixed mapping enum based on item tuples.

    If a member value is defined as a mapping, the member's ``_value_`` attribute
    is converted to a tuple of item tuples during ``__init__()``.

    Implementations should always call ``super().__init__()`` if it is overridden.
    """

    __slots__ = (
        '__iter__',
        '__getitem__',
        '__len__',
        '__reversed__',
        'name',
        'value',
        '_name_',
        '_value_')

    def __init__(self, *args):
        if len(args) == 1 and isinstance(args[0], Mapping):
            self._value_ = args = tuple(args[0].items())
        m = dict(args)
        self.__len__ = m.__len__
        self.__iter__ = m.__iter__
        self.__getitem__ = m.__getitem__
        self.__reversed__ = m.__reversed__
        self.name = self._name_
        self.value = self._value_

    keys = Mapping.keys
    items = Mapping.items
    values = Mapping.values
    get = Mapping.get

    def __or__(self, other):
        return dict(self) | other

    def __ror__(self, other):
        return other | dict(self)

    def _asdict(self):
        'Compatibility for JSON serialization.'
        return dict(self)



from .abcs import Copyable

pass


class SetView(Set, Copyable, immutcopy=True):
    'Set cover.'

    __slots__ = ('__contains__', '__iter__', '__len__')

    def __new__(cls, set_, /,):
        if not isinstance(set_, Set):
            raise TypeError(type(set_))
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

from .hybrids import EMPTY_QSET as EMPTY_QSET
from .hybrids import SequenceSet as SequenceSet
from .hybrids import qset as qset
from .hybrids import qsetf as qsetf

pass

from . import lazy as lazy
