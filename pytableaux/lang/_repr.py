from __future__ import annotations

import reprlib



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


_mode = 1
reg = {
    1: LangRepr1(),
    2: LangRepr2(),
    3: LangRepr3()
}

bkup = {

}

def _extrepr(x):
    return reg[_mode].repr(x)

def setup(clss):
    for C in clss:
        bkup[C] = C.__repr__
        ...
        # C.__repr__ = _extrepr


__all__ = ()


"""
Lexical



    def __repr__(self):
        try:
            return f'<{self.TYPE.role}: {str(self)}>'
        except AttributeError:
            return f'<{type(self).__name__}: ERR>'


LexicalsItem

    def __str__(self, /, *, mode = 1):
        'Write the item with the system ``LexWriter``.'
        if mode == 2:
            return 'testmode2'
        try:
            return LexWriter._sys(self)
        except NameError:
            try:
                return str(self.ident)
            except AttributeError as err:
                return f'{type(self).__name__}({err})'


LexicalEnum:


    def __str__(self):
        'Returns the name.'
        return self.name


Predicate

    def __str__(self):
        return str(self.name) if self.is_system else super().__str__()


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