from ..utils import BaseCase

class Base(BaseCase):
    logic = 'T'

class TestRules(Base, autorules=True, bare=True): pass

class TestT(Base):

    def test_valid_np_collapse_1(self):
        self.valid_tab('NP Collapse 1')

    def test_invalid_s4_material_inf_1(self):
        self.invalid_tab('S4 Material Inference 1')

    def test_valid_optimize_nec_rule1(self):
        self.valid_tab('NLVxNFx', 'LMSxFx', build_timeout = 1000)

    def test_invalid_s4_cond_inf_2(self):
        self.invalid_tab('S4 Conditional Inference 2')

    def test_rule_Reflexive_eg(self):
        rule, tab = self.rule_eg('Reflexive')
        b, = tab
        self.assertTrue(b.has({'world1': 0, 'world2': 0}))

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