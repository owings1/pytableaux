from ..utils import BaseCase

class Base(BaseCase):
    logic = 'MH'

class TestRules(Base, autorules=True): pass
class TestArguments(Base, autoargs=True): pass

class TestTables(Base, autotables=True):
    tables = dict(
        Assertion = 'FNT',
        Negation = 'TNF',
        Conjunction = 'FFFFNNFNT',
        Disjunction = 'FNTNFTTTT',
        MaterialConditional = 'TTTNFTFNT',
        MaterialBiconditional = 'TNFNFNFNT',
        Conditional = 'TTTTTTFFT',
        Biconditional = 'TTFTTFFFT',
    )
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
        ConjunctionNegatedDesignated=1,
        ConjunctionNegatedUndesignated=0,
        ConjunctionUndesignated=1,
        DesignationClosure=0,
        DisjunctionDesignated=1,
        DisjunctionNegatedDesignated=1,
        DisjunctionNegatedUndesignated=3,
        DisjunctionUndesignated=0,
        DoubleNegationDesignated=0,
        DoubleNegationUndesignated=0,
        GlutClosure=0,
        MaterialBiconditionalDesignated=0,
        MaterialBiconditionalNegatedDesignated=0,
        MaterialBiconditionalNegatedUndesignated=0,
        MaterialBiconditionalUndesignated=0,
        MaterialConditionalDesignated=1,
        MaterialConditionalNegatedDesignated=1,
        MaterialConditionalNegatedUndesignated=0,
        MaterialConditionalUndesignated=0)


    def test_known_branchable_values(self):
        for rulecls in self.logic.Rules.all():
            self.assertEqual(rulecls.branching, self.exp[rulecls.name])