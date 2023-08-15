from ..utils import BaseCase
from pytableaux.lang import *


class Base(BaseCase):
    logic = 'D'

class TestTabRules(Base, autorules=True): pass

class Test(Base):

    def test_valid_long_serial_max_steps_50(self):
        self.valid_tab('MMMMMa', 'LLLLLa', max_steps = 50)

    def test_valid_serial_inf_1(self):
        self.valid_tab('Serial Inference 1')

    def test_invalid_reflex_inf_1(self):
        self.invalid_tab('Reflexive Inference 1')

    def test_invalid_optimize_nec_rule1_max_steps_50(self):
        self.invalid_tab('NLVxNFx', 'LMSxFx', max_steps = 50)

    def test_invalid_s4_cond_inf_2(self):
        self.invalid_tab('S4 Conditional Inference 2')

    def test_rule_Serial_not_applies_to_branch_empty(self):
        tab = self.tab()
        rule = tab.rules.get('Serial')
        self.assertFalse(rule.target(tab.branch()))

    def test_verify_core_bugfix_branch_should_not_have_w1_with_more_than_one_w2(self):
        tab = self.tab('CaLMa')
        # sanity check
        self.assertEqual(len(tab), 1)
        b = tab[0]
        # use internal properties just to be sure, since the bug was with the .find method
        access = {}
        for node in b:
            if 'world1' in node:
                w1 = node['world1']
                w2 = node['world2']
                if w1 not in access:
                    # use a list to also make sure we don't have redundant nodes
                    access[w1] = list()
                access[w1].append(w2)
        for w1 in access:
            self.assertEqual(len(access[w1]), 1)
        self.assertEqual(len(access), (len(b.worlds) - 1))
        # sanity check
        self.assertGreater(len(b.worlds), 2)
