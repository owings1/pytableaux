from ..utils import BaseCase

class Base(BaseCase):
    logic = 'S4'

class TestRules(Base, autorules=True): pass

class TestArguments(Base, autoargs=True):

    def test_valid_s4_complex_possibility_with_max_steps(self):
        self.valid_tab('MNb:LCaMMMNb:Ma', max_steps = 200)

    def test_valid_optimize_nec_rule1(self):
        self.valid_tab('NLVxNFx:LMSxFx', build_timeout = 1000)

    def test_invalid_problematic_1_with_timeout(self):
        self.invalid_tab('b:LMa', build_timeout = 2000)

    def test_invalid_nested_diamond_within_box1(self):
        self.invalid_tab('KMNbc:LCaMNb:Ma')
        # model.add_access(0, 1)
        # model.add_access(1, 2)
        # model.finish()
        # assert 2 in model.visibles(0)

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
        self.invalid_tab('b:LVxSyUFxLMGy', max_steps = 200)

class TestTables(Base, autotables=True):
    tables = dict(
        Assertion = 'FT',
        Negation = 'TF',
        Conjunction = 'FFFT',
        Disjunction = 'FTTT',
        MaterialConditional = 'TTFT',
        MaterialBiconditional = 'TFFT',
        Conditional = 'TTFT',
        Biconditional = 'TFFT')


class TestModels(Base):

    def test_model_finish_transitity_visibles(self):
        with self.m() as m:
            m.R.add((0,1))
            m.R.add((1,2))
        self.assertIn(2, m.R[0])