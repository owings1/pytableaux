import pytest

from logic import *
from notations import standard, polish
from writers import ascii, asciiv, html
import examples

# Sentence Writers

std = standard.Writer()
pol = polish.Writer()

class TestStandard(object):

    def test_atomic(self):
        s = atomic(0, 0)
        res = std.write(s)
        assert res == 'A'

class TestPolish(object):

    def test_atomic(self):
        s = atomic(0, 0)
        res = pol.write(s)
        assert res == 'a'

# Proof writers

asc = ascii.Writer()
htm = html.Writer()
asv = asciiv.Writer()

def example_proof(logic, name, is_build=True):
    arg = examples.argument(name)
    proof = tableau(logic, arg)
    if is_build:
        proof.build()
    return proof

class TestAscii(object):

    def test_write_std_fde_1(self):
        proof = example_proof('fde', 'Addition')
        res = asc.write(proof, standard)
        # TODO: assert something

class TestAsciiv(object):

    def test_write_std_fde_1(self):
        proof = example_proof('fde', 'Addition')
        res = asv.write(proof, standard)
        # TODO: assert something
    
class TestHtml(object):

    def test_write_std_fde_1(self):
        proof = example_proof('fde', 'Addition')
        res = htm.write(proof, standard)
        # TODO: assert something