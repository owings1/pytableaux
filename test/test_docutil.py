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
# pytableaux - docutil test cases
import pytest

import docutil
import examples

def test_get_truth_table_html_negation_cpl():
    res = docutil.get_truth_table_html('cpl', 'Negation')
    assert len(res) > 0

def test_get_truth_tables_for_logic():
    res = docutil.get_truth_tables_for_logic('cpl')
    assert len(res) > 0

def test_get_replace_sentence_expressions_result_1():
    sstr = 'P{A > B}'
    res = docutil.get_replace_sentence_expressions_result(sstr)
    assert res['is_found']
    assert sstr not in res['text']

def test_get_rule_example_html_1():
    res = docutil.get_rule_example_html('cpl', 'ContradictionClosure')
    assert len(res) > 0

def test_get_build_trunk_example_html_1():
    res = docutil.get_build_trunk_example_html('cpl', examples.argument('Addition'))
    assert len(res) > 0

def test_get_argument_example_html_1():
    res = docutil.get_argument_example_html(examples.argument('Addition'))
    assert len(res) > 0