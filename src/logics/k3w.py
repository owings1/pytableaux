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
# pytableaux - Weak Kleene Logic

"""
Semantics
=========
K3W is a 3-valued logic with values **T**, **F**, and **N**. The logic is similar
to `K3`_, but with slightly different behavior of the **N** value. This logic is also
known as Bochvar Internal (B3).

Truth Tables
------------
**Truth-functional operators** are defined via the following truth tables. Note that,
for the binary connectives, if either operand has the value **N**, then the whole
sentence has the value **N**. Hence the saying, "one bit of rat's dung spoils the soup."

/truth_tables/

Predication
-----------

Predication is the same as `K3`_, where there is an **exclusivity constraint**
on a predicate's extension/anti-extension. A sentence P{Fa} gets the value:

- **T** iff *a* is in the extension of *F*.
- **F** iff *a* is in the anti-extension of *F*.
- **N** iff *a* is neither in the extension nor the anti-extension of *F*.

Quantification
--------------

Quantification is the same as `K3`_:

- **Universal Quantifier**: *for all x, x is F* has the value:

    - **T** iff everything is in the extension of *F*.
    - **N** iff not everything is in the extension of *F* and its anti-extension is empty.
    - **F** iff not everything is in the extension of *F* and its anti-extension is non-empty.

- **Existential Quantifier**: P{XxFx} is interpreted as P{~Lx~Fx}.

Logical Consequence
-------------------

**Logical Consequence** is defined just like in `CPL`_ and `K3`_:

- *C* is a **Logical Consequence** of *A* iff all cases where the value of *A* is **T**
  are cases where *C* also has the value **T**.

.. _CPL: cpl.html
.. _K3: k3.html
.. _FDE: fde.html
"""
name = 'K3W'
title = 'Weak Kleene 3-valued logic'
description = 'Three-valued logic with values T, F, and N'
tags = set(['many-valued', 'gappy', 'non-modal', 'first-order'])
tags_list = list(tags)

import logic
from logic import negate, operate
from . import fde, k3

class Model(k3.Model):
    def truth_function(self, operator, a, b=None):
        if logic.arity(operator) == 2 and (a == self.char_values['N'] or b == self.char_values['N']):
            return self.char_values['N']
        return super(Model, self).truth_function(operator, a, b)

# legacy properties
truth_values = [0, 0.5, 1]
truth_value_chars = Model.truth_value_chars
truth_functional_operators = Model.truth_functional_operators

def truth_function(operator, a, b=None):
    # legacy api
    return Model().truth_function(operator, a, b)

class TableauxSystem(fde.TableauxSystem):
    """
    K3W's Tableaux System inherits directly from `FDE`_'s.
    """
    pass
        
class TableauxRules(object):
    """
    The Tableaux System for K3W contains the `FDE closure rule`_, and the
    `K3 closure rule`_. Several of the operator rules are the same as `FDE`_.
    However, many rules for K3W are different from `FDE`_, given
    the behavior of the *N* value.
    
    .. _FDE closure rule: fde.html#logics.fde.TableauxRules.Closure
    .. _K3 closure rule: k3.html#logics.k3.TableauxRules.Closure
    """

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
        From an unticked, designated, negated conjunction node *n* on a branch *b*, make
        three new branches *b'*, *b''*, and *b'''* from *b*. On *b'* add a designated
        node with the first conjunct, and a designated node with the negation of the
        second conjunct. On *b''* add a designated node with the negation of the first
        conjunct, and a designated node with the second conjunct. On *b'''* add
        designated nodes with the negation of each conjunct. Then tick *n*.
        """

        def apply_to_node(self, node, branch):
            s = self.sentence(node)
            d = self.designation
            b1 = branch
            b2 = self.tableau.branch(branch)
            b3 = self.tableau.branch(branch)
            b1.update([
                { 'sentence' :        s.lhs , 'designated' : d },
                { 'sentence' : negate(s.rhs), 'designated' : d }
            ]).tick(node)
            b2.update([
                { 'sentence' : negate(s.lhs), 'designated' : d },
                { 'sentence' :        s.rhs , 'designated' : d }
            ]).tick(node)
            b3.update([
                { 'sentence' : negate(s.lhs), 'designated' : d },
                { 'sentence' : negate(s.rhs), 'designated' : d }
            ]).tick(node)

    class ConjunctionUndesignated(fde.TableauxRules.ConjunctionUndesignated):
        """
        This rule is the same as the `FDE ConjunctionUndesignated rule`_.

        .. _FDE ConjunctionUndesignated rule: fde.html#logics.fde.TableauxRules.ConjunctionUndesignated
        """
        pass

    class ConjunctionNegatedUndesignated(fde.TableauxRules.ConjunctionNegatedUndesignated):
        """
        From an unticked, undesignated, negated conjunction node *n* on a branch *b*, make
        three new branches *b'*, *b''*, and *b'''* from *b*. On *b'* add undesignated nodes
        for the first conjunct and its negation. On *b''* add undesignated nodes for the
        second conjunct and its negation. On *b'''* add a designated node for each conjunct.
        Then tick *n*. 
        """

        def apply_to_node(self, node, branch):
            s = self.sentence(node)
            d = self.designation
            b1 = branch
            b2 = self.tableau.branch(branch)
            b3 = self.tableau.branch(branch)
            b1.update([
                { 'sentence' :        s.lhs , 'designated' : d },
                { 'sentence' : negate(s.lhs), 'designated' : d }
            ]).tick(node)
            b2.update([
                { 'sentence' :        s.rhs , 'designated' : d },
                { 'sentence' : negate(s.rhs), 'designated' : d }
            ]).tick(node)
            b3.update([
                { 'sentence' :        s.lhs , 'designated' : not d },
                { 'sentence' :        s.rhs , 'designated' : not d }
            ]).tick(node)

    class DisjunctionDesignated(fde.TableauxRules.DisjunctionDesignated):
        """
        From an unticked, designated, disjunction node *n* on a branch *b*, make
        three new branches *b'*, *b''*, and *b'''* from *b*. On *b'* add a designated
        node with the first disjunct, and a designated node with the negation of the
        second disjunct. On *b''* add a designated node with the negation of the first
        disjunct, and a designated node with the second disjunct. On *b'''* add a
        designated node with each disjunct. Then tick *n*.
        """

        def apply_to_node(self, node, branch):
            s = self.sentence(node)
            d = self.designation
            b1 = branch
            b2 = self.tableau.branch(branch)
            b3 = self.tableau.branch(branch)
            b1.update([
                { 'sentence' :        s.lhs , 'designated' : d },
                { 'sentence' : negate(s.rhs), 'designated' : d }
            ]).tick(node)
            b2.update([
                { 'sentence' : negate(s.lhs), 'designated' : d },
                { 'sentence' :        s.rhs , 'designated' : d }
            ]).tick(node)
            b3.update([
                { 'sentence' :        s.lhs , 'designated' : d },
                { 'sentence' :        s.rhs , 'designated' : d }
            ]).tick(node)

    class DisjunctionNegatedDesignated(fde.TableauxRules.DisjunctionNegatedDesignated):
        """
        This rule is the same as the `FDE DisjunctionNegatedDesignated rule`_.

        .. _FDE DisjunctionNegatedDesignated rule: fde.html#logics.fde.TableauxRules.DisjunctionNegatedDesignated
        """
        pass

    class DisjunctionUndesignated(fde.TableauxRules.DisjunctionUndesignated):
        """
        From an unticked, undesignated disjunction node *n* on a branch *b*, make three
        new branches *b'*, *b''*, and *b'''* from b. On *b'* add undesignated nodes for
        the first disjunct and its negation. On *b''* add undesignated nodes for the
        second disjunct and its negation. On *b'''* add designated nodes for the negation
        of each disjunct. Then tick *n*.
        """

        def apply_to_node(self, node, branch):
            s = self.sentence(node)
            d = self.designation
            b1 = branch
            b2 = self.tableau.branch(branch)
            b3 = self.tableau.branch(branch)
            b1.update([
                { 'sentence' :        s.lhs , 'designated' : d },
                { 'sentence' : negate(s.lhs), 'designated' : d }
            ]).tick(node)
            b2.update([
                { 'sentence' :        s.rhs , 'designated' : d },
                { 'sentence' : negate(s.rhs), 'designated' : d }
            ]).tick(node)
            b3.update([
                { 'sentence' : negate(s.lhs), 'designated' : not d },
                { 'sentence' : negate(s.rhs), 'designated' : not d }
            ]).tick(node)

    class DisjunctionNegatedUndesignated(fde.TableauxRules.DisjunctionNegatedUndesignated):
        """
        It's not the case that both disjuncts are False. Thus, either both disjuncts are True,
        one disjunct is True and the other False, or both dijuncts are Neither. So, from an
        unticked, undesignated, negated disjunction node *n*, on a branch *b*, make four nodes
        *b'*, *b''*, *b'''*, *b''''* from *b*. On *b'*, add a designated node for each disjunct.
        On *b''* add a designated node for the first disjunct, an undesignated node for the second
        disjunct, and a designated node for the negation of the second disjunct. On *b'''* do the
        same as before, except with the second and first disjuncts, respectively. Finally, on
        *b''''*, add undesignated nodes for each disjunct and their negations. Then, tick *n*.
        """

        def apply_to_node(self, node, branch):
            s = self.sentence(node)
            b1 = branch
            b2 = self.tableau.branch(branch)
            b3 = self.tableau.branch(branch)
            b4 = self.tableau.branch(branch)
            b1.update([
                { 'sentence' :        s.lhs , 'designated' : True },
                { 'sentence' :        s.rhs , 'designated' : True }
            ]).tick(node)
            b2.update([
                { 'sentence' :        s.lhs,  'designated' : True  },
                { 'sentence' : negate(s.rhs), 'designated' : True  }
            ]).tick(node)
            b3.update([
                { 'sentence' : negate(s.lhs), 'designated' : True  },
                { 'sentence' :        s.rhs,  'designated' : True  }
            ]).tick(node)
            b4.update([
                { 'sentence' :        s.lhs,  'designated' : False },
                { 'sentence' : negate(s.lhs), 'designated' : False },
                { 'sentence' :        s.rhs,  'designated' : False },
                { 'sentence' : negate(s.rhs), 'designated' : False }
            ]).tick(node)

    class MaterialConditionalDesignated(fde.TableauxRules.MaterialConditionalDesignated):
        """
        This rule reduces to a disjunction.
        """

        def apply_to_node(self, node, branch):
            s = self.sentence(node)
            d = self.designation
            branch.add({
                'sentence' : operate('Disjunction', [
                    negate(s.lhs),
                           s.rhs
                ]),
                'designated' : d
            }).tick(node)

    class MaterialConditionalNegatedDesignated(fde.TableauxRules.MaterialConditionalNegatedDesignated):
        """
        This rule reduces to a negated disjunction.
        """

        def apply_to_node(self, node, branch):
            s = self.sentence(node)
            d = self.designation
            branch.add({
                'sentence' : negate(
                    operate('Disjunction', [
                        negate(s.lhs),
                               s.rhs
                    ])
                ),
                'designated' : d
            }).tick(node)

    class MaterialConditionalUndesignated(MaterialConditionalDesignated):
        """
        This rule reduces to a disjunction.
        """

        designation = False

    class MaterialConditionalNegatedUndesignated(MaterialConditionalNegatedDesignated):
        """
        This rule reduces to a negated disjunction.
        """

        designation = False

    class MaterialBiconditionalDesignated(fde.TableauxRules.MaterialBiconditionalDesignated):
        """
        This rule reduces to a conjunction of material conditionals.
        """

        def apply_to_node(self, node, branch):
            s = self.sentence(node)
            d = self.designation
            branch.add({
                'sentence' : operate('Conjunction', [
                    operate('Material Conditional', s.operands),
                    operate('Material Conditional', list(reversed(s.operands)))
                ]),
                'designated' : d
            }).tick(node)

    class MaterialBiconditionalNegatedDesignated(fde.TableauxRules.MaterialBiconditionalNegatedDesignated):
        """
        This rule reduces to a negated conjunction of material conditionals.
        """

        def apply_to_node(self, node, branch):
            s = self.sentence(node)
            d = self.designation
            branch.add({
                'sentence' : negate(
                    operate('Conjunction', [
                        operate('Material Conditional', s.operands),
                        operate('Material Conditional', list(reversed(s.operands)))
                    ])
                ),
                'designated' : d
            }).tick(node)

    class MaterialBiconditionalUndesignated(MaterialBiconditionalDesignated):
        """
        This rule reduces to a conjunction of material conditionals.
        """

        designation = False

    class MaterialBiconditionalNegatedUndesignated(MaterialBiconditionalNegatedDesignated):
        """
        This rule reduces to a negated conjunction of material conditionals.
        """

        designation = False

    class ConditionalDesignated(MaterialConditionalDesignated):
        """
        Same as for the material conditional designated.
        """

        operator = 'Conditional'

    class ConditionalNegatedDesignated(MaterialConditionalNegatedDesignated):
        """
        Same as for the negated material conditional designated.
        """

        operator = 'Conditional'

    class ConditionalUndesignated(MaterialConditionalUndesignated):
        """
        Same as for the material conditional undesignated.
        """

        operator = 'Conditional'

    class ConditionalNegatedUndesignated(MaterialConditionalNegatedUndesignated):
        """
        Same as for the negated material conditional undesignated.
        """

        operator = 'Conditional'

    class BiconditionalDesignated(MaterialBiconditionalDesignated):
        """
        Same as for the material biconditional designated.
        """

        operator = 'Biconditional'

    class BiconditionalNegatedDesignated(MaterialBiconditionalNegatedDesignated):
        """
        Same as for the negated material biconditional designated.
        """

        operator = 'Biconditional'

    class BiconditionalUndesignated(MaterialBiconditionalUndesignated):
        """
        Same as for the material biconditional undesignated.
        """

        operator = 'Biconditional'

    class BiconditionalNegatedUndesignated(MaterialBiconditionalNegatedUndesignated):
        """
        Same as for the negated material biconditional undesignated.
        """

        operator = 'Biconditional'

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

        k3.TableauxRules.Closure,
        fde.TableauxRules.Closure,

        # non-branching rules

        AssertionDesignated,
        AssertionUndesignated,
        AssertionNegatedDesignated,
        AssertionNegatedUndesignated,
        ConjunctionDesignated, 
        DisjunctionNegatedDesignated,
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
        # reduction rules (thus, non-branching)
        MaterialConditionalDesignated,
        MaterialConditionalUndesignated,
        MaterialConditionalNegatedDesignated,
        MaterialConditionalNegatedUndesignated,
        ConditionalDesignated,
        ConditionalUndesignated,
        ConditionalNegatedDesignated,
        ConditionalNegatedUndesignated,
        MaterialBiconditionalDesignated,
        MaterialBiconditionalUndesignated,
        MaterialBiconditionalNegatedDesignated,
        MaterialBiconditionalNegatedUndesignated,
        BiconditionalDesignated,
        BiconditionalUndesignated,
        BiconditionalNegatedDesignated,
        BiconditionalNegatedUndesignated,

        # two-branching rules
        ConjunctionUndesignated,

        # three-branching rules
        DisjunctionDesignated,
        DisjunctionUndesignated,
        ConjunctionNegatedDesignated,
        ConjunctionNegatedUndesignated,

        # four-branching rules
        DisjunctionNegatedUndesignated
    ]