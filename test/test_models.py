
from pytableaux.errors import *
from pytableaux.lang import Operator
from pytableaux.logics import registry
from pytableaux.models import BaseModel

from .utils import BaseCase as Base


class TestModel(Base):

    logic = 'CPL'

    def test_truth_table_cpl_negation(self):
        m = self.m()
        tbl = m.truth_table(Operator.Negation)
        self.assertEqual(len(tbl.inputs), 2)
        self.assertEqual(len(tbl.outputs), 2)
        self.assertEqual(tbl.inputs[0][0], 'F')
        self.assertEqual(tbl.outputs[0], 'T')

    def test_truth_tables_cpl(self):
        m = self.m()
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
