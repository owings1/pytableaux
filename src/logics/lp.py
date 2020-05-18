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
resemble those of `FDE`_ with the **N** value removed.

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

class Model(fde.Model):
    truth_values = set([0, 0.75, 1])
    undesignated_values = set([0])
    unassigned_value = 0
    char_values = {
        'F' : 0,
        'B' : 0.75,
        'T' : 1
    }
    truth_value_chars = {
        0    : 'F',
        0.75 : 'B',
        1    : 'T'
    }

# legacy properties
truth_values = [0, 0.75, 1]
truth_value_chars = Model.truth_value_chars
truth_functional_operators = Model.truth_functional_operators

def truth_function(operator, a, b=None):
    # legacy api
    return Model().truth_function(operator, a, b)

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

    class DoubleNegationDesignated(fde.TableauxRules.DoubleNegationDesignated):
        """
        This rule is the same as the `FDE DoubleNegationDesignated rule`_.

        .. _FDE DoubleNegationDesignated rule: fde.html#logics.fde.TableauxRules.DoubleNegationDesignated
        """
        pass

    class DoubleNegationUndesignated(fde.TableauxRules.DoubleNegationUndesignated):
        """
        This rule is the same as the `FDE DoubleNegationUndesignated rule`_.

        .. _FDE DoubleNegationUndesignated rule: fde.html#logics.fde.TableauxRules.DoubleNegationUndesignated
        """
        pass

    class AssertionDesignated(fde.TableauxRules.AssertionDesignated):
        """
        This rule is the same as the `FDE AssertionDesignated rule`_.

        .. _FDE AssertionDesignated rule: fde.html#logics.fde.TableauxRules.AssertionDesignated
        """
        pass

    class AssertionNegatedDesignated(fde.TableauxRules.AssertionNegatedDesignated):
        """
        This rule is the same as the `FDE AssertionNegatedDesignated rule`_.

        .. _FDE AssertionNegatedDesignated rule: fde.html#logics.fde.TableauxRules.AssertionNegatedDesignated
        """
        pass

    class AssertionUndesignated(fde.TableauxRules.AssertionUndesignated):
        """
        This rule is the same as the `FDE AssertionUndesignated rule`_.

        .. _FDE AssertionUndesignated rule: fde.html#logics.fde.TableauxRules.AssertionUndesignated
        """
        pass

    class AssertionNegatedUndesignated(fde.TableauxRules.AssertionNegatedUndesignated):
        """
        This rule is the same as the `FDE AssertionNegatedUndesignated rule`_.

        .. _FDE AssertionNegatedUndesignated rule: fde.html#logics.fde.TableauxRules.AssertionNegatedUndesignated
        """
        pass

    class ConjunctionDesignated(fde.TableauxRules.ConjunctionDesignated):
        """
        This rule is the same as the `FDE ConjunctionDesignated rule`_.

        .. _FDE ConjunctionDesignated rule: fde.html#logics.fde.TableauxRules.ConjunctionDesignated
        """
        pass

    class ConjunctionNegatedDesignated(fde.TableauxRules.ConjunctionNegatedDesignated):
        """
        This rule is the same as the `FDE ConjunctionNegatedDesignated rule`_.

        .. _FDE ConjunctionNegatedDesignated rule: fde.html#logics.fde.TableauxRules.ConjunctionNegatedDesignated
        """
        pass

    class ConjunctionUndesignated(fde.TableauxRules.ConjunctionUndesignated):
        """
        This rule is the same as the `FDE ConjunctionUndesignated rule`_.

        .. _FDE ConjunctionUndesignated rule: fde.html#logics.fde.TableauxRules.ConjunctionUndesignated
        """
        pass

    class ConjunctionNegatedUndesignated(fde.TableauxRules.ConjunctionNegatedUndesignated):
        """
        This rule is the same as the `FDE ConjunctionNegatedUndesignated rule`_.

        .. _FDE ConjunctionNegatedUndesignated rule: fde.html#logics.fde.TableauxRules.ConjunctionNegatedUndesignated
        """
        pass

    class DisjunctionDesignated(fde.TableauxRules.DisjunctionDesignated):
        """
        This rule is the same as the `FDE DisjunctionDesignated rule`_.

        .. _FDE DisjunctionDesignated rule: fde.html#logics.fde.TableauxRules.DisjunctionDesignated
        """
        pass

    class DisjunctionNegatedDesignated(fde.TableauxRules.DisjunctionNegatedDesignated):
        """
        This rule is the same as the `FDE DisjunctionNegatedDesignated rule`_.

        .. _FDE DisjunctionNegatedDesignated rule: fde.html#logics.fde.TableauxRules.DisjunctionNegatedDesignated
        """
        pass

    class DisjunctionUndesignated(fde.TableauxRules.DisjunctionUndesignated):
        """
        This rule is the same as the `FDE DisjunctionUndesignated rule`_.

        .. _FDE DisjunctionUndesignated rule: fde.html#logics.fde.TableauxRules.DisjunctionUndesignated
        """
        pass

    class DisjunctionNegatedUndesignated(fde.TableauxRules.DisjunctionNegatedUndesignated):
        """
        This rule is the same as the `FDE DisjunctionNegatedUndesignated rule`_.

        .. _FDE DisjunctionNegatedUndesignated rule: fde.html#logics.fde.TableauxRules.DisjunctionNegatedUndesignated
        """
        pass

    class MaterialConditionalDesignated(fde.TableauxRules.MaterialConditionalDesignated):
        """
        This rule is the same as the `FDE MaterialConditionalDesignated rule`_.

        .. _FDE MaterialConditionalDesignated rule: fde.html#logics.fde.TableauxRules.MaterialConditionalDesignated
        """
        pass

    class MaterialConditionalNegatedDesignated(fde.TableauxRules.MaterialConditionalNegatedDesignated):
        """
        This rule is the same as the `FDE MaterialConditionalNegatedDesignated rule`_.

        .. _FDE MaterialConditionalNegatedDesignated rule: fde.html#logics.fde.TableauxRules.MaterialConditionalNegatedDesignated
        """
        pass

    class MaterialConditionalNegatedUndesignated(fde.TableauxRules.MaterialConditionalNegatedUndesignated):
        """
        This rule is the same as the `FDE MaterialConditionalNegatedUndesignated rule`_.

        .. _FDE MaterialConditionalNegatedUndesignated rule: fde.html#logics.fde.TableauxRules.MaterialConditionalNegatedUndesignated
        """
        pass

    class MaterialConditionalUndesignated(fde.TableauxRules.MaterialConditionalUndesignated):
        """
        This rule is the same as the `FDE MaterialConditionalUndesignated rule`_.

        .. _FDE MaterialConditionalUndesignated rule: fde.html#logics.fde.TableauxRules.MaterialConditionalUndesignated
        """
        pass

    class MaterialBiconditionalDesignated(fde.TableauxRules.MaterialBiconditionalDesignated):
        """
        This rule is the same as the `FDE MaterialBiconditionalDesignated rule`_.

        .. _FDE MaterialBiconditionalDesignated rule: fde.html#logics.fde.TableauxRules.MaterialBiconditionalDesignated
        """
        pass

    class MaterialBiconditionalNegatedDesignated(fde.TableauxRules.MaterialBiconditionalNegatedDesignated):
        """
        This rule is the same as the `FDE MaterialBiconditionalNegatedDesignated rule`_.

        .. _FDE MaterialBiconditionalNegatedDesignated rule: fde.html#logics.fde.TableauxRules.MaterialBiconditionalNegatedDesignated
        """
        pass

    class MaterialBiconditionalUndesignated(fde.TableauxRules.MaterialBiconditionalUndesignated):
        """
        This rule is the same as the `FDE MaterialBiconditionalUndesignated rule`_.

        .. _FDE MaterialBiconditionalUndesignated rule: fde.html#logics.fde.TableauxRules.MaterialBiconditionalUndesignated
        """
        pass

    class MaterialBiconditionalNegatedUndesignated(fde.TableauxRules.MaterialBiconditionalNegatedUndesignated):
        """
        This rule is the same as the `FDE MaterialBiconditionalNegatedUndesignated rule`_.

        .. _FDE MaterialBiconditionalNegatedUndesignated rule: fde.html#logics.fde.TableauxRules.MaterialBiconditionalNegatedUndesignated
        """
        pass

    class ConditionalDesignated(fde.TableauxRules.ConditionalDesignated):
        """
        This rule is the same as the `FDE ConditionalDesignated rule`_.

        .. _FDE ConditionalDesignated rule: fde.html#logics.fde.TableauxRules.ConditionalDesignated
        """
        pass

    class ConditionalNegatedDesignated(fde.TableauxRules.ConditionalNegatedDesignated):
        """
        This rule is the same as the `FDE ConditionalNegatedDesignated rule`_.

        .. _FDE ConditionalNegatedDesignated rule: fde.html#logics.fde.TableauxRules.ConditionalNegatedDesignated
        """
        pass

    class ConditionalUndesignated(fde.TableauxRules.ConditionalUndesignated):
        """
        This rule is the same as the `FDE ConditionalUndesignated rule`_.

        .. _FDE ConditionalUndesignated rule: fde.html#logics.fde.TableauxRules.ConditionalUndesignated
        """
        pass

    class ConditionalNegatedUndesignated(fde.TableauxRules.ConditionalNegatedUndesignated):
        """
        This rule is the same as the `FDE ConditionalNegatedUndesignated rule`_.

        .. _FDE ConditionalNegatedUndesignated rule: fde.html#logics.fde.TableauxRules.ConditionalNegatedUndesignated
        """
        pass
        
    class BiconditionalDesignated(fde.TableauxRules.BiconditionalDesignated):
        """
        This rule is the same as the `FDE BiconditionalDesignated rule`_.

        .. _FDE BiconditionalDesignated rule: fde.html#logics.fde.TableauxRules.BiconditionalDesignated
        """
        pass

    class BiconditionalNegatedDesignated(fde.TableauxRules.BiconditionalNegatedDesignated):
        """
        This rule is the same as the `FDE BiconditionalNegatedDesignated rule`_.

        .. _FDE BiconditionalNegatedDesignated rule: fde.html#logics.fde.TableauxRules.BiconditionalNegatedDesignated
        """
        pass

    class BiconditionalUndesignated(fde.TableauxRules.BiconditionalUndesignated):
        """
        This rule is the same as the `FDE BiconditionalUndesignated rule`_.

        .. _FDE BiconditionalUndesignated rule: fde.html#logics.fde.TableauxRules.BiconditionalUndesignated
        """
        pass

    class BiconditionalNegatedUndesignated(fde.TableauxRules.BiconditionalNegatedUndesignated):
        """
        This rule is the same as the `FDE BiconditionalNegatedUndesignated rule`_.

        .. _FDE BiconditionalNegatedUndesignated rule: fde.html#logics.fde.TableauxRules.BiconditionalNegatedUndesignated
        """
        pass

    class ExistentialDesignated(fde.TableauxRules.ExistentialDesignated):
        """
        This rule is the same as the `FDE ExistentialDesignated rule`_.

        .. _FDE ExistentialDesignated rule: fde.html#logics.fde.TableauxRules.ExistentialDesignated
        """
        pass

    class ExistentialNegatedDesignated(fde.TableauxRules.ExistentialNegatedDesignated):
        """
        This rule is the same as the `FDE ExistentialNegatedDesignated rule`_.

        .. _FDE ExistentialNegatedDesignated rule: fde.html#logics.fde.TableauxRules.ExistentialNegatedDesignated
        """
        pass

    class ExistentialUndesignated(fde.TableauxRules.ExistentialUndesignated):
        """
        This rule is the same as the `FDE ExistentialUndesignated rule`_.

        .. _FDE ExistentialUndesignated rule: fde.html#logics.fde.TableauxRules.ExistentialUndesignated
        """
        pass

    class ExistentialNegatedUndesignated(fde.TableauxRules.ExistentialNegatedUndesignated):
        """
        This rule is the same as the `FDE ExistentialNegatedUndesignated rule`_.

        .. _FDE ExistentialNegatedUndesignated rule: fde.html#logics.fde.TableauxRules.ExistentialNegatedUndesignated
        """
        pass

    class UniversalDesignated(fde.TableauxRules.UniversalDesignated):
        """
        This rule is the same as the `FDE UniversalDesignated rule`_.

        .. _FDE UniversalDesignated rule: fde.html#logics.fde.TableauxRules.UniversalDesignated
        """
        pass

    class UniversalNegatedDesignated(fde.TableauxRules.UniversalNegatedDesignated):
        """
        This rule is the same as the `FDE UniversalNegatedDesignated rule`_.

        .. _FDE UniversalNegatedDesignated rule: fde.html#logics.fde.TableauxRules.UniversalNegatedDesignated
        """
        pass

    class UniversalUndesignated(fde.TableauxRules.UniversalUndesignated):
        """
        This rule is the same as the `FDE UniversalUndesignated rule`_.

        .. _FDE UniversalUndesignated rule: fde.html#logics.fde.TableauxRules.UniversalUndesignated
        """
        pass

    class UniversalNegatedUndesignated(fde.TableauxRules.UniversalNegatedUndesignated):
        """
        This rule is the same as the `FDE UniversalNegatedUndesignated rule`_.

        .. _FDE UniversalNegatedUndesignated rule: fde.html#logics.fde.TableauxRules.UniversalNegatedUndesignated
        """
        pass

    rules = [

        fde.TableauxRules.Closure,
        Closure,

        # non-branching rules
        AssertionDesignated,
        AssertionUndesignated,
        AssertionNegatedDesignated,
        AssertionNegatedUndesignated,
        ConjunctionDesignated, 
        DisjunctionNegatedDesignated,
        DisjunctionUndesignated,
        DisjunctionNegatedUndesignated,
        MaterialConditionalNegatedDesignated,
        MaterialConditionalUndesignated,
        ConditionalUndesignated, 
        ConditionalNegatedDesignated,
        ExistentialDesignated,
        ExistentialNegatedDesignated,
        ExistentialUndesignated,
        ExistentialNegatedUndesignated,
        UniversalDesignated,
        UniversalNegatedDesignated,
        UniversalUndesignated,
        UniversalNegatedUndesignated,
        DoubleNegationDesignated,
        DoubleNegationUndesignated,

        # branching rules

        ConjunctionNegatedDesignated,
        ConjunctionUndesignated,
        ConjunctionNegatedUndesignated,
        DisjunctionDesignated,
        MaterialConditionalDesignated,
        MaterialConditionalNegatedUndesignated,
        MaterialBiconditionalDesignated,
        MaterialBiconditionalNegatedDesignated,
        MaterialBiconditionalUndesignated,
        MaterialBiconditionalNegatedUndesignated,
        ConditionalDesignated,
        ConditionalNegatedUndesignated,
        BiconditionalDesignated,
        BiconditionalNegatedDesignated,
        BiconditionalUndesignated,
        BiconditionalNegatedUndesignated

    ]