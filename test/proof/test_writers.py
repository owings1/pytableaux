# -*- coding: utf-8 -*-
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
# pytableaux.proof.writers tests
from __future__ import annotations

from pytableaux import examples
from pytableaux.errors import *
from pytableaux.lang import *
from pytableaux.proof import *

from ..utils import BaseCase

# Proof writers

class TestTabWriter(BaseCase):

    def test_construct_kwargs(self):
        pw = TabWriter(format='html', notation='standard')
        self.assertEqual(pw.format, 'html')
        self.assertEqual(pw.lw.notation, Notation.standard)

class TestHtml(BaseCase):

    def test_write_no_arg(self):
        tab = Tableau('FDE').build()
        pw = TabWriter('html', 'standard')
        res = pw(tab)

    def test_write_std_fde_1(self):
        arg = examples.argument('Addition')
        pw = TabWriter('html', 'standard')
        tab = Tableau('fde', arg).build()
        res = pw(tab)

    
class TestLatex(BaseCase):

    def test_write_no_arg(self):
        tab = Tableau('FDE')
        pw = TabWriter('latex', 'standard')
        tab.build()
        res = pw(tab)

    def test_write_std_fde_1(self):
        arg = examples.argument('Addition')
        pw = TabWriter('latex', 'standard')
        tab = Tableau('fde', arg).build()
        res = pw(tab)