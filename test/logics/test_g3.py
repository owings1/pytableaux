from ..utils import BaseCase

class Base(BaseCase):
    logic = 'G3'

class TestTabRules(Base, autorules=True): pass

class TestArguments(Base):

    def test_invalid_demorgan_8_model(self):
        tab = self.invalid_tab('DeMorgan 8')
        model = tab.open[0].model
        assert model.is_countermodel_to(tab.argument)

    def test_valid_demorgan_6(self):
        self.valid_tab('DeMorgan 6')

    def test_invalid_lem(self):
        self.invalid_tab('Law of Excluded Middle')

    def test_invalid_not_not_a_arrow_a(self):
        # Rescher p.45
        self.invalid_tab('UNNaa')

    def test_invalid_not_a_arrow_not_b_arrow_b_arrow_a(self):
        # Rescher p.45
        self.invalid_tab('UUNaNbUba')

    def test_valid_a_arrow_b_or_b_arrow_a(self):
        # Rescher p.45
        self.valid_tab('AUabUba')

    def test_valid_not_not_a_arrow_a_arrow_a_or_not_a(self):
        # Rescher p.45
        self.valid_tab('UUNNaaAaNa')

    def test_valid_a_dblarrow_a(self):
        self.valid_tab('Baa')

    def test_valid_a_dblarrow_b_thus_a_arrow_b_and_b_arrow_a(self):
        self.valid_tab('KUabUba', 'Bab')

    def test_valid_a_arrow_b_and_b_arrow_a_thus_a_dblarrow_b(self):
        self.valid_tab('Bab', 'KUabUba')

    def test_valid_not_a_arrow_b_or_not_b_arrow_a_thus_not_a_dblarrow_b(self):
        self.valid_tab('NBab', 'ANUabNUba')

    def test_valid_not_a_dblarrow_b_thus_not_a_arrow_b_or_not_b_arrow_a(self):
        self.valid_tab('ANUabNUba', 'NBab')
