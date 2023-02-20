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
# pytableaux - parsing test cases
from pytest import raises

from pytableaux.errors import ParseError
from pytableaux.lang.lex import Predicate, LexType
from pytableaux.lang.collect import Predicates
from pytableaux.lang.parsing import Parser

preds = Predicates(Predicate.gen(3))
std = Parser('standard', preds)
pol = Parser('polish', preds)

def test_parse_standard():
    s = Parser('standard')('A & B')
    assert s.TYPE is LexType.Operated
    assert s.operator == 'Conjunction'

def test_parse_polish():
    s = Parser('polish')('Kab')
    assert s.TYPE is LexType.Operated
    assert s.operator == 'Conjunction'

def test_argument_no_prems_1_std_untitled():
    a = std.argument('A')
    assert len(a.premises) == 0
    assert a.conclusion.TYPE is LexType.Atomic

def test_argument_prems_preparsed_titled():
    premises = pol('Aab'), pol('Nb')
    conclusion = pol('a')
    a = pol.argument(conclusion, premises, title='TestArgument')
    assert len(a.premises) == 2
    assert a.title == 'TestArgument'

def test_argument_parse_prems_preparsed_conclusion():
    premises = ('Aab', 'Nb')
    conclusion = pol('a')
    a = pol.argument(conclusion, premises)
    assert len(a.premises) == 2
    assert a.conclusion == conclusion

def test_argument_repr_coverage():
    a = pol.argument('a', title='TestArg')
    res = a.__repr__()
    assert '(0, 0)' in res or 'TestArg' in res

class TestStandard:

    def test_parse_atomic(self):
        s = std('A')
        assert s.TYPE is LexType.Atomic

    def test_parse_negated(self):
        s = std('~A')
        assert s.operator == 'Negation'

    def test_parse_conjunction_parens(self):
        s = std('(A & B)')
        assert s.operator == 'Conjunction'

    def test_parse_conjunction_no_parens(self):
        s = std('A & B')
        assert s.operator == 'Conjunction'

    def test_complex_quantified_1(self):
        s = std('((A & B) V XxXy(=xy > !a))')
        assert s.operator == 'Disjunction'
        assert s.rhs.TYPE is LexType.Quantified

    def test_complex_quantified_1_equivalence(self):
        s1 = std('((A&B0)VXxXy(=xy>!a))')
        s2 = std('((A & B) V XxXy(=xy > !a))')
        assert s1 == s2
        assert s1.lhs.rhs.subscript == 0

    def test_complex_modal_1(self):
        s = std('(PXx!x V N=ab)')
        assert s.TYPE is LexType.Operated
        assert s.lhs.operator == 'Possibility'

    def test_infix_pred(self):
        s = std('a=b')
        assert s.predicate.name == 'Identity'

    def test_fail_missing_close_paren(self):
        with raises(ParseError):
            std('(A & B')

    def test_binary_prefix_error(self):
        with raises(ParseError):
            std('&AB')

    def test_unary_infix_pred_error(self):
        with raises(ParseError):
            std('aF')

    def test_undefined_pred_error(self):
        with raises(ParseError):
            std('F1ab')

    def test_unbound_var_error(self):
        with raises(ParseError):
            std('Fx')

    def test_rebind_var_error(self):
        with raises(ParseError):
            std('LxLxFx')

    def test_unused_var_error(self):
        with raises(ParseError):
            std('LxFa')

class TestPolish(object):

    def test_parse_atomic(self):
        assert pol('a').TYPE is LexType.Atomic

    def test_parse_negated(self):
        assert pol('Na').operator == 'Negation'

    def test_unexpected_constant_error(self):
        with raises(ParseError):
            pol('m')

    def test_empty_error(self):
        with raises(ParseError):
            pol('')