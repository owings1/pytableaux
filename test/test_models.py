from models import BaseModel
from lexicals import Operator
from tools.misc import get_logic
from errors import *
from pytest import raises

def test_truth_table_cpl_negation():
    m: BaseModel = get_logic('cpl').Model()
    tbl = m.truth_table(Operator.Negation)
    assert len(tbl.inputs) == 2
    assert len(tbl.outputs) == 2
    assert tbl.inputs[0][0] == 'F'
    assert tbl.outputs[0] == 'T'

def test_truth_tables_cpl():
    m: BaseModel = get_logic('cpl').Model()
    tbl = m.truth_table(Operator.Negation)
    assert tbl.outputs[0] == 'T'

def test_get_logic_cpl_case_insensitive():
    assert get_logic('cpl') == get_logic('CPL')

def test_get_logic_none_bad_argument():
    with raises(TypeError):
        get_logic(None)

class TestModel(object):

    def test_abstract(self):
        with raises(TypeError):
            BaseModel()
        # with raises(NotImplementedError):
        #     model.read_branch(None)
        # with raises(NotImplementedError):
        #     model.truth_function(None, None)
        # with raises(NotImplementedError):
        #     model.value_of_opaque(None)
        # with raises(NotImplementedError):
        #     model.value_of_predicated(None)
        # with raises(NotImplementedError):
        #     s = Atomic(0, 0).negate()
        #     model.value_of_operated(s)
        # with raises(NotImplementedError):
        #     model.value_of_quantified(None)
        # with raises(NotImplementedError):
        #     model.is_countermodel_to(None)
        # with raises(NotImplementedError):
        #     model.value_of_atomic(None)

    # def test_get_data_empty(self):
    #     model = BaseModel()
    #     res = model.get_data()
    #     assert len(res) == 0