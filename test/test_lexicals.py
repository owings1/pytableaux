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
from lexicals import Vocabulary as Vocab, Variable, Constant, Parameter, Predicate, \
    Atomic, Predicated, Quantified, Operated, Sentence, get_system_predicate
from parsers import parse
from errors import *

from pytest import raises

class TestParameter(object):
    def test_cannot_construct(self):
        with raises(TypeError):
            Parameter(0, 0)

class TestPredicate(object):
    def test_sys_name_not_allowed(self):
        with raises(ValueError):
            Predicate.create(1, 0, 2, 'Identity')

    def test_neg_idx_not_allowed(self):
        with raises(ValueError):
            Predicate.create(-1, 4, 2)

class TestVocabulary(object):

    def test_predicate_error_pred_defs_duple(self):
        with raises(TypeError):
            Vocab([('foo', 4)])

    def test_get_predicate_by_name_sys_identity(self):
        assert Vocab().get('Identity').name == 'Identity'

    def test_get_predicate_by_index_subscript_sys_identity(self):
        assert Vocab().get((-1, 0)).name == 'Identity'

    def test_get_predicate_notfound_bad_name(self):
        with raises(NotFoundError):
            Vocab().get('NonExistentPredicate')

    def test_get_predicate_notfound_bad_custom_index(self):
        with raises(NotFoundError):
            Vocab().get((1, 2))

    def test_get_predicate_no_such_predicate_error_bad_sys_index(self):
        with raises(NotFoundError):
            Vocab().get((-1, 2))

    def test_get_pred_coords_tuple(self):
        v = Vocab()
        v.declare(1, 1, 1)

    def test_pred_no_name(self):
        v = Vocab()
        p = v.declare(1, 0, 1)
        p1 = v.get((1, 0))
        assert p == p1
        p = v.declare(1, 1, 2)
        p2 = v.get((1, 1))
        assert p == p2

    def test_declare1(self):
        p = Vocab().declare(0, 0, 1)
        assert p.index == 0
        assert p.subscript == 0
        assert p.arity == 1

    def test_vocab_copy_get_predicate(self):
        v = Vocab()
        spec = (0, 0, 1)
        predicate = v.declare(spec)
        v2 = v.copy()
        assert v2.get(spec) == predicate

    def test_add_predicate_raises_non_predicate(self):
        with raises(TypeError):
            Vocab().add('foo')

    def test_add_predicate_raises_sys_predicate(self):
        pred = get_system_predicate('Identity')
        with raises(TypeError):
            Vocab().add(pred)

    def test_declare_already_declared_sys(self):
        with raises(ValueError):
            Vocab().declare(0, 0, 2, 'Identity')

    def test_declare_already_declared_user(self):
        v = Vocab()
        v.declare(0, 0, 1)
        with raises(ValueError):
            v.declare(0, 0, 1)

    def test_declare_already_declared_diff_name(self):
        v = Vocab()
        v.declare(0, 0, 1, 'MyPredicate')
        with raises(ValueError):
            v.declare(0, 0, 1, 'MyPredicate2')

    def test_declare_index_too_large(self):
        with raises(ValueError):
            Vocab().declare(Predicate.MAXI + 1, 0, 1)

    def test_declare_arity_non_int(self):
        with raises(TypeError):
            Vocab().declare(0, 0, None)

    def test_declare_arity_0_error(self):
        with raises(ValueError):
            Vocab().declare(0, 0, 0)

    def test_new_predicate_subscript_non_int(self):
        with raises(TypeError):
            Predicate.create(0, None, 1)

    def test_new_predicate_subscript_less_than_0_error(self):
        with raises(ValueError):
            Predicate.create(0, -1, 1)

    def test_predicate_is_system_predicate_true(self):
        assert get_system_predicate('Identity').is_system

    def test_predicate_eq_true(self):
        assert get_system_predicate('Identity') == get_system_predicate('Identity')

    def test_predicate_system_less_than_user(self):
        pred = Vocab().declare(0, 0, 1)
        assert get_system_predicate('Identity') < pred

    def test_predicate_system_less_than_or_equal_to_user(self):
        pred = Vocab().declare(0, 0, 1)
        assert get_system_predicate('Identity') <= pred

    def test_predicate_user_greater_than_system(self):
        pred = Vocab().declare(0, 0, 1)
        assert pred > get_system_predicate('Identity')

    def test_predicate_user_greater_than_or_equal_to_system(self):
        pred = Vocab().declare(0, 0, 1)
        assert pred >= get_system_predicate('Identity')

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
        vocab = Vocab()
        vocab.declare(0, 0, 2)
        s1 = parse('SxMVyFxy', vocab=vocab)
        m = Constant(0, 0)
        s2 = s1.sentence.substitute(m, s1.variable)
        s3 = parse('MVyFmy', vocab=vocab)
        assert s2 == s3

    def test_with_pred_defs_single_pred_with_length4(self):
        v = Vocab((0, 0, 1))
        assert v.has((0, 0))
        assert v.has((0, 0, 1))

    def test_with_pred_defs_single_def_list(self):
        vocab = Vocab([(0, 0, 2)])
        predicate = vocab.get((0, 0))
        assert predicate.arity == 2

    def test_with_pred_defs_single_def_tuple(self):
        vocab = Vocab(((0, 0, 3),))
        predicate = vocab.get((0, 0))
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
        vocab = Vocab()
        p = vocab.declare(0, 0, 1)
        s1 = Predicated(p, [c1])
        s2 = Predicated(p, [c2])
        sentences = [s2, s1]
        res = list(sorted(sentences))
        assert res[0] == s1
        assert res[1] == s2


