from ..utils import BaseCase

class Base(BaseCase):
    logic = 'NH'

class TestRules(Base, autorules=True): pass
class TestArguments(Base, autoargs=True): pass

class TestTables(Base, autotables=True):
    tables = dict(
        Assertion = 'FBT',
        Negation = 'TBF',
        Conjunction = 'FFFFTBFBT',
        Disjunction = 'FBTBBTTTT',
        MaterialConditional = 'TTTBBTFBT',
        MaterialBiconditional = 'TBFBTBFBT',
        Conditional = 'TTTFTTFTT',
        Biconditional = 'TFFFTTFTT')

class TestBranchables(Base):
    exp = dict(
        AssertionDesignated=0,
        AssertionNegatedDesignated=0,
        AssertionNegatedUndesignated=0,
        AssertionUndesignated=0,
        BiconditionalDesignated=0,
        BiconditionalNegatedDesignated=0,
        BiconditionalNegatedUndesignated=0,
        BiconditionalUndesignated=0,
        ConditionalDesignated=1,
        ConditionalNegatedDesignated=0,
        ConditionalNegatedUndesignated=1,
        ConditionalUndesignated=0,
        ConjunctionDesignated=0,
        ConjunctionNegatedDesignated=3,
        ConjunctionNegatedUndesignated=1,
        ConjunctionUndesignated=1,
        DesignationClosure=0,
        DisjunctionDesignated=1,
        DisjunctionNegatedDesignated=0,
        DisjunctionNegatedUndesignated=1,
        DisjunctionUndesignated=0,
        DoubleNegationDesignated=0,
        DoubleNegationUndesignated=0,
        GapClosure=0,
        MaterialBiconditionalDesignated=0,
        MaterialBiconditionalNegatedDesignated=0,
        MaterialBiconditionalNegatedUndesignated=0,
        MaterialBiconditionalUndesignated=0,
        MaterialConditionalDesignated=1,
        MaterialConditionalNegatedDesignated=0,
        MaterialConditionalNegatedUndesignated=0,
        MaterialConditionalUndesignated=0)


    def test_known_branchable_values(self):
        for rulecls in self.logic.Rules.all():
            self.assertEqual(rulecls.branching, self.exp[rulecls.name])