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
# pytableaux - docutil test cases
import docutil

helper = docutil.Helper()

def test_html_truth_table_negation_cpl():
    res = helper.html_truth_table('cpl', 'Negation')
    assert len(res) > 0

def test_lines_logic_truth_tables():
    res = helper.lines_logic_truth_tables('cpl')
    assert len(res) > 0

# def test_doc_replace_lexicals():
#     sstr = 'P{A > B}'
#     res = helper.doc_replace_lexicals(sstr)
#     assert len(res) > 0

def test_rule_example_html_1():
    res = helper.html_rule_example('GlutClosure', 'k3')
    assert len(res) > 0

def test_lines_trunk_example():
    res = helper.lines_trunk_example('cpl')
    assert len(res) > 0
