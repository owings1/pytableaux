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
# pytableaux - writers test cases
from pytableaux import examples
from pytableaux.errors import *
from pytableaux.lang import *
from pytableaux.proof import *

from .utils import BaseCase
# Sentence Writers

std = LexWriter('standard')
stdasc = LexWriter('standard', format = 'ascii')
stduni = LexWriter('standard', format = 'unicode')
stdhtm = LexWriter('standard', format = 'html')

pol = LexWriter('polish')
ppol = Parser('polish')
pstd = Parser('standard')

htm = TabWriter('html', 'standard')
ltx = TabWriter('latex', 'standard')

class TestStandard(BaseCase):

    def test_atomic(self):
        s = Atomic(0, 0)
        res = std(s)
        self.assertEqual(res, 'A')

    def test_writes_parens_asc(self):
        s = ppol('UUaba')
        res = stdasc(s)
        self.assertIn('(', res)
        self.assertIn(')', res)
    def test_writes_parens_uni(self):
        s = ppol('UUaba')
        res = stduni(s)
        self.assertIn('(', res)
        self.assertIn(')', res)
    def test_writes_parens_htm(self):
        s = ppol('UUaba')
        res = stdhtm(s)
        self.assertIn('(', res)
        self.assertIn(')', res)
    def test_drop_parens_asc(self):
        s = ppol('Uab')
        lw = LexWriter('standard', 'ascii', drop_parens=True)
        res = lw(s)
        self.assertNotIn('(', res)
        self.assertNotIn(')', res)
    def test_drop_parens_uni(self):
        s = ppol('Uab')
        lw = LexWriter('standard', 'unicode', drop_parens=True)
        res = lw(s)
        self.assertNotIn('(', res)
        self.assertNotIn(')', res)
    def test_drop_parens_htm(self):
        s = ppol('Uab')
        lw = LexWriter('standard', 'html', drop_parens=True)
        res = lw(s)
        self.assertNotIn('(', res)
        self.assertNotIn(')', res)
    # def test_symset_returns_same(self):
        # ss = std.symset('default')
        # res = std.symset(ss)
        # self.assertEqual(res, ss)

    def test_write_predicate_sys(self):
        res = std(Predicate.System['Identity'])
        self.assertEqual(res, '=')

    # def test_write_parameter_not_impl_base_param(self):
    #     param = Parameter(0, 0)
    #     with pytest.raises(TypeError):
    #         std(param)

    def test_write_subscript_html(self):

        res = stdhtm._write_subscript(1)
        self.assertIn('>1</s', res)

    def test_write_neg_ident_html(self):
        s1 = ppol('NImn')
        res = stdhtm(s1)
        self.assertIn('&ne;', res)

    # def test_write_operated_3ary_not_impl(self):
    #     operators['Schmoogation'] = 3
    #     with pytest.raises(NotImplementedError):
    #         try:
    #             std(Operated('Schmoogation', [parse('a'), parse('a'), parse('a')]))
    #         except:
    #             del operators['Schmoogation']
    #             raise
    #         else:
    #             del operators['Schmoogation']

    def test_parse_errors_various_parens(self):
        # coverage
        with self.assertRaises(ParseError):
            pstd('(A & &A)')
        with self.assertRaises(ParseError):
            pstd('(A & ())')

class TestPolish(BaseCase):

    def test_atomic(self):
        s = Atomic(0, 0)
        res = pol(s)
        self.assertEqual(res, 'a')

# Proof writers

class TestHtml(BaseCase):

    def test_write_no_arg(self):
        tab = Tableau('FDE')
        tab.build()
        res = htm(tab)

    def test_write_std_fde_1(self):
        arg = examples.argument('Addition')
        tab = Tableau('fde', arg).build()
        htm(tab)

    
class TestLatex(BaseCase):

    def test_write_no_arg(self):
        tab = Tableau('FDE')
        tab.build()
        res = ltx(tab)

    def test_write_std_fde_1(self):
        arg = examples.argument('Addition')
        tab = Tableau('fde', arg).build()
        ltx(tab)