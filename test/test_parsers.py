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
from . import BaseCase

preds = Predicates(Predicate.gen(3))
std = Parser('standard', preds)
pol = Parser('polish', preds)

class TestParsers(BaseCase):

    def test_parse_standard(self):
        s = Parser('standard')('A & B')
        self.assertIs(s.TYPE, LexType.Operated)
        self.assertEqual(s.operator , 'Conjunction')

    def test_parse_polish(self):
        s = Parser('polish')('Kab')
        self.assertIs(s.TYPE, LexType.Operated)
        self.assertEqual(s.operator , 'Conjunction')

    def test_argument_no_prems_1_std_untitled(self):
        a = std.argument('A')
        self.assertEqual(len(a.premises) , 0)
        self.assertIs(a.conclusion.TYPE, LexType.Atomic)

    def test_argument_prems_preparsed_titled(self):
        premises = pol('Aab'), pol('Nb')
        conclusion = pol('a')
        a = pol.argument(conclusion, premises, title='TestArgument')
        self.assertEqual(len(a.premises) , 2)
        self.assertEqual(a.title , 'TestArgument')

    def test_argument_parse_prems_preparsed_conclusion(self):
        premises = ('Aab', 'Nb')
        conclusion = pol('a')
        a = pol.argument(conclusion, premises)
        self.assertEqual(len(a.premises) , 2)
        self.assertEqual(a.conclusion , conclusion)

    def test_argument_repr_coverage(self):
        a = pol.argument('a', title='TestArg')
        res = a.__repr__()
        assert '(0, 0)' in res or 'TestArg' in res

    def test_parse_atomic(self):
        s = std('A')
        self.assertIs(s.TYPE, LexType.Atomic)

    def test_parse_negated(self):
        s = std('~A')
        self.assertEqual(s.operator , 'Negation')

    def test_parse_conjunction_parens(self):
        s = std('(A & B)')
        self.assertEqual(s.operator , 'Conjunction')

    def test_parse_conjunction_no_parens(self):
        s = std('A & B')
        self.assertEqual(s.operator , 'Conjunction')

    def test_complex_quantified_1(self):
        s = std('((A & B) V XxXy(=xy > !a))')
        self.assertEqual(s.operator , 'Disjunction')
        self.assertIs(s.rhs.TYPE, LexType.Quantified)

    def test_complex_quantified_1_equivalence(self):
        s1 = std('((A&B0)VXxXy(=xy>!a))')
        s2 = std('((A & B) V XxXy(=xy > !a))')
        self.assertEqual(s1 , s2)
        self.assertEqual(s1.lhs.rhs.subscript , 0)

    def test_complex_modal_1(self):
        s = std('(PXx!x V N=ab)')
        self.assertIs(s.TYPE, LexType.Operated)
        self.assertEqual(s.lhs.operator , 'Possibility')

    def test_infix_pred(self):
        s = std('a=b')
        self.assertEqual(s.predicate.name , 'Identity')

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

class TestPolish(BaseCase):

    def test_parse_atomic(self):
        self.assertIs(pol('a').TYPE, LexType.Atomic)

    def test_parse_negated(self):
        self.assertEqual(pol('Na').operator , 'Negation')

    def test_unexpected_constant_error(self):
        with raises(ParseError):
            pol('m')

    def test_empty_error(self):
        with raises(ParseError):
            pol('')