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
# pytableaux - Strong Kleene Logic

"""
K3 is a 3-valued logic (True, False, and Neither).

Semantics
---------

The semantics of K3 can be thought of as the same as FDE, with the **B** value removed.

Two primitive operators, negation and disjunction, are defined via truth tables.

**Negation**:

+------------+------------+
| A          | not-A      |
+============+============+
|  T         |  F         |
+------------+------------+
|  N         |  N         |
+------------+------------+
|  F         |  T         |
+------------+------------+

**Disjunction**:

+-----------+----------+-----------+---------+
|  A or B   |          |           |         |
+===========+==========+===========+=========+
|           |  **T**   |   **N**   |  **F**  |
+-----------+----------+-----------+---------+
|  **T**    |    T     |     T     |    T    |
+-----------+----------+-----------+---------+
|  **N**    |    T     |     N     |    N    |
+-----------+----------+-----------+---------+
|  **F**    |    T     |     N     |    F    | 
+-----------+----------+-----------+---------+

Other operators are defined via semantic equivalencies:

- **Conjunction**: ``A and B := not (not-A or not-B)``

- **Material Conditional**: ``if A then B := not-A or B``
    
- **Material Biconditional**: ``A if and only if B := (if A then B) and (if B then A)``

The truth table for some defined connectives are as follows:

**Conjunction**:

+-----------+----------+-----------+---------+
|  A and B  |          |           |         |
+===========+==========+===========+=========+
|           |  **T**   |   **N**   |  **F**  |
+-----------+----------+-----------+---------+
|  **T**    |    T     |     N     |    F    |
+-----------+----------+-----------+---------+
|  **N**    |    N     |     N     |    F    |
+-----------+----------+-----------+---------+
|  **F**    |    F     |     F     |    F    | 
+-----------+----------+-----------+---------+

**Material Conditional**:

+-----------+----------+-----------+---------+
|  A or B   |          |           |         |
+===========+==========+===========+=========+
|           |  **T**   |   **N**   |  **F**  |
+-----------+----------+-----------+---------+
|  **T**    |    T     |     N     |    F    |
+-----------+----------+-----------+---------+
|  **N**    |    T     |     N     |    N    |
+-----------+----------+-----------+---------+
|  **F**    |    T     |     T     |    T    | 
+-----------+----------+-----------+---------+

The **Conditional** and **Biconditional** operators are equivalent to their material counterparts.

**Predicate Sentences** like *a is F* are handled via a predicate's *extension* and *anti-extension*:

- *a is F* iff the object denoted by *a* is in the extension of *F*.

- it's not the case that *a is F* iff the object denoted by *a* is in the anti-extension of *F*.

There is an **exclusivity constraint** on a predicate's extension/anti-extension, such that no
object can be in both a predicate's extension and its anti-extension. There is no exhaustion
constraint, however, so an object may fail to be in either a predicate's extension or anti-extension
Thus **Quantification** can be thought of along these lines:

- **Universal Quantifier**: *for all x, x is F* has the value:

    - **T** iff everything is in the extension of *F* and its anti-extension is empty.
    - **N** iff not everything is in the extension of *F* and its anti-extension is empty.
    - **F** iff not everything is in the extension of *F* and its anti-extension is non-empty.

- **Existential Quantifier**: ``there exists an x that is F := not (for all x, not (x is F))``

*C* is a **Logical Consequence** of *A* iff all cases where the value of *A* is **T**
are cases where *C* also has the value **T**.

Notes
-----

Some notable features of K3 include:

* Everything valid in FDE is valid in LP.

* Like FDE, the law of excluded middle, and conditional identity (if A then A) fail.

* Unlike FDE, K3 has some logical truths, for example the law of non-contradiction, and conditional identity (if A then A).

* Some Classical validities such as Modus Ponens, Modus Tollens, Disjunctive Syllogism, are valid.

* DeMorgan laws are valid.
"""
name = 'K3'
description = 'Strong Kleene 3-valued logic'

import fde

def example_validities():
    args = fde.example_validities()
    args.update({
        'Law of Non-contradiction'    : [[ 'KaNa' ], 'b' ],
        'Disjunctive Syllogism'       : [[ 'Aab', 'Nb' ], 'a'  ],
        'Material Modus Ponens'       : [[ 'Cab', 'a'  ], 'b'  ],
        'Material Modus Tollens'      : [[ 'Cab', 'Nb' ], 'Na' ],
        'Conditional Modus Ponens'    : [[ 'Uab', 'a'  ], 'b'  ],
        'Conditional Modus Tollens'   : [[ 'Uab', 'Nb' ], 'Na' ]
    })
    return args
    
def example_invalidities():
    import cfol
    args = cfol.example_invalidities()
    args.update({
        'Material Identity'               : 'Caa',
        'Conditional Identity'            : 'Uaa',
        'Material Biconditional Identity' : 'Eaa',
        'Biconditional Identity'          : 'Baa',
        'Law of Excluded Middle'          : 'AaNa'
    })
    return args
    
import logic
from logic import negate

class TableauxSystem(fde.TableauxSystem):
    """
    K3's Tableaux System inherits directly from FDE's.
    """
    pass
        
class TableauxRules(object):
    """
    The Tableaux System for K3 contains all the rules from FDE, as well as an additional
    Closure rule below.
    """
    
    class Closure(logic.TableauxSystem.ClosureRule):
        """
        A branch closes when a sentence and its negation both appear as designated nodes.
        This rule is **in addition to** the FDE Closure rule.
        """
        
        def applies_to_branch(self, branch):
            for node in branch.get_nodes():
                if node.props['designated']:
                    if branch.has({
                        'sentence'   : negate(node.props['sentence']),
                        'designated' : True
                    }):
                        return branch
            return False

        def example(self):
            a = logic.atomic(0, 0)
            self.tableau.branch().update([
                { 'sentence' :        a  , 'designated' : True },
                { 'sentence' : negate(a) , 'designated' : True }
            ])
    
    rules = list(fde.TableauxRules.rules)
    rules.insert(0, Closure)