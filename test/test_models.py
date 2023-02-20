
from pytableaux.errors import *
from pytableaux.models import BaseModel
from pytableaux.lang.lex import Operator
from pytableaux.logics import registry

from .tutils import BaseCase


class TestModel(BaseCase):

    def test_truth_table_cpl_negation(self):
        m: BaseModel = registry('cpl').Model()
        tbl = m.truth_table(Operator.Negation)
        self.assertEqual(len(tbl.inputs), 2)
        self.assertEqual(len(tbl.outputs), 2)
        self.assertEqual(tbl.inputs[0][0], 'F')
        self.assertEqual(tbl.outputs[0], 'T')

    def test_truth_tables_cpl(self):
        m: BaseModel = registry('cpl').Model()
        tbl = m.truth_table(Operator.Negation)
        self.assertEqual(tbl.outputs[0], 'T')

    def test_get_logic_cpl_case_insensitive(self):
        self.assertEqual(registry('cpl'), registry('CPL'))

    def test_get_logic_none_bad_argument(self):
        with self.assertRaises(TypeError):
            registry(None)

    def test_abstract(self):
        with self.assertRaises(TypeError):
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