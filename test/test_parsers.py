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
# pytableaux - parsers test cases
import pytest

from logic import *
from notations import standard, polish

voc = Vocabulary()
std = standard.Parser(voc)
pol = polish.Parser(voc)

class TestStandard(object):

    def test_parse_atomic(self):
        s = std.parse('A')
        assert s.is_atomic()

    def test_parse_negated(self):
        s = std.parse('~A')
        assert s.is_literal()
        assert s.operator == 'Negation'

    def test_parse_conjunction_parens(self):
        s = std.parse('(A & B)')
        assert s.operator == 'Conjunction'

    def test_parse_conjunction_no_parens(self):
        s = std.parse('A & B')
        assert s.operator == 'Conjunction'

    def test_fail_missing_close_paren(self):
        with pytest.raises(Parser.ParseError):
            std.parse('(A & B')

    def test_complex_quantified_1(self):
        s = std.parse('((A & B) V XxXy(=xy > !a))')
        assert s.operator == 'Disjunction'
        assert s.rhs.is_quantified()

    def test_complex_quantified_1_equivalence(self):
        s1 = std.parse('((A&B0)VXxXy(=xy>!a))')
        s2 = std.parse('((A & B) V XxXy(=xy > !a))')
        assert s1 == s2
        assert s1.lhs.rhs.subscript == 0

    def test_complex_modal_1(self):
        s = std.parse('(PXx!x V N=ab)')
        assert s.lhs.operator == 'Possibility'

class TestPolish(object):

    def test_parse_atomic(self):
        s = pol.parse('a')
        assert s.is_atomic()

    def test_parse_negated(self):
        s = pol.parse('Na')
        assert s.is_literal()
        assert s.operator == 'Negation'