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

import itertools
from abc import abstractmethod
from types import DynamicClassAttribute as dynca
from types import MappingProxyType as MapProxy
from typing import Any, ClassVar

from ..errors import Emsg, check
from ..tools import EMPTY_SET, abcs, closure
from . import (Atomic, Constant, CoordsItem, LangCommonMeta, Lexical, LexType,
               Marking, Notation, Operated, Operator, Predicate, Predicated,
               Quantified, RenderSet)

__all__ = (
    'LexWriter',
    'StandardLexWriter',
    'PolishLexWriter')

class LexWriterMeta(LangCommonMeta):
    'LexWriter Metaclass.'

    def __call__(cls, *args, **kw):
        if cls is LexWriter:
            if args:
                notn = Notation(args[0])
                args = args[1:]
            else:
                notn = Notation.default
            return notn.DefaultWriter(*args, **kw)
        return super().__call__(*args, **kw)

    @closure
    def _sys():

        def checkcls(cls):
            try:
                if cls is not LexWriter:
                    raise AttributeError
            except NameError:
                raise AttributeError

        syslws = dict(set = None, unset = None)

        def fget(cls) -> LexWriter:
            'The system instance for representing.'
            checkcls(cls)
            if syslws['set'] is not None:
                return syslws['set']
            if syslws['unset'] is None:
                syslws['unset'] = LexWriter()
            return syslws['unset']

        def fset(cls, lw: LexWriter|None):
            checkcls(cls)
            if lw is not None:
                check.inst(lw, LexWriter)
            syslws['unset'] = None
            syslws['set'] = lw

        def fdel(cls):
            syslws.pop('unset')

        return dynca(fget, fset, fdel, doc = fget.__doc__)

class LexWriter(metaclass = LexWriterMeta):
    'LexWriter interface and coordinator.'

    __slots__ = 'opts', 'renderset'

    #******  Class Variables

    notation: ClassVar[Notation]
    defaults = {}
    _methodmap = MapProxy(dict(zip(LexType, itertools.repeat(NotImplemented))))
    _sys: LexWriter

    #******  Instance Variables

    renderset: RenderSet
    opts: dict
    charset: str

    @property
    def charset(self) -> str:
        return self.renderset.charset

    #******  External API

    def write(self, item) -> str:
        'Write a lexical item.'
        return self._write(item)

    __call__ = write

    @classmethod
    def canwrite(cls, obj: Any) -> bool:
        "Whether the object can be written."
        try:
            return obj.TYPE in cls._methodmap
        except AttributeError:
            return False

    #******  Instance Init

    def __init__(self, charset: str|None = None, renderset: RenderSet|None = None, **opts):
        if renderset is None:
            notn = self.notation
            if charset is None:
                charset = notn.default_charset
            renderset = RenderSet.fetch(notn, charset)
        elif charset is not None and charset != renderset.charset:
            raise Emsg.WrongValue(charset, renderset.charset)
        self.opts = dict(self.defaults, **opts)
        self.renderset = renderset

    #******  Internal API

    def _write(self, item) -> str:
        'Wrapped internal write method.'
        try:
            method = self._methodmap[item.TYPE]
        except AttributeError:
            raise TypeError(type(item))
        except KeyError:
            raise NotImplementedError(type(item))
        return getattr(self, method)(item)

    def _test(self):
        'Smoke test. Returns a rendered list of each lex type.'
        return list(map(self, (t.cls.first() for t in LexType)))

    #******  Class Init

    @classmethod
    def register(cls, subcls: type[LexWriter]):
        'Update available writers.'
        if not issubclass(subcls, __class__):
            raise TypeError(subcls, __class__)
        for ltype, meth in subcls._methodmap.items():
            try:
                getattr(subcls, meth)
            except TypeError:
                raise TypeError(meth, ltype)
            except AttributeError:
                raise TypeError('Missing method', meth, subcls)
        notn = subcls.notation = Notation(subcls.notation)
        type(cls).register(cls, subcls)
        notn.writers.add(subcls)
        if notn.DefaultWriter is None:
            notn.DefaultWriter = subcls
        return subcls

    def __init_subclass__(subcls: type[LexWriter], **kw):
        'Merge and freeze method map from mro. Sync ``__call__()``.'
        super().__init_subclass__(**kw)
        abcs.merge_attr(
            subcls, '_methodmap', supcls = __class__, transform = MapProxy)
        subcls.__call__ = subcls.write

class BaseLexWriter(LexWriter):
    "Common lexical writer abstract class."

    __slots__ = EMPTY_SET

    _methodmap = {
        LexType.Operator   : '_write_plain',
        LexType.Quantifier : '_write_plain',
        LexType.Predicate  : '_write_predicate',
        LexType.Constant   : '_write_coordsitem',
        LexType.Variable   : '_write_coordsitem',
        LexType.Atomic     : '_write_coordsitem',
        LexType.Predicated : '_write_predicated',
        LexType.Quantified : '_write_quantified',
        LexType.Operated   : '_write_operated'}

    @abstractmethod
    def _write_operated(self, item: Operated) -> str: ...

    def _strfor(self, *args, **kw) -> str:
        return self.renderset.string(*args, **kw)

    def _write_plain(self, item: Lexical) -> str:
        return self._strfor(item.TYPE, item)

    def _write_coordsitem(self, item: CoordsItem) -> str:
        return ''.join((
            self._strfor(item.TYPE, item.index),
            self._write_subscript(item.subscript)))

    def _write_predicate(self, item: Predicate) -> str:
        return ''.join((
            self._strfor((LexType.Predicate, item.is_system), item.index),
            self._write_subscript(item.subscript)))

    def _write_quantified(self, item: Quantified) -> str:
        return ''.join(map(self._write, item.items))

    def _write_predicated(self, item: Predicated) -> str:
        return ''.join(map(self._write, (item.predicate, *item)))

    def _write_subscript(self, s: int) -> str:
        if s == 0: return ''
        return self._strfor(Marking.subscript, s)

@LexWriter.register
class PolishLexWriter(BaseLexWriter):
    "Polish notation lexical writer implementation."

    __slots__ = EMPTY_SET

    notation = Notation.polish
    defaults = {}

    def _write_operated(self, item: Operated) -> str:
        return ''.join(map(self._write, (item.operator, *item)))

@LexWriter.register
class StandardLexWriter(BaseLexWriter):
    "Standard notation lexical writer implementation."

    __slots__ = EMPTY_SET

    notation = Notation.standard
    defaults = dict(drop_parens = True)

    def write(self, item):
        if self.opts['drop_parens'] and isinstance(item, Operated):
            return self._write_operated(item, drop_parens = True)
        return super().write(item)

    def _write_predicated(self, item: Predicated) -> str:
        if len(item) < 2:
            return super()._write_predicated(item)
        # Infix notation for predicates of arity > 1
        pred = item.predicate
        # For Identity, add spaces (a = b instead of a=b)
        if pred == Predicate.System.Identity:
            ws = self._strfor(Marking.whitespace, 0)
        else:
            ws = ''
        return ''.join((
            self._write(item.params[0]),
            ws,
            self._write(pred),
            ws,
            ''.join(map(self._write, item.params[1:]))))

    def _write_operated(self, item: Operated, drop_parens = False) -> str:
        oper = item.operator
        arity = oper.arity
        if arity == 1:
            s = item.lhs
            if (
                oper == Operator.Negation and
                type(s) is Predicated and
                s.predicate == Predicate.System.Identity
            ):
                return self._write_negated_identity(item)
            else:
                return self._write(oper) + self._write(s)
        elif arity == 2:
            lhs, rhs = item
            return ''.join((
                self._strfor(Marking.paren_open, 0) if not drop_parens else '',
                self._strfor(Marking.whitespace, 0).join(map(self._write, (lhs, oper, rhs))),
                self._strfor(Marking.paren_close, 0) if not drop_parens else ''))
        raise NotImplementedError('arity %s' % arity)

    def _write_negated_identity(self, item: Operated) -> str:
        si: Predicated = item.lhs
        params = si.params
        return self._strfor(Marking.whitespace, 0).join((
            self._write(params[0]),
            self._strfor((LexType.Predicate, True), (item.operator, si.predicate)),
            self._write(params[1])))

    def _test(self) -> list[str]:
        s1 = Predicate.System.Identity(Constant.gen(2)).negate()
        s2 = Operator.Conjunction(Atomic.gen(2))
        s3 = s2.disjoin(Atomic.first())
        return super()._test() + list(map(self, [s1, s2, s3]))
