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
pytableaux.lang.writing
^^^^^^^^^^^^^^^^^^^^^^^

"""
from __future__ import annotations

from abc import abstractmethod
from types import MappingProxyType as MapProxy
from typing import Any, ClassVar, TYPE_CHECKING

from ..errors import Emsg
from ..tools import EMPTY_MAP
from . import (Atomic, Constant, CoordsItem, LangCommonMeta, Lexical, LexType,
               Marking, Notation, Operated, Operator, Predicate, Predicated,
               Quantified, Quantifier, StringTable, Variable)

if TYPE_CHECKING:
    from typing import overload

__all__ = (
    'LexWriter',
    'StandardLexWriter',
    'PolishLexWriter')


class LexWriterMeta(LangCommonMeta):
    'LexWriter Metaclass.'

    DEFAULT_FORMAT = 'text'
    DEFAULT_NOTATION = Notation.polish

    def __call__(cls, *args, **kw):
        if cls is LexWriter:
            if args:
                notn = Notation(args[0])
                args = args[1:]
            elif 'notation' in kw:
                notn = Notation(kw.pop('notation'))
            else:
                notn = LexWriter.DEFAULT_NOTATION
            return notn.DefaultWriter(*args, **kw)
        return super().__call__(*args, **kw)


class LexWriter(metaclass = LexWriterMeta):
    'LexWriter interface and coordinator.'

    notation: ClassVar[Notation]
    defaults = EMPTY_MAP
    _methodmap = MapProxy({
        Operator   : '_write_plain',
        Quantifier : '_write_plain',
        Predicate  : '_write_coordsitem',
        Constant   : '_write_coordsitem',
        Variable   : '_write_coordsitem',
        Atomic     : '_write_coordsitem',
        Predicated : '_write_predicated',
        Quantified : '_write_quantified',
        Operated   : '_write_operated'})

    __slots__ = ('opts', 'strings')

    strings: StringTable
    opts: dict
    format: str

    @property
    def format(self) -> str:
        return self.strings.format

    @property
    def dialect(self) -> str:
        return self.strings.dialect

    def __init__(self, format: str|None = None, dialect: str = None, strings: StringTable|None = None, **opts):
        if strings is None:
            if format is None:
                format = LexWriter.DEFAULT_FORMAT
            strings = StringTable.fetch(
                format=format,
                notation=self.notation,
                dialect=dialect)
        elif (
            format is not None and format != strings.format or
            dialect is not None and dialect != strings.dialect):
            raise Emsg.WrongValue(format, strings.format)
        self.opts = dict(self.defaults, **opts)
        self.strings = strings

    if TYPE_CHECKING:
        @overload
        def __init__(self,
            notation:str|Notation|None=...,
            format:str|None=...,
            dialect:str|None=...,
            strings:StringTable|None=...,
            **opts): ...

    def __call__(self, item) -> str:
        'Write a lexical item.'
        return self._write(item)

    def canwrite(self, obj: Any) -> bool:
        "Whether the object can be written."
        try:
            if obj in self.strings:
                return True
        except TypeError:
            pass
        try:
            return callable(self._methodmap[type(obj)])
        except (AttributeError, KeyError):
            return False

    def _write(self, item) -> str:
        'Wrapped internal write method.'
        try:
            return self.strings[item]
        except KeyError:
            pass
        try:
            method = self._methodmap[type(item)]
        except AttributeError:
            raise TypeError(type(item))
        except KeyError:
            raise NotImplementedError(type(item))
        return getattr(self, method)(item)

    @abstractmethod
    def _write_operated(self, item: Operated) -> str: ...

    def _write_plain(self, item: Lexical) -> str:
        return self.strings[item]

    def _write_coordsitem(self, item: CoordsItem) -> str:
        return ''.join((
            self.strings[type(item), item.index],
            self._write_subscript(item.subscript)))

    def _write_quantified(self, item: Quantified) -> str:
        return ''.join(map(self._write, item.items))

    def _write_predicated(self, item: Predicated) -> str:
        return ''.join(map(self._write, (item.predicate, *item)))

    def _write_subscript(self, s: int) -> str:
        if s == 0: return ''
        return ''.join((
            self.strings[Marking.subscript_open],
            str(s),
            self.strings[Marking.subscript_close]))

    def _test(self):
        'Smoke test. Returns a rendered list of each lex type.'
        return list(map(self, (t.cls.first() for t in LexType)))

    @classmethod
    def register(cls, subcls: type[LexWriter]):
        'Update available writers.'
        subcls.notation.writers.add(subcls)
        if subcls.notation.DefaultWriter is None:
            subcls.notation.DefaultWriter = subcls
        return subcls

@LexWriter.register
class PolishLexWriter(LexWriter):
    "Polish notation lexical writer implementation."

    notation = Notation.polish

    def _write_operated(self, item: Operated) -> str:
        return ''.join(map(self._write, (item.operator, *item)))

@LexWriter.register
class StandardLexWriter(LexWriter):
    "Standard notation lexical writer implementation."

    notation = Notation.standard
    defaults = MapProxy(dict(
        drop_parens=True,
        identity_infix=True,
        max_infix=0))

    def __call__(self, item):
        if self.opts['drop_parens'] and type(item) is Operated:
            return self._write_operated(item, drop_parens=True)
        return super().__call__(item)

    def _write_predicated(self, s: Predicated) -> str:
        pred = s.predicate
        arity = pred.arity
        opts = self.opts
        should_infix = (
            arity > 1 and (
                arity < opts['max_infix'] or
                pred is Predicate.Identity and opts['identity_infix']))
        if not should_infix:
            return super()._write_predicated(s)
        if pred is Predicate.Identity:
            ws = self.strings[Marking.whitespace]
        else:
            ws = ''
        return ws.join((
            self._write(s[0]),
            self._write(pred),
            ''.join(map(self._write, s[1:]))))

    def _write_operated(self, s: Operated,/, *, drop_parens = False) -> str:
        oper = s.operator
        arity = oper.arity
        strings = self.strings
        ws = strings[Marking.whitespace]
        if arity == 1:
            s = s.lhs
            is_neg_identity = (
                oper is Operator.Negation and
                type(s) is Predicated
                and s.predicate is Predicate.Identity)
            if is_neg_identity and self.opts['identity_infix']:
                symbol = strings[Operator.Negation, Predicate.Identity]
                return ws.join((
                    self._write(s[0]),
                    symbol,
                    self._write(s[1])))
            return self._write(oper) + self._write(s)
        if arity != 2:
            raise NotImplementedError from ValueError(oper)
        lhs, rhs = s
        if drop_parens:
            paren_open = ''
            paren_close = ''
        else:
            paren_open = strings[Marking.paren_open]
            paren_close = strings[Marking.paren_close]
        return ''.join((
            paren_open,
            ws.join(map(self._write, (lhs, oper, rhs))),
            paren_close))

    def _test(self) -> list[str]:
        s1 = ~Predicate.Identity(Constant.gen(2))
        s2 = Operator.Conjunction(Atomic.gen(2))
        s3 = s2 | Atomic.first()
        return super()._test() + list(map(self, [s1, s2, s3]))
