# pytableaux, a multi-logic proof generator.
# Copyright (C) 2014-2020 Doug Owings.
# 
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
# 
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Affero General Public License for more details.
# 
# You should have received a copy of the GNU Affero General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
# ------------------
#
# pytableaux - logics test cases
import pytest

from logic import *
import examples

def validities(logic):
    return get_logic(logic).example_validities()

def invalidities(logic):
    return get_logic(logic).example_invalidities()

def example_proof(logic, name, is_build=True):
    arg = examples.argument(name)
    proof = tableau(logic, arg)
    if is_build:
        proof.build()
    return proof


class TestFDE(object):

    def test_examples(self):
        valids = validities('fde')
        invalids = invalidities('fde')
        assert 'Addition' in valids
        assert 'Law of Excluded Middle' in invalids

    def test_valid_addition(self):
        proof = example_proof('fde', 'Addition')
        assert proof.valid

    def test_invalid_lem(self):
        proof = example_proof('fde', 'Law of Excluded Middle')
        assert not proof.valid

class TestK3(object):

    def test_examples(self):
        valids = validities('k3')
        invalids = invalidities('k3')
        assert 'Biconditional Elimination 1' in valids
        assert 'Law of Excluded Middle' in invalids

    def test_valid_bicond_elim_1(self):
        proof = example_proof('k3', 'Biconditional Elimination 1')
        assert proof.valid

    def test_invalid_lem(self):
        proof = example_proof('k3', 'Law of Excluded Middle')
        assert not proof.valid

class TestK3W(object):

    def test_examples(self):
        valids = validities('k3w')
        invalids = invalidities('k3w')
        assert 'Conditional Contraction' in valids
        assert 'Addition' in invalids

    def test_valid_cond_contraction(self):
        proof = example_proof('k3w', 'Conditional Contraction')
        assert proof.valid

    def test_invalid_addition(self):
        proof = example_proof('k3w', 'Addition')
        assert not proof.valid

class TestB3E(object):

    def test_examples(self):
        valids = validities('b3e')
        invalids = invalidities('b3e')
        assert 'Conditional Contraction' in valids
        assert 'Triviality 1' in invalids

    def test_valid_cond_contraction(self):
        proof = example_proof('b3e', 'Conditional Contraction')
        assert proof.valid

    def test_invalid_lem(self):
        proof = example_proof('b3e', 'Law of Excluded Middle')
        assert not proof.valid

class TestLP(object):

    def test_examples(self):
        valids = validities('lp')
        invalids = invalidities('lp')
        assert 'Biconditional Identity' in valids
        assert 'Law of Non-contradiction' in invalids

    def test_valid_material_ident(self):
        proof = example_proof('lp', 'Material Identity')
        assert proof.valid

    def test_invalid_lnc(self):
        proof = example_proof('lp', 'Law of Non-contradiction')
        assert not proof.valid

class TestGO(object):

    def test_examples(self):
        valids = validities('go')
        invalids = invalidities('go')
        assert 'DeMorgan 3' in valids
        assert 'DeMorgan 1' in invalids

    def test_valid_demorgan_3(self):
        proof = example_proof('go', 'DeMorgan 3')
        assert proof.valid

    def test_invalid_demorgan_1(self):
        proof = example_proof('go', 'DeMorgan 1')
        assert not proof.valid

class TestCPL(object):

    def test_examples(self):
        valids = validities('cpl')
        invalids = invalidities('cpl')
        assert 'Simplification' in valids
        assert 'Syllogism' in invalids

    def test_valid_simplification(self):
        proof = example_proof('cpl', 'Simplification')
        assert proof.valid

    def test_invalid_syllogism(self):
        proof = example_proof('cpl', 'Syllogism')
        assert not proof.valid

class TestCFOL(object):

    def test_examples(self):
        valids = validities('cfol')
        invalids = invalidities('cfol')
        assert 'Syllogism' in valids
        assert 'Possibility Addition' in invalids

    def test_valid_syllogism(self):
        proof = example_proof('cfol', 'Syllogism')
        assert proof.valid

    def test_invalid_possibility_addition(self):
        proof = example_proof('cfol', 'Possibility Addition')
        assert not proof.valid

class TestK(object):

    def test_examples(self):
        valids = validities('k')
        invalids = invalidities('k')
        assert 'Necessity Distribution' in valids
        assert 'Necessity Elimination' in invalids

    def test_valid_nec_dist(self):
        proof = example_proof('k', 'Necessity Distribution')
        assert proof.valid

    def test_invalid_nec_elim(self):
        proof = example_proof('k', 'Necessity Elimination')
        assert not proof.valid

class TestD(object):

    def test_examples(self):
        valids = validities('d')
        invalids = invalidities('d')
        assert 'Serial Inference 1' in valids
        assert 'Reflexive Inference 1' in invalids

    def test_valid_serial_inf_1(self):
        proof = example_proof('d', 'Serial Inference 1')
        assert proof.valid

    def test_invalid_reflex_inf_1(self):
        proof = example_proof('d', 'Reflexive Inference 1')
        assert not proof.valid

class TestT(object):

    def test_examples(self):
        valids = validities('t')
        invalids = invalidities('t')
        assert 'NP Collapse 1' in valids
        assert 'S4 Inference 1' in invalids

    def test_valid_np_collapse_1(self):
        proof = example_proof('t', 'NP Collapse 1')
        assert proof.valid

    def test_invalid_s4_inf_1(self):
        proof = example_proof('t', 'S4 Inference 1')
        assert not proof.valid

class TestS4(object):

    def test_examples(self):
        valids = validities('s4')
        invalids = invalidities('s4')
        assert 'S4 Inference 1' in valids
        assert 'S5 Conditional Inference 1' in invalids

    def test_valid_s4_inf_1(self):
        proof = example_proof('s4', 'S4 Inference 1')
        assert proof.valid

    def test_valid_np_collapse_1(self):
        proof = example_proof('s4', 'NP Collapse 1')
        assert proof.valid

    def test_invalid_s5_cond_inf_1(self):
        proof = example_proof('s4', 'S5 Conditional Inference 1')
        assert not proof.valid

class TestL3(object):

    def test_examples(self):
        valids = validities('l3')
        invalids = invalidities('l3')
        assert 'Conditional Identity' in valids
        assert 'Material Identity' in invalids

    def test_valid_cond_identity(self):
        proof = example_proof('l3', 'Conditional Identity')
        assert proof.valid

    def test_invalid_material_identify(self):
        proof = example_proof('l3', 'Material Identity')
        assert not proof.valid