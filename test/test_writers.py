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
# pytableaux - writers test cases
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