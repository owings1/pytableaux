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
# pytableaux - Classical Predicate Logic

"""
Classical Predicate Logic (CPL) is the standard bivalent logic (True, False).

Semantics
---------

Two primitive operators, negation and disjunction, are defined via truth tables.

**Negation**:

+------------+------------+
| A          | not A      |
+============+============+
|  T         |  F         |
+------------+------------+
|  F         |  T         |
+------------+------------+

**Disjunction**:

+-----------+----------+---------+
|  A or B   |          |         |
+===========+==========+=========+
|           |  **T**   |  **F**  |
+-----------+----------+---------+
|  **T**    |    T     |    T    |
+-----------+----------+---------+
|  **F**    |    T     |    F    | 
+-----------+----------+---------+

Other operators are defined via semantic equivalencies in the usual way:

- **Conjunction**: ``A and B := not (not-A or not-B)``

- **Material Conditional**: ``if A then B := not-A or B``

- **Material Biconditional**: ``A if and only if B := (if A then B) and (if B then A)``

The truth tables for defined connectives are as follows:

**Conjunction**:

+-----------+----------+---------+
|  A and B  |          |         |
+===========+==========+=========+
|           |  **T**   |  **F**  |
+-----------+----------+---------+
|  **T**    |    T     |    F    |
+-----------+----------+---------+
|  **F**    |    F     |    F    | 
+-----------+----------+---------+

**Material Conditional**:

+-----------+----------+---------+
|  if A, B  |          |         |
+===========+==========+=========+
|           |  **T**   |  **F**  |
+-----------+----------+---------+
|  **T**    |    T     |    F    |
+-----------+----------+---------+
|  **F**    |    T     |    T    | 
+-----------+----------+---------+

**Material Biconditional**:

+-----------+----------+---------+
|  A iff B  |          |         |
+===========+==========+=========+
|           |  **T**   |  **F**  |
+-----------+----------+---------+
|  **T**    |    T     |    F    |
+-----------+----------+---------+
|  **F**    |    F     |    T    | 
+-----------+----------+---------+

The **Conditional** and **Biconditional** operators are equivalent to their material counterparts.

**Predicate Sentences** like *a is F* are handled via a predicate's *extension*:

- *a is F* iff the object denoted by the constant *a* is in the extension of the predicate *F*.

*C* is a **Logical Consequence** of *A* iff all cases where the value of *A* is **T**
are cases where *C* also has the value **T**.
"""

import k

name = 'CPL'
description = 'Classical Predicate Logic'

def example_validities():
    # Everything valid in K3 or LP is valid in CPL, except quantifier validities
    args = set([
        'Addition'                        ,
        'Biconditional Elimination 1'     ,
        'Biconditional Elimination 2'     ,
        'Biconditional Identity'          ,
        'Conditional Contraction'         ,
        'Conditional Identity'            ,
        'Conditional Modus Ponens'        ,
        'Conditional Modus Tollens'       ,
        'Conditional Pseudo Contraction'  ,
        'DeMorgan 1'                      ,
        'DeMorgan 2'                      ,
        'DeMorgan 3'                      ,
        'DeMorgan 4'                      ,
        'Disjunctive Syllogism'           ,
        'Law of Excluded Middle'          ,
        'Law of Non-contradiction'        ,
        'Material Biconditional Identity' ,
        'Material Contraction'            ,
        'Material Identity'               ,
        'Material Modus Ponens'           ,
        'Material Modus Tollens'          ,
        'Material Pseudo Contraction'     ,
        'Modal Platitude 1'               ,
        'Modal Platitude 2'               ,
        'Modal Platitude 3'               ,
        'Simplification'                  ,
    ])
    return args

def example_invalidities():
    import cfol
    args = cfol.example_invalidities()
    args.update([
        'Existential Syllogism'         ,
        'Syllogism'                     ,
        'Universal Predicate Syllogism' ,
    ])
    return args

import logic, examples
from logic import negate

class TableauxSystem(logic.TableauxSystem):
    """
    A branch can be thought of as representing a case where each node's sentence
    is true.
    """

    @staticmethod
    def build_trunk(tableau, argument):
        """
        To build the trunk for an argument, add a node for each premise, and
        a node with the negation of the conclusion.        
        """
        branch = tableau.branch()
        for premise in argument.premises:
            branch.add({ 'sentence' : premise })
        branch.add({ 'sentence':  negate(argument.conclusion) })

class TableauxRules(object):
    """
    The Tableaux System for CPL contains all the operator rules from K, except for
    the rules for the modal operators (Necessity, Possibility), and the quantifiers
    (Universal, Existential).
    """

    class Closure(logic.TableauxSystem.ClosureRule):
        """
        A branch is closed iff a sentence and its negation appear on the branch.
        """

        def applies_to_branch(self, branch):
            for node in branch.get_nodes():
                if branch.has({ 'sentence' : negate(node.props['sentence']) }):
                    return branch
            return False

        def example(self):
            a = logic.atomic(0, 0)
            self.tableau.branch().update([{ 'sentence' : a }, { 'sentence' : negate(a) }])

    rules = [

        Closure,

        # non-branching rules

        k.TableauxRules.Conjunction,
        k.TableauxRules.DisjunctionNegated,
        k.TableauxRules.MaterialConditionalNegated,
        k.TableauxRules.ConditionalNegated,
        k.TableauxRules.DoubleNegation,

        # branching rules

        k.TableauxRules.ConjunctionNegated,
        k.TableauxRules.Disjunction,
        k.TableauxRules.MaterialConditional,
        k.TableauxRules.MaterialBiconditional,
        k.TableauxRules.MaterialBiconditionalNegated,
        k.TableauxRules.Conditional,
        k.TableauxRules.Biconditional,
        k.TableauxRules.BiconditionalNegated

    ]