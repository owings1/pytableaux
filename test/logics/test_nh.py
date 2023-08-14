from .. import BaseCase

class Base(BaseCase):
    logic = 'NH'

class TestTabRules(Base, autorules=True): pass

class TestArguments(Base):

    def test_valid_hnh_ax1(self):
        self.valid_tab('UaUba')

    def test_valid_hnh_ax2(self):
        self.valid_tab('UUaUbcUUabUac')

    def test_valid_hnh_ax3(self):
        self.valid_tab('UKaba')

    def test_valid_hnh_ax4(self):
        self.valid_tab('UKabb')

    def test_valid_hnh_ax5(self):
        self.valid_tab('UUabUUacUaKbc')

    def test_valid_hnh_ax6(self):
        self.valid_tab('UaAab')

    def test_valid_hnh_ax7(self):
        self.valid_tab('UbAab')

    def test_valid_hnh_ax8(self):
        self.valid_tab('UUacUUbcUAabc')

    def test_valid_hnh_ax9(self):
        self.valid_tab('BNNaa')

    def test_valid_hnh_ax17(self):
        self.valid_tab('NKKaNaNKaNa')

    def test_valid_hnh_ax18(self):
        self.valid_tab('NKUabNUab')

    def test_valid_hnh_ax19(self):
        self.valid_tab('UNKaNaUUbaUNaNb')

    def test_valid_hnh_ax20(self):
        self.valid_tab('BKNaNbNAab')

    def test_valid_hnh_ax21(self):
        self.valid_tab('BANaNbANKabKKaNaKbNb')

    def test_valid_hnh_ax22(self):
        self.valid_tab('UKNKaNaNaUab')

    def test_valid_hnh_ax23(self):
        self.valid_tab('UKaKNKbNbNbNUab')

    def test_invalid_efq(self):
        self.invalid_tab('b', 'KaNa')

    def test_valid_lem(self):
        self.valid_tab('AbNb', 'a')

    def test_invalid_dem(self):
        self.invalid_tab('NAab', 'ANaNb')


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
        MaterialConditionalDesignated=0,
        MaterialConditionalNegatedDesignated=0,
        MaterialConditionalNegatedUndesignated=0,
        MaterialConditionalUndesignated=0)


    def test_known_branchable_values(self):
        for rulecls in self.logic.TabRules.all_rules:
            self.assertEqual(rulecls.branching, self.exp[rulecls.name])