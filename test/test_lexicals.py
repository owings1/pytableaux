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
# pytableaux - lex module tests
# import pytest

from pytableaux.errors import *
from pytableaux.lang.collect import *
from pytableaux.lang.lex import *
from pytableaux.tools.sets import EMPTY_SET

try:
    from test.tutils import BaseSuite, skip
except ModuleNotFoundError:
    from tutils import BaseSuite, skip

import operator as opr
from copy import copy
from itertools import product

from pytest import raises

Firsts = dict(
    (cls, cls.first()) for cls in LexType.classes
)

F, G, H = Predicate.gen(3)
a, b, c = Constant.gen(3)
x, y, z = Variable.gen(3)
A, B, C = Atomic.gen(3)

Pred, Preds, Sys = Predicate, Predicates, Predicate.System


class TestParameter(BaseSuite):

    class TestAbstract(BaseSuite):

        def test_cannot_construct(self):
            with raises(TypeError):
                Parameter(0, 0)

    class TestConstant(BaseSuite):

        def test_sorting(self):
            res = sorted([b, a])
            assert res[0] == a
            assert res[1] == b

        def test_index_too_large(self):
            with raises(ValueError):
                Constant(Constant.TYPE.maxi + 1, 0)

        def test_is_constante(self):
            c = Constant(0, 0)
            assert c.is_constant
            assert not c.is_variable

    class TestVariable(BaseSuite):

        def test_variable_index_too_large(self):
            with raises(ValueError):
                Variable(Variable.TYPE.maxi + 1, 0)

class TestPredicate(BaseSuite):

    def test_errors(self):
        with raises(TypeError):
            Predicate(1, 0, 2, 'Identity')
        with raises(ValueError):
            Predicate(-1, 4, 2)
        with raises(TypeError):
            Predicate(0, None, 1)
        with raises(ValueError):
            Predicate(0, -1, 1)
        with raises(AttributeError):
            F._value_ = F
        with raises(AttributeError):
            F._name_ = F.name
        with raises(AttributeError):
            F.__objclass__ = F.__class__
    def test_sys_attrs(self):
        p = Sys.Identity
        assert p._value_ is p
        assert p._name_ == p.name
        assert p.__objclass__ is Sys
        assert p.is_system

class TestPredicates(BaseSuite):

    def test_errors(self):
        with raises((TypeError,ValueError)):
            Predicates().add('foo')
        with raises(TypeError):
            Predicates([('foo', 4)])
        with raises(TypeError):
            Predicates()['nonIndexKey']
        with raises(TypeError):
            Predicates()[(-1, 2)]
        with raises(KeyError):
            Predicates().get('NonExistentPred')
        with raises(KeyError):
            Predicates().get((-1, 2))
        with raises(KeyError):
            Predicates().get((1, 2))
        with raises(TypeError):
            Predicates().add((0, 0, 2, 'Identity'))
        with raises(TypeError): # bad arity
            Predicates().add((0, 0, None))
        with raises(TypeError): # bad arity
            Predicates().add((0, 0,))
        with raises(ValueError): # bad arity
            Predicates().add((0, 0, 0))
        with raises(ValueError): # index too large
            Predicates().add((Predicate.TYPE.maxi + 1, 0, 1))
        preds = Predicates({(0, 0, 1)})
        with raises(ValueError): # arity mismatch
            preds.add((0, 0, 2))

    def test_get_predicate_by_index_subscript_sys_identity(self):
        assert Predicates().get((-1, 0)).name == 'Identity'

    def test_get_pred_coords_tuple(self):
        pred, = Predicates({(1, 1, 1)})
        assert pred.spec == (1, 1, 1)
        assert pred.bicoords == (1, 1)

    def test_pred_no_name(self):
        v = Predicates()
        p = Predicate((1, 0, 1))
        v.add(p)
        p1 = v.get((1, 0))
        assert p == p1
        p = Predicate((1, 1, 2))
        v.add(p)
        p2 = v.get((1, 1))
        assert p == p2

    def test_declare1(self):
        p, = Predicates({(0, 0, 1)})
        assert p.index == 0
        assert p.subscript == 0
        assert p.arity == 1

    def test_copy_get_predicate(self):
        v = Predicates()
        spec = (0, 0, 1)
        v.add(spec)
        pred = v.get(spec)
        v2 = copy(v)
        assert v2.get(spec) == pred
        assert v is not v2

    def test_compare_id_with_user_pred(self):
        pred, = Predicates({(0, 0, 1)})
        assert Sys.Identity < pred
        assert Sys.Identity <= pred
        assert pred > Sys.Identity
        assert pred >= Sys.Identity

    def test_lookup_refs(self):
        v = Predicates(((0, 0, 1),))
        assert (0, 0) in v
        assert (0, 0, 1) in v

    def test_init_iter_types(self):
        v = Predicates([(0, 0, 2)])
        p = v.get((0, 0))
        assert p.arity == 2
        v = Predicates(((0, 0, 3),))
        p = v.get((0, 0))
        assert p.arity == 3
        v = Predicates(Predicate.gen(4))
        assert len(v) == 4
        v2 = Predicates(v)
        assert v == v2 and len(v2) == 4
        assert v is not v2

    def test_copy_preds(self):
        p1, p2, p3 = Predicate.gen(3)
        v1 = Predicates((p1, p2))
        v2 = copy(v1)
        assert v1 == v2 and v1 is not v2
        assert p3 not in v1
        v1.add(p3)
        assert p3 in v1
        assert p3 not in v2

    class TestSystem(BaseSuite):

        def test_predicate_equality(self):
            assert Predicates().get('Identity').name == 'Identity'
            assert Predicate.System['Identity'] == Predicate.System.Identity

        def test_sys_preds_enum_value(self):
            assert Pred != Preds
            assert Sys is Predicate.System
            assert Pred.System is Preds.System
            assert Sys.Identity is Sys['Identity']
            assert sorted(Preds.System) == list(Preds.System)


class TestSentence(BaseSuite):

    class TestAbstract(BaseSuite):
        def test_base_cannot_construct(self):
            with raises(TypeError):
                Sentence()

    class TestAtomic(BaseSuite):

        def test_errors(self):
            with raises(ValueError):
                Atomic(Atomic.TYPE.maxi + 1, 0)

        def test_setence_impl(self):
            s = A
            assert s.TYPE is LexType.Atomic
            assert s.constants == EMPTY_SET
            assert s.variables == EMPTY_SET
            assert s.predicates == EMPTY_SET
            assert s.atomics == {s}
            assert s.operators == tuple()
            assert s.substitute(a, x) == s
            assert s.negate() == self.p('Na')
            assert s.negative() == self.p('Na')
            assert s.asserted() == self.p('Ta')
            assert s.disjoin(B) == self.p('Aab')
            assert s.conjoin(B) == self.p('Kab')
            # assert s.variable_occurs(x) == False

        def test_next(self):
            s = A.next()
            assert s.index == 1
            assert s.subscript == 0
            s =  Atomic(Atomic.TYPE.maxi, 0).next()
            assert s.index == 0
            assert s.subscript == 1

    class TestPredicated(BaseSuite):

        def test_errors(self):
            with raises(ValueError):
                Predicated('MyPredicate', (a, b))
            with raises(TypeError):
                Predicated('Identity', (a,))

        def test_setence_impl(self):
            s = Predicated(F,(a,))
            assert s.predicate == Predicate((0, 0, 1))
            assert s.TYPE is LexType.Predicated
            assert s.constants == {a}
            assert s.variables == EMPTY_SET
            assert s.predicates == {F}
            assert s.atomics == EMPTY_SET
            assert s.operators == tuple()
            assert s.substitute(a, x) == s
            assert s.negate() == self.p('NFm')
            assert s.negative() == self.p('NFm')
            assert s.asserted() == self.p('TFm')
            assert s.disjoin(B) == self.p('AFmb')
            assert s.conjoin(B) == self.p('KFmb')
            # assert s.variable_occurs(x) == False
            s = Predicated(F, (x,))
            assert s.TYPE is LexType.Predicated
            assert s.substitute(a, x) == F((a,))
            assert s.variables == {x}
            # assert s.variable_occurs(x) == True

        def test_atomic_less_than_predicated(self):
            s2 = Predicated.first()
            assert A < s2
            assert A <= s2
            assert s2 > A
            assert s2 >= A

        def test_sorting_predicated_sentences(self):
            # Lexical items should be sortable for models.
            ss = list(map(Predicate.first(), Constant.gen(2)))
            s1, s2 = ss
            ss.reverse()
            assert ss == [s2, s1]
            res = sorted(ss)
            assert res == [s1, s2]

        def test_predicated_substitute_a_for_x_identity(self):
            s = Predicated('Identity', (x, b))
            res = s.substitute(a, x)
            assert res.params == (a, b)

    class TestQuantified(BaseSuite):

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
            assert res == check

        def test_complex_quantified_substitution(self):
            preds = Predicates({(0, 0, 2)})
            s1: Quantified = self.p('SxMVyFxy', preds)
            m = Constant(0, 0)
            s2 = s1.sentence.substitute(m, s1.variable)
            s3 = self.p('MVyFmy', preds)
            assert s2 == s3

    class TestOperated(BaseSuite):

        def test_errors(self):
            with raises(ValueError):
                Operated('Misjunction', (A, A))
            with raises((ValueError, TypeError)):
                Operated(Operator.Negation, (A, A))

        def test_operators(self):
            assert self.p('KAMVxJxNbTNNImn').operators == (
                Operator.Conjunction,
                Operator.Disjunction,
                Operator.Possibility,
                Operator.Negation,
                Operator.Assertion,
                Operator.Negation,
                Operator.Negation,
            )


class TestGenericApi(BaseSuite):

    def test_first_all_lex_classes(self):

        assert Lexical.first()      == Predicate.first()
        assert LexicalAbc.first()   == Predicate.first()
        assert LexicalEnum.first()  == Quantifier.first()
        assert CoordsItem.first()   == Predicate.first()
        assert Parameter.first()    == Constant.first()
        assert Sentence.first()     == Atomic.first()

        assert type(Variable.first())   is Variable
        assert type(Quantifier.first()) is Quantifier
        assert type(Operator.first())   is Operator
        assert type(Atomic.first())     is Atomic
        assert type(Predicated.first()) is Predicated
        assert type(Quantified.first()) is Quantified
        assert type(Operated.first())   is Operated

    def test_gen_all_lex_classes(self):
        assert list(Lexical.gen(1))[0]     == Predicate.first()
        assert list(LexicalAbc.gen(1))[0]  == Predicate.first()
        assert list(LexicalEnum.gen(1))[0] == Quantifier.first()
        assert list(CoordsItem.gen(1))[0]  == Predicate.first()
        assert list(Parameter.gen(1))[0]   == Constant.first()
        assert list(Sentence.gen(1))[0]    == Atomic.first()

        assert type(list(Variable.gen(1))[0])   is Variable
        assert type(list(Quantifier.gen(1))[0]) is Quantifier
        assert type(list(Operator.gen(1))[0])   is Operator
        assert type(list(Atomic.gen(1))[0])     is Atomic
        assert type(list(Predicated.gen(1))[0]) is Predicated
        assert type(list(Quantified.gen(1))[0]) is Quantified
        assert type(list(Operated.gen(1))[0])   is Operated

    def test_first_next(self):
        for cls in LexType.classes:
            inst = cls.first()
            for x in range(2):
                assert isinstance(inst, cls)
                assert isinstance(inst, Lexical)
                inst = inst.next()
                st = inst.sort_tuple
                assert isinstance(st, tuple)
                assert len(st)
                for v in st:
                    assert isinstance(v, int)
                assert isinstance(hash(inst), int)
                if cls is Quantifier: break

    def test_deep_copy(self):
        from copy import copy, deepcopy
        for cls in LexType.classes:
            a = cls.first()
            b = copy(a)
            assert a == b
            assert a is b
            c = deepcopy(a)
            assert a == c
            assert a is c

    def test_sort_tuple(self):
        for cls, itm in Firsts.items():
            assert itm.sort_tuple[0] == cls.TYPE.rank
            for i in itm.sort_tuple:
                assert type(i) is int
class TestCrossCompare(BaseSuite):

    class TestCrossSorting(BaseSuite):

        def test_le_lt_ge_gt_symmetry(self):
            assert F < a
            assert a < x
            assert x < A
            assert F < A

            assert F <= a
            assert a <= x
            assert x <= A
            assert F <= A

            assert a > F
            assert x > a
            assert A > x
            assert A > F

            assert a >= F
            assert x >= a
            assert A >= x
            assert A >= F

        def test_bug_le_ge(self):
            assert a < x
            assert a <= x
            assert not (x < a)
            assert not (x <= a)

    class TestNotImplTypes(BaseSuite):
        def test_incompatible(self):
            itms = Firsts.values()
            itms = [Atomic.first()]
            others = [
                1, None, False, '', slice(None, None, None), [], set(), {}
            ]
            opers = (opr.lt, opr.le, opr.gt, opr.ge, opr.eq)
            it = product(opers, itms, others)
            for oper, itm, other in it:
                print(oper, itm, other)
                meth = getattr(itm, '__%s__' % oper.__name__)
                res = meth(other)
                assert res is NotImplemented
                if oper is not opr.eq:
                    with raises(TypeError):
                        oper(itm, other)
                # assert meth(itm) == 0
                # assert oper(itm, itm) == 0

class TestArgument(BaseSuite):

    class TestSorting(BaseSuite):

        def test_compare1(self):
            a1 = self.parg('Denying the Antecedent')
            a2 = self.parg('Biconditional Introduction 3')
            assert a1.conclusion < a2.conclusion
            assert len(a1) == len(a2)
            assert a2 > a1
            assert a2 >= a1
            assert a1 < a2
            assert a1 <= a2

        def test_gen_sentence1(self):
            a1 = Argument(A)
            for _ in range(10):
                a2 = Argument(a1.conclusion.next())
                assert a2 > a1
                assert a2 >= a1
                assert a1 < a2
                assert a1 <= a2
                assert a1 != a2
                a1 = a2

class TestClasses(BaseSuite):
    def test_readonly(self):
        with raises(AttributeError):
            Predicate.x = 1
        with raises(AttributeError):
            del Predicate.Coords
        with raises(AttributeError):
            del Predicate.first().arity
        with raises(AttributeError):
            s = Atomic.first()
            s.index = 2
        # A.index = A.index
