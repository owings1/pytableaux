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
#
# ------------------
#
# pytableaux - writers test cases
import pytest
from pytableaux import examples
from pytableaux.errors import *
from pytableaux.lang.collect import Predicates
from pytableaux.lang.lex import Atomic
from pytableaux.lang.parsing import Parser
from pytableaux.lang.writing import LexWriter
from pytableaux.proof.tableaux import Tableau
from pytableaux.proof.writers import TabWriter

# Sentence Writers

std = LexWriter('standard')
stdasc = LexWriter('standard', charset = 'ascii')
stduni = LexWriter('standard', charset = 'unicode')
stdhtm = LexWriter('standard', charset = 'html')

pol = LexWriter('polish')
ppol = Parser('polish')
pstd = Parser('standard')

htm = TabWriter('html', 'standard')

class TestBase(object):

    pass
    # def test_write_operated_not_impl(self):
    #     s = Operated('Negation', [Atomic(0, 0)])
    #     symset = SymbolSet.get_instance('standard.ascii')
    #     w = BaseLexWriter(symset)
    #     with pytest.raises(NotImplementedError):
    #         w.write(s) 
        
class TestStandard(object):

    def test_atomic(self):
        s = Atomic(0, 0)
        res = std(s)
        assert res == 'A'

    def test_writes_parens_asc(self):
        s = ppol('UUaba')
        res = stdasc(s)
        assert '(' in res
        assert ')' in res
    def test_writes_parens_uni(self):
        s = ppol('UUaba')
        res = stduni(s)
        assert '(' in res
        assert ')' in res
    def test_writes_parens_htm(self):
        s = ppol('UUaba')
        res = stdhtm(s)
        assert '(' in res
        assert ')' in res
    def test_drop_parens_asc(self):
        s = ppol('Uab')
        lw = LexWriter('standard', 'ascii', drop_parens=True)
        res = lw(s)
        assert '(' not in res
        assert ')' not in res
    def test_drop_parens_uni(self):
        s = ppol('Uab')
        lw = LexWriter('standard', 'unicode', drop_parens=True)
        res = lw.write(s)
        assert '(' not in res
        assert ')' not in res
    def test_drop_parens_htm(self):
        s = ppol('Uab')
        lw = LexWriter('standard', 'html', drop_parens=True)
        res = lw(s)
        assert '(' not in res
        assert ')' not in res
    # def test_symset_returns_same(self):
        # ss = std.symset('default')
        # res = std.symset(ss)
        # assert res == ss

    def test_write_predicate_sys(self):
        res = std(Predicates.System['Identity'])
        assert res == '='

    # def test_write_parameter_not_impl_base_param(self):
    #     param = Parameter(0, 0)
    #     with pytest.raises(TypeError):
    #         std.write(param)

    def test_write_subscript_html(self):

        res = stdhtm._write_subscript(1)
        assert '>1</s' in res

    def test_write_neg_ident_html(self):
        s1 = ppol('NImn')
        res = stdhtm(s1)
        assert '&ne;' in res

    # def test_write_operated_3ary_not_impl(self):
    #     operators['Schmoogation'] = 3
    #     with pytest.raises(NotImplementedError):
    #         try:
    #             std.write(Operated('Schmoogation', [parse('a'), parse('a'), parse('a')]))
    #         except:
    #             del operators['Schmoogation']
    #             raise
    #         else:
    #             del operators['Schmoogation']

    def test_parse_errors_various_parens(self):
        # coverage
        with pytest.raises(ParseError):
            pstd('(A & &A)')
        with pytest.raises(ParseError):
            pstd('(A & ())')

class TestPolish(object):

    def test_atomic(self):
        s = Atomic(0, 0)
        res = pol(s)
        assert res == 'a'

# Proof writers

class TestHtml(object):

    def test_write_no_arg(self):
        tab = Tableau('FDE')
        tab.build()
        res = htm.write(tab)

    def test_write_std_fde_1(self):
        arg = examples.argument('Addition')
        tab = Tableau('fde', arg).build()
        htm(tab)

    
