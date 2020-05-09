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
# pytableaux - Logic of Paradox

"""
Semantics
=========

LP is a 3-valued logic (**T**, **F**, and **B**). It can be understood as `FDE`_ without
the **N** value. A common intepretation of these values is:

- **T**: just true
- **F**: just false
- **B**: both true and false

Truth Tables
------------

**Truth-functional operators** are defined via the following truth tables. The truth tables
resemble those of `FDE`_ with the *N* value removed.

/truth_tables/

Predication
-----------

**Predicate Sentences** like *a is F* are handled via a predicate's *extension* and *anti-extension*,
similar to `FDE`_:

- P{Fa} is true iff the object denoted by *a* is in the extension of *F*.

- P{Fa} is false iff the object denoted by *a* is in the anti-extension of *F*.

Like in `FDE`_, there is no exclusivity constraint, which means that an object
might be in both the extension and the anti-extesion of a predicate.

Unlike `FDE`_, however, there is an **exhaustion constraint** on a predicate's
extension/anti-extension. This means that every object must be in (at least one of)
a predicate's extension or anti-extension.

In this way, a sentence P{Fa} gets the value:

- **T** iff *a* is in the extension of *F*, and it is *not* in the anti-extension of *F*.
- **F** iff *a* is in the anti-extension of *F*, and it is *not* in the extension of *F*.
- **B** iff *a* is in both the extension and anti-extension of *F*.

Quantification
--------------

**Quantification** is interpreted as follows:

- **Universal Quantifier**: as sentence P{LxFx} has the value:

    - **T** iff everything is in the extension of *F* and its anti-extension is empty.
    - **B** iff everything is in the extension of *F* and its anti-extension is non-empty.
    - **F** iff not everything is in the extension of *F* and its anti-extension is non-empty.

- **Existential Quantifier**: P{XxFx} is interpreted as P{~Lx~Fx}.

Logical Consequence
-------------------

**Logical Consequence** is defined, just as in `FDE`_, in terms of *designated* values **T**
and **B**:

- *C* is a **Logical Consequence** of *A* iff all cases where *A* has a *designated*
  value (**T** or **B**) are cases where *C* also has a *designated* value.

Notes
-----

Some notable features of LP include:

* Everything valid in `FDE`_ is valid in LP.

* Like `FDE`_, the Law of Non-Contradiction fails P{~(A & ~A)}.

* Unlike `FDE`_, LP has some logical truths. For example, the Law of Excluded Middle (P{(A V ~A)}),
  and Conditional Identity (P{(A $ A)}).

* Many classical validities fail, such as Modus Ponens, Modus Tollens, and Disjunctive Syllogism.

* DeMorgan laws are valid.

For futher reading see:

- `Stanford Encyclopedia entry on paraconsistent logic <http://plato.stanford.edu/entries/logic-paraconsistent/>`_

.. _FDE: fde.html
"""

name = 'LP'
title = 'Logic of Paradox'
description = 'Three-valued logic (True, False, Both)'
tags = set(['many-valued', 'glutty', 'non-modal', 'first-order'])
tags_list = list(tags)

from . import fde, k

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
    from . import cfol
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
    LP tableaux behave just like `FDE`_'s using designation markers. The trunk
    is built in the same way.
    """
    pass

class TableauxRules(object):
    """
    The Tableaux System for LP contains all the rules from `FDE`_, as well as an additional
    closure rule.
    """

    class Closure(logic.TableauxSystem.ClosureRule):
        """
        A branch closes when a sentence and its negation both appear as undesignated nodes.
        This rule is **in addition to** the `FDE closure rule`_.

        .. _FDE closure Rule: fde.html#logics.fde.TableauxRules.Closure
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