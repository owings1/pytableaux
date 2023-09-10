# pytableaux, a multi-logic proof generator.
# Copyright (C) 2014-2023 Doug Owings.
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
# pytableaux.logics.go tests
from __future__ import annotations

from pytableaux.lang import *
from pytableaux.proof import *

from ..utils import BaseCase


class Base(BaseCase):
    logic = 'GO'

class TestArguments(Base, autoargs=True): pass

class TestTables(Base, autotables=True):
    tables = dict(
        Assertion = 'FFT',
        Negation = 'TNF',
        Disjunction = 'FFTFFTTTT',
        Conjunction = 'FFFFFFFFT',
        MaterialConditional = 'TTTFFTFFT',
        MaterialBiconditional = 'TFFFFFFFT',
        Conditional = 'TTTFTTFFT',
        Biconditional = 'TFFFTFFFT')

class TestRules(Base, autorules=True):

    def test_MaterialConditionalNegatedDesignated_step(self):
        sdn = self.sdnode
        tab = self.tab()
        b = tab.branch()
        b += sdn('NCab', True)
        tab.step()
        self.assertTrue(b.has(sdn('Na',  False)))
        self.assertTrue(b.has(sdn('b',  False)))

    def test_MaterialBionditionalNegatedDesignated_step(self):
        sdn = self.sdnode
        tab = self.tab()
        b = tab.branch()
        b += sdn('NEab', True)
        tab.step()
        b1, b2 = tab
        self.assertTrue(b1.has(sdn('Na', False)))
        self.assertTrue(b1.has(sdn('b', False)))
        self.assertTrue(b2.has(sdn('a', False)))
        self.assertTrue(b2.has(sdn('Nb', False)))

    def test_ConditionalDesignated_step(self):
        sdn = self.sdnode
        tab = self.tab()
        b = tab.branch()
        b += sdn('Uab', True)
        tab.step()
        b1, b2 = tab
        self.assertTrue(b1.has(sdn('ANab', True)))
        self.assertTrue(b2.has(sdn('a', False)))
        self.assertTrue(b2.has(sdn('b', False)))
        self.assertTrue(b2.has(sdn('Na', False)))
        self.assertTrue(b2.has(sdn('Nb', False)))

    def test_ConditionalNegatedDesignated_step(self):
        sdn = self.sdnode
        tab = self.tab()
        b = tab.branch()
        b += sdn('NUab', True)
        tab.step()
        b1, b2 = tab
        self.assertTrue(b1.has(sdn('a', True)))
        self.assertTrue(b1.has(sdn('b', False)))
        self.assertTrue(b2.has(sdn('Na', False)))
        self.assertTrue(b2.has(sdn('Nb', True)))

    def test_BiconditionalDesignated_step(self):
        sdn = self.sdnode
        tab = self.tab()
        b = tab.branch()
        b += sdn('Bab', True)
        tab.step()
        self.assertTrue(b.has(sdn('Uab', True)))
        self.assertTrue(b.has(sdn('Uba', True)))

    def test_BiconditionalNegatedDesignated_step(self):
        sdn = self.sdnode
        tab = self.tab()
        b = tab.branch()
        b += sdn('NBab', True)
        tab.step()
        b1, b2 = tab
        self.assertTrue(b1.has(sdn('NUab', True)))
        self.assertTrue(b2.has(sdn('NUba', True)))

    def test_AssertionUndesignated_step(self):
        sdn = self.sdnode
        tab = self.tab()
        b = tab.branch()
        b += sdn('Ta', False)
        tab.step()
        self.assertTrue(b.has(sdn('a', False)))

    def test_AssertionNegatedDesignated_step(self):
        sdn = self.sdnode
        tab = self.tab()
        b = tab.branch()
        b += sdn('NTa', True)
        tab.step()
        self.assertTrue(b.has(sdn('a', False)))

    def test_AssertionNegatedUndesignated_step(self):
        sdn = self.sdnode
        tab = self.tab()
        b = tab.branch()
        b += sdn('NTa', False)
        tab.step()
        self.assertTrue(b.has(sdn('a', True)))

    def test_branching_complexity_inherits_branchables(self):
        sdn = self.sdnode
        tab = self.tab()
        b = tab.branch()
        b += sdn('Kab', False)
        node = b[0]
        self.assertEqual(self.logic.System.branching_complexity(node, tab.rules), 0)