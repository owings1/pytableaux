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
# pytableaux - lexicals module tests
# import pytest

import examples
from lexicals import Predicates, Variable, Constant, Parameter, Predicate, \
    Atomic, Predicated, Quantified, Operated, Sentence
from parsers import parse
from errors import *
from copy import copy, deepcopy

from pytest import raises

class TestParameter(object):
    def test_cannot_construct(self):
        with raises(TypeError):
            Parameter(0, 0)

class TestPredicate(object):
    def test_sys_name_not_allowed(self):
        with raises(ValueError):
            Predicate(1, 0, 2, 'Identity')

    def test_neg_idx_not_allowed(self):
        with raises(ValueError):
            Predicate(-1, 4, 2)

class TestPredicates(object):

    def test_predicate_error_pred_defs_duple(self):
        with raises(TypeError):
            Predicates([('foo', 4)])

    def test_get_predicate_by_name_sys_identity(self):
        assert Predicates()['Identity'].name == 'Identity'

    def test_get_predicate_by_index_subscript_sys_identity(self):
        assert Predicates()[(-1, 0)].name == 'Identity'

    def test_get_predicate_notfound_bad_name(self):
        with raises(KeyError):
            Predicates()['NonExistentPredicate']

    def test_get_predicate_notfound_bad_custom_index(self):
        with raises(KeyError):
            Predicates()[(1, 2)]

    def test_get_predicate_no_such_predicate_error_bad_sys_index(self):
        with raises(KeyError):
            Predicates()[(-1, 2)]

    def test_get_pred_coords_tuple(self):
        v = Predicates()
        v.add((1, 1, 1))

    def test_pred_no_name(self):
        v = Predicates()
        p = v.add((1, 0, 1))
        p1 = v[(1, 0)]
        assert p == p1
        p = v.add((1, 1, 2))
        p2 = v[(1, 1)]
        assert p == p2

    def test_declare1(self):
        p = Predicates().add((0, 0, 1))
        assert p.index == 0
        assert p.subscript == 0
        assert p.arity == 1

    def test_vocab_copy_get_predicate(self):
        v = Predicates()
        spec = (0, 0, 1)
        predicate = v.add(spec)
        v2 = copy(v)
        assert v2[spec] == predicate

    def test_add_predicate_raises_non_predicate(self):
        with raises(TypeError):
            Predicates().add('foo')

    def test_declare_already_declared_sys(self):
        with raises(ValueError):
            Predicates().add((0, 0, 2, 'Identity'))

    def test_add_arity_mismatch(self):
        v = Predicates((0, 0, 1))
        v.add((0, 0, 1))
        with raises(ValueError):
            v.add((0, 0, 2))

    def test_declare_index_too_large(self):
        with raises(ValueError):
            Predicates().add((Predicate.MAXI + 1, 0, 1))

    def test_declare_arity_non_int(self):
        with raises(TypeError):
            Predicates().add((0, 0, None))
        with raises(TypeError):
            Predicates().add((0, 0,))

    def test_declare_arity_0_error(self):
        with raises(ValueError):
            Predicates().add((0, 0, 0))

    def test_new_predicate_subscript_non_int(self):
        with raises(TypeError):
            Predicate(0, None, 1)

    def test_new_predicate_subscript_less_than_0_error(self):
        with raises(ValueError):
            Predicate(0, -1, 1)

    def test_predicate_is_system_predicate_true(self):
        assert Predicates.system['Identity'].is_system

    def test_predicate_eq_true(self):
        assert Predicates.system['Identity'] == Predicates.system['Identity']

    def test_predicate_system_less_than_user(self):
        pred = Predicates().add((0, 0, 1))
        assert Predicates.system['Identity'] < pred

    def test_predicate_system_less_than_or_equal_to_user(self):
        pred = Predicates().add((0, 0, 1))
        assert Predicates.system['Identity'] <= pred

    def test_predicate_user_greater_than_system(self):
        pred = Predicates().add((0, 0, 1))
        assert pred > Predicates.system['Identity']

    def test_predicate_user_greater_than_or_equal_to_system(self):
        pred = Predicates().add((0, 0, 1))
        assert pred >= Predicates.system['Identity']

    def test_constant_index_too_large(self):
        with raises(ValueError):
            Constant(Constant.MAXI + 1, 0)

    def test_constant_is_constant_not_variable(self):
        c = Constant(0, 0)
        assert c.is_constant
        assert not c.is_variable

    def test_variable_index_too_large(self):
        with raises(ValueError):
            Variable(Variable.MAXI + 1, 0)

    def test_base_cannot_construct(self):
        with raises(TypeError):
            Sentence()

    def test_atomic_index_too_large(self):
        with raises(ValueError):
            Atomic(Atomic.MAXI + 1, 0)
        
    def test_atomic_substitute(self):
        s = Atomic(0, 0)
        c = Constant(0, 0)
        v = Variable(0, 0)
        res = s.substitute(c, v)
        assert res == s

    def test_atomic_constants_empty(self):
        s = Atomic(0, 0)
        res = s.constants()
        assert len(res) == 0

    def test_atomic_variables_empty(self):
        s = Atomic(0, 0)
        res = s.variables()
        assert len(res) == 0

    def test_atomic_next_a0_to_b0(self):
        s = Atomic(0, 0)
        res = s.next()
        assert res.index == 1
        assert res.subscript == 0

    def test_atomic_next_e0_to_a1(self):
        s = Atomic(Atomic.MAXI, 0)
        res = s.next()
        assert res.index == 0
        assert res.subscript == 1

    def test_predicated_no_such_predicate_no_vocab(self):
        params = [Constant(0, 0), Constant(1, 0)]
        with raises(NotFoundError):
            Predicated('MyPredicate', params)

    def test_predicated_arity_mismatch_identity(self):
        params = [Constant(0, 0)]
        with raises(TypeError):
            Predicated('Identity', params)

    def test_predicated_substitute_a_for_x_identity(self):
        s = Predicated('Identity', [Variable(0, 0), Constant(1, 0)])
        res = s.substitute(Constant(0, 0), Variable(0, 0))
        assert res.params[0] == Constant(0, 0)
        assert res.params[1] == Constant(1, 0)

    def test_quantified_substitute_inner_quantified(self):
        x = Variable(0, 0)
        y = Variable(1, 0)
        m = Constant(0, 0)
        s1 = Predicated('Identity', [x, y])
        s2 = Quantified('Existential', x, s1)
        s3 = Quantified('Existential', y, s2)
        res = s3.sentence.substitute(m, y)
        check = Quantified(
            'Existential',
            Variable(0, 0),
            Predicated(
                'Identity', [Variable(0, 0), Constant(0, 0)]
            )
        )
        assert res == check

    def test_operated_no_such_operator(self):
        s = Atomic(0, 0)
        with raises(NotFoundError):
            Operated('Misjunction', [s, s])

    def test_operated_arity_mismatch_negation(self):
        s = Atomic(0, 0)
        with raises(TypeError):
            Operated('Negation', [s, s])

    def test_constant_repr_contains_subscript(self):
        c = Constant(0, 8)
        res = str(c)
        assert '8' in res

    def test_atomic_less_than_predicated(self):
        s1 = Atomic(0, 4)
        s2 = examples.predicated()
        assert s1 < s2
        assert s1 <= s2
        assert s2 > s1
        assert s2 >= s1

    def test_sentence_operators_collection(self):
        s = parse('KAMVxJxNbTNNImn')
        ops = s.operators()
        assert len(ops) == 7
        assert ','.join(ops) == 'Conjunction,Disjunction,Possibility,Negation,Assertion,Negation,Negation'

    def test_complex_quantified_substitution(self):
        vocab = Predicates()
        vocab.add((0, 0, 2))
        s1 = parse('SxMVyFxy', vocab=vocab)
        m = Constant(0, 0)
        s2 = s1.sentence.substitute(m, s1.variable)
        s3 = parse('MVyFmy', vocab=vocab)
        assert s2 == s3

    def test_with_pred_defs_single_pred_with_length4(self):
        v = Predicates((0, 0, 1))
        assert (0, 0) in v
        assert (0, 0, 1) in v

    def test_with_pred_defs_single_def_list(self):
        vocab = Predicates([(0, 0, 2)])
        predicate = vocab[(0, 0)]
        assert predicate.arity == 2

    def test_with_pred_defs_single_def_tuple(self):
        vocab = Predicates(((0, 0, 3),))
        predicate = vocab[(0, 0)]
        assert predicate.arity == 3

    def test_sorting_constants(self):
        c1 = Constant(1, 0)
        c2 = Constant(2, 0)
        res = list(sorted([c2, c1]))
        assert res[0] == c1
        assert res[1] == c2

    def test_sorting_predicated_sentences(self):
        """
        Lexical items should be sortable for models.
        """
        c1 = Constant(1, 0)
        c2 = Constant(2, 0)
        vocab = Predicates()
        p = vocab.add((0, 0, 1))
        s1 = Predicated(p, [c1])
        s2 = Predicated(p, [c2])
        sentences = [s2, s1]
        res = list(sorted(sentences))
        assert res[0] == s1
        assert res[1] == s2

    def test_copy_preds(self):
        p1, p2, p3 = Predicate.gen(3)
        v1 = Predicates(p1, p2)
        v2 = copy(v1)
        assert v1 != v2
        assert p3 not in v1
        v1.add(p3)
        assert p3 in v1
        assert p3 not in v2
