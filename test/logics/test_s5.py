from ..utils import BaseCase

class Base(BaseCase):
    logic = 'S5'

class TestRules(Base, autorules=True, bare=True):
    def test_benchmark_rule_order_max_steps_nested_qt_modal1(self):

        # Rule ordering benchmark result:
        
        #           [# non-branching rules]
        #                 [S4:Transitive]
        #           [Necessity, Possibility]
        #                 [T:Reflexive]
        #           [# branching rules]
        #         - [Existential, Universal]
        #                 [S5:Symmetric]
        #             [D:Serial],
        #       S5: 8 branches, 142 steps
        #       S4: 8 branches, 132 steps
        #        T: 8 branches, 91 steps
        #        D: 8 branches, 57 steps
        # 200 might be agressive
        self.invalid_tab('b', 'LVxSyUFxLMGy', max_steps = 200)

class TestArguments(Base, autoargs=True):

    def test_valid_s4_complex_possibility_with_max_steps(self):
        self.valid_tab('MNb', ('LCaMMMNb', 'Ma'), max_steps = 200)

    def test_valid_optimize_nec_rule1(self):
        self.valid_tab('NLVxNFx', 'LMSxFx', build_timeout = 1000)

    def test_valid_intermediate_mix_modal_quantifiers1(self):
        # For this we needed to put Universal and Existential rules
        # in the same group, and toward the end.
        self.valid_tab('MSxGx', ('VxLSyUFxMGy', 'Fm'), max_steps = 100)

    def test_invalid_nested_diamond_within_box1(self):
        self.invalid_tab('KMNbc', ('LCaMNb', 'Ma'))

class TestTables(Base, autotables=True):
    tables = dict(
        Assertion = 'FT',
        Negation = 'TF',
        Conjunction = 'FFFT',
        Disjunction = 'FTTT',
        MaterialConditional = 'TTFT',
        MaterialBiconditional = 'TFFT',
        Conditional = 'TTFT',
        Biconditional = 'TFFT',
    )

class TestModels(Base):

    def test_model_finish_symmetry_visibles(self):
        model = self.m()
        model.R.add((0,1))
        model.finish()
        self.assertIn(0, model.R[1])
        # model.add_access(0, 1)
        # model.finish()
        # assert 0 in model.visibles(1)

