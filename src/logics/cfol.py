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
# pytableaux - Classical First-Order Logic

"""
Classical First-Order Logic (CFOL) is the standard bivalent logic (True, False).

Semantics
---------

Two primitive operators, negation and disjunction, are defined via truth tables.

**Negation**:

+------------+------------+
| A          | not A      |
+============+============+
|  T         |  F         |
+------------+------------+
|  F         |  T         |
+------------+------------+

**Disjunction**:

+-----------+----------+---------+
|  A or B   |          |         |
+===========+==========+=========+
|           |  **T**   |  **F**  |
+-----------+----------+---------+
|  **T**    |    T     |    T    |
+-----------+----------+---------+
|  **F**    |    T     |    F    | 
+-----------+----------+---------+

Other operators are defined via semantic equivalencies in the usual way:

- **Conjunction**: ``A and B := not (not-A or not-B)``

- **Material Conditional**: ``if A then B := not-A or B``

- **Material Biconditional**: ``A if and only if B := (if A then B) and (if B then A)``

The truth tables for defined connectives are as follows:

**Conjunction**:

+-----------+----------+---------+
|  A and B  |          |         |
+===========+==========+=========+
|           |  **T**   |  **F**  |
+-----------+----------+---------+
|  **T**    |    T     |    F    |
+-----------+----------+---------+
|  **F**    |    F     |    F    | 
+-----------+----------+---------+

**Material Conditional**:

+-----------+----------+---------+
|  if A, B  |          |         |
+===========+==========+=========+
|           |  **T**   |  **F**  |
+-----------+----------+---------+
|  **T**    |    T     |    F    |
+-----------+----------+---------+
|  **F**    |    T     |    T    | 
+-----------+----------+---------+

**Material Biconditional**:

+-----------+----------+---------+
|  A iff B  |          |         |
+===========+==========+=========+
|           |  **T**   |  **F**  |
+-----------+----------+---------+
|  **T**    |    T     |    F    |
+-----------+----------+---------+
|  **F**    |    F     |    T    | 
+-----------+----------+---------+

The **Conditional** and **Biconditional** operators are equivalent to their material counterparts.

**Predicate Sentences** like *a is F* are handled via a predicate's *extension*:

- *a is F* iff the object denoted by the constant *a* is in the extension of the predicate *F*.

**Quantification** can be thought of along these lines:

- **Universal Quantifier**: *for all x, x is F* has the value:

    - **T** iff everything is in the extension of *F*.
    - **F** iff not everything is in the extension of *F*.

- **Existential Quantifier**: ``there exists an x that is F := not (for all x, not (x is F))``

*C* is a **Logical Consequence** of *A* iff all cases where the value of *A* is **T**
are cases where *C* also has the value **T**.
"""

name = 'CFOL'
description = 'Classical First Order Logic'

def example_validities():
    # Everything valid in K3 or LP is valid in CFOL
    import k3, lp
    args = k3.example_validities()
    args.update(lp.example_validities())
    args.update({
        'Law of Excluded Middle'      : 'AaNa',
        'Identity'                    : 'Caa',
        'Pseudo Contraction'          : 'CCaCabCab',
        'Law of Non-contradiction'    : [[ 'KaNa' ], 'b'  ],
        'Disjunctive Syllogism'       : [[ 'Aab', 'Nb' ], 'a'  ],
        'Modus Ponens'                : [[ 'Cab', 'a'  ], 'b'  ],
        'Modus Tollens'               : [[ 'Cab', 'Nb' ], 'Na' ],
        'Biconditional Elimination'   : [[ 'Eab', 'a'  ], 'b'  ],
        'Biconditional Elimination 2' : [[ 'Eab', 'Na' ], 'Nb' ],
        'Syllogism'                   : [[ 'VxCFxGx', 'VxCGxHx' ], 'VxCFxHx'],
        'Existential Syllogism'       : [[ 'VxCFxGx', 'Fn'     ],  'Gn'],
        'Universal Predicate Syllogism' : [[ 'VxVyCO0xyO1xy', 'O0nm'], 'O1nm']
    })
    return args

def example_invalidities():
    return {
        'Triviality 1'				: 'a',
        'Triviality 2'				: [[ 'a'    ], 'b'    ],
        'Conditional Equivalence'	: [[ 'Cab'  ], 'Cba'  ],
        'Extracting the Consequent' : [[ 'Cab'  ], 'b'    ],
        'Extracting the Antecedent' : [[ 'Cab'  ], 'a'    ],
        'Extracting as Disjunct 1'	: [[ 'Aab'  ], 'b'    ],
        'Extracting as Disjunct 2'	: [[ 'AaNb' ], 'Na'   ],
        'Existential from Universal': [[ 'SxFx' ], 'VxFx' ],
        'Affirming the Consequent'	: [[ 'Cab', 'b'  ], 'a'  ],
        'Affirming a Disjunct 1'	: [[ 'Aab', 'a'  ], 'b'  ],
        'Affirming a Disjunct 2'	: [[ 'Aab', 'a'  ], 'Nb' ],
        'Denying the Antecedent' 	: [[ 'Cab', 'Na' ], 'b'  ]
    }

import logic
from logic import negate, operate, quantify, Vocabulary

class TableauxSystem(logic.TableauxSystem):
    """
    A branch can be thought of as representing a case where each node's sentence
    is true.
    """

    @staticmethod
    def build_trunk(tableau, argument):
        """
        To build the trunk for an argument, add a node for each premise, and
        a node with the negation of the conclusion.        
        """
        branch = tableau.branch()
        for premise in argument.premises:
            branch.add({ 'sentence' : premise })
        branch.add({ 'sentence':  negate(argument.conclusion) })

class TableauxRules(object):
    """
    In general, there are two rules for each connectives: one regular, one negation.
    The special case of negation has only a rule for double negation.
    """

    class Closure(logic.TableauxSystem.ClosureRule):
        """
        A branch is closed iff a sentence and its negation appear on the branch.
        """

        def applies_to_branch(self, branch):
            for node in branch.get_nodes():
                if branch.has({ 'sentence' : negate(node.props['sentence']) }):
                    return branch
            return False

        def example(self):
            a = logic.atomic(0, 0)
            self.tableau.branch().update([{ 'sentence' : a }, { 'sentence' : negate(a) }])

    class Conjunction(logic.TableauxSystem.ConditionalNodeRule):
        """
        From an unticked conjunction node *n* on a branch *b*, add a node with each
        conjunct to *b*, then tick *n*.
        """

        operator = 'Conjunction'

        def apply_to_node(self, node, branch):
            for conjunct in node.props['sentence'].operands:
                branch.add({ 'sentence': conjunct })
            branch.tick(node)

    class ConjunctionNegated(logic.TableauxSystem.ConditionalNodeRule):
        """
        From an unticked negated conjunction node *n* on a branch *b*, for each conjunct,
        make a new branch *b'* from *b* and add the negation of the conjunct to *b'*,
        then tick *n*.
        """

        negated  = True
        operator = 'Conjunction'

        def apply_to_node(self, node, branch):
            for conjunct in node.props['sentence'].operand.operands:
                self.tableau.branch(branch).add({ 'sentence' : negate(conjunct) }).tick(node)

    class Disjunction(logic.TableauxSystem.ConditionalNodeRule):
        """
        From an unticked disjunction node *n* on a branch *b*, for each disjunct, make a
        new branch *b'* from *b* and add the disjunct to *b'*, then tick *n*.
        """

        operator = 'Disjunction'

        def apply_to_node(self, node, branch):
            for disjunct in node.props['sentence'].operands:
                self.tableau.branch(branch).add({ 'sentence' : disjunct }).tick(node)

    class DisjunctionNegated(logic.TableauxSystem.ConditionalNodeRule):
        """
        From an unticked negated disjunction node *n* on a branch *b*, for each disjunct,
        add a node to *b* with the negation of the disjunct, then tick *n*.
        """

        negated  = True
        operator = 'Disjunction'

        def apply_to_node(self, node, branch):
            for disjunct in node.props['sentence'].operand.operands:
                branch.add({ 'sentence' : negate(disjunct) })
            branch.tick(node)

    class MaterialConditional(logic.TableauxSystem.ConditionalNodeRule):
        """
        From an unticked material conditional node *n* on a branch *b*, make two new
        branches *b'* and *b''* from *b*, add a node with the negation of the antecedent
        to *b'*, and add a node with the consequent to *b''*, then tick *n*.
        """

        operator = 'Material Conditional'

        def apply_to_node(self, node, branch):
            newBranches = self.tableau.branch_multi(branch, 2)            
            s = node.props['sentence']
            newBranches[0].add({ 'sentence': negate(s.lhs) }).tick(node)
            newBranches[1].add({ 'sentence':        s.rhs  }).tick(node)

    class MaterialConditionalNegated(logic.TableauxSystem.ConditionalNodeRule):
        """
        From an unticked negated material conditional node *n* on a branch *b*, add two
        nodes to *b*, one with the antecedent, the other with the negation of the consequent,
        then tick *n*.
        """

        negated  = True
        operator = 'Material Conditional'

        def apply_to_node(self, node, branch):
            s = node.props['sentence'].operand
            branch.update([
                { 'sentence':        s.lhs  }, 
                { 'sentence': negate(s.rhs) }
            ]).tick(node)

    class MaterialBiconditional(logic.TableauxSystem.ConditionalNodeRule):
        """
        From an unticked material biconditional node *n* on a branch *b*, make two new
        branches *b'* and *b''* from *b*, add a node with the negation of the antecedent
        and a node with the negation of the consequent to *b'*, and add a node with the
        antecedent and a node with the consequent to *b''*, then tick *n*.
        """

        operator = 'Material Biconditional'

        def apply_to_node(self, node, branch):
            newBranches = self.tableau.branch_multi(branch, 2)
            s = node.props['sentence']
            newBranches[0].update([
                { 'sentence': negate(s.lhs) }, 
                { 'sentence': negate(s.rhs) }
            ]).tick(node)
            newBranches[1].update([
                { 'sentence': s.rhs }, 
                { 'sentence': s.lhs }
            ]).tick(node)

    class MaterialBiconditionalNegated(logic.TableauxSystem.ConditionalNodeRule):
        """
        From an unticked negated material biconditional node *n* on a branch *b*, make two
        new branches *b'* and *b''* from *b*, add a node with the antecedent and a node with
        the negation of the consequent to *b'*, and add a node with the negation of the
        antecendent and a node with the consequent to *b''*, then tick *n*.
        """

        negated  = True
        operator = 'Material Biconditional'

        def apply_to_node(self, node, branch):
            newBranches = self.tableau.branch_multi(branch, 2)
            s = node.props['sentence'].operand
            newBranches[0].update([
                { 'sentence':        s.lhs  },
                { 'sentence': negate(s.rhs) }
            ]).tick(node)
            newBranches[1].update([
                { 'sentence': negate(s.rhs) },
                { 'sentence':        s.lhs  }
            ]).tick(node)

    class Conditional(MaterialConditional):
        """
        This rule functions the same as the corresponding material conditional rule.

        From an unticked conditional node *n* on a branch *b*, make two new branches *b'*
        and *b''* from *b*, add a node with the negation of the antecedent to *b'*, and
        add a node with the consequent to *b''*, then tick *n*.
        """

        operator = 'Conditional'

    class ConditionalNegated(MaterialConditionalNegated):
        """
        This rule functions the same as the corresponding material conditional rule.

        From an unticked negated conditional node *n* on a branch *b*, add two nodes to *b*,
        one with the antecedent, the other with the negation of the consequent, then tick *n*.
        """

        operator = 'Conditional'

    class Biconditional(MaterialBiconditional):
        """
        This rule functions the same as the corresponding material biconditional rule.

        From an unticked biconditional node *n* on a branch *b*, make two new branches *b'*
        and *b''* from *b*, add a node with the negation of the antecedent and a node with
        the negation of the consequent to *b'*, and add a node with the antecedent and a
        node with the consequent to *b''*, then tick *n*.
        """

        operator = 'Biconditional'

    class BiconditionalNegated(MaterialBiconditionalNegated):
        """
        This rule functions the same as the corresponding material biconditional rule.

        From an unticked negated biconditional node *n* on a branch *b*, make two new
        branches *b'* and *b''* from *b*, add a node with the antecedent and a node with
        the negation of the consequent to *b'*, and add a node with the negation of the
        antecendent and a node with the consequent to *b''*, then tick *n*.
        """

        operator = 'Biconditional'

    class Existential(logic.TableauxSystem.ConditionalNodeRule):
        """
        From an unticked existential node *n* on a branch *b* quantifying over variable
        *v* into sentence *s*, add a node with the substituion of a new constant not
        yet appearing on *b* for *v* into *s*, then tick *n*.
        """

        quantifier = 'Existential'

        def apply_to_node(self, node, branch):
            s = node.props['sentence']
            v = node.props['sentence'].variable
            branch.add({ 'sentence': s.substitute(branch.new_constant(), v) }).tick(node)

    class ExistentialNegated(logic.TableauxSystem.ConditionalNodeRule):
        """
        From an unticked negated existential node *n* on a branch *b* quantifying over
        variable *v* into sentence *s*, add a node that universally quantifies over
        *v* into the negation of *s*, then tick *n*.
        """

        negated    = True
        quantifier = 'Existential'
        convert_to = 'Universal'

        def apply_to_node(self, node, branch):
            s = node.props['sentence'].operand.sentence
            v = node.props['sentence'].operand.variable
            branch.add({ 'sentence': quantify(self.convert_to, v, negate(s)) }).tick(node)

    class Universal(logic.TableauxSystem.BranchRule):
        """
        From a universal node *n* on a branch *b* quantifying over variable *v* into
        sentence *s*, for any constant *c* on *b*, or a new constant if none exists,
        if the result *r* of susbtituting *c* for *v* into *s* does not appear on *b*,
        add a node with *r* to *b*. The node *n* is never ticked.
        """

        quantifier = 'Universal'

        def applies_to_branch(self, branch):
            constants = branch.constants()
            for node in branch.get_nodes():
                if 'sentence' in node.props and node.props['sentence'].quantifier == self.quantifier:
                    v = node.props['sentence'].variable
                    s = node.props['sentence']
                    if len(constants):
                        for c in constants:
                            r = s.substitute(c, v)
                            if not branch.has({ 'sentence': r }):
                                return { 'branch' : branch, 'sentence' : r, 'node' : node }
                        continue
                    return { 'branch' : branch, 'sentence' : s.substitute(branch.new_constant(), v), 'node' : node }
            return False

        def apply(self, target):
            target['branch'].add({ 'sentence': target['sentence'] })

        def example(self):
            self.tableau.branch().add({ 'sentence' : Vocabulary.get_example_quantifier_sentence(self.quantifier) })

    class UniversalNegated(ExistentialNegated):
        """
        From an unticked negated universal node *n* on a branch *b* quantifying over
        variable *v* into sentence *s*, add a node that existentially quantifies over
        *v* into the negation of *s*, then tick *n*.
        """

        quantifier = 'Universal'
        convert_to = 'Existential'

    class DoubleNegation(logic.TableauxSystem.ConditionalNodeRule):
        """
        From an unticked double negation node *n* on a branch *b*, add a node with the
        double-negatum to *b*, then tick *n*.
        """

        negated  = True
        operator = 'Negation'

        def apply_to_node(self, node, branch):
            branch.add({ 'sentence': node.props['sentence'].operand.operand }).tick(node)

    rules = [

        Closure,

        # non-branching rules

        Conjunction,
        DisjunctionNegated,
        MaterialConditionalNegated,
        ConditionalNegated,
        Existential,
        ExistentialNegated,
        Universal,
        UniversalNegated,
        DoubleNegation,

        # branching rules

        ConjunctionNegated,
        Disjunction,
        MaterialConditional,
        MaterialBiconditional,
        MaterialBiconditionalNegated,
        Conditional,
        Biconditional,
        BiconditionalNegated

    ]