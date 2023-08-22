from collections import defaultdict

from pytableaux.lang import *

from ..utils import BaseCase


class Base(BaseCase):
    logic = 'D'

class TestRules(Base, autorules=True):

    def test_rule_Serial_not_applies_to_branch_empty(self):
        tab = self.tab()
        rule = tab.rules.get('Serial')
        self.assertFalse(rule.target(tab.branch()))

class TestArguments(Base, autoargs=True):

    def test_valid_long_serial_max_steps_50(self):
        self.valid_tab('MMMMMa', 'LLLLLa', max_steps = 50)

    def test_invalid_optimize_nec_rule1_max_steps_50(self):
        self.invalid_tab('NLVxNFx', 'LMSxFx', max_steps = 50)

    def test_verify_core_bugfix_branch_should_not_have_w1_with_more_than_one_w2(self):
        tab = self.tab('CaLMa')
        # sanity check
        self.assertEqual(len(tab), 1)
        b = tab[0]
        # use internal properties just to be sure, since the bug was with the .find method
        # use a list to also make sure we don't have redundant nodes
        access = defaultdict(list)
        for node in b:
            if 'world1' in node:
                w1, w2 = node.worlds()
                access[w1].append(w2)
        for w1 in access:
            self.assertEqual(len(access[w1]), 1)
        self.assertEqual(len(access), (len(b.worlds) - 1))
        # sanity check
        self.assertGreater(len(b.worlds), 2)

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