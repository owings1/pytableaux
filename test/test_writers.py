# pytableaux, a multi-logic proof generator.
# Copyright (C) 2014-2021 Doug Owings.
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

from lexicals import Atomic, Operated, BaseLexWriter, Predicates, \
    create_lexwriter
from parsers import parse, create_parser
from errors import *
from proof.tableaux import Tableau
from proof.writers import create_tabwriter
import examples

# Sentence Writers

std = create_lexwriter(notn='standard')
stdasc = create_lexwriter(notn='standard', enc='ascii')
stduni = create_lexwriter(notn='standard', enc='unicode')
stdhtm = create_lexwriter(notn='standard', enc='html')

pol = create_lexwriter(notn='polish')
pstd = create_parser('standard')

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
        res = std.write(s)
        assert res == 'A'

    def test_writes_parens_asc(self):
        s = parse('UUaba')
        res = stdasc.write(s)
        assert '(' in res
        assert ')' in res
    def test_writes_parens_uni(self):
        s = parse('UUaba')
        res = stduni.write(s)
        assert '(' in res
        assert ')' in res
    def test_writes_parens_htm(self):
        s = parse('UUaba')
        res = stdhtm.write(s)
        assert '(' in res
        assert ')' in res
    def test_drop_parens_asc(self):
        s = parse('Uab')
        lw = create_lexwriter('standard', 'ascii', drop_parens=True)
        res = lw.write(s)
        assert '(' not in res
        assert ')' not in res
    def test_drop_parens_uni(self):
        s = parse('Uab')
        lw = create_lexwriter('standard', 'unicode', drop_parens=True)
        res = lw.write(s)
        assert '(' not in res
        assert ')' not in res
    def test_drop_parens_htm(self):
        s = parse('Uab')
        lw = create_lexwriter('standard', 'html', drop_parens=True)
        res = lw.write(s)
        assert '(' not in res
        assert ')' not in res
    # def test_symset_returns_same(self):
        # ss = std.symset('default')
        # res = std.symset(ss)
        # assert res == ss

    def test_write_predicate_sys(self):
        res = std.write(Predicates.system['Identity'])
        assert res == '='

    # def test_write_parameter_not_impl_base_param(self):
    #     param = Parameter(0, 0)
    #     with pytest.raises(TypeError):
    #         std.write(param)

    def test_write_subscript_html(self):

        res = stdhtm._write_subscript(1)
        assert '>1</s' in res

    def test_write_neg_ident_html(self):
        s1 = parse('NImn')
        res = stdhtm.write(s1)
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
            parse('(A & &A)', notn='standard')
        with pytest.raises(ParseError):
            parse('(A & ())', notn='standard')

class TestPolish(object):

    def test_atomic(self):
        s = Atomic(0, 0)
        res = pol.write(s)
        assert res == 'a'

# Proof writers

# asc = ascii.Writer()
htm = create_tabwriter(notn='standard', format='html')
# asv = asciiv.Writer()

def example_proof(logic, name, is_build=True):
    arg = examples.argument(name)
    proof = Tableau(logic, arg)
    if is_build:
        proof.build()
    return proof

class TestHtml(object):

    def test_write_no_arg(self):
        proof = Tableau('FDE')
        proof.build()
        res = htm.write(proof)

    def test_write_std_fde_1(self):
        proof = example_proof('fde', 'Addition')
        res = htm.write(proof)

    
