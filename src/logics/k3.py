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

The truth-functional operators are defined via truth tables below.

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

* Everything valid in FDE is valid in K3.

* Like FDE, the law of excluded middle, and conditional identity (if A then A) fail.

* Unlike FDE, K3 has some logical truths, for example the law of non-contradiction, and conditional identity (if A then A).

* Some Classical validities such as Modus Ponens, Modus Tollens, Disjunctive Syllogism, are valid.

* DeMorgan laws are valid.
"""
name = 'K3'
description = 'Strong Kleene 3-valued logic'

import fde, k

def example_validities():
    args = fde.example_validities()
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
    
def example_invalidities():
    import cfol
    args = cfol.example_invalidities()
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
    
import logic
from logic import negate

truth_values = [0, 0.5, 1]
truth_value_chars = {
    0   : 'F',
    0.5 : 'N',
    1   : 'T'
}
designated_values = k.designated_values
undesignated_values = set([0, 0.5])
unassigned_value = 0.5
truth_functional_operators = fde.truth_functional_operators
truth_function = fde.truth_function

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
                    n = branch.find({
                        'sentence'   : negate(node.props['sentence']),
                        'designated' : True
                    })
                    if n:
                        return { 'nodes' : set([node, n]), 'type' : 'Nodes' }
            return False

        def example(self):
            a = logic.atomic(0, 0)
            self.tableau.branch().update([
                { 'sentence' :        a  , 'designated' : True },
                { 'sentence' : negate(a) , 'designated' : True }
            ])
    
    rules = list(fde.TableauxRules.rules)
    rules.insert(0, Closure)