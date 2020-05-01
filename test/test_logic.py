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
# pytableaux - core logic test cases
import pytest

import logic


def test_parse_standard():
    s = logic.parse('A & B', notation='standard')
    assert s.is_operated
    assert s.operator == 'Conjunction'

def test_parse_polish():
    s = logic.parse('Kab', notation='polish')
    assert s.is_operated
    assert s.operator == 'Conjunction'

def test_argument_no_prems_1_std_untitled():
    a = logic.argument(conclusion='A', notation='standard')
    assert len(a.premises) == 0
    assert a.conclusion.is_atomic()

def test_argument_prems_preparsed_titled():
    premises = [logic.parse('Aab'), logic.parse('Nb')]
    conclusion = logic.parse('a')
    a = logic.argument(conclusion=conclusion, premises=premises, title='TestArgument')
    assert len(a.premises) == 2
    assert a.title == 'TestArgument'

def test_argument_parse_prems_preparsed_conclusion():
    premises = ['Aab', 'Nb']
    conclusion = logic.parse('a')
    a = logic.argument(conclusion=conclusion, premises=premises, notation='polish')
    assert len(a.premises) == 2
    assert a.conclusion == conclusion

def test_argument_parse_prems_missing_notation():
    premises = ['Aab', 'Nb']
    conclusion = logic.parse('a')
    with pytest.raises(logic.argument.MissingNotationError):
        logic.argument(conclusion=conclusion, premises=premises)

def test_argument_parse_conclusion_missing_notation():
    with pytest.raises(logic.argument.MissingNotationError):
        logic.argument(conclusion='a')

def test_argument_repr_untitled():
    a = logic.argument(conclusion='a', notation='polish')
    res = a.__repr__()
    assert 'title' not in res

def test_argument_repr_titled():
    a = logic.argument(conclusion='a', notation='polish', title='TestArg')
    res = a.__repr__()
    assert 'title' in res

def test_truth_table_cpl_negation():
    tbl = logic.truth_table('cpl', 'Negation')
    assert len(tbl['inputs']) == 2
    assert len(tbl['outputs']) == 2
    assert tbl['inputs'][0][0] == 0
    assert tbl['outputs'][0] == 1

def test_truth_tables_cpl():
    tbls = logic.truth_tables('cpl')
    assert tbls['Negation']['outputs'][0] == 1

def test_get_logic_cpl_case_insensitive():
    lgc1 = logic.get_logic('cpl')
    lgc2 = logic.get_logic('CPL')
    assert lgc1 == lgc2

def test_get_logic_none_bad_argument():
    with pytest.raises(logic.BadArgumentError):
        logic.get_logic(None)

class TestVocabulary(object):

    def test_predicate_error_pred_defs_duple(self):
        with pytest.raises(logic.Vocabulary.PredicateError):
            logic.Vocabulary(predicate_defs=[('foo', 4)])

    def test_get_predicate_by_name_sys_identity(self):
        v = logic.Vocabulary()
        p = v.get_predicate('Identity')
        assert p.name == 'Identity'

    def test_get_predicate_by_index_subscript_sys_identity(self):
        v = logic.Vocabulary()
        p = v.get_predicate(-1, subscript=0)
        # TODO: after refactor test for get_predicate(-1, 0)
        assert p.name == 'Identity'

    def test_get_predicate_no_such_predicate_error_bad_name(self):
        v = logic.Vocabulary()
        with pytest.raises(logic.Vocabulary.NoSuchPredicateError):
            v.get_predicate('NonExistentPredicate')

    def test_get_predicate_no_such_predicate_error_bad_custom_index(self):
        v = logic.Vocabulary()
        with pytest.raises(logic.Vocabulary.NoSuchPredicateError):
            v.get_predicate(index=1, subscript=2)

    def test_get_predicate_no_such_predicate_error_bad_sys_index(self):
        v = logic.Vocabulary()
        with pytest.raises(logic.Vocabulary.NoSuchPredicateError):
            v.get_predicate(index=-1, subscript=2)

    def test_get_predicate_no_such_predicate_error_not_enough_info(self):
        v = logic.Vocabulary()
        with pytest.raises(logic.Vocabulary.PredicateError):
            v.get_predicate(index=-1)

    def test_declare_predicate1(self):
        v = logic.Vocabulary()
        p = v.declare_predicate('MyPredicate', 0, 0, 1)
        assert p.name == 'MyPredicate'
        assert p.index == 0
        assert p.subscript == 0
        assert p.arity == 1

    def test_declare_predicate_already_declared_sys(self):
        v = logic.Vocabulary()
        with pytest.raises(logic.Vocabulary.PredicateAlreadyDeclaredError):
            v.declare_predicate('Identity', 0, 0, 2)

    def test_declare_predicate_already_declared_user_name(self):
        v = logic.Vocabulary()
        v.declare_predicate('MyPredicate', 0, 0, 1)
        with pytest.raises(logic.Vocabulary.PredicateAlreadyDeclaredError):
            v.declare_predicate('MyPredicate', 0, 0, 1)

    def test_declare_predicate_already_declared_user_index_subscript(self):
        v = logic.Vocabulary()
        v.declare_predicate('MyPredicate', 0, 0, 1)
        with pytest.raises(logic.Vocabulary.PredicateAlreadyDeclaredError):
            v.declare_predicate('MyPredicate2', 0, 0, 1)

    def test_list_predicates_contains_identity(self):
        v = logic.Vocabulary()
        names = v.list_predicates()
        assert 'Identity' in names

    def test_list_predicates_contains_user_pred(self):
        v = logic.Vocabulary()
        v.declare_predicate('MyPredicate', 0, 0, 1)
        names = v.list_predicates()
        assert 'MyPredicate' in names

    def test_list_user_predicates_contains_user_pred(self):
        v = logic.Vocabulary()
        v.declare_predicate('MyPredicate', 0, 0, 1)
        names = v.list_user_predicates()
        assert 'MyPredicate' in names

    def test_list_user_predicates_not_contains_sys(self):
        v = logic.Vocabulary()
        v.declare_predicate('MyPredicate', 0, 0, 1)
        names = v.list_user_predicates()
        assert 'Identity' not in names

    def test_constant_is_constant_not_variable(self):
        c = logic.constant(0, 0)
        assert c.is_constant()
        assert not c.is_variable()

    def test_sentence_is_sentence(self):
        s = logic.parse('a')
        assert s.is_sentence()

    def test_base_substitute_not_implemented(self):
        s = logic.Vocabulary.Sentence()
        c = logic.constant(0, 0)
        v = logic.variable(0, 0)
        with pytest.raises(logic.NotImplementedError):
            s.substitute(c, v)

    def test_base_constants_not_implemented(self):
        s = logic.Vocabulary.Sentence()
        with pytest.raises(logic.NotImplementedError):
            s.constants()

    def test_base_variables_not_implemented(self):
        s = logic.Vocabulary.Sentence()
        with pytest.raises(logic.NotImplementedError):
            s.variables()

    def test_atomic_substitute(self):
        s = logic.atomic(0, 0)
        c = logic.constant(0, 0)
        v = logic.variable(0, 0)
        res = s.substitute(c, v)
        assert res == s

    def test_atomic_constants_empty(self):
        s = logic.atomic(0, 0)
        res = s.constants()
        assert len(res) == 0

    def test_atomic_variables_empty(self):
        s = logic.atomic(0, 0)
        res = s.variables()
        assert len(res) == 0