from .. import BaseCase

class Base(BaseCase):
    logic = 'MH'

class TestTabRules(Base, autorules=True): pass

class TestMH(Base):

    def test_valid_hmh_ax1(self):
        self.valid_tab('UaUba')

    def test_valid_hmh_ax2(self):
        self.valid_tab('UUaUbcUUabUac')

    def test_valid_hmh_ax3(self):
        self.valid_tab('UKaba')

    def test_valid_hmh_ax4(self):
        self.valid_tab('UKabb')

    def test_valid_hmh_ax5(self):
        self.valid_tab('UUabUUacUaKbc')

    def test_valid_hmh_ax6(self):
        self.valid_tab('UaAab')

    def test_valid_hmh_ax7(self):
        self.valid_tab('UbAab')

    def test_valid_hmh_ax8(self):
        self.valid_tab('UUacUUbcUAabc')

    def test_valid_hmh_ax9(self):
        self.valid_tab('BNNaa')

    def test_valid_hmh_ax10(self):
        self.valid_tab('AAaNaNAaNa')

    def test_valid_hmh_ax11(self):
        self.valid_tab('AUabNUab')

    def test_valid_hmh_ax12(self):
        self.valid_tab('UAaNaUUabUNbNa')

    def test_valid_hmh_ax13(self):
        self.valid_tab('BNKabANaNb')

    def test_valid_hmh_ax14(self):
        self.valid_tab('BNAabAKNaNbKNAaNaNAbNb')

    def test_valid_hmh_ax15(self):
        self.valid_tab('UANaNAaNaUab')

    def test_valid_hmh_ax16(self):
        self.valid_tab('UKaANbNAbNbNUab')

    def test_valid_mp(self):
        self.valid_tab('Conditional Modus Ponens')

    def test_valid_inden(self):
        self.valid_tab('Uaa')

    def test_valid_ifn(self):
        self.valid_tab('BNAaNaNANaNNa')

    def test_valid_adj(self):
        self.valid_tab('Kab', 'a', 'b')

    def test_invalid_p(self):
        self.invalid_tab('UNbNa', 'NAaNa', 'Uab')