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
# pytableaux - Strong Kleene Logic

"""
Semantics
=========

K3 is a three-valued logic (**T**, **F**, and **N**). It can be understood as `FDE`_
without the **B** value. A common interpretation of these values is:

- **T**: true
- **F**: false
- **N**: neither true nor false

Truth Tables
------------

**Truth-functional operators** are defined via the following truth tables. The truth tables
resemble those of `FDE`_ with the *B* value removed.

/truth_tables/

Predication
-----------

**Predicate Sentences** like P{Fa} are handled via a predicate's *extension* and *anti-extension*,
similar to `FDE`_:

- P{Fa} is true iff the object denoted by *a* is in the extension of *F*.

- P{Fa} is false iff the object denoted by *a* is in the anti-extension of *F*.

Like in `FDE`_, there is no exhaustion constraint, which means that an object
might be in neither the extension nor the anti-extesion of a predicate.

Unlike `FDE`_, however, there is an **exclusivity constraint** on a predicate's extension/anti-extension.
This means that no object can be in both a predicate's extension and its anti-extension.

In this way, a sentence P{Fa} gets the value:

- **T** iff *a* is in the extension of *F*.
- **F** iff *a* is in the anti-extension of *F*.
- **N** iff *a* is neither in the extension nor the anti-extension of *F*.

Quantification
--------------

**Quantification** is interpreted as follows:

- **Universal Quantifier**: *for all x, x is F* has the value:

    - **T** iff everything is in the extension of *F*.
    - **N** iff not everything is in the extension of *F* and its anti-extension is empty.
    - **F** iff not everything is in the extension of *F* and its anti-extension is non-empty.

- **Existential Quantifier**: P{XxFx} is interpreted as P{~Lx~Fx}.

Logical Consequence
-------------------

**Logical Consequence** is defined just like in `CPL`_:

- *C* is a **Logical Consequence** of *A* iff all cases where the value of *A* is **T**
  are cases where *C* also has the value **T**.

Notes
-----

Some notable features of K3 include:

* Everything valid in `FDE`_ is valid in K3.

* Like `FDE`_, the law of excluded middle, and Conditional Identity P{(A $ A)} fail.

* Unlike `FDE`_, K3 has some logical truths, for example the Law of Non-Contradiction,
  P{~(A & ~A)}, and Conditional Identity P{A $ A}.

* Some Classical validities, such as Modus Ponens, Modus Tollens, Disjunctive Syllogism,
  and DeMorgan laws, are valid.

.. _FDE: fde.html
.. _CPL: cpl.html
"""
name = 'K3'
title = 'Strong Kleene 3-valued logic'
description = 'Three-valued logic (True, False, Neither)'
tags = set(['many-valued', 'gappy', 'non-modal', 'first-order'])
tags_list = list(tags)

from . import fde, k

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
    from . import cfol
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
    K3's Tableaux System inherits directly from `FDE`_'s.
    """
    pass
        
class TableauxRules(object):
    """
    The Tableaux System for K3 contains all the rules from `FDE`_, as well as an additional
    closure rule.
    """
    
    class Closure(logic.TableauxSystem.ClosureRule):
        """
        A branch closes when a sentence and its negation both appear as designated nodes.
        This rule is **in addition to** the `FDE closure rule`_.

        .. _FDE closure Rule: fde.html#logics.fde.TableauxRules.Closure
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