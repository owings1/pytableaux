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
# pytableaux - First Degree Entailment Logic

"""
FDE is a 4-valued logic (True, False, Neither and Both).

Semantics
---------

Truth-functional operators are defined via truth tables (below).

**Predicate Sentences** like *a is F* are handled via a predicate's *extension* and *anti-extension*:

- *a is F* iff the object denoted by *a* is in the extension of *F*.

- it's not the case that *a is F* iff the object denoted by *a* is in the anti-extension of *F*.

There is no exclusivity or exhaustion constraint on a predicate's extension/anti-extension, so
there can be cases where an object is in neither or both. Thus **Quantification** can be thought
of along these lines:

- **Universal Quantifier**: *for all x, x is F* has the value:

    - **T** iff everything is in the extension of *F* and its anti-extension is empty.
    - **B** iff everything is in the extension of *F* and its anti-extension is non-empty.
    - **N** iff not everything is in the extension of *F* and its anti-extension is empty.
    - **F** iff not everything is in the extension of *F* and its anti-extension is non-empty.

- **Existential Quantifier**: ``there exists an x that is F := not (for all x, not (x is F))``

*C* is a **Logical Consequence** of *A* iff all cases where the value of *A* is either **T** or
**B** (the *designated* values) are cases where *C* also has a *designated* value.

Notes
-----

Some notable features of FDE include:

* No logical truths. The means that the law of excluded middle, and the law of non-contradiction
  fail, as well as conditional identity (if A then A).
  
* Failure of Modus Ponens, Modus Tollens, Disjunctive Syllogism, and other Classical validities.

* DeMorgan laws are valid, as well as conditional contraction.

For futher reading see:

- `Stanford Encyclopedia on Paraconsistent Logic`_

.. _Stanford Encyclopedia on Paraconsistent Logic: http://plato.stanford.edu/entries/logic-paraconsistent/

"""
name = 'FDE'
description = 'First Degree Entailment'

def example_validities():
    return set([
        'Addition'                ,
        'Conditional Contraction' ,
        'DeMorgan 1'              ,
        'DeMorgan 2'              ,
        'DeMorgan 3'              ,
        'DeMorgan 4'              ,
        'Material Contraction'    ,
        'Modal Platitude 1'       ,
        'Modal Platitude 2'       ,
        'Modal Platitude 3'       ,
        'Simplification'          ,
    ])

def example_invalidities():
    # Everything invalid in K3 or LP is also invalid in FDE.
    import k3, lp
    args = k3.example_invalidities()
    args.update(lp.example_invalidities())
    return args

import logic, examples
from logic import negate, quantify, atomic

truth_values = [0, 0.25, 0.75, 1]
truth_value_chars = {
    0    : 'F',
    0.25 : 'N',
    0.75 : 'B',
    1    : 'T'
}
designated_values = set([0.75, 1])
undesignated_values = set([0, 0.25])
unassigned_value = 0.25

truth_functional_operators = set([
    'Assertion'                 ,
    'Negation'                  ,
    'Conjunction'               ,
    'Disjunction'               ,
    'Material Conditional'      ,
    'Conditional'               ,
    'Material Biconditional'    ,
    'Biconditional'             ,
])

def truth_function(operator, a, b=None):
    if operator == 'Assertion':
        return a
    if operator == 'Negation':
        if a == 0 or a == 1:
            return 1 - a
        return a
    elif operator == 'Conjunction':
        return min(a, b)
    elif operator == 'Disjunction':
        return max(a, b)
    elif operator == 'Material Conditional' or operator == 'Conditional':
        return max(truth_function('Negation', a), b)
    elif operator == 'Material Biconditional' or  operator == 'Biconditional':
        return min(max(truth_function('Negation', a), b), max(truth_function('Negation', b), a))

class Model(object):

    pass
class TableauxSystem(logic.TableauxSystem):
    """
    Nodes for FDE have a boolean *designation* property, and a branch is closed iff
    the same sentence appears on both a designated and undesignated node. This allows
    for both a sentence and its negation to appear as designated (xor undesignated)
    on an open branch.
    """

    @staticmethod
    def build_trunk(tableau, argument):
        """
        To build the trunk for an argument, add a designated node for each premise, and
        an undesignated node for the conclusion.
        """

        branch = tableau.branch()
        for premise in argument.premises:
            branch.add({ 'sentence' : premise, 'designated' : True, 'world' : None })
        branch.add({ 'sentence' : argument.conclusion, 'designated' : False, 'world': None })

class TableauxRules(object):
    """
    In general, rules for connectives consist of four rules per connective:
    a designated rule, an undesignated rule, a negated designated rule, and a negated
    undesignated rule. The special case of negation has a total of two rules which apply
    to double negation only, one designated rule, and one undesignated rule.
    """

    class Closure(logic.TableauxSystem.ClosureRule):
        """
        A branch closes when a sentence appears on a node marked *designated*,
        and the same sentence appears on a node marked *undesignated*.
        """

        def applies_to_branch(self, branch):
            for node in branch.get_nodes():
                n = branch.find({ 'sentence' : node.props['sentence'], 'designated' : not node.props['designated'] })
                if n != None:
                    return {'nodes' : set([node, n]), 'type' : 'Nodes'}
            return False

        def example(self):
            a = atomic(0, 0)
            self.tableau.branch().update([
                { 'sentence' : a, 'designated' : True  },
                { 'sentence' : a, 'designated' : False }
            ])

    class ConjunctionDesignated(logic.TableauxSystem.ConditionalNodeRule):
        """
        From an unticked designated conjunction node *n* on a branch *b*, for each conjunct
        *c*, add a designated node with *c* to *b*, then tick *n*.
        """

        operator    = 'Conjunction'
        designation = True

        def apply_to_node(self, node, branch):
            s = self.sentence(node)
            d = self.designation
            for conjunct in s.operands:
                branch.add({ 'sentence' : conjunct, 'designated' : d })
            branch.tick(node)

    class ConjunctionNegatedDesignated(logic.TableauxSystem.ConditionalNodeRule):
        """
        From an unticked designated negated conjunction node *n* on a branch *b*, for each conjunct
        *c*, make a new branch *b'* from *b* and add a designated node with the negation of *c* to *b'*,
        then tick *n*.
        """

        negated     = True
        operator    = 'Conjunction'
        designation = True

        def apply_to_node(self, node, branch):
            s = self.sentence(node)
            d = self.designation
            b1 = branch
            b2 = self.tableau.branch(branch)
            b1.add({ 'sentence' : negate(s.lhs), 'designated' : d }).tick(node)
            b2.add({ 'sentence' : negate(s.rhs), 'designated' : d }).tick(node)


    class ConjunctionUndesignated(logic.TableauxSystem.ConditionalNodeRule):
        """
        From an unticked undesignated conjunction node *n* on a branch *b*, for each conjunct
        *c*, make a new branch *b'* from *b* and add an undesignated node with *c* to *b'*,
        then tick *n*.
        """

        operator    = 'Conjunction'
        designation = False

        def apply_to_node(self, node, branch):
            s = self.sentence(node)
            d = self.designation
            b1 = branch
            b2 = self.tableau.branch(branch)
            b1.add({ 'sentence' : s.lhs, 'designated' : d }).tick(node)
            b2.add({ 'sentence' : s.rhs, 'designated' : d }).tick(node)

    class ConjunctionNegatedUndesignated(logic.TableauxSystem.ConditionalNodeRule):
        """
        From an unticked undesignated negated conjunction node *n* on a branch *b*, for each conjunct
        *c*, add an undesignated node with the negation of *c* to *b*, then tick *n*.
        """

        negated     = True
        operator    = 'Conjunction'
        designation = False

        def apply_to_node(self, node, branch):
            s = self.sentence(node)
            d = self.designation
            for conjunct in s.operands:
                branch.add({ 'sentence' : negate(conjunct), 'designated' : d })
            branch.tick(node)

    class DisjunctionDesignated(ConjunctionUndesignated):
        """
        From an unticked designated disjunction node *n* on a branch *b*, for each disjunt
        *d*, make a new branch *b'* from *b* and add a designated node with *d* to *b'*,
        then tick *n*.
        """

        operator    = 'Disjunction'
        designation = True

    class DisjunctionNegatedDesignated(ConjunctionNegatedUndesignated):
        """
        From an unticked designated negated disjunction node *n* on a branch *b*, for each disjunct
        *d*, add a designated node with the negation of *d* to *b*, then tick *n*.
        """

        operator    = 'Disjunction'
        designation = True

    class DisjunctionUndesignated(ConjunctionDesignated):
        """
        From an unticked undesignated disjunction node *n* on a branch *b*, for each disjunct
        *d*, add an undesignated node with *d* to *b*, then tick *n*.
        """

        operator    = 'Disjunction'
        designation = False

    class DisjunctionNegatedUndesignated(ConjunctionNegatedDesignated):
        """
        From an unticked undesignated negated disjunction node *n* on a branch *b*, for each disjunct
        *d*, make a new branch *b'* from *b* and add an undesignated node with the negation of *d* to
        *b'*, then tick *n*.
        """

        operator    = 'Disjunction'
        designation = False

    class MaterialConditionalDesignated(logic.TableauxSystem.ConditionalNodeRule):
        """
        From an unticked designated material conditional node *n* on a branch *b*, make
        two new branches *b'* and *b''* from *b*, add a designated node with the negation
        of the antecedent to *b'*, add a designated node with the consequent to *b''*,
        then tick *n*.
        """

        operator    = 'Material Conditional'
        designation = True

        def apply_to_node(self, node, branch):
            s = self.sentence(node)
            d = self.designation
            b1 = branch
            b2 = self.tableau.branch(branch)
            b1.add({ 'sentence' : negate(s.lhs) , 'designated' : d }).tick(node)
            b2.add({ 'sentence' :        s.rhs  , 'designated' : d }).tick(node)

    class MaterialConditionalNegatedDesignated(logic.TableauxSystem.ConditionalNodeRule):
        """
        From an unticked designated negated material conditional node *n* on a branch *b*, add
        a designated node with the antecedent, and a designated node with the negation of the
        consequent to *b*, then tick *n*.
        """

        negated     = True
        operator    = 'Material Conditional'
        designation = True

        def apply_to_node(self, node, branch):
            s = self.sentence(node)
            d = self.designation
            branch.update([
                { 'sentence' :        s.lhs  , 'designated' : d },
                { 'sentence' : negate(s.rhs) , 'designated' : d }
            ]).tick(node)

    class MaterialConditionalUndesignated(logic.TableauxSystem.ConditionalNodeRule):
        """
        From an unticked undesignated material conditional node *n* on a branch *b*, add
        an undesignated node with the negation of the antecedent and an undesignated node
        with the consequent to *b*, then tick *n*.
        """

        operator    = 'Material Conditional'
        designation = False

        def apply_to_node(self, node, branch):
            s = self.sentence(node)
            d = self.designation
            branch.update([
                { 'sentence' : negate(s.lhs) , 'designated' : d },
                { 'sentence' :        s.rhs  , 'designated' : d }
            ]).tick(node)

    class MaterialConditionalNegatedUndesignated(logic.TableauxSystem.ConditionalNodeRule):
        """
        From an unticked undesignated negated material conditional node *n* on a branch *b*, make
        two new branches *b'* and *b''* from *b*, add an undesignated node with the antecedent to
        *b'*, and add an undesignated node with the negation of the consequent to *b''*, then
        tick *n*.
        """

        negated     = True
        operator    = 'Material Conditional'
        designation = False

        def apply_to_node(self, node, branch):
            s = self.sentence(node)
            d = self.designation
            b1 = branch
            b2 = self.tableau.branch(branch)
            b1.add({ 'sentence' :        s.lhs  , 'designated' : d }).tick(node)
            b2.add({ 'sentence' : negate(s.rhs) , 'designated' : d }).tick(node)

    class MaterialBiconditionalDesignated(logic.TableauxSystem.ConditionalNodeRule):
        """
        From an unticked designated material biconditional node *n* on a branch *b*, make
        two new branches *b'* and *b''* from *b*, add a designated node with the negation
        of the antecedent and a designated node with the negation of the consequent to *b'*,
        and add a designated node with the antecedent and a designated node with the
        consequent to *b''*, then tick *n*.
        """

        operator    = 'Material Biconditional'
        designation = True

        def apply_to_node(self, node, branch):
            s = self.sentence(node)
            d = self.designation
            b1 = branch
            b2 = self.tableau.branch(branch)
            b1.update([
                { 'sentence' : negate(s.lhs), 'designated' : d },
                { 'sentence' : negate(s.rhs), 'designated' : d }
            ]).tick(node)
            b2.update([
                { 'sentence' : s.rhs, 'designated' : d },
                { 'sentence' : s.lhs, 'designated' : d }
            ]).tick(node)

    class MaterialBiconditionalNegatedDesignated(logic.TableauxSystem.ConditionalNodeRule):
        """
        From an unticked designated negated material biconditional node *n* on a branch *b*, make
        two branches *b'* and *b''* from *b*, add a designated node with the antecedent and a
        designated node with the negation of the consequent to *b'*, and add a designated node
        with the negation of the antecedent and a designated node with the consequent to *b''*,
        then tick *n*.
        """

        negated     = True
        operator    = 'Material Biconditional'
        designation = True

        def apply_to_node(self, node, branch):
            s = self.sentence(node)
            d = self.designation
            b1 = branch
            b2 = self.tableau.branch(branch)
            b1.update([
                { 'sentence' :        s.lhs  , 'designated' : d },
                { 'sentence' : negate(s.rhs) , 'designated' : d }
            ]).tick(node)
            b2.update([
                { 'sentence' : negate(s.lhs) , 'designated' : d },
                { 'sentence' :        s.rhs  , 'designated' : d }
            ]).tick(node)
                    
    class MaterialBiconditionalUndesignated(MaterialBiconditionalNegatedDesignated):
        """
        From an unticked undesignated material biconditional node *n* on a branch *b*, make
        two new branches *b'* and *b''* from *b*, add an undesignated node with the negation
        of the antecedent and an undesignated node with the consequent to *b'*, and add an
        undesignated node with the antecedent and an undesignated node with the negation of
        the consequent to *b''*, then tick *n*.
        """

        negated     = False
        designation = False

    class MaterialBiconditionalNegatedUndesignated(MaterialBiconditionalDesignated):
        """
        From an undesignated negated material biconditional node *n* on a branch *b*, make
        two branches *b'* and *b''* from *b*, add an undesignated node with the negation of
        the antecendent and an undesignated node with the negation of the consequent to *b'*,
        and add an undesignated node with the antecedent and an undesignated node with the
        consequent to *b''*, then tick *n*.
        """

        negated     = True
        designation = False

    class ConditionalDesignated(MaterialConditionalDesignated):
        """
        This rule functions the same as the corresponding material conditional rule.

        From an unticked designated conditional node *n* on a branch *b*, make two new
        branches *b'* and *b''* from *b*, add a designated node with the negation of
        the antecedent to *b'*, add a designated node with the consequent to *b''*,
        then tick *n*.
        """

        operator = 'Conditional'

    class ConditionalNegatedDesignated(MaterialConditionalNegatedDesignated):
        """
        This rule functions the same as the corresponding material conditional rule.

        From an unticked designated negated conditional node *n* on a branch *b*, add a
        designated node with the antecedent, and a designated node with the negation of
        the consequent to *b*, then tick *n*.
        """

        operator = 'Conditional'

    class ConditionalUndesignated(MaterialConditionalUndesignated):
        """
        This rule functions the same as the corresponding material conditional rule.

        From an unticked undesignated conditional node *n* on a branch *b*, add an
        undesignated node with the negation of the antecedent and an undesignated node
        with the consequent to *b*, then tick *n*.
        """

        operator = 'Conditional'

    class ConditionalNegatedUndesignated(MaterialConditionalNegatedUndesignated):
        """
        This rule functions the same as the corresponding material conditional rule.

        From an unticked undesignated negated conditional node *n* on a branch *b*, make two
        new branches *b'* and *b''* from *b*, add an undesignated node with the antecedent to
        *b'*, and add an undesignated node with the negation of the consequent to *b''*, then
        tick *n*.
        """

        operator = 'Conditional'

    class BiconditionalDesignated(MaterialBiconditionalDesignated):
        """
        This rule functions the same as the corresponding material biconditional rule.

        From an unticked designated biconditional node *n* on a branch *b*, make two new
        branches *b'* and *b''* from *b*, add a designated node with the negation of the
        antecedent and a designated node with the negation of the consequent to *b'*,
        and add a designated node with the antecedent and a designated node with the
        consequent to *b''*, then tick *n*.
        """

        operator = 'Biconditional'

    class BiconditionalNegatedDesignated(MaterialBiconditionalNegatedDesignated):
        """
        This rule functions the same as the corresponding material biconditional rule.

        From an unticked designated negated biconditional node *n* on a branch *b*, make two
        branches *b'* and *b''* from *b*, add a designated node with the antecedent and a
        designated node with the negation of the consequent to *b'*, and add a designated node
        with the negation of the antecedent and a designated node with the consequent to *b''*,
        then tick *n*.
        """

        operator = 'Biconditional'

    class BiconditionalUndesignated(MaterialBiconditionalUndesignated):
        """
        This rule functions the same as the corresponding material biconditional rule.

        From an unticked undesignated material biconditional node *n* on a branch *b*, make
        two new branches *b'* and *b''* from *b*, add an undesignated node with the negation
        of the antecedent and an undesignated node with the consequent to *b'*, and add an
        undesignated node with the antecedent and an undesignated node with the negation of
        the consequent to *b''*, then tick *n*.
        """

        operator = 'Biconditional'

    class BiconditionalNegatedUndesignated(MaterialBiconditionalNegatedUndesignated):
        """
        This rule functions the same as the corresponding material biconditional rule.

        From an undesignated negated biconditional node *n* on a branch *b*, make two
        branches *b'* and *b''* from *b*, add an undesignated node with the negation of the
        antecendent and an undesignated node with the negation of the consequent to *b'*,
        and add an undesignated node with the antecedent and an undesignated node with the
        consequent to *b''*, then tick *n*.
        """

        operator = 'Biconditional'

    class ExistentialDesignated(logic.TableauxSystem.ConditionalNodeRule):
        """
        From an unticked designated existential node *n* on a branch *b* quantifying over
        variable *v* into sentence *s*, add a designated node to *b* with the substitution
        into *s* of a new constant not yet appearing on *b* for *v*, then tick *n*.
        """

        quantifier  = 'Existential'
        designation = True

        def apply_to_node(self, node, branch):
            s = self.sentence(node)
            d = self.designation
            v = s.variable
            c = branch.new_constant()
            branch.add({
                'sentence'   : s.substitute(c, v),
                'designated' : d
            }).tick(node)

    class ExistentialNegatedDesignated(logic.TableauxSystem.ConditionalNodeRule):
        """
        From an unticked designated negated existential node *n* on a branch *b*,
        quantifying over variable *v* into sentence *s*, add a designated node to *b*
        that universally quantifies over *v* into the negation of *s* (i.e. change
        'not exists x: A' to 'for all x: not A'), then tick *n*.
        """

        negated     = True
        quantifier  = 'Existential'
        convert_to  = 'Universal'
        designation = True

        def apply_to_node(self, node, branch):
            s = self.sentence(node)
            d = self.designation
            v = s.variable
            branch.add({
                'sentence'   : quantify(self.convert_to, v, negate(s)),
                'designated' : d
            }).tick(node)

    class ExistentialUndesignated(logic.TableauxSystem.BranchRule):
        """
        From an undesignated existential node *n* on a branch *b*, for any constant *c* on
        *b* such that the result *r* of substituting *c* for the variable bound by the
        sentence of *n* does not appear on *b*, then add an undesignated node with *r* to *b*.
        If there are no constants yet on *b*, then instantiate with a new constant. The node
        *n* is never ticked.
        """

        quantifier  = 'Existential'
        designation = False

        def applies_to_branch(self, branch):
            target = False
            d = self.designation
            q = self.quantifier
            constants = branch.constants()
            for n in branch.get_nodes():
                # keep quantifier and designation neutral for inheritance below
                if 'sentence' not in n.props or n.props['designated'] != d:
                    continue
                s = n.props['sentence']
                if s.quantifier != q:
                    continue
                v = s.variable
                if not len(constants):
                    c = branch.new_constant()
                    target = { 'branch' : branch, 'sentence' : s.substitute(c, v), 'node' : n }
                else:
                    for c in constants:
                        r = s.substitute(c, v)
                        if not branch.has({ 'sentence': r, 'designated' : d }):
                            target = { 'branch' : branch, 'sentence' : r, 'node' : n }
                            break
                if target:
                    break
            return target

        def apply(self, target):
            # keep designation neutral for inheritance below
            target['branch'].add({ 'sentence' : target['sentence'], 'designated' : self.designation })

        def example(self):
            # keep quantifier and designation neutral for inheritance below
            s = examples.quantified(self.quantifier)
            self.tableau.branch().add({ 'sentence' : s, 'designated' : self.designation })

    class ExistentialNegatedUndesignated(ExistentialNegatedDesignated):
        """
        From an unticked undesignated negated existential node *n* on a branch *b*,
        quantifying over variable *v* into sentence *s*, add an undesignated node to *b*
        that universally quantifies over *v* into the negation of *s* (i.e. change 'not
        exists x: A' to 'for all x: not A'), then tick *n*.
        """

        quantifier  = 'Existential'
        convert_to  = 'Universal'
        designation = False

    class UniversalDesignated(ExistentialUndesignated):
        """
        From a designated universal node *n* on a branch *b*, for any constant *c* on *b*
        such that the result *r* of substituting *c* for the variable bound by the sentence
        of *n* does not appear on *b*, then add a designated node with *r* to *b*. If there
        are no constants yet on *b*, then instantiate with a new constant. The node *n* is
        never ticked.
        """

        quantifier  = 'Universal'
        designation = True

    class UniversalNegatedDesignated(ExistentialNegatedDesignated):
        """
        From an unticked designated negated universal node *n* on a branch *b*,
        quantifying over variable *v* into sentence *s*, add a designated node to *b*
        with the existential quantifier over *v* into the negation of *s* (i.e. change
        'not all x: A' to 'exists x: not A'), then tick *n*.
        """

        quantifier  = 'Universal'
        convert_to  = 'Existential'
        designation = True

    class UniversalUndesignated(ExistentialDesignated):
        """
        From an unticked undesignated universal node *n* on a branch *b* quantifying over *v*
        into sentence *s*, add an undesignated node to *b* with the result of substituting into
        *s* a constant new to *b* for *v*, then tick *n*.
        """

        quantifier  = 'Universal'
        designation = False

    class UniversalNegatedUndesignated(ExistentialNegatedDesignated):
        """
        From an unticked undesignated negated universal node *n* on a branch *b*,
        quantifying over variable *v* into sentence *s*, add an undesignated node to *b*
        with the existential quantifier over *v* into the negation of *s* (i.e. change
        'not all x: A' to 'exists x: not A'), then tick *n*.
        """

        quantifier  = 'Universal'
        convert_to  = 'Existential'
        designation = False

    class DoubleNegationDesignated(logic.TableauxSystem.ConditionalNodeRule):
        """
        From an unticked designated negated negation node *n* on a branch *b*, add a designated
        node to *b* with the double-negatum of *n*, then tick *n*.
        """

        negated     = True
        operator    = 'Negation'
        designation = True

        def apply_to_node(self, node, branch):
            s = self.sentence(node)
            d = self.designation
            branch.add({ 'sentence' : s.operand, 'designated' : d }).tick(node)

    class DoubleNegationUndesignated(DoubleNegationDesignated):
        """
        From an unticked undesignated negated negation node *n* on a branch *b*, add an
        undesignated node to *b* with the double-negatum of *n*, then tick *n*.
        """

        designation = False

    class AssertionDesignated(logic.TableauxSystem.ConditionalNodeRule):
        """
        From an unticked, designated, assertion node *n* on a branch *b*, add a designated
        node to *b* with the operand of *b*, then tick *n*.
        """

        operator = 'Assertion'
        designation = True

        def apply_to_node(self, node, branch):
            s = self.sentence(node)
            d = self.designation
            branch.add({ 'sentence' : s.operand, 'designated' : d }).tick(node)

    class AssertionUndesignated(AssertionDesignated):
        """
        From an unticked, undesignated, assertion node *n* on a branch *b*, add an undesignated
        node to *b* with the operand of *n*, then tick *n*.
        """

        designation = False

    class AssertionNegatedDesignated(logic.TableauxSystem.ConditionalNodeRule):
        """
        From an unticked, designated, negated assertion node *n* on branch *b*, add a designated
        node to *b* with the negation of the assertion's operand to *b*, then tick *n*.
        """

        operator = 'Assertion'
        negated = True
        designation = True

        def apply_to_node(self, node, branch):
            s = self.sentence(node)
            d = self.designation
            branch.add({ 'sentence' : negate(s.operand), 'designated' : d }).tick(node)

    class AssertionNegatedUndesignated(AssertionNegatedDesignated):
        """
        From an unticked, undesignated, negated assertion node *n* on branch *b*, add an undesignated
        node to *b* with the negation of the assertion's operand to *b*, then tick *n*.
        """

        designation = False

    rules = [

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