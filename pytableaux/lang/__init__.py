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
pytableaux.lang
---------------

"""
from __future__ import annotations

from collections.abc import Mapping
from types import MappingProxyType as MapProxy
from typing import Any, ClassVar, Iterable, NamedTuple, Self

from ..errors import Emsg
from ..tools import EMPTY_MAP, EMPTY_SET, NoSetAttr, abcs, closure, dxopy

__all__ = (
    # Classes
    # 'BiCoords',
    # 'LangCommonEnum',
    # 'LangCommonEnumMeta',
    # 'LangCommonMeta',
    # 'LexicalAbcMeta',
    'Marking',
    'Notation',
    'RenderSet',
    # 'TableStore',
    # 'TriCoords',

    # Subpackage convenience import
    'Argument',
    'Atomic',
    'Constant',
    'CoordsItem',
    'Lexical',
    'LexicalAbc',
    'LexicalEnum',
    'LexType',
    'LexWriter',
    'Operated',
    'Operator',
    'Parameter',
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

#==========================+
#  Meta classes            |
#==========================+

class LangCommonMeta(abcs.AbcMeta):
    "Common metaclass for lang classes."
    
    # The nosetattr member is shared among these classes and is activated after
    # the modules are fully initialized.

    @classmethod
    def __prepare__(cls, clsname, bases, **kw):
        return dict(__slots__=EMPTY_SET)

    _readonly : bool
    __delattr__ = Emsg.ReadOnly.razr
    __setattr__ = nosetattr(abcs.AbcMeta)

class LangCommonEnumMeta(abcs.EbcMeta):
    'Common Enum metaclass for lang classes.'

    _readonly : bool
    # Set in base __init__ for Python 3.11 Enum compat
    # __delattr__ = Emsg.ReadOnly.razr
    __setattr__ = nosetattr(abcs.EbcMeta)

class LexicalAbcMeta(LangCommonMeta):
    "Common metaclass for non-Enum lexical classes."

    # Populated in lex module.
    __call__ = NotImplemented

#==========================+
#  Base classes            |
#==========================+

class LangCommonEnum(abcs.Ebc, metaclass=LangCommonEnumMeta):
    'Common Enum base class for lang classes.'

    # __slots__   = 'value', '_value_', '_name_',

    # Set in base __init__ for Python 3.11 Enum compat
    # __delattr__ = Emsg.ReadOnly.razr
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

    @classmethod
    def make(cls, it: Iterable):
        if isinstance(it, Mapping):
            it = map(it.__getitem__, cls._fields)
        return cls._make(it)

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

    @classmethod
    def make(cls, it: Iterable):
        if isinstance(it, Mapping):
            it = map(it.__getitem__, cls._fields)
        return cls._make(it)

BiCoords.first = BiCoords.make(BiCoords.first)
TriCoords.first = TriCoords.make(TriCoords.first)


class TableStore(metaclass=LangCommonMeta):

    default_fetch_key: ClassVar[str]

    _instances: ClassVar[dict[Notation, dict[Any, Self]]]

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

    def __init__(self, data: Mapping, keypair: tuple, /):
        self.data = dxopy(data, True)
        self.__getitem__ = self.data.__getitem__
        self.keypair = keypair
        self.notation = Notation(self.data['notation'])
        self.renders = self.data.get('renders', EMPTY_MAP)
        self.strings = self.data.get('strings', EMPTY_MAP)
        self.hash = self._compute_hash()
        self.notation.charsets.add(self.charset)
        self.notation.rendersets.add(self)

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
        return type(self) is type(other) and hash(self) == hash(other)

    def _compute_hash(self) -> int:
        r, s = self.renders, self.strings
        vv = *(*r.values(), *s.values()),
        ktup = *(*r.keys(), *s.keys()),
        vtup = *((*v.items(),) if isinstance(v, Mapping) else v for v in vv),
        return hash((ktup, vtup))



from .lex import Atomic, Constant
from .lex import CoordsItem as CoordsItem
from .lex import Lexical as Lexical
from .lex import LexType as LexType
from .lex import Operated as Operated
from .lex import Operator as Operator
from .lex import Parameter as Parameter
from .lex import LexicalAbc as LexicalAbc
from .lex import LexicalEnum as LexicalEnum

pass

from .lex import Predicate as Predicate
from .lex import Predicated as Predicated
from .lex import Quantified as Quantified
from .lex import Quantifier as Quantifier
from .lex import Sentence as Sentence
from .lex import Variable as Variable

pass
from .parsing import Parser as Parser
from .parsing import DefaultParser as DefaultParser
from .parsing import ParseTable as ParseTable
from .parsing import PolishParser as PolishParser
from .parsing import StandardParser as StandardParser

pass
from .collect import Argument as Argument
from .collect import Predicates as Predicates

pass
from .writing import LexWriter as LexWriter
from .writing import DefaultLexWriter as DefaultLexWriter
from .writing import PolishLexWriter as PolishLexWriter
from .writing import StandardLexWriter as StandardLexWriter


@closure
def init():

    from . import _symdata

    RenderSet._initcache(Notation, _symdata.rendersets())
    ParseTable._initcache(Notation, _symdata.parsetables())
    LexWriter._sys = LexWriter('standard', 'unicode')

    def tostr_item(item: LexicalAbc):
        return LexWriter._sys(item)

    def tostr_enum(enum: LexicalEnum):
        return enum.name

    def tostr_pred(pred: Predicate):
        try:
            if pred.is_system:
                return pred.name
        except AttributeError:
            pass
        return tostr_item(pred)

    LexicalEnum.__str__ = tostr_enum
    LexicalAbc.__str__ = tostr_item
    Predicate.__str__ = tostr_pred

    def repr_lex(obj: Lexical):
        try:
            return f'<{obj.TYPE.role.__name__}: {obj}>'
        except AttributeError:
            return object.__repr__(obj)

    Lexical.__repr__ = repr_lex

    from . import lex
    from ..errors import Emsg

    for cls in (LangCommonEnumMeta, LangCommonEnum):
        cls.__delattr__ = Emsg.ReadOnly.razr

    for cls in (LangCommonEnum, LexicalAbc, Predicates, Argument, Lexical):
        cls._readonly = True

    lex.nosetattr.enabled = True
    lex.nosetattr.cache.clear()

    del(lex.nosetattr)

del(init)