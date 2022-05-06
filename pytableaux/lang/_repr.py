from __future__ import annotations

import reprlib

from pytableaux.lang.lex import (Lexical, LexicalEnum, LexicalAbc, LexType,
                                 Predicate)
from pytableaux.lang.writing import LexWriter
from pytableaux.tools import closure


class LangRepr(reprlib.Repr):

    def repr_Constant(self, obj, level):
        return 'foo repr'
        return self.repr(tuple(obj))


class LangRepr1(LangRepr):
    'Functional mode.'
    pass

class LangRepr2(LangRepr):
    'Pretty mode.'
    pass

class LangRepr3(LangRepr):
    'Dumb mode.'
    pass


@closure
def _setup():
    conf = dict(
        mode = 1,
        lw = LexWriter('standard', 'unicode')
    )

    def __repr__(self):
        try:
            return f'<{self.TYPE.role}: {self}>'
        except AttributeError:
            return object.__repr__(self)

    def __str__item(self):
        mode = conf['mode']
        lw = conf['lw']
        if mode == 1:
            return lw(self)
        if mode == 2:
            return lw(self)
        if mode == 3:
            return f'~~ {lw(self)} ~~'
        return object.__repr__(self)

    def __str__enum(self):
        mode = conf['mode']
        if mode == 1:
            return self.name
        return __str__item(self)

    def __str__pred(self):
        if self.is_system:
            return __str__enum(self)
        return __str__item(self)

    Lexical.__repr__ = __repr__
    Predicate.__str__ = __str__pred
    LexicalAbc.__str__ = __str__item
    LexicalEnum.__str__ = __str__enum

    reg = {
        1: LangRepr1(),
        2: LangRepr2(),
        3: LangRepr3(),
    }
    # _ = MapProxy(conf)

__all__ = ()

# C.__repr__ = _extrepr
# def _extrepr(x):
#     return reg[_mode].repr(x)
# bkup = {}
# bkup[C] = C.__repr__

def pr():
    items = [Predicate.System.Identity]
    items.extend(c.first() for c in LexType.classes)
    for item in items:
        print(f'type = {item.TYPE.name}')
        print(f'str  = {str(item)}')
        print(f'repr = {repr(item)}')
        print('')


"""

from tabulate import tabulate; from pytableaux.lang.lex import * ; rows = [(item, item.spec) for item in (member.cls.first() for member in LexType)]


LexType

    def __repr__(self, /):
        name = __class__.__name__
        try:
            return f'<{name}.{self.cls}>'
        except AttributeError:
            return f'<{name} ?ERR?>'


Argument

    def __repr__(self):
        if self.title:
            desc = repr(self.title)
        else:
            desc = f'len({len(self)})'
        return f'<{type(self).__name__}:{desc}>'
"""
