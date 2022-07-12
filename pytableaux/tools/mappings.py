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

from collections import deque
from collections.abc import Mapping
from itertools import chain
from types import MappingProxyType as MapProxy

from pytableaux import __docformat__
from pytableaux.tools import EMPTY_MAP, EMPTY_SET, abcs, isattrstr, itemsiter

__all__ = (
    'DequeCache',
    'dictattr',
    'dictns',
    'EMPTY_MAP',
    'ItemMapEnum',
    'KeySetAttr',
    'MapCover',
)

class MapCover(Mapping, abcs.Copyable, immutcopy = True):
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

    def update(self, it = None, /, **kw):
        if it is None:
            it = iter(EMPTY_SET)
        else:
            it = itemsiter(it)
        if len(kw):
            it = chain(it, itemsiter(kw))
        setitem = self.__setitem__
        for key, value in it:
            setitem(key, value)

    @classmethod
    def _keyattr_ok(cls, name: str) -> bool:
        'Return whether it is ok to set the attribute name.'
        return not hasattr(cls, name)

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

class ItemMapEnum(abcs.Ebc):
    """Fixed mapping enum based on item tuples.

    If a member value is defined as a mapping, the member's ``_value_`` attribute
    is converted to a tuple of item tuples during ``__init__()``.

    Implementations should always call ``super().__init__()`` if it is overridden.

    Note that ``.get()`` is implemented as ``.mget()``, since ``AbcEnumMeta``
    uses ``'get'`` as a class method to lookup enum members.
    """

    __slots__ = ('__iter__', '__getitem__', '__len__', '__reversed__',
                 'name', 'value', '_value_')

    def __init__(self, *args):
        if len(args) == 1 and isinstance(args[0], Mapping):
            self._value_ = args = tuple(args[0].items())
        m = dict(args)
        self.__len__ = m.__len__
        self.__iter__ = m.__iter__
        self.__getitem__ = m.__getitem__
        self.__reversed__ = m.__reversed__

    keys = Mapping.keys
    items = Mapping.items
    values = Mapping.values
    mget = Mapping.get # get() is not allowed for Ebc
    _asdict = MapCover._asdict
    __or__ = MapCover.__or__
    __ror__ = MapCover.__ror__

class DequeCache(abcs.Abc):

    __slots__ = ('__getitem__', '__len__', 'queue', 'idx', 'rev')

    @property
    def maxlen(self) -> int:
        return self.queue.maxlen

    def __init__(self, maxlen = 100):

        self.idx = {}
        self.rev: dict[object, set] = {}
        self.queue = deque(maxlen = maxlen)

        self.__getitem__ = self.idx.__getitem__
        self.__len__ = self.rev.__len__

    def __setitem__(self, key, item, /):
        if item in self.rev:
            item = self.idx[item]
        else:
            if len(self) >= self.queue.maxlen:
                old = self.queue.popleft()
                for k in self.rev.pop(old):
                    del(self.idx[k])
            self.idx[item] = item
            self.rev[item] = {item}
            self.queue.append(item)
        self.idx[key] = item
        self.rev[item].add(key)


