# pytableaux - Lukasiewicz 3-valued Logic
#
# Copyright (C) 2014, Doug Owings. All Rights Reserved.
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
        