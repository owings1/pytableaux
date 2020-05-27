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
# pytableaux - Gappy Object 3-valued Logic
"""
Semantics
=========

GO is a 3-valued logic (**T**, **F**, and **N**) with non-standard readings of
disjunction and conjunction.

Truth Tables
------------

The truth-functional operators are defined via tables below.

/truth_tables/

Note that, given the tables above, conjunctions and disjunctions always have a classical
value (**T** or **F**). This means that only atomic sentences (with zero or more negations)
can have the non-classical **N** value.

This property of "classical containment" means, that we can define a conditional operator
that satisfies Identity P{A $ A}. It also allows us to give a formal description of
a subset of sentences that obey all principles of classical logic. For example, although
the Law of Excluded Middle fails for atomic sentences P{A V ~A}, complex sentences -- those
with at least one binary connective -- do obey the law: P{(A V A) V ~(A V A)}.

Predication
-----------

**Predicate Sentences** are handled the same way as in `K3 Predication`_.

Quantification
--------------

**Quantification** is defined as follows:

- **Universal Quantifier**: P{LxFx} has the value **T** iff everything is in 
  the extension of *F*, else it has the value *F*.

- **Existential Quantifier**: P{XxFx} has the value **T** iff
  something is in the extension of *F*, else it has the value *F*.

This is in accordance with thinking of the universal and existential quantifiers
as generalized conjunction and disjunction, respectively. Since conjunctions and
disjunctions can only have a classical value (**T** or **F**), so, too, must
quantified sentences.

Logical Consequence
-------------------

**Logical Consequence** is defined just like in `CPL`_ and `K3`_:

- *C* is a **Logical Consequence** of *A* iff all cases where the value of *A* is **T**
  are cases where *C* also has the value **T**.

Notes
-----

- GO has some similarities to `K3`_. Material Identity P{A $ A} and the
  Law of Excluded Middle P{A V ~A} fail.

- Unlike `K3`_, there are logical truths, e.g. The Law of Non Contradiction P{~(A & ~A)}.

- GO contains an additional conditional operator besides the material conditional,
  which is similar to `L3`_. However, this conditional is *non-primitive*, unlike `L3`_,
  and it obeys contraction (P{A $ (A $ B)} implies P{A $ B}).

- This logic was developed as part of my dissertation, `Indeterminacy and Logical Atoms`_
  at the University of Connecticut, under `Professor Jc Beall`_.


.. _Professor Jc Beall: http://entailments.net

.. _Indeterminacy and Logical Atoms: https://bitbucket.org/owings1/dissertation/raw/master/output/dissertation.pdf

.. _K3: k3.html

.. _K3 Predication: k3.html#predication

.. _L3: l3.html

.. _B3E: b3e.html

.. _FDE: fde.html

.. _CPL: cpl.html
"""
name = 'GO'
title = 'Gappy Object 3-valued Logic'
description = 'Three-valued logic (True, False, Neither) with classical-like binary operators'
tags_list = ['many-valued', 'gappy', 'non-modal', 'first-order']
tags = set(tags_list)
category = 'Many-valued'
category_display_order = 5

import logic, math, examples
from . import fde, k3, b3e
from logic import negate, operate, quantify

def gap(v):
    return min(v, 1 - v)

def crunch(v):
    return v - gap(v)

class Model(k3.Model):
    def truth_function(self, operator, a, b=None):
        if operator == 'Assertion':
            return crunch(a)
        elif operator == 'Disjunction':
            return max(crunch(a), crunch(b))
        elif operator == 'Conjunction':
            return min(crunch(a), crunch(b))
        elif operator == 'Conditional':
            return crunch(max(1 - a, b, gap(a) + gap(b)))
        return super(Model, self).truth_function(operator, a, b)

class TableauxSystem(fde.TableauxSystem):
    """
    GO's Tableaux System inherits directly from `FDE`_'s, employing designation markers,
    and building the trunk in the same way.
    """
    pass

class TableauxRules(object):
    """
    The closure rules for GO are the `FDE closure rule`_, and the `K3 closure rule`_.
    Most of the operators rules are unique to GO, with a few rules that are
    the same as `FDE`_. The rules for assertion mirror those of `B3E`_.
    
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

    class AssertionNegatedDesignated(b3e.TableauxRules.AssertionNegatedDesignated):
        """
        This rule is the same as the `B3E AssertionDesignated rule`_.

        .. _B3E AssertionDesignated rule: b3e.html#logics.b3e.TableauxRules.AssertionDesignated
        """
        pass

    class AssertionUndesignated(b3e.TableauxRules.AssertionUndesignated):
        """
        This rule is the same as the `B3E AssertionUndesignated rule`_.

        .. _B3E AssertionUndesignated rule: b3e.html#logics.b3e.TableauxRules.AssertionUndesignated
        """
        pass

    class AssertionNegatedUndesignated(b3e.TableauxRules.AssertionNegatedUndesignated):
        """
        This rule is the same as the `B3E AssertionNegatedUndesignated rule`_.

        .. _B3E AssertionNegatedUndesignated rule: b3e.html#logics.b3e.TableauxRules.AssertionNegatedUndesignated
        """
        pass

    class ConjunctionDesignated(fde.TableauxRules.ConjunctionDesignated):
        """
        This rule is the same as the `FDE ConjunctionDesignated rule`_.

        .. _FDE ConjunctionDesignated rule: fde.html#logics.fde.TableauxRules.ConjunctionDesignated
        """
        pass

    class ConjunctionNegatedDesignated(logic.TableauxSystem.ConditionalNodeRule):
        """
        From an unticked, designated, negated conjunction node *n* on a branch *b*,
        make two new branches *b'* and *b''* from *b*, add an undesignated node to
        *b'* with one conjunct, and an undesignated node to *b''* with the other
        conjunct, then tick *n*.
        """

        negated     = True
        operator    = 'Conjunction'
        designation = True

        def apply_to_node(self, node, branch):
            b1 = branch
            b2 = self.tableau.branch(branch)
            s = node.props['sentence'].operand
            b1.add({ 'sentence' : s.lhs, 'designated' : False }).tick(node)
            b2.add({ 'sentence' : s.rhs, 'designated' : False }).tick(node)

    class ConjunctionUndesignated(logic.TableauxSystem.ConditionalNodeRule):
        """
        From an unticked, undesignated conjunction node *n* on a branch *b*, add a
        designated node to *b* with the negation of the conjunction, then tick *n*.
        """

        operator    = 'Conjunction'
        designation = False

        def apply_to_node(self, node, branch):
            branch.add({ 'sentence': negate(node.props['sentence']), 'designated' : True }).tick(node)

    class ConjunctionNegatedUndesignated(logic.TableauxSystem.ConditionalNodeRule):
        """
        From an unticked, undesignated, negated conjunction node *n* on a branch *b*,
        add a designated node to *b* with the (un-negated) conjuction, then tick *n*.
        """

        negated     = True
        operator    = 'Conjunction'
        designation = False

        def apply_to_node(self, node, branch):
            s = self.sentence(node)
            branch.add({ 'sentence' : s, 'designated' : True }).tick(node)

    class DisjunctionDesignated(fde.TableauxRules.DisjunctionDesignated):
        """
        This rule is the same as the `FDE DisjunctionDesignated rule`_.

        .. _FDE DisjunctionDesignated rule: fde.html#logics.fde.TableauxRules.DisjunctionDesignated
        """
        pass
        
    class DisjunctionNegatedDesignated(logic.TableauxSystem.ConditionalNodeRule):
        """
        From an unticked, designated, negated disjunction node *n* on a branch *b*,
        add an undesignated node to *b* for each disjunct, then tick *n*.
        """

        negated     = True
        operator    = 'Disjunction'
        designation = True

        def apply_to_node(self, node, branch):
            s = node.props['sentence'].operand
            branch.update([
                { 'sentence': s.lhs, 'designated' : False },
                { 'sentence': s.rhs, 'designated' : False }
            ]).tick(node)

    class DisjunctionUndesignated(ConjunctionUndesignated):
        """
        From an unticked, undesignated disjunction node *n* on a branch *b*, add a
        designated node to *b* with the negation of the disjunction, then tick *n*.
        """

        operator = 'Disjunction'

    class DisjunctionNegatedUndesignated(ConjunctionNegatedUndesignated):
        """
        From an unticked, undesignated, negated disjunction node *n* on a branch *b*,
        add a designated node to *b* with the (un-negated) disjunction, then tick *n*.
        """

        operator = 'Disjunction'

    class MaterialConditionalDesignated(fde.TableauxRules.MaterialConditionalDesignated):
        """
        This rule is the same as the `FDE MaterialConditionalDesignated rule`_.

        .. _FDE MaterialConditionalDesignated rule: fde.html#logics.fde.TableauxRules.MaterialConditionalDesignated
        """
        pass
        
    class MaterialConditionalNegatedDesignated(logic.TableauxSystem.ConditionalNodeRule):
        """
        From an unticked, designated, negated material conditional node *n* on a branch
        *b*, add an undesignated node with the negation of the antecedent, and an
        undesignated node with the consequent to *b*, then tick *n*.
        """

        negated     = True
        operator    = 'Material Conditional'
        designation = True

        def apply_to_node(self, node, branch):
            s = node.props['sentence'].operand
            branch.update([
                { 'sentence' : negate(s.lhs) , 'designated' : False },
                { 'sentence' :        s.rhs  , 'designated' : False }
            ]).tick(node)

    class MaterialConditionalUndesignated(ConjunctionUndesignated):
        """
        From an unticked, undesignated, material conditional node *n* on a branch *b*,
        add a designated node to *b* with the negation of the conditional, then tick *n*.
        """

        operator = 'Material Conditional'

    class MaterialConditionalNegatedUndesignated(ConjunctionNegatedUndesignated):
        """
        From an unticked, undesignated, negated material conditional node *n* on a branch
        *b*, add a designated node with the (un-negated) conditional to *b*, then tick *n*.
        """

        operator = 'Material Conditional'

    class MaterialBiconditionalDesignated(fde.TableauxRules.MaterialBiconditionalDesignated):
        """
        This rule is the same as the `FDE MaterialBiconditionalDesignated rule`_.

        .. _FDE MaterialBiconditionalDesignated rule: fde.html#logics.fde.TableauxRules.MaterialBiconditionalDesignated
        """
        pass
        
    class MaterialBiconditionalNegatedDesignated(logic.TableauxSystem.ConditionalNodeRule):
        """
        From an unticked, designated, negated, material biconditional node *n* on a branch
        *b*, make two branches *b'* and *b''* from *b*. On *b'* add undesignated nodes for
        the negation of the antecent, and for the consequent. On *b''* add undesignated
        nodes for the antecedent, and for the negation of the consequent. Then tick *n*.
        """

        negated     = True
        operator    = 'Material Biconditional'
        designation = True

        def apply_to_node(self, node, branch):
            s = node.props['sentence'].operand
            b1 = branch
            b2 = self.tableau.branch(branch)
            b1.update([
                { 'sentence' : negate(s.lhs) , 'designated' : False },
                { 'sentence' :        s.rhs  , 'designated' : False },
            ]).tick(node)
            b2.update([
                { 'sentence' :        s.lhs , 'designated' : False },
                { 'sentence' : negate(s.rhs), 'designated' : False }
            ]).tick(node)

    class MaterialBiconditionalUndesignated(ConjunctionUndesignated):
        """
        From an unticked, undesignated, material biconditional node *n* on a branch *b*,
        add a designated node to *b* with the negation of the biconditional, then tick *n*.
        """

        operator = 'Material Biconditional'

    class MaterialBiconditionalNegatedUndesignated(ConjunctionNegatedUndesignated):
        """
        From an unticked, undesignated, negated material biconditional node *n* on a branch
        *b*, add a designated node to *b* with the (un-negated) biconditional, then tick *n*.
        """

        operator = 'Material Biconditional'

    class ConditionalDesignated(logic.TableauxSystem.ConditionalNodeRule):
        """
        From an unticked, designated, conditional node *n* on a branch *b*, make two branches
        *b'* and *b''* from *b*. On *b'* add a designated node with a disjunction of the
        negated antecedent and the consequent. On *b''* add undesignated nodes for the
        antecedent, consequent, and their negations. Then tick *n*.
        """

        operator    = 'Conditional'
        designation = True

        def apply_to_node(self, node, branch):
            s = node.props['sentence']
            disj = operate('Disjunction', [negate(s.lhs), s.rhs])
            b1 = branch
            b2 = self.tableau.branch(branch)
            b1.add({ 'sentence' : disj, 'designated' : True }).tick(node)
            b2.update([
                { 'sentence' :        s.lhs  , 'designated' : False },
                { 'sentence' :        s.rhs  , 'designated' : False },
                { 'sentence' : negate(s.lhs) , 'designated' : False },
                { 'sentence' : negate(s.rhs) , 'designated' : False }
            ]).tick(node)

    class ConditionalNegatedDesignated(logic.TableauxSystem.ConditionalNodeRule):
        """
        From an unticked, designated, negated conditional node *n* on a branch *b*, make
        two branches *b'* and *b''* from *b*. On *b'* add a designated node with the
        antecedent, and an undesignated node with the consequent. On *b''* add an
        undesignated node with the negation of the antencedent, and a designated node
        with the negation of the consequent. Then tick *n*.
        """

        negated     = True
        operator    = 'Conditional'
        designation = True

        def apply_to_node(self, node, branch):
            b1 = branch
            b2 = self.tableau.branch(branch)
            s = node.props['sentence'].operand
            b1.update([
                { 'sentence' : s.lhs, 'designated' : True  },
                { 'sentence' : s.rhs, 'designated' : False }
            ]).tick(node)
            b2.update([
                { 'sentence' : negate(s.lhs), 'designated' : False  },
                { 'sentence' : negate(s.rhs), 'designated' : True }
            ]).tick(node)

    class ConditionalUndesignated(ConjunctionUndesignated):
        """
        From an unticked, undesignated conditional node *n* on a branch *b*, add a
        designated node to *b* with the negation of the conditional, then tick *n*.
        """

        operator = 'Conditional'

    class ConditionalNegatedUndesignated(ConjunctionNegatedUndesignated):
        """
        From an unticked, undesignated, negated conditional node *n* on a branch *b*,
        add a designated node to *b* with the (un-negated) conditional, then tick *n*.
        """

        operator = 'Conditional'

    class BiconditionalDesignated(logic.TableauxSystem.ConditionalNodeRule):
        """
        From an unticked, designated biconditional node *n* on a branch *b*, add two
        designated conditional nodes to *b*, one with the operands of the biconditional,
        and the other with the reversed operands. Then tick *n*.
        """

        operator    = 'Biconditional'
        designation = True

        def apply_to_node(self, node, branch):
            s = node.props['sentence']
            branch.update([
                { 'sentence' : operate('Conditional', [s.lhs, s.rhs]), 'designated' : True },
                { 'sentence' : operate('Conditional', [s.rhs, s.lhs]), 'designated' : True }
            ]).tick(node)

    class BiconditionalNegatedDesignated(logic.TableauxSystem.ConditionalNodeRule):
        """
        From an unticked, designated, negated biconditional node *n* on a branch *b*, make
        two branches *b'* and *b''* from *b*. On *b'* add a designated negated conditional
        node with the operands of the biconditional. On *b''* add a designated negated
        conditional node with the reversed operands of the biconditional. Then tick *n*.
        """

        negated     = True
        operator    = 'Biconditional'
        designation = True

        def apply_to_node(self, node, branch):
            b1 = branch
            b2 = self.tableau.branch(branch)
            s = node.props['sentence'].operand
            b1.add({ 'sentence' : negate(operate('Conditional', [s.lhs, s.rhs])), 'designated': True }).tick(node)
            b2.add({ 'sentence' : negate(operate('Conditional', [s.rhs, s.lhs])), 'designated': True }).tick(node)

    class BiconditionalUndesignated(ConjunctionUndesignated):
        """
        From an unticked, undesignated biconditional node *n* on a branch *b*, add a
        designated node to *b* with the negation of the biconditional, then tick *n*.
        """

        operator = 'Biconditional'

    class BiconditionalNegatedUndesignated(ConjunctionNegatedUndesignated):
        """
        From an unticked, undesignated, negated biconditional node *n* on a branch *b*,
        add a designated node to *b* with the (un-negated) biconditional, then tick *n*.
        """

        operator = 'Biconditional'

    class ExistentialDesignated(fde.TableauxRules.ExistentialDesignated):
        """
        This rule is the same as the `FDE ExistentialDesignated rule`_.

        .. _FDE ExistentialDesignated rule: fde.html#logics.fde.TableauxRules.ExistentialDesignated
        """
        pass
        
    class ExistentialNegatedDesignated(logic.TableauxSystem.ConditionalNodeRule):
        """
        From an unticked, designated negated existential node *n* on a branch *b*,
        add a designated node *n'* to *b* with a universal sentence consisting of
        disjunction, whose first disjunct is the negated inner sentence of *n*,
        and whose second disjunct is the negation of a disjunction *d*, where the
        first disjunct of *d* is the inner sentence of *n*, and the second disjunct
        of *d* is the negation of the inner setntence of *n*. Then tick *n*.
        """
        quantifier  = 'Existential'
        negated     = True
        designation = True
        convert_to  = 'Universal'

        def apply_to_node(self, node, branch):
            s = self.sentence(node)
            d = self.designation
            v = s.variable
            si = s.sentence

            si_lem_fail = negate(operate('Disjunction', [si, negate(si)]))
            si_disj = operate('Disjunction', [negate(si), si_lem_fail])
            branch.add({'sentence': quantify(self.convert_to, v, si_disj), 'designated': d}).tick(node)

    class ExistentialUndesignated(ConjunctionUndesignated):
        """
        From an unticked, undesignated existential node *n* on a branch *b*, add a designated
        node to *b* with the negation of the existential sentence, then tick *n*.
        """

        operator   = None
        quantifier = 'Existential'

    class ExistentialNegatedUndesignated(ConjunctionNegatedUndesignated):
        """
        From an unticked, undesignated negated existential node *n* on a branch *b*, add a designated
        node to *b* with the negated existential sentence (negatum), then tick *n*.
        """

        operator   = None
        quantifier = 'Existential'


    class UniversalDesignated(fde.TableauxRules.UniversalDesignated):
        """
        This rule is the same as the `FDE UniversalDesignated rule`_.

        .. _FDE UniversalDesignated rule: fde.html#logics.fde.TableauxRules.UniversalDesignated
        """
        pass
        
    class UniversalNegatedDesignated(logic.TableauxSystem.ConditionalNodeRule):
        """
        From an unticked, designated universal existential node *n* on a branch *b*, make two branches
        *b'* and *b''* from *b*. On *b'*, add a designtated node with the standard 
        translation of the sentence on *b*. For *b''*, substitute a new constant *c* for
        the quantified variable, and add two undesignated nodes to *b''*, one with the
        substituted inner sentence, and one with its negation, then tick *n*.
        """
        quantifier  = 'Universal'
        designation = True
        negated     = True
        convert_to  = 'Existential'

        def apply_to_node(self, node, branch):
            s = self.sentence(node)
            d = self.designation
            v = s.variable

            c = branch.new_constant()
            si = s.sentence
            ss = s.substitute(c, v)

            b1 = branch
            b2 = self.tableau.branch(branch)
            b1.add({'sentence': quantify(self.convert_to, v, negate(si)), 'designated': d}).tick(node)
            b2.update([
                {'sentence': ss, 'designated': not d},
                {'sentence': negate(ss), 'designated': not d}
            ]).tick(node)

    class UniversalUndesignated(ExistentialUndesignated):
        """
        From an unticked, undesignated universal node *n* on a branch *b*, add a designated
        node to *b* with the negation of the universal sentence, then tick *n*.
        """

        quantifier = 'Universal'

    class UniversalNegatedUndesignated(ExistentialNegatedUndesignated):
        """
        From an unticked, undesignated negated universal node *n* on a branch *b*, add a designated
        node to *b* with the negated universal sentence (negatum), then tick *n*.
        """

        quantifier = 'Universal'

    rules = [

        # closure rules
        fde.TableauxRules.Closure,
        k3.TableauxRules.Closure,

        # non-branching rules
        AssertionDesignated,
        AssertionUndesignated,
        AssertionNegatedDesignated,
        AssertionNegatedUndesignated,
        ConjunctionDesignated,
        ConjunctionUndesignated,
        ConjunctionNegatedUndesignated,
        DisjunctionNegatedDesignated,
        DisjunctionUndesignated,
        DisjunctionNegatedUndesignated,
        MaterialConditionalNegatedDesignated,
        MaterialConditionalUndesignated,
        MaterialConditionalNegatedUndesignated,
        MaterialBiconditionalUndesignated,
        MaterialBiconditionalNegatedUndesignated,
        ConditionalUndesignated,
        ConditionalNegatedUndesignated,
        BiconditionalUndesignated,
        BiconditionalNegatedUndesignated,
        BiconditionalDesignated,
        ExistentialDesignated,
        ExistentialNegatedDesignated,
        ExistentialUndesignated,
        ExistentialNegatedUndesignated,
        UniversalDesignated,
        UniversalUndesignated,
        UniversalNegatedUndesignated,
        DoubleNegationDesignated,
        DoubleNegationUndesignated,

        # branching rules
        DisjunctionDesignated,
        ConjunctionNegatedDesignated,
        MaterialConditionalDesignated,
        MaterialBiconditionalDesignated,
        MaterialBiconditionalNegatedDesignated,
        ConditionalDesignated,
        ConditionalNegatedDesignated,
        BiconditionalNegatedDesignated,
        UniversalNegatedDesignated,
    ]