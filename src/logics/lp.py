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
LP is a 3-valued logic (True, False, and Both). Two primitive operators, negation and
disjunction, are defined via truth tables.

Semantics
---------

Truth-functional operators are defined via truth tables (below).

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

import fde, k

def example_validities():
    args = fde.example_validities()
    args.update([
        'Biconditional Identity'          ,
        'Conditional Identity'            ,
        'Conditional Pseudo Contraction'  ,
        'Law of Excluded Middle'          ,
        'Material Biconditional Identity' ,
        'Material Identity'               ,
        'Material Pseudo Contraction'     ,
    ])
    return args
    
def example_invalidities():
    import cfol
    args = cfol.example_invalidities()
    args.update([
        'Biconditional Elimination 1'   ,
        'Biconditional Elimination 2'   ,
        'Conditional Modus Ponens'      ,
        'Conditional Modus Tollens'     ,
        'Disjunctive Syllogism'         ,
        'Existential Syllogism'         ,
        'Law of Non-contradiction'      ,
        'Material Modus Ponens'         ,
        'Material Modus Tollens'        ,
        'Syllogism'                     ,
        'Universal Predicate Syllogism' ,
    ])
    return args
    
import logic
from logic import negate

truth_values = [0, 0.75, 1]
truth_value_chars = {
    0    : 'F',
    0.75 : 'B',
    1    : 'T'
}
designated_values = fde.designated_values
undesignated_values = k.undesignated_values
unassigned_value = 0
truth_functional_operators = fde.truth_functional_operators
truth_function = fde.truth_function

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
                    n = branch.find({
                        'sentence'   : negate(node.props['sentence']),
                        'designated' : False
                    })
                    if n:
                        return { 'nodes' : set([node, n]), 'type' : 'Nodes' }
            return False

        def example(self):
            a = logic.atomic(0, 0)
            self.tableau.branch().update([
                { 'sentence' :        a  , 'designated' : False },
                { 'sentence' : negate(a) , 'designated' : False }
            ])

    rules = list(fde.TableauxRules.rules)
    rules.insert(0, Closure)