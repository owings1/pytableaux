from models import BaseModel, truth_table, truth_tables
from lexicals import Atomic, Operator
from utils import get_logic
from errors import *
from pytest import raises
def test_truth_table_cpl_negation():
    tbl = truth_table('cpl', Operator.Negation)
    assert len(tbl['inputs']) == 2
    assert len(tbl['outputs']) == 2
    assert tbl['inputs'][0][0] == 'F'
    assert tbl['outputs'][0] == 'T'

def test_truth_tables_cpl():
    tbls = truth_tables('cpl')
    assert tbls[Operator.Negation]['outputs'][0] == 'T'

def test_get_logic_cpl_case_insensitive():
    assert get_logic('cpl') == get_logic('CPL')

def test_get_logic_none_bad_argument():
    with raises(TypeError):
        get_logic(None)

class TestModel(object):

    def test_not_impl_various(self):
        model = BaseModel()
        with raises(NotImplementedError):
            model.read_branch(None)
        with raises(NotImplementedError):
            model.truth_function(None, None)
        with raises(NotImplementedError):
            model.value_of_opaque(None)
        with raises(NotImplementedError):
            model.value_of_predicated(None)
        with raises(NotImplementedError):
            s = Atomic(0, 0).negate()
            model.value_of_operated(s)
        with raises(NotImplementedError):
            model.value_of_quantified(None)
        with raises(NotImplementedError):
            model.is_countermodel_to(None)
        with raises(NotImplementedError):
            model.value_of_atomic(None)

    def test_get_data_empty(self):
        model = BaseModel()
        res = model.get_data()
        assert len(res) == 0