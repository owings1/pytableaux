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
# pytableaux - Bochvar 3 External logic
"""
B3E is similar to K3W, with a special Assertion operator, that always results in
a classical value (T or F).

Semantics
---------

Truth-functional operators are defined via truth tables below.

**Predicate Sentences** and **Quantification** are handled the same as in FDE.

**Logical Consequence** is defined the same as in K3.

"""
name = 'B3E'
description = 'Bochvar 3 External Logic'

import logic, k3, k3w, go, fde
from logic import assertion, operate, negate

def example_validities():
    args = k3w.example_validities()
    args.update([
        #'Biconditional Identity' ,
        #'Conditional Identity'   ,
    ])
    return args
    
def example_invalidities():
    import cpl
    args = cpl.example_invalidities()
    return args

truth_values = k3w.truth_values
truth_value_chars = k3w.truth_value_chars
designated_values = k3w.designated_values
undesignated_values = k3w.undesignated_values
unassigned_value = k3w.unassigned_value
truth_functional_operators = fde.truth_functional_operators

def truth_function(operator, a, b=None):
    if operator == 'Assertion':
        return go.truth_function(operator, a, b)
    elif operator == 'Conditional':
        return truth_function('Disjunction', truth_function('Negation', truth_function('Assertion', a)), truth_function('Assertion', b))
    elif operator == 'Biconditional':
        return truth_function('Conjunction', truth_function('Conditional', a, b), truth_function('Conditional', b, a))
    else:
        return k3w.truth_function(operator, a, b)

class TableauxSystem(fde.TableauxSystem):
    """
    B3E's Tableaux System inherits directly from FDE's.
    """

class TableauxRules(object):

    class ConditionalDesignated(logic.TableauxSystem.ConditionalNodeRule):
        """
        From an unticked, designated conditional node *n* on a branch *b*,
        add a designated node to *b* with a disjunction, where the
        first disjunction is the negation of the assertion of the antecedent,
        and the second disjunct is the assertion of the consequent. Then tick *n*.
        """

        operator    = 'Conditional'
        designation = True

        def apply_to_node(self, node, branch):
            s = self.sentence(node)
            d = self.designation
            sn = operate('Disjunction', [
                negate(assertion(s.lhs)),
                assertion(s.rhs)
            ])
            if self.negated:
                sn = negate(sn)
            branch.add({
                'sentence'   : sn,
                'designated' : d
            }).tick(node)


    class ConditionalUndesignated(ConditionalDesignated):
        """
        From an unticked, undesignated conditional node *n* on a branch *b*,
        add an undesignated node to *b* with a material conditional, where the
        operands are preceded by the Assertion operator, then tick *n*.
        """
        
        designation = False


    class ConditionalNegatedDesignated(ConditionalDesignated):
        """
        From an unticked, undesignated, negated conditional node *n* on a branch *b*,
        add a designated node to *b* with a negated material conditional, where the
        operands are preceded by the Assertion operator, then tick *n*.
        """

        negated     = True

    class ConditionalNegatedUndesignated(ConditionalDesignated):
        """
        From an unticked, undesignated, negated conditional node *n* on a branch *b*,
        add an undesignated node to *b* with a negated material conditional, where the
        operands are preceded by the Assertion operator, then tick *n*.
        """

        designation = False
        negated     = True

    class BiconditionalDesignated(logic.TableauxSystem.ConditionalNodeRule):
        """
        From an unticked, designated biconditional node *n* on a branch *b*, add two
        designated nodes to *b*, one with a disjunction, where the
        first disjunct is the negated asserted antecedent, and the second disjunct
        is the asserted consequent, and the other node is the same with the disjuncts
        inverted. Then tick *n*.
        """

        operator    = 'Biconditional'
        designation = True

        def apply_to_node(self, node, branch):
            s = self.sentence(node)
            d = self.designation
            sn1 = operate('Disjunction', [
                negate(assertion(s.lhs)),
                assertion(s.rhs)
            ])
            sn2 = operate('Disjunction', [
                negate(assertion(s.rhs)),
                assertion(s.lhs)
            ])
            if self.negated:
                sn1 = negate(sn1)
                sn2 = negate(sn2)
            branch.update([
                { 'sentence' : sn1, 'designated' : d},
                { 'sentence' : sn2, 'designated' : d}
            ]).tick(node)

    class BiconditionalUndesignated(BiconditionalDesignated):
        """
        From an unticked, undesignated biconditional node *n* on a branch *b*, add two
        undesignated nodes to *b*, one with a disjunction, where the
        first disjunct is the negated asserted antecedent, and the second disjunct
        is the asserted consequent, and the other node is the same with the disjuncts
        inverted. Then tick *n*.
        """

        designation = False

    class BiconditionalNegatedDesignated(BiconditionalDesignated):
        """
        From an unticked, designated, biconditional node *n* on a branch *b*, add two
        undesignated nodes to *b*, one with a negated disjunction, where the
        first disjunct is the negated asserted antecedent, and the second disjunct
        is the asserted consequent, and the other node is the same with the disjuncts
        inverted. Then tick *n*.
        """

        negated     = True

    class BiconditionalNegatedUndesignated(BiconditionalUndesignated):
        """
        From an unticked, designated, biconditional node *n* on a branch *b*, add two
        undesignated nodes to *b*, one with a negated disjunction, where the
        first disjunct is the negated asserted antecedent, and the second disjunct
        is the asserted consequent, and the other node is the same with the disjuncts
        inverted. Then tick *n*.
        """

        designation = False
        negated     = True

    rules = [
        k3.TableauxRules.Closure,
        fde.TableauxRules.Closure,

        # non-branching rules

        fde.TableauxRules.AssertionDesignated,
        fde.TableauxRules.AssertionUndesignated,
        fde.TableauxRules.AssertionNegatedDesignated,
        fde.TableauxRules.AssertionNegatedUndesignated,
        fde.TableauxRules.ConjunctionDesignated, 
        fde.TableauxRules.DisjunctionNegatedDesignated,
        fde.TableauxRules.ExistentialDesignated,
        fde.TableauxRules.ExistentialNegatedDesignated,
        fde.TableauxRules.ExistentialUndesignated,
        fde.TableauxRules.ExistentialNegatedUndesignated,
        fde.TableauxRules.UniversalDesignated,
        fde.TableauxRules.UniversalNegatedDesignated,
        fde.TableauxRules.UniversalUndesignated,
        fde.TableauxRules.UniversalNegatedUndesignated,
        fde.TableauxRules.DoubleNegationDesignated,
        fde.TableauxRules.DoubleNegationUndesignated,
        # reduction rules (thus, non-branching)
        k3w.TableauxRules.MaterialConditionalDesignated,
        k3w.TableauxRules.MaterialConditionalUndesignated,
        k3w.TableauxRules.MaterialConditionalNegatedDesignated,
        k3w.TableauxRules.MaterialConditionalNegatedUndesignated,
        ConditionalDesignated,
        ConditionalUndesignated,
        ConditionalNegatedDesignated,
        ConditionalNegatedUndesignated,
        k3w.TableauxRules.MaterialBiconditionalDesignated,
        k3w.TableauxRules.MaterialBiconditionalUndesignated,
        k3w.TableauxRules.MaterialBiconditionalNegatedDesignated,
        k3w.TableauxRules.MaterialBiconditionalNegatedUndesignated,
        BiconditionalDesignated,
        BiconditionalUndesignated,
        BiconditionalNegatedDesignated,
        BiconditionalNegatedUndesignated,

        # two-branching rules
        fde.TableauxRules.ConjunctionUndesignated,

        # three-branching rules
        k3w.TableauxRules.DisjunctionDesignated,
        k3w.TableauxRules.DisjunctionUndesignated,
        k3w.TableauxRules.ConjunctionNegatedDesignated,
        k3w.TableauxRules.ConjunctionNegatedUndesignated,

        # four-branching rules
        k3w.TableauxRules.DisjunctionNegatedUndesignated
    ]