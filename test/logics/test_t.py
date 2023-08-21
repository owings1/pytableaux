from ..utils import BaseCase

class Base(BaseCase):
    logic = 'T'

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

    def test_valid_optimize_nec_rule1(self):
        self.valid_tab('NLVxNFx', 'LMSxFx', build_timeout = 1000)

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
