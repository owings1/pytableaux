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
# pytableaux - Logic of Paradox

"""
Semantics
---------

LP is a 3-valued logic (True, False, and Both). Two primitive operators, negation and
disjunction, are defined via truth tables.

**Negation**:

+------------+------------+
| A          | not-A      |
+============+============+
|  T         |  F         |
+------------+------------+
|  B         |  B         |
+------------+------------+
|  F         |  T         |
+------------+------------+

**Disjunction**:

+-----------+----------+-----------+---------+
|  A or B   |          |           |         |
+===========+==========+===========+=========+
|           |  **T**   |   **B**   |  **F**  |
+-----------+----------+-----------+---------+
|  **T**    |    T     |     T     |    T    |
+-----------+----------+-----------+---------+
|  **B**    |    T     |     B     |    F    |
+-----------+----------+-----------+---------+
|  **F**    |    T     |     F     |    F    | 
+-----------+----------+-----------+---------+

Other operators are defined via semantic equivalencies:

- **Conjunction**: ``A and B := not (not-A or not-B)``

- **Material Conditional**: ``if A then B := not-A or B``
    
- **Material Biconditional**: ``A if and only if B := (if A then B) and (if B then A)``

The **Conditional** and **Biconditional** operators are equivalent to their material counterparts.

**Predicate Sentences** like *a is F* are handled via a predicate's *extension* and *anti-extension*:

- *a is F* iff the object denoted by *a* is in the extension of *F*.

- it's not the case that *a is F* iff the object denoted by *a* is in the anti-extension of *F*.

There is **exhaustion constraint** on a predicate's extension/anti-extension, such that every
object must be in a predicates extension or anti-extension. There is no exclusivity constraint, so
an object might be in both the extension and anti-extesion of a predicate. Thus **Quantification**
can be thought of along these lines:

- **Universal Quantifier**: *for all x, x is F* has the value:

    - **T** iff everything is in the extension of *F* and its anti-extension is empty.
    - **B** iff everything is in the extension of *F* and its anti-extension is non-empty.
    - **F** iff not everything is in the extension of *F* and its anti-extension is non-empty.

- **Existential Quantifier**: ``there exists an x that is F := not (for all x, not (x is F))``

*C* is a **Logical Consequence** of *A* iff all cases where the value of *A* is either **T** or
**B** (the *designated* values) are cases where *C* also has a *designated* value.

Notes
-----

Some notable features of LP include:

* Everything valid in FDE is valid in LP.

* Like FDE, the law of non-contradition fails.

* Unlike FDE, LP has some logical truths, for example the law of excluded middle, and conditional identity (if A then A).

* Failure of Modus Ponens, Modus Tollens, Disjunctive Syllogism, and other Classical validities.

* DeMorgan laws are valid.

For futher reading see:

- `Stanford Encyclopedia entry on paraconsistent logic <http://plato.stanford.edu/entries/logic-paraconsistent/>`_
"""
name = 'LP'
description = 'Logic of Paradox'

import fde

def example_validities():
    args = fde.example_validities()
    args.update([
        'Material Identity'      ,
        'Conditional Identity'   ,
        'Law of Excluded Middle' ,
    ])
    return args
    
def example_invalidities():
    import cfol
    args = cfol.example_invalidities()
    args.update([
        'Law of Non-contradiction'   ,
        'Disjunctive Syllogism'      ,
        'Material Modus Ponens'      ,
        'Material Modus Tollens'     ,
        'Conditional Modus Ponens'   ,
        'Conditional Modus Tollens'  ,
    ])
    return args
    
import logic
from logic import negate

class TableauxSystem(fde.TableauxSystem):
    """
    LP's Tableaux System inherits directly from FDE's.
    """
    pass

class TableauxRules(object):
    """
    The Tableaux System for LP contains all the rules from FDE, as well as an additional
    Closure rule below.
    """

    class Closure(logic.TableauxSystem.ClosureRule):
        """
        A branch closes when a sentence and its negation both appear as undesignated nodes.
        This rule is **in addition to** the FDE Closure rule.
        """

        def applies_to_branch(self, branch):
            for node in branch.get_nodes():
                if not node.props['designated']:
                    if branch.has({
                        'sentence'   : negate(node.props['sentence']),
                        'designated' : False
                    }):
                        return branch
            return False

        def example(self):
            a = logic.atomic(0, 0)
            self.tableau.branch().update([
                { 'sentence' :        a  , 'designated' : False },
                { 'sentence' : negate(a) , 'designated' : False }
            ])

    rules = list(fde.TableauxRules.rules)
    rules.insert(0, Closure)