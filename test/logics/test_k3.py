from pytableaux.errors import *
from pytableaux.lang import *
from pytableaux.proof import *

from ..utils import BaseCase


class Base(BaseCase):
    logic = 'K3'

class TestRules(Base, autorules=True): pass

class TestArguments(Base, autoargs=True): pass

class TestTables(Base, autotables=True):
    tables = dict(
        Assertion = 'FNT',
        Negation = 'TNF',
        Conjunction = 'FFFFNNFNT',
        Disjunction = 'FNTNNTTTT',
        MaterialConditional = 'TTTNNTFNT',
        MaterialBiconditional = 'TNFNNNFNT',
        Conditional = 'TTTNNTFNT',
        Biconditional = 'TNFNNNFNT')
