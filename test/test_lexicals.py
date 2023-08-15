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
# pytableaux - lex module tests
# import pytest

import operator as opr
import pickle
from copy import copy
from itertools import product
from typing import cast

from pytableaux import errors
from pytableaux.errors import *
from pytableaux.lang import *
from pytableaux.lang.lex import *
from pytableaux.tools import EMPTY_SET

from .utils import BaseCase

Firsts = dict(
    (cls, cls.first()) for cls in LexType.classes)

F, G, H = Predicate.gen(3)
a, b, c = Constant.gen(3)
x, y, z = Variable.gen(3)
A, B, C = Atomic.gen(3)


class TestAbstract(BaseCase):

    def test_cannot_construct(self):
        with self.assertRaises(TypeError):
            Parameter(0, 0)

class TestConstant(BaseCase):

    def test_sorting(self):
        res = sorted([b, a])
        self.assertEqual(res[0], a)
        self.assertEqual(res[1], b)

    def test_index_too_large(self):
        with self.assertRaises(ValueError):
            Constant(Constant.TYPE.maxi + 1, 0)

    def test_is_constante(self):
        c = Constant(0, 0)
        self.assertTrue(c.is_constant)
        self.assertFalse(c.is_variable)

class TestVariable(BaseCase):

    def test_variable_index_too_large(self):
        with self.assertRaises(ValueError):
            Variable(Variable.TYPE.maxi + 1, 0)

class TestPredicate(BaseCase):

    def test_errors(self):
        with self.assertRaises(TypeError):
            Predicate(1, 0, 2, 'Identity')
        with self.assertRaises(ValueError):
            Predicate(-1, 4, 2)
        with self.assertRaises(TypeError):
            Predicate(0, None, 1)
        with self.assertRaises(ValueError):
            Predicate(0, -1, 1)
        # pickle problems
        # with self.assertRaises(AttributeError):
        #     F._value_ = F
        # with self.assertRaises(AttributeError):
        #     F._name_ = F.name
        # with self.assertRaises(AttributeError):
        #     F.__objclass__ = F.__class__

    def test_sys_attrs(self):
        p = Predicate.Identity
        self.assertIs(p._value_, p)
        self.assertEqual(p._name_, p.name)
        self.assertIs(p.__objclass__, Predicate.System)
        self.assertTrue(p.is_system)

class TestPredicates(BaseCase):

    def test_errors(self):
        with self.assertRaises((TypeError,ValueError)):
            Predicates().add('foo')
        with self.assertRaises((TypeError,ValueError)):
            Predicates([('foo', 4)])
        with self.assertRaises(TypeError):
            Predicates()['nonIndexKey']
        with self.assertRaises(TypeError):
            Predicates()[(-1, 2)]
        with self.assertRaises(KeyError):
            Predicates().get('NonExistentPred')
        with self.assertRaises(KeyError):
            Predicates().get((-1, 2))
        with self.assertRaises(KeyError):
            Predicates().get((1, 2))
        with self.assertRaises((TypeError,ValueError)):
            Predicates().add((0, 0, 2, 'Identity'))
        with self.assertRaises((TypeError,ValueError)): # bad arity
            Predicates().add((0, 0, None))
        with self.assertRaises((TypeError,ValueError)): # bad arity
            Predicates().add((0, 0,))
        with self.assertRaises((TypeError,ValueError)): # bad arity
            Predicates().add((0, 0, 0))
        with self.assertRaises(ValueError): # index too large
            Predicates().add((Predicate.TYPE.maxi + 1, 0, 1))
        preds = Predicates({(0, 0, 1)})
        with self.assertRaises(ValueError): # arity mismatch
            preds.add((0, 0, 2))

    def test_get_predicate_by_index_subscript_sys_identity(self):
        self.assertEqual(Predicates().get((-1, 0)).name, 'Identity')

    def test_get_pred_coords_tuple(self):
        pred, = Predicates({(1, 1, 1)})
        self.assertEqual(pred.spec, (1, 1, 1))
        self.assertEqual(pred.bicoords, (1, 1))

    def test_pred_no_name(self):
        v = Predicates()
        p = Predicate((1, 0, 1))
        v.add(p)
        p1 = v.get((1, 0))
        self.assertEqual(p, p1)
        p = Predicate((1, 1, 2))
        v.add(p)
        p2 = v.get((1, 1))
        self.assertEqual(p, p2)

    def test_declare1(self):
        p, = Predicates({(0, 0, 1)})
        self.assertEqual(p.index, 0)
        self.assertEqual(p.subscript, 0)
        self.assertEqual(p.arity, 1)

    def test_copy_get_predicate(self):
        v = Predicates()
        spec = (0, 0, 1)
        v.add(spec)
        pred = v.get(spec)
        v2 = copy(v)
        self.assertEqual(v2.get(spec), pred)
        self.assertIsNot(v, v2)

    def test_compare_id_with_user_pred(self):
        pred, = Predicates({(0, 0, 1)})
        self.assertLess(Predicate.Identity, pred)
        self.assertLessEqual(Predicate.Identity, pred)
        self.assertGreater(pred, Predicate.Identity)
        self.assertGreaterEqual(pred, Predicate.Identity)

    def test_lookup_refs(self):
        v = Predicates(((0, 0, 1),))
        self.assertIn((0, 0), v)
        self.assertIn((0, 0, 1), v)

    def test_init_iter_types(self):
        v = Predicates([(0, 0, 2)])
        p = v.get((0, 0))
        self.assertEqual(p.arity, 2)
        v = Predicates(((0, 0, 3),))
        p = v.get((0, 0))
        self.assertEqual(p.arity, 3)
        v = Predicates(Predicate.gen(4))
        self.assertEqual(len(v), 4)
        v2 = Predicates(v)
        self.assertEqual(v, v2)
        self.assertEqual(len(v2), 4)
        self.assertIsNot(v, v2)

    def test_copy_preds(self):
        p1, p2, p3 = Predicate.gen(3)
        v1 = Predicates((p1, p2))
        v2 = copy(v1)
        self.assertEqual(v1, v2)
        self.assertIsNot(v1, v2)
        self.assertNotIn(p3, v1)
        v1.add(p3)
        self.assertIn(p3, v1)
        self.assertNotIn(p3, v2)

class TestSystem(BaseCase):

    def test_predicate_equality(self):
        self.assertEqual(Predicates().get('Identity').name, 'Identity')
        self.assertEqual(Predicate.System['Identity'], Predicate.System.Identity)

    def test_sys_preds_enum_value(self):
        self.assertIs(Predicate.System.Identity, Predicate.System['Identity'])
        self.assertEqual(sorted(Predicate.System), list(Predicate.System))


class TestAbstract(BaseCase):
    def test_base_cannot_construct(self):
        with self.assertRaises(TypeError):
            Sentence()

class TestAtomic(BaseCase):

    def test_errors(self):
        with self.assertRaises(ValueError):
            Atomic(Atomic.TYPE.maxi + 1, 0)

    def test_setence_impl(self):
        s = A
        self.assertIs(s.TYPE, LexType.Atomic)
        self.assertEqual(s.constants, EMPTY_SET)
        self.assertEqual(s.variables, EMPTY_SET)
        self.assertEqual(s.predicates, EMPTY_SET)
        self.assertEqual(s.atomics, {s})
        self.assertEqual(s.operators, tuple())
        self.assertEqual(s.substitute(a, x), s)
        self.assertEqual(s.negate(), self.p('Na'))
        self.assertEqual(s.negative(), self.p('Na'))
        self.assertEqual(s.asserted(), self.p('Ta'))
        self.assertEqual(s.disjoin(B), self.p('Aab'))
        self.assertEqual(s.conjoin(B), self.p('Kab'))

    def test_next(self):
        s = A.next()
        self.assertEqual(s.index, 1)
        self.assertEqual(s.subscript, 0)
        s = Atomic(Atomic.TYPE.maxi, 0).next()
        self.assertEqual(s.index, 0)
        self.assertEqual(s.subscript, 1)

class TestPredicated(BaseCase):

    def test_errors(self):
        with self.assertRaises(ValueError):
            Predicated('MyPredicate', (a, b))
        with self.assertRaises(TypeError):
            Predicated('Identity', (a,))

    def test_setence_impl(self):
        s = Predicated(F,(a,))
        self.assertEqual(s.predicate, Predicate((0, 0, 1)))
        self.assertIs(s.TYPE, LexType.Predicated)
        self.assertEqual(s.constants, {a})
        self.assertEqual(s.variables, EMPTY_SET)
        self.assertEqual(s.predicates, {F})
        self.assertEqual(s.atomics, EMPTY_SET)
        self.assertEqual(s.operators, tuple())
        self.assertEqual(s.substitute(a, x), s)
        self.assertEqual(s.negate(), self.p('NFm'))
        self.assertEqual(s.negative(), self.p('NFm'))
        self.assertEqual(s.asserted(), self.p('TFm'))
        self.assertEqual(s.disjoin(B), self.p('AFmb'))
        self.assertEqual(s.conjoin(B), self.p('KFmb'))
        # self.assertEqual(s.variable_occurs(x), False)
        s = Predicated(F, (x,))
        self.assertIs(s.TYPE, LexType.Predicated)
        self.assertEqual(s.substitute(a, x), F((a,)))
        self.assertEqual(s.variables, {x})
        # self.assertEqual(s.variable_occurs(x), True)

    def test_atomic_less_than_predicated(self):
        s2 = Predicated.first()
        self.assertLess(A, s2)
        self.assertLessEqual(A, s2)
        self.assertGreater(s2, A)
        self.assertGreaterEqual(s2, A)

    def test_sorting_predicated_sentences(self):
        # Lexical items should be sortable for models.
        ss = list(map(Predicate.first(), Constant.gen(2)))
        s1, s2 = ss
        ss.reverse()
        self.assertEqual(ss, [s2, s1])
        res = sorted(ss)
        self.assertEqual(res, [s1, s2])

    def test_predicated_substitute_a_for_x_identity(self):
        s = Predicated('Identity', (x, b))
        res = s.substitute(a, x)
        self.assertEqual(res.params, (a, b))

class TestQuantified(BaseCase):

    def test_quantified_substitute_inner_quantified(self):
        q = Quantifier.Existential
        s1 = Predicated('Identity', (x, y))
        s2 = Quantified(q, x, s1)
        s3 = Quantified(q, y, s2)
        res = s3.sentence.substitute(a, y)
        check = Quantified(
            q,
            Variable(0, 0),
            Predicated(
                'Identity', (Variable(0, 0), Constant(0, 0))
            )
        )
        self.assertEqual(res, check)

    def test_complex_quantified_substitution(self):
        preds = Predicates({(0, 0, 2)})
        s1 = cast(Quantified, self.p('SxMVyFxy', preds))
        m = Constant(0, 0)
        s2 = s1.sentence.substitute(m, s1.variable)
        s3 = self.p('MVyFmy', preds)
        self.assertEqual(s2, s3)

class TestOperated(BaseCase):

    def test_errors(self):
        with self.assertRaises(ValueError):
            Operated('Misjunction', (A, A))
        with self.assertRaises((ValueError, TypeError)):
            Operated(Operator.Negation, (A, A))

    def test_operators(self):
        self.assertEqual(self.p('KAMVxJxNbTNNImn').operators, (
            Operator.Conjunction,
            Operator.Disjunction,
            Operator.Possibility,
            Operator.Negation,
            Operator.Assertion,
            Operator.Negation,
            Operator.Negation))


class TestGenericApi(BaseCase):

    def test_first_all_lex_classes(self):

        self.assertEqual(Lexical.first()     , Predicate.first())
        self.assertEqual(LexicalAbc.first()  , Predicate.first())
        self.assertEqual(LexicalEnum.first() , Quantifier.first())
        self.assertEqual(CoordsItem.first()  , Predicate.first())
        self.assertEqual(Parameter.first()   , Constant.first())
        self.assertEqual(Sentence.first()    , Atomic.first())

        self.assertIs(type(Variable.first())  , Variable)
        self.assertIs(type(Quantifier.first()), Quantifier)
        self.assertIs(type(Operator.first())  , Operator)
        self.assertIs(type(Atomic.first())    , Atomic)
        self.assertIs(type(Predicated.first()), Predicated)
        self.assertIs(type(Quantified.first()), Quantified)
        self.assertIs(type(Operated.first())  , Operated)

    def test_gen_all_lex_classes(self):
        self.assertEqual(list(Lexical.gen(1))[0]    , Predicate.first())
        self.assertEqual(list(LexicalAbc.gen(1))[0] , Predicate.first())
        self.assertEqual(list(LexicalEnum.gen(1))[0], Quantifier.first())
        self.assertEqual(list(CoordsItem.gen(1))[0] , Predicate.first())
        self.assertEqual(list(Parameter.gen(1))[0]  , Constant.first())
        self.assertEqual(list(Sentence.gen(1))[0]   , Atomic.first())

        self.assertIs(type(list(Variable.gen(1))[0])  , Variable)
        self.assertIs(type(list(Quantifier.gen(1))[0]), Quantifier)
        self.assertIs(type(list(Operator.gen(1))[0])  , Operator)
        self.assertIs(type(list(Atomic.gen(1))[0])    , Atomic)
        self.assertIs(type(list(Predicated.gen(1))[0]), Predicated)
        self.assertIs(type(list(Quantified.gen(1))[0]), Quantified)
        self.assertIs(type(list(Operated.gen(1))[0])  , Operated)

    def test_first_next(self):
        for cls in LexType.classes:
            inst = cls.first()
            for x in range(2):
                self.assertIsInstance(inst, cls)
                self.assertIsInstance(inst, Lexical)
                inst = inst.next()
                st = inst.sort_tuple
                self.assertIsInstance(st, tuple)
                self.assertGreater(len(st), 0)
                for v in st:
                    self.assertIsInstance(v, int)
                self.assertIsInstance(hash(inst), int)
                if cls is Quantifier: break

    def test_deep_copy(self):
        from copy import copy, deepcopy
        for cls in LexType.classes:
            a = cls.first()
            b = copy(a)
            self.assertEqual(a, b)
            self.assertIs(a, b)
            c = deepcopy(a)
            self.assertEqual(a, c)
            self.assertIs(a, c)

    def test_sort_tuple(self):
        for cls, itm in Firsts.items():
            self.assertEqual(itm.sort_tuple[0], cls.TYPE.rank)
            for i in itm.sort_tuple:
                self.assertIs(type(i), int)



class TestCrossSorting(BaseCase):

    def test_le_lt_ge_gt_symmetry(self):

        self.assertLess(F, a)
        self.assertLess(a, x)
        self.assertLess(x, A)
        self.assertLess(F, A)

        self.assertLessEqual(F, a)
        self.assertLessEqual(a, x)
        self.assertLessEqual(x, A)
        self.assertLessEqual(F, A)

        self.assertGreater(a, F)
        self.assertGreater(x, a)
        self.assertGreater(A, x)
        self.assertGreater(A, F)

        self.assertGreaterEqual(a, F)
        self.assertGreaterEqual(x, a)
        self.assertGreaterEqual(A, x)
        self.assertGreaterEqual(A, F)

    def test_bug_le_ge(self):
        self.assertLess(a, x)
        self.assertLessEqual(a, x)
        self.assertFalse(x < a)
        self.assertFalse(x <= a)

class TestNotImplTypes(BaseCase):
    def test_incompatible(self):
        itms = Firsts.values()
        itms = [Atomic.first()]
        others = [
            1, None, False, '', slice(None, None, None), [], set(), {}]
        opers = (opr.lt, opr.le, opr.gt, opr.ge, opr.eq)
        it = product(opers, itms, others)
        for oper, itm, other in it:
            # print(oper, itm, other)
            meth = getattr(itm, '__%s__' % oper.__name__)
            res = meth(other)
            self.assertIs(res, NotImplemented)
            if oper is not opr.eq:
                with self.assertRaises(TypeError):
                    oper(itm, other)
            # self.assertEqual(meth(itm), 0)
            # self.assertEqual(oper(itm, itm), 0)


class TestSorting(BaseCase):

    def test_compare1(self):
        a1 = self.parg('Denying the Antecedent')
        a2 = self.parg('Biconditional Introduction 3')
        self.assertLess(a1.conclusion, a2.conclusion)
        self.assertEqual(len(a1), len(a2))
        self.assertGreater(a2, a1)
        self.assertGreaterEqual(a2, a1)
        self.assertLess(a1, a2)
        self.assertLessEqual(a1, a2)

    def test_gen_sentence1(self):
        a1 = Argument(A)
        for _ in range(10):
            a2 = Argument(a1.conclusion.next())
            self.assertGreater(a2, a1)
            self.assertGreaterEqual(a2, a1)
            self.assertLess(a1, a2)
            self.assertLessEqual(a1, a2)
            self.assertNotEqual(a1, a2)
            a1 = a2


class TestClasses(BaseCase):

    def test_readonly(self):
        with self.assertRaises(AttributeError):
            Predicate.x = 1
        with self.assertRaises(AttributeError):
            del Predicate.Coords
        with self.assertRaises(AttributeError):
            del Predicate.first().arity
        with self.assertRaises(AttributeError):
            s = Atomic.first()
            s.index = 2

    def test_pickle(self):
        import warnings
        with warnings.catch_warnings():
            warnings.simplefilter('ignore', category=errors.RepeatValueWarning)
            for cls in LexType.classes:
                item = cls.first().next()
                s = pickle.dumps(item)
                item2 = pickle.loads(s)
                self.assertEqual(item, item2)

class TestIdentCreate(BaseCase):

    def test_atomic_sentence_from_ident(self):
        self.assertEqual(Sentence(('Atomic', (0, 0))), Atomic(0,0))

    def test_operated_sentence_from_ident(self):
        s1 = Sentence(('Operated', ('Assertion', (('Atomic', (0, 0)),))))
        s2 = Atomic(0,0).asserted()
        self.assertEqual(s1, s2)

    def test_predicated_sentence_from_ident(self):
        s1 = Sentence(('Predicated', ((0, 0, 1), (('Constant', (0, 0)),))))
        s2 = Predicate((0, 0, 1))(Constant(0,0))
        self.assertEqual(s1, s2)

    def test_predicate_parameter_from_ident(self):
        self.assertEqual(Parameter(('Constant', (0, 0))), Constant(0,0))

    def test_operator_lexicalabc_from_ident(self):
        self.assertIs(LexicalAbc(('Operator', ('Conjunction',))), Operator.Conjunction)