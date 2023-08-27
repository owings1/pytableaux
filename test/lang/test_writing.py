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
#
# ------------------
#
# pytableaux.lang.writing tests
from __future__ import annotations

from pytableaux.lang import *

from ..utils import BaseCase


class Base(BaseCase):

    lw: LexWriter

    lwopts = {}

    def lwsetup(self, **kw):
        opts = dict(self.lwopts, **kw)
        self.lw = LexWriter(**opts)

    def setUp(self) -> None:
        self.lwsetup()
        return super().setUp()

    def w(self, item):
        if isinstance(item, str):
            item = self.p(item)
        return self.lw(item)

    def assertOutputEqual(self, item, *args, **kw):
        self.assertEqual(self.w(item), *args, **kw)

class TestPolishTextAscii(Base):

    lwopts = dict(notation='polish', format='text', dialect='ascii')

    def test_atomic_pol(self):
        self.assertOutputEqual('a', 'a')

class TestStandardTextAscii(Base):

    lwopts = dict(notation='standard', format='text', dialect='ascii')

    def test_atomic_std(self):
        self.assertOutputEqual('a', 'A')

    def test_writes_parens_asc(self):
        self.assertOutputEqual('UUaba', '(A $ B) $ A')

    def test_drop_parens_asc(self):
        self.assertOutputEqual('Uab', 'A $ B')

    def test_no_drop_parens_asc(self):
        self.lwsetup(drop_parens=False)
        self.assertOutputEqual('Uab', '(A $ B)')

    def test_write_predicate_sys(self):
        self.assertOutputEqual(Predicate.Identity, '=')

class TestStandardTextUnicode(Base):

    lwopts = dict(notation='standard', format='text', dialect='unicode')

    def test_writes_parens_uni(self):
        self.assertOutputEqual('UUaba', '(A → B) → A')

    def test_drop_parens_uni(self):
        self.assertOutputEqual('Uab', 'A → B')

class TestStandardHtml(Base):

    lwopts = dict(notation='standard', format='html')

    def test_writes_parens_htm(self):
        self.assertOutputEqual('UUaba', '(A &rarr; B) &rarr; A')

    def test_drop_parens_htm(self):
        self.assertOutputEqual('Uab', 'A &rarr; B')

    def test_write_subscript_html(self):
        res = self.lw._write_subscript(1)
        self.assertIn('>1</s', res)

    def test_write_neg_ident_html(self):
        self.assertOutputEqual('NImn', 'a &ne; b')


class TestStringTable(BaseCase):

    def test_equals_mapping_copy(self):
        t1 = StringTable.fetch('text', 'polish', 'ascii')
        data = dict(
            format = 'text',
            notation = 'polish',
            dialect = 'ascii',
            strings = dict(t1))
        t2 = StringTable(data)
        self.assertEqual(t1, t2)

    def test_load_duplicate_key(self):
        t1 = StringTable.fetch('text', 'polish', 'ascii')
        data = dict(
            format = 'text',
            notation = 'polish',
            dialect = 'ascii',
            strings = dict(t1))
        with self.assertRaises(KeyError):
            StringTable.load(data)