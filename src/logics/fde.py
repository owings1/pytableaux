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
Semantics
---------

FDE is a 4-valued logic (True, False, Neither and Both). Two primitive operators, negation and
disjunction, are defined via truth tables.

**Negation**:

+------------+------------+
| A          | not-A      |
+============+============+
|  T         |  F         |
+------------+------------+
|  B         |  B         |
+------------+------------+
|  N         |  N         |
+------------+------------+
|  F         |  T         |
+------------+------------+

**Disjunction**:

+-----------+----------+-----------+-----------+---------+
|  A or B   |          |           |           |         |
+===========+==========+===========+===========+=========+
|           |  **T**   |   **B**   |   **N**   |  **F**  |
+-----------+----------+-----------+-----------+---------+
|  **T**    |    T     |     T     |     T     |    T    |
+-----------+----------+-----------+-----------+---------+
|  **B**    |    T     |     B     |     B     |    F    |
+-----------+----------+-----------+-----------+---------+
|  **N**    |    T     |     B     |     N     |    N    |
+-----------+----------+-----------+-----------+---------+
|  **F**    |    T     |     F     |     N     |    F    | 
+-----------+----------+-----------+-----------+---------+

Other operators are defined via semantic equivalencies:

- **Conjunction**: ``A and B := not (not-A or not-B)``

- **Material Conditional**: ``if A then B := not-A or B``
    
- **Material Biconditional**: ``A if and only if B := (if A then B) and (if B then A)``

The **Conditional** and **Biconditional** operators are equivalent to their material counterparts.

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

* DeMorgan laws are valid.

For futher reading see:

- `Stanford Encyclopedia entry on paraconsistent logic <http://plato.stanford.edu/entries/logic-paraconsistent/>`_
"""
name = 'FDE'
description = 'First Degree Entailment Logic'

def example_validities():
    return {
        'Addition'                : [[ 'a'     ], 'Aab'   ],
        'Simplification'          : [[ 'Kab'   ], 'a'     ],
        'DeMorgan 1'              : [[ 'NAab'  ], 'KNaNb' ],
        'DeMorgan 2'              : [[ 'NKab'  ], 'ANaNb' ],
        'DeMorgan 3'              : [[ 'KNaNb' ], 'NAab'  ],
        'DeMorgan 4'              : [[ 'ANaNb' ], 'NKab'  ],
        'Material Contraction'    : [[ 'CaCab' ], 'Cab'   ],
        'Conditional Contraction' : [[ 'CaCab' ], 'Cab'   ]        
    }

def example_invalidities():
    # Everything invalid in K3 or LP is also invalid in FDE.
    import k3, lp
    args = k3.example_invalidities()
    args.update(lp.example_invalidities())
    return args

import logic
from logic import negate, quantify, atomic, Vocabulary

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
            branch.add({ 'sentence' : premise, 'designated' : True })
        branch.add({ 'sentence' : argument.conclusion, 'designated' : False })

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
                if branch.has({ 'sentence' : node.props['sentence'], 'designated' : not node.props['designated'] }):
                    return branch
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
            for operand in node.props['sentence'].operands:
                # allow disjunction inheritance below
                branch.add({ 'sentence' : operand, 'designated' : self.designation })
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
            for conjunct in node.props['sentence'].operand.operands:
                # allow disjunction inheritance below
                self.tableau.branch(branch).add({ 'sentence' : negate(conjunct), 'designated' : self.designation }).tick(node)

    class ConjunctionUndesignated(logic.TableauxSystem.ConditionalNodeRule):
        """
        From an unticked undesignated conjunction node *n* on a branch *b*, for each conjunct
        *c*, make a new branch *b'* from *b* and add an undesignated node with *c* to *b'*,
        then tick *n*.
        """

        operator    = 'Conjunction'
        designation = False

        def apply_to_node(self, node, branch):
            for operand in node.props['sentence'].operands:
                # allow disjunction inheritance below
                self.tableau.branch(branch).add({ 'sentence' : operand, 'designated' : self.designation }).tick(node)

    class ConjunctionNegatedUndesignated(logic.TableauxSystem.ConditionalNodeRule):
        """
        From an unticked undesignated negated conjunction node *n* on a branch *b*, for each conjunct
        *c*, add an undesignated node with the negation of *c* to *b*, then tick *n*.
        """

        negated     = True
        operator    = 'Conjunction'
        designation = False

        def apply_to_node(self, node, branch):
            for operand in node.props['sentence'].operand.operands:
                # allow disjunction inheritance below
                branch.add({ 'sentence' : negate(operand), 'designated' : self.designation })
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
            newBranches = self.tableau.branch_multi(branch, 2)
            s = node.props['sentence']
            newBranches[0].add({ 'sentence' : negate(s.lhs) , 'designated' : True }).tick(node)
            newBranches[1].add({ 'sentence' :        s.rhs  , 'designated' : True }).tick(node)

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
            s = node.props['sentence'].operand
            branch.update([
                { 'sentence' :        s.lhs  , 'designated' : True },
                { 'sentence' : negate(s.rhs) , 'designated' : True }
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
            s = node.props['sentence']
            branch.update([
                { 'sentence' : negate(s.lhs) , 'designated' : False },
                { 'sentence' :        s.rhs  , 'designated' : False }
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
            newBranches = self.tableau.branch_multi(branch, 2)
            s  = node.props['sentence'].operand
            newBranches[0].add({ 'sentence' :        s.lhs  , 'designated' : False }).tick(node)
            newBranches[1].add({ 'sentence' : negate(s.rhs) , 'designated' : False }).tick(node)

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
            newBranches = self.tableau.branch_multi(branch, 2)
            s = node.props['sentence']
            # allow for negation rule inheritance below
            if self.negated:
                s = s.operand
            # keep designation neutral for inheritance below
            newBranches[0].update([
                { 'sentence' : negate(s.lhs), 'designated' : self.designation },
                { 'sentence' : negate(s.rhs), 'designated' : self.designation }
            ]).tick(node)
            newBranches[1].update([
                { 'sentence' : s.rhs, 'designated' : self.designation },
                { 'sentence' : s.lhs, 'designated' : self.designation }
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
            newBranches = self.tableau.branch_multi(branch, 2)
            s = node.props['sentence']
            # allow for unnegated rule inheritance below
            if self.negated:
                s = s.operand
            # keep designation neutral for inheritance below
            newBranches[0].update([
                { 'sentence' :        s.lhs  , 'designated' : self.designation },
                { 'sentence' : negate(s.rhs) , 'designated' : self.designation }
            ]).tick(node)
            newBranches[1].update([
                { 'sentence' : negate(s.lhs) , 'designated' : self.designation },
                { 'sentence' :        s.rhs  , 'designated' : self.designation }
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
            s = node.props['sentence'].sentence
            v = node.props['sentence'].variable
            # keep designation neutral for inheritance below
            branch.add({ 'sentence' : s.substitute(branch.new_constant(), v), 'designated' : self.designation }).tick(node)

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
            s = node.props['sentence'].operand.sentence
            v = node.props['sentence'].operand.variable
            # keep quantifier conversion neutral to allow inheritance below
            branch.add({ 'sentence' : quantify(self.convert_to, v, negate(s)), 'designated' : self.designation }).tick(node)

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
            constants = branch.constants()
            for n in branch.get_nodes():
                # keep quantifier and designation neutral for inheritance below
                if n.props['sentence'].quantifier == self.quantifier and n.props['designated'] == self.designation:
                    v = n.props['sentence'].variable
                    s = n.props['sentence'].sentence
                    if not len(constants):
                        return { 'branch' : branch, 'sentence' : s.substitute(branch.new_constant(), v), 'node' : n }
                    for c in constants:
                        r = s.substitute(c, v)
                        if not branch.has({ 'sentence': r, 'designated' : self.designation }):
                            return { 'branch' : branch, 'sentence' : r, 'node' : n }
            return False

        def apply(self, target):
            # keep designation neutral for inheritance below
            target['branch'].add({ 'sentence' : target['sentence'], 'designated' : self.designation })

        def example(self):
            # keep quantifier and designation neutral for inheritance below
            s = Vocabulary.get_example_quantifier_sentence(self.quantifier)
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
            # designation is neutral to allow for inheritance below
            branch.add({ 'sentence' : node.props['sentence'].operand.operand, 'designated' : self.designation }).tick(node)

    class DoubleNegationUndesignated(DoubleNegationDesignated):
        """
        From an unticked undesignated negated negation node *n* on a branch *b*, add an
        undesignated node to *b* with the double-negatum of *n*, then tick *n*.
        """

        designation = False

    rules = [

        Closure,

        # non-branching rules

        ConjunctionDesignated, 
        DisjunctionNegatedDesignated,
        DisjunctionUndesignated,
        DisjunctionNegatedUndesignated,
        MaterialConditionalNegatedDesignated,
        MaterialConditionalUndesignated,
        MaterialConditionalNegatedUndesignated,
        ConditionalUndesignated, 
        ConditionalNegatedDesignated,
        ConditionalNegatedUndesignated,
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
        MaterialBiconditionalDesignated,
        MaterialBiconditionalNegatedDesignated,
        MaterialBiconditionalUndesignated,
        MaterialBiconditionalNegatedUndesignated,
        ConditionalDesignated,
        BiconditionalDesignated,
        BiconditionalNegatedDesignated,
        BiconditionalUndesignated,
        BiconditionalNegatedUndesignated

    ]