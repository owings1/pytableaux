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
pytableaux.lang
---------------

"""
from __future__ import annotations

from collections.abc import Mapping
from types import MappingProxyType as MapProxy
from typing import ClassVar, NamedTuple

from pytableaux.errors import Emsg
from pytableaux.tools import (EMPTY_MAP, EMPTY_SET, NoSetAttr, abcs, closure,
                              dxopy, raisr)

__all__ = (
    # Classes
    'BiCoords',
    'LangCommonEnum',
    'LangCommonEnumMeta',
    'LangCommonMeta',
    'LexicalAbcMeta',
    'Marking',
    'Notation',
    'RenderSet',
    'SysPredEnumMeta',
    'TableStore',
    'TriCoords',

    # Subpackage convenience import
    'Argument',
    'Atomic',
    'Constant',
    'Lexical',
    'LexType',
    'LexWriter',
    'Operated',
    'Operator',
    'Parser',
    'ParseTable',
    'Predicate',
    'Predicated',
    'Predicates',
    'Quantified',
    'Quantifier',
    'Sentence',
    'Variable')

nosetattr = NoSetAttr(attr = '_readonly', enabled = False)
raiseae = raisr(AttributeError)

#==========================+
#  Meta classes            |
#==========================+

class LangCommonMeta(abcs.AbcMeta):
    "Common metaclass for lang classes."
    
    # The nosetattr member is shared among these classes and is activated after
    # the modules are fully initialized.

    _readonly : bool
    __delattr__ = raiseae
    __setattr__ = nosetattr(abcs.AbcMeta)

class LangCommonEnumMeta(abcs.EbcMeta):
    'Common Enum metaclass for lang classes.'

    _readonly : bool
    __delattr__ = raiseae
    __setattr__ = nosetattr(abcs.EbcMeta)

class LexicalAbcMeta(LangCommonMeta):
    "Common metaclass for non-Enum lexical classes."

    # Populated in lex module.
    __call__ = NotImplemented

class SysPredEnumMeta(LangCommonEnumMeta):
    "Meta class for special system predicates enum."

#==========================+
#  Base classes            |
#==========================+

class LangCommonEnum(abcs.Ebc, metaclass = LangCommonEnumMeta):
    'Common Enum base class for lang classes.'

    # __slots__   = 'value', '_value_', '_name_',

    __delattr__ = raiseae
    __setattr__ = nosetattr(abcs.Ebc, cls = True)

#==========================+
#  Enum classes            |
#==========================+

class Notation(LangCommonEnum):
    'Notation (polish/standard) enum class.'

    default: ClassVar[Notation]
    "The default notation."

    charsets: set[str]
    "All render charsets for the notation's writer classes."

    default_charset: str
    "The render charset of the notation's default writer."

    writers: set[type[LexWriter]]
    "All writer classes for the notation."

    DefaultWriter: type[LexWriter]
    "The notations's default writer class."

    rendersets: set[RenderSet]
    "All RenderSets of the notation."

    Parser: type[Parser]
    "The notation's parser class."

    #--- Members

    polish = 'polish',
    "Polish notation."

    standard = 'standard',
    "Standard notation."

    def __init__(self, name, /):
        default_charset = 'unicode'
        self.charsets = set((default_charset,))
        self.default_charset = default_charset
        self.writers = set()
        self.DefaultWriter = None
        self.rendersets = set()

    __slots__ = (
        'charsets',
        'default_charset',
        'DefaultWriter',
        'Parser',
        'rendersets',
        'writers')

    @classmethod
    def get_common_charsets(cls) -> list[str]:
        "Get charsets common to all notations."
        charsets: set[str] = set(
            charset
            for notn in Notation
                for charset in notn.charsets)
        for notn in Notation:
            charsets.intersection_update(notn.charsets)
        return sorted(charsets)

    @closure
    def __setattr__():
        from enum import Enum
        esa = Enum.__setattr__
        def setter(self, name: str, value):
            if name == 'Parser' and not hasattr(self, name):
                esa(self, name, value)
            else:
                super().__setattr__(name, value)
        return setter

    @classmethod
    def _member_keys(cls, member: Notation, /):
        return super()._member_keys(member).union({member.name.capitalize()})

    @abcs.abcf.after
    def _(cls):
        cls.default = cls.polish


class Marking(str, LangCommonEnum):
    'Miscellaneous marking/punctuation enum.'

    paren_open = 'paren_open'
    "Open parenthesis marking."

    paren_close = 'paren_close'
    "Close parenthesis marking."

    whitespace = 'whitespace'
    "Whitespace marking."

    digit = 'digit'
    "Digit marking."

    meta = 'meta'
    "Meta marking."

    subscript = 'subscript'
    "Subscript marking."

    tableau = 'tableau'
    "Tableau marking."

#==========================+
#  Aux classes             |
#==========================+

class BiCoords(NamedTuple):
    "An (`index`, `subscript`) integer tuple."

    index: int
    "The index integer."

    subscript: int
    "The subscript integer."

    class Sorting(NamedTuple):
        "BiCoords sorting tuple (`subscript`, `index`)."

        subscript: int
        "The subscript integer."

        index: int
        "The index integer."

    def sorting(self):
        "Return the sorting tuple."
        return self.Sorting(self.subscript, self.index)

    first = (0, 0)

    def __repr__(self):
        return repr(tuple(self))

    @staticmethod
    def min_unused(used, maxi):
        # finds the mimimum available by searching for gaps.
        if not used:
            return BiCoords.first
        index = 0
        sub = 0
        while (index, sub) in used:
            index += 1
            if index > maxi:
                index, sub = 0, sub + 1
        return BiCoords(index, sub)

class TriCoords(NamedTuple):
    "An (`index`, `subscript`, `arity`) integer tuple."

    index: int
    "The index integer."

    subscript: int
    "The subscript integer."

    arity: int
    "The arity integer."

    class Sorting(NamedTuple):
        "TriCoords sorting tuple (`subscript`, `index`, `arity`)."

        subscript: int
        "The subscript integer."

        index: int
        "The index integer."

        arity: int
        "The arity integer."

    def sorting(self):
        "Return the sorting tuple."
        return self.Sorting(self.subscript, self.index, self.arity)

    first = (0, 0, 1)

    def __repr__(self):
        return repr(tuple(self))

BiCoords.first = BiCoords._make(BiCoords.first)
TriCoords.first = TriCoords._make(TriCoords.first)


class TableStore(metaclass = LangCommonMeta):

    default_fetch_key: ClassVar[str]

    _instances: ClassVar[dict]

    __slots__ = EMPTY_SET

    @classmethod
    def load(cls, notn, key, data, /):
        """Create and store instance from data.

        Args:
            notn: The notation
            key: The unique key
            data: The data mapping

        Raises:
            Emsg.DuplicateKey: on duplicate key for notation

        Returns:
            The instance
        """
        notn = Notation[notn]
        idx = cls._instances[notn]
        if key in idx:
            raise Emsg.DuplicateKey((notn, key))
        return idx.setdefault(key, cls(data, (notn, key)))

    @classmethod
    def fetch(cls, notn, key = None, /):
        """Get a loaded instance.

        Args:
            notn: The notation
            key: The unique key. Defaults to class default.

        Returns:
            The instance
        """        
        if key is None:
            key = cls.default_fetch_key
        notn = Notation[notn]
        idx = cls._instances[notn]
        try:
            return idx[key]
        except KeyError:
            pass
        store = cls._builtin[notn]
        data = store[key]
        return cls.load(notn, key, data)

    @classmethod
    def available(cls, notn):
        """List the loaded keys for a notation.

        Args:
            notn: The notation

        Returns:
            list: The sorted keys
        """        
        notn = Notation(notn)
        idx = cls._instances[notn]
        store = cls._builtin[notn]
        return sorted(set(idx).union(store))

    @classmethod
    def _initcache(cls, notns, builtin):
        if cls is __class__ or hasattr(cls, '_builtin'):
            raise TypeError
        cls._builtin = MapProxy(dict(builtin))
        notns = set(notns).union(cls._builtin)
        cls._instances = {notn: {} for notn in notns}
        # Prefetch
        for notn in notns:
            # Default for notation.
            cls.fetch(notn)
            # All available.
            for key in cls.available(notn):
                cls.fetch(notn, key)


class RenderSet(TableStore, Mapping):
    'Lexical writer table data class.'

    default_fetch_key = 'ascii'

    notation: Notation
    "The notation."

    renders: Mapping
    "Render functions."

    strings: Mapping
    "Fixed strings mapping."

    data: Mapping
    keypair: tuple

    @property
    def charset(self) -> str:
        "The charset name."
        return self['charset']

    @property
    def fetchkey(self) -> str:
        return self.keypair[1]

    __slots__ = (
        '__getitem__',
        'data',
        'keypair',
        'notation',
        'renders',
        'strings',
        'hash')

    def __init__(self, data, keypair, /):
        self.data = data = dxopy(data, True)
        self.__getitem__ = data.__getitem__
        self.keypair = keypair
        self.notation = notn = Notation(data['notation'])
        self.renders = data.get('renders', EMPTY_MAP)
        self.strings = data.get('strings', EMPTY_MAP)
        self.hash = self._compute_hash()
        notn.charsets.add(self.charset)
        notn.rendersets.add(self)

    def string(self, ctype, value) -> str:
        if ctype in self.renders:
            return self.renders[ctype](value)
        return self.strings[ctype][value]

    def __len__(self):
        return len(self.data)

    def __iter__(self):
        return iter(self.data)

    def __reversed__(self):
        return reversed(self.data)

    def __hash__(self):
        return self.hash

    def __eq__(self, other):
        if self is other:
            return True
        return type(self) is type(other) and self.data == other.data

    def _compute_hash(self) -> int:
        r, s = self.renders, self.strings
        vv = *(*r.values(), *s.values()),
        ktup = *(*r.keys(), *s.keys()),
        vtup = *((*v.items(),) if isinstance(v, Mapping) else v for v in vv),
        return hash((ktup, vtup))



from pytableaux.lang.lex import Atomic, Constant
from pytableaux.lang.lex import CoordsItem as CoordsItem
from pytableaux.lang.lex import Lexical, LexType, Operated, Operator
from pytableaux.lang.lex import Parameter as Parameter

pass

from pytableaux.lang.lex import (Predicate, Predicated, Quantified, Quantifier,
                                 Sentence, Variable)

pass
from pytableaux.lang.parsing import Parser, ParseTable

pass
from pytableaux.lang.collect import Argument, Predicates

pass
from pytableaux.lang.writing import LexWriter
