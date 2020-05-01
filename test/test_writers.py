# pytableaux, a multi-logic proof generator.
# Copyright (C) 2014-2020 Doug Owings.
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

from logic import *
from notations import standard, polish
from writers import ascii, asciiv, html
import examples

# Sentence Writers

std = standard.Writer()
pol = polish.Writer()

class TestBase(object):

    def test_write_operated_not_impl(self):
        s = operate('Negation', [atomic(0, 0)])
        w = Vocabulary.Writer(std.symset)
        with pytest.raises(NotImplementedError):
            w.write(s) 
        
class TestStandard(object):

    def test_atomic(self):
        s = atomic(0, 0)
        res = std.write(s)
        assert res == 'A'

    def test_symset_returns_same(self):
        ss = std.symset('default')
        res = std.symset(ss)
        assert res == ss

    def test_write_not_impl_base_sentence(self):
        s = Vocabulary.Sentence()
        with pytest.raises(NotImplementedError):
            std.write(s)

    def test_write_predicate_sys(self):
        res = std.write_predicate(system_predicates['Identity'])
        assert res == '='

    def test_write_parameter_not_impl_base_param(str):
        param = Vocabulary.Parameter(0, 0)
        with pytest.raises(NotImplementedError):
            std.write_parameter(param)

    def test_write_subscript_html(str):
        res = std.write_subscript(1, symbol_set='html')
        assert '>1</span>' in res

class TestPolish(object):

    def test_atomic(self):
        s = atomic(0, 0)
        res = pol.write(s)
        assert res == 'a'

# Proof writers

asc = ascii.Writer()
htm = html.Writer()
asv = asciiv.Writer()

def example_proof(logic, name, is_build=True):
    arg = examples.argument(name)
    proof = tableau(logic, arg)
    if is_build:
        proof.build()
    return proof

class TestAscii(object):

    def test_write_std_fde_1(self):
        proof = example_proof('fde', 'Addition')
        res = asc.write(proof, standard)
        # TODO: assert something

class TestAsciiv(object):

    def test_write_std_fde_1(self):
        proof = example_proof('fde', 'Addition')
        res = asv.write(proof, standard)
        # TODO: assert something
    
class TestHtml(object):

    def test_write_std_fde_1(self):
        proof = example_proof('fde', 'Addition')
        res = htm.write(proof, standard)
        # TODO: assert something