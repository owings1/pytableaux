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

from collections import defaultdict
from collections.abc import Mapping
from typing import Any, Iterable, NamedTuple, Self

from ..errors import Emsg
from ..tools import EMPTY_SET, MapCover, NoSetAttr, abcs, closure

__all__ = (
    # Classes
    # 'BiCoords',
    # 'LangCommonEnum',
    # 'LangCommonEnumMeta',
    # 'LangCommonMeta',
    # 'LexicalAbcMeta',
    'Marking',
    'Notation',
    'StringTable',
    # 'TriCoords',

    # Subpackage export
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

    def __prepare__(clsname, bases, **kw):
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
    """Notation (polish/standard) enum class.

    .. csv-table::
        :generator: member-table
        :generator-args: name
    """

    formats: dict[str, set[str]]
    "Mapping from format to dialects."

    writers: set[type[LexWriter]]
    "All writer classes for the notation."

    DefaultWriter: type[LexWriter]
    "The notations's default writer class."

    Parser: type[Parser]
    "The notation's parser class."

    #--- Members

    polish = 'polish',
    "Polish notation."

    standard = 'standard',
    "Standard notation."

    def __init__(self, name, /):
        self.formats = defaultdict(set)
        self.writers = set()
        self.DefaultWriter = None

    __slots__ = (
        'formats',
        'DefaultWriter',
        'Parser',
        'writers')

    @classmethod
    def get_common_formats(cls) -> list[str]:
        "Get formats common to all notations."
        formats: set[str] = set(
            format
            for notn in Notation
                for format in notn.formats)
        for notn in Notation:
            formats.intersection_update(notn.formats)
        return sorted(formats)

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


class Marking(str, LangCommonEnum):
    """Miscellaneous marking/punctuation enum.

    .. csv-table::
        :generator: member-table
        :generator-args: name
    """
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
    subscript_open = 'subscript_open'
    "Subscript open marking."
    subscript_close = 'subscript_close'
    "Subscript close marking."
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

from .lex import Atomic, Constant
from .lex import CoordsItem as CoordsItem
from .lex import Lexical as Lexical
from .lex import LexicalAbc as LexicalAbc
from .lex import LexicalEnum as LexicalEnum
from .lex import LexType as LexType
from .lex import Operated as Operated
from .lex import Operator as Operator
from .lex import Parameter as Parameter

pass

from .lex import Predicate as Predicate
from .lex import Predicated as Predicated
from .lex import Quantified as Quantified
from .lex import Quantifier as Quantifier
from .lex import Sentence as Sentence
from .lex import Variable as Variable

pass
from .parsing import DefaultParser as DefaultParser
from .parsing import Parser as Parser
from .parsing import ParseTable as ParseTable
from .parsing import PolishParser as PolishParser
from .parsing import StandardParser as StandardParser

pass
from .collect import Argument as Argument
from .collect import Predicates as Predicates

pass
from .writing import LexWriter as LexWriter
from .writing import PolishLexWriter as PolishLexWriter
from .writing import StandardLexWriter as StandardLexWriter
from .writing import StringTable as StringTable


@closure
def init():

    from ..tools import wraps
    from . import _symdata

    for _ in map(ParseTable.load, _symdata.parse_tables()): pass
    for _ in map(StringTable.load, _symdata.string_tables()): pass

    for notn in Notation:
        StringTable._instances.setdefault(
            ('text', notn, 'text'),
            StringTable._instances['text', notn, 'ascii'])
    
    syslw = LexWriter(
        notation=Notation.standard,
        format='text',
        dialect='unicode')

    @wraps(LexicalAbc.__str__)
    def tostr_item(item: LexicalAbc):
        return syslw(item)

    @wraps(LexicalEnum.__str__)
    def tostr_enum(enum: LexicalEnum):
        return enum.name

    @wraps(Predicate.__str__)
    def tostr_pred(pred: Predicate):
        try:
            if pred.is_system:
                return pred.name
        except AttributeError: # pragma: no cover
            pass
        return syslw(pred)

    @wraps(Lexical.__repr__)
    def repr_lex(obj: Lexical):
        try:
            return f'<{obj.TYPE.role.__name__}: {obj}>'
        except AttributeError: # pragma: no cover
            return object.__repr__(obj)

    LexicalEnum.__str__ = tostr_enum
    LexicalAbc.__str__ = tostr_item
    Predicate.__str__ = tostr_pred
    Lexical.__repr__ = repr_lex

    from .collect import ArgumentMeta

    argstrlw = LexWriter(
        notation=Notation.polish,
        format='text',
        dialect='ascii')
    ArgumentMeta._argstr_lw = argstrlw
    ArgumentMeta._argstr_pclass = argstrlw.notation.Parser
    ArgumentMeta._argstr_parser_empty = argstrlw.notation.Parser(predicates=Predicates.EMPTY)

    from ..errors import Emsg
    from . import lex

    for cls in (LangCommonEnumMeta, LangCommonEnum):
        cls.__delattr__ = Emsg.ReadOnly.razr

    for cls in (LangCommonEnum, LexicalAbc, Predicates, Argument, Lexical):
        cls._readonly = True

    lex.nosetattr.enabled = True
    lex.nosetattr.cache.clear()

    del(lex.nosetattr)

del(init)