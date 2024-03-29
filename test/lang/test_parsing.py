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
# pytableaux.lang.parsing tests
from pytest import raises

from pytableaux.errors import ParseError
from pytableaux.lang import *
from ..utils import BaseCase

std = Parser('standard')
pol = Parser('polish')

class TestParsers(BaseCase):

    def test_parse_conjunction(self):
        s = Parser('standard')('A & B')
        self.assertIs(s.TYPE, LexType.Operated)
        self.assertEqual(s.operator , 'Conjunction')

    def test_argument_no_prems_1_std_untitled(self):
        a = std.argument('A')
        self.assertEqual(len(a.premises) , 0)
        self.assertIs(a.conclusion.TYPE, LexType.Atomic)

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
        p = Parser(notation='standard', auto_preds=False)
        with raises(ParseError):
            p('F1ab')

    def test_unbound_var_error(self):
        with raises(ParseError):
            std('Fx')

    def test_rebind_var_error(self):
        with raises(ParseError):
            std('LxLxFx')

    def test_unused_var_error(self):
        with raises(ParseError):
            std('LxFa')

    def test_parse_errors_various_parens(self):
        # coverage
        with self.assertRaises(ParseError):
            std('(A & &A)')
        with self.assertRaises(ParseError):
            std('(A & ())')

    def test_infix_identity_variable(self):
        p = Parser('standard')
        s = p('Lxx=x')
        self.assertEqual(type(s), Quantified)

    def test_comma_raises_parse_error(self):
        p = Parser('standard')
        with self.assertRaises(ParseError):
            p('A % B,')

class TestPolish(BaseCase):

    def test_parse_conjunction(self):
        s = Parser('polish')('Kab')
        self.assertIs(s.TYPE, LexType.Operated)
        self.assertEqual(s.operator , 'Conjunction')

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

    def test_argument_prems_preparsed_titled(self):
        premises = map(pol, ('Aab', 'Nb'))
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
        self.assertTrue('(0, 0)' in res or 'TestArg' in res)
    
    def test_subscript_non_standard_digit_char(self):
        table = ParseTable(dict(
            notation = Notation.polish,
            dialect = 'test',
            mapping = dict(ParseTable.fetch('polish', 'default')) | {
                '@': (Marking.digit, 0)}))
        p = Parser(notation='polish', table=table)
        s: Atomic = p('a2@3')
        self.assertIsInstance(s, Atomic)
        self.assertEqual(s.index, 0)
        self.assertEqual(s.subscript, 203)
