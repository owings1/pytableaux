# pytableaux, a multi-logic proof generator.
# Copyright (C) 2014-2021 Doug Owings.
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
# pytableaux - examples test cases
import pytest

import examples

def test_predicated():
    s = examples.predicated()
    assert s.is_predicated()

def test_identity():
    s = examples.identity()
    assert s.is_predicated()
    assert s.predicate.name == 'Identity'

def test_self_identity():
    s = examples.self_identity()
    assert s.predicate.name == 'Identity'
    assert s.parameters[0] == s.parameters[1]

def test_quantified_universal():
    s = examples.quantified('Universal')
    assert s.is_quantified()
    assert s.quantifier == 'Universal'

def test_quantified_existential():
    s = examples.quantified('Existential')
    assert s.is_quantified()
    assert s.quantifier == 'Existential'

def test_operated_conjunction():
    s = examples.operated('Conjunction')
    assert s.is_operated()
    assert s.operator == 'Conjunction'