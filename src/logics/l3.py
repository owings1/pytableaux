# pytableaux, a multi-logic proof generator.
# Copyright (C) 2014-2017 Doug Owings.
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
# pytableaux - Lukasiewicz 3-valued Logic

"""
**Conditional**:

+------------+----------+-----------+---------+
|  if A, B   |          |           |         |
+============+==========+===========+=========+
|            |  **T**   |   **N**   |  **F**  |
+------------+----------+-----------+---------+
|  **T**     |    T     |     F     |    F    |
+------------+----------+-----------+---------+
|  **N**     |    T     |     T     |    F    |
+------------+----------+-----------+---------+
|  **F**     |    T     |     R     |    R    | 
+------------+----------+-----------+---------+
"""
name = 'L3'
description = 'Lukasiewicz 3-valued Logic'

class TableauxSystem(fde.TableauxSystem):
    """
    L3's Tableaux System inherits directly from FDE's.
    """
    pass

class TableauxRules(object):
    """
    The Tableaux rules for L3 contain the rules for K3, except for different
    rules for the conditional operator.
    """

    class ConditionalDesignated(logic.TableauxSystem.ConditionalNodeRule):

    operator    = 'Conditional'
    designation = True

    def apply_to_node(self, node, branch):
        