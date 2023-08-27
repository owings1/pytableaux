
from pytableaux.errors import *
from pytableaux.lang import Operator
from pytableaux.logics import registry
from pytableaux.models import BaseModel

from .utils import BaseCase as Base


class TestModel(Base):

    logic = 'CPL'

    def test_abstract(self):
        with self.assertRaises(TypeError):
            BaseModel()
