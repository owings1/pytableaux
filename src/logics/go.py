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
# pytableaux - Gappy Object 3-valued Logic
"""
GO is a 3-valued (True, False, Neither) logic, with non-standard readings of
disjunction and conjunction. It has some similarities to K3, e.g. Material
Identity and the Law of Excluded Middle fail, however, unlike K3, there are
logical truths. It contains an additional conditional operator besides the
material conditional, which is similar to L3. However, this conditional is
*non-primitive*, and obeys contraction (if A and (if A then B) implies if A then B).

Semantics
---------

The truth-functional operators are defined via tables below.

Note that, given the tables below, conjunctions and disjunctions always have a classical
value (True or False). This means that only atomic sentences (with zero or more negations)
can have the Neither value.

This property of "classical containment" means, that we can define a conditional operator
that satisfies Identity (if A then A). It also allows us to give a formal description of
a subset of sentences that obey all principles of classical logic. For example, although
the Law of Excluded Middle fails for atomic sentences (A or not-A), complex sentences -- those
with at least one binary connective -- do obey the law: (A or A) or not-(A or A).

**Predicate Sentences** are handled the same way as in K3.

**Quantification** is defined in a different way, in accordance with thinking of the
universal and existential quantifiers as generalized conjunction and disjunction,
respectively.

- **Universal Quantifier**: *for all x, x is F* has the value **T** iff everything is in 
  the extension of *F*, else it has the value *F*.

- **Existential Quantifier**: *there exists an x that is F* has the value **T** iff
  something is in the extension of *F*, else it has the value *F*.


References
----------

This logic was developed as part of my dissertation, `Indeterminacy and Logical Atoms`_
at the University of Connecticut, under `Professor Jc Beall`_.


.. _Professor Jc Beall: http://entailments.net

.. _Indeterminacy and Logical Atoms: https://bitbucket.org/owings1/dissertation/raw/master/output/dissertation.pdf

"""
name = 'GO'
description = 'Gappy Object 3-valued Logic'

# Syllogism ?
# Universal Predicate Syllogism ?
def example_validities():
    return set([
        'Addition'                       ,
        'Biconditional Elimination 1'    ,
        'Biconditional Elimination 2'    ,
        'Biconditional Identity'         ,
        'Conditional Contraction'        ,
        'Conditional Identity'           ,
        'Conditional Modus Ponens'       ,
        'Conditional Modus Tollens'      ,
        'Conditional Pseudo Contraction' ,
        'DeMorgan 3'                     ,
        'DeMorgan 4'                     ,
        'Disjunctive Syllogism'          ,
        'Existential Syllogism'          ,
        'Law of Non-contradiction'       ,
        'Material Contraction'           ,
        'Material Modus Ponens'          ,
        'Material Modus Tollens'         ,
        'Material Pseudo Contraction'    ,
        'Modal Platitude 1'              ,
        'Modal Platitude 2'              ,
        'Modal Platitude 3'              ,
        'Simplification'                 ,
    ])

def example_invalidities():
    import cfol
    args = cfol.example_invalidities()
    args.update([
        'DeMorgan 1'                      ,
        'DeMorgan 2'                      ,
        'Law of Excluded Middle'          ,
        'Material Biconditional Identity' ,
        'Material Identity'               ,
        'Material Identity'               ,
    ])
    return args

import logic, fde, k3, math
from logic import negate, operate

truth_values = k3.truth_values
truth_value_chars = k3.truth_value_chars
designated_values = k3.designated_values
undesignated_values = k3.undesignated_values
unassigned_value = k3.unassigned_value
truth_functional_operators = fde.truth_functional_operators

def gap(v):
    return min(v, 1 - v)

def crunch(v):
    return v - gap(v)
        
def truth_function(operator, a, b=None):
    if operator == 'Assertion':
        return crunch(a)
    elif operator == 'Negation':
        return 1 - a
    elif operator == 'Disjunction':
        return max(crunch(a), crunch(b))
    elif operator == 'Conjunction':
        return min(crunch(a), crunch(b))
    elif operator == 'Material Conditional':
        return truth_function('Disjunction', 1 - a, b)
    elif operator == 'Material Biconditional':
        return truth_function('Conjunction', truth_function('Disjunction', 1 - a, b), truth_function('Disjunction', 1 - b, a))
    elif operator == 'Conditional':
        return crunch(max(1 - a, b, gap(a) + gap(b)))
    elif operator == 'Biconditional':
        return truth_function('Conjunction', truth_function('Conditional', a, b), truth_function('Conditional', b, a))

class TableauxSystem(fde.TableauxSystem):
    """
    GO's Tableaux System inherits directly from FDE's.
    """
    pass

class TableauxRules(object):
    """
    The rules for GO consist of the rules for K3, except for those defined below.
    """

    class ConjunctionUndesignated(logic.TableauxSystem.ConditionalNodeRule):
        """
        From an unticked, undesignated conjunction node *n* on a branch *b*, add a
        designated node to *b* with the negation of the conjunction, then tick *n*.
        """

        operator    = 'Conjunction'
        designation = False

        def apply_to_node(self, node, branch):
            branch.add({ 'sentence': negate(node.props['sentence']), 'designated' : True }).tick(node)

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

    class ExistentialUndesignated(ConjunctionUndesignated):
        """
        From an unticked, undesignated existential node *n* on a branch *b*, add a designated
        node to *b* with the negation of the existential sentence, then tick *n*.
        """

        operator   = None
        quantifier = 'Existential'

    class UniversalUndesignated(ExistentialUndesignated):
        """
        From an unticked, undesignated universal node *n* on a branch *b*, add a designated
        node to *b* with the negation of the universal sentence, then tick *n*.
        """

        quantifier = 'Universal'

    class ExistentialNegatedDesignated(object):
        # needs implemented
        pass

    class ExistentialNegatedUndesignated(object):
        pass

    class UniversalNegatedDesignated(object):
        # """
        #         not(Forall x: Fx) is True. Thus (Forall x: Fx) is False.
        #         """
        # needs implmented
        pass

    class UniversalNegatedUndesignated(object):
        pass

    class AssertionUndesignated(logic.TableauxSystem.ConditionalNodeRule):
        """
        From an unticked, undesignated assertion node *n* on a branch *b*, add
        an undesignated node to *b* with the assertion of *n*, then tick *n*.
        """

        operator = 'Assertion'
        designation = False
        def apply_to_node(self, node, branch):
            s = self.sentence(node)
            d = self.designation
            branch.add({ 'sentence' : s.operand, 'designated' : d }).tick(node)

    class AssertionNegatedDesignated(logic.TableauxSystem.ConditionalNodeRule):
        """
        From an unticked, designated, negated assertion node *n* on a branch *b*,
        add an undesignated node to *b* with the assertion of *n*, then tick *n*.
        """
        operator    = 'Assertion'
        negated     = True
        designation = True

        def apply_to_node(self, node, branch):
            s = self.sentence(node)
            d = self.designation
            branch.add({ 'sentence' : s.operand, 'designated' : not d }).tick(node)

    class AssertionNegatedUndesignated(logic.TableauxSystem.ConditionalNodeRule):
        """
        From an unticked, undesignated, negated assertion node *n* on a branch *b*, add
        an designated node to *b* with the assertion of *n*, then tick *n*.
        """

        operator    = 'Assertion'
        negated     = True
        designation = False
        def apply_to_node(self, node, branch):
            s = self.sentence(node)
            d = self.designation
            branch.add({ 'sentence' : s.operand, 'designated' : d }).tick(node)

    rules = [

        # closure rules
        fde.TableauxRules.Closure,
        k3.TableauxRules.Closure,

        # non-branching rules
        fde.TableauxRules.AssertionDesignated,
        AssertionUndesignated,
        AssertionNegatedDesignated,
        AssertionNegatedUndesignated,
        fde.TableauxRules.ConjunctionDesignated,
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
        fde.TableauxRules.UniversalDesignated,
        fde.TableauxRules.ExistentialDesignated,
        UniversalUndesignated,
        ExistentialUndesignated,
        fde.TableauxRules.DoubleNegationDesignated,
        fde.TableauxRules.DoubleNegationUndesignated,

        # branching rules
        fde.TableauxRules.DisjunctionDesignated,
        ConjunctionNegatedDesignated,
        fde.TableauxRules.MaterialConditionalDesignated,
        fde.TableauxRules.MaterialBiconditionalDesignated,
        MaterialBiconditionalNegatedDesignated,
        ConditionalDesignated,
        ConditionalNegatedDesignated,
        BiconditionalNegatedDesignated

    ]