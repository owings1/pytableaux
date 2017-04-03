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
# pytableaux - Lukasiewicz 3-valued Logic

"""
Lukasiewicz 3-valued logic is the same as K3, with a different conditional
operator that respects the law of conditional identity (if A, then A).

Semantics
---------

The semantics for L3 is the same as K3, except for the Conditional and Biconditional
operators (see below).
"""
name = 'L3'
description = 'Lukasiewicz 3-valued Logic'

import fde, k3
import logic
from logic import operate, negate

def example_validities():
    args = k3.example_validities()
    args.remove('Conditional Contraction')
    args.update([
        'Biconditional Identity' ,
        'Conditional Identity'   ,
    ])
    return args

def example_invalidities():
    import cfol
    args = cfol.example_invalidities()
    args.update([
        'Conditional Contraction'         ,
        'Conditional Pseudo Contraction'  ,
        'Law of Excluded Middle'          ,
        'Material Biconditional Identity' ,
        'Material Identity'               ,
        'Material Pseudo Contraction'     ,
    ])
    return args

truth_values = k3.truth_values
truth_value_chars = k3.truth_value_chars
designated_values = k3.designated_values
undesignated_values = k3.undesignated_values
unassigned_value = k3.unassigned_value
truth_functional_operators = fde.truth_functional_operators

def truth_function(operator, a, b=None):
    if operator == 'Conditional' or operator == 'Biconditional':
        if a == 0.5 and b == 0.5:
            return 1
    return fde.truth_function(operator, a, b)

class TableauxSystem(fde.TableauxSystem):
    """
    L3's Tableaux System inherits directly from FDE's.
    """
    pass

class TableauxRules(object):
    """
    The Tableaux rules for L3 contain the rules for FDE, except for different
    rules for the conditional and biconditional operators. It also contains the
    additional K3 closure rule.

    In this implementation, we have chosen rules for the defined biconditional
    operator, that reduce a biconditional sentence to a conjunction of conditionals
    (A iff B reduces to (if A then B) and (if B then A)). We then rely on the rules
    for conjunction and the conditional to further break down these nodes.
    """

    class ConditionalDesignated(logic.TableauxSystem.ConditionalNodeRule):
        """
        From an unticked designated conditional node *n* on a branch *b*, make two
        new branches *b'* and *b''* from *b*, add a material conditional designated
        node to *b'* with the same operands as *n*, and add four undesignated nodes
        to *b''*: a node with the antecedent, a node with the negation of the antecedent,
        a node with the consequent, and a node with the negation of the consequent.
        Then tick *n*.
        """
        operator    = 'Conditional'
        designation = True

        def apply_to_node(self, node, branch):
            b1 = branch
            b2 = self.tableau.branch(branch)
            s = node.props['sentence']
            b1.add(
                { 'sentence' : operate('Material Conditional', s.operands), 'designated' : True }
            ).tick(node)
            b2.update([
                { 'sentence' :        s.lhs,  'designated' : False },
                { 'sentence' : negate(s.lhs), 'designated' : False },
                { 'sentence' :        s.rhs,  'designated' : False },
                { 'sentence' : negate(s.rhs), 'designated' : False }
            ]).tick(node)

    class ConditionalUndesignated(logic.TableauxSystem.ConditionalNodeRule):
        """
        From an unticked undesignated conditional node *n* on a branch *b*, add a
        material conditional undesignated node to *b* with the same operands as *n*,
        then make two new branches *b'* and *b''* from *b*, and add a designated node
        with the antecedent and an undesignated node with the consequent to *b'* ,
        and add an undesignated node with the antecedent, an undesignated node with
        the negation of the antecedent, and a designated node to *b''* with the
        negation of the consequent to *b''*, then tick *n*.        
        """

        operator    = 'Conditional'
        designation = False

        def apply_to_node(self, node, branch):
            s = node.props['sentence']
            b1 = branch
            b1.add({ 'sentence' : operate('Material Conditional', s.operands), 'designated' : False })
            b2 = self.tableau.branch(branch)
            b1.update([
                { 'sentence' :        s.lhs,  'designated' : True  },
                { 'sentence' :        s.rhs,  'designated' : False }
            ]).tick(node)
            b2.update([
                { 'sentence' :        s.lhs,  'designated' : False },
                { 'sentence' : negate(s.lhs), 'designated' : False },
                { 'sentence' : negate(s.rhs), 'designated' : True  }
            ]).tick(node)

    class BiconditionalDesignated(logic.TableauxSystem.ConditionalNodeRule):
        """
        From an unticked designated biconditional node *n* on a branch *b*, add a
        conjunction designated node to *b*, with first conjunct being a conditional
        with the same operands as *n*, and the second conjunct being a conditional
        with the reversed operands of *n*, then tick *n*.
        """

        operator    = 'Biconditional'
        designation = True

        def apply_to_node(self, node, branch):
            s = node.props['sentence']
            branch.add({
                'sentence' : operate('Conjunction', [
                    operate('Conditional', s.operands),
                    operate('Conditional', [s.rhs, s.lhs])
                ]),
                'designated' : True
            })
            branch.tick(node)

    class BiconditionalNegatedDesignated(logic.TableauxSystem.ConditionalNodeRule):
        """
        From an unticked designated negated biconditional node *n* on a branch *b*,
        add a negated conjunction designated node to *b*, with the first conjunct being
        a conditional with the same operands as *b*, and the second conjunct being a
        conditional with the reversed operands of *n*, then tick *n*.
        """

        negated     = True
        operator    = 'Biconditional'
        designation = True

        def apply_to_node(self, node, branch):
            s = node.props['sentence'].operand
            branch.add({
                'sentence' : negate(
                    operate('Conjunction', [
                        operate('Conditional', s.operands),
                        operate('Conditional', [s.rhs, s.lhs])
                    ])
                ),
                'designated' : True
            })
            branch.tick(node)

    class BiconditionalUndesignated(logic.TableauxSystem.ConditionalNodeRule):
        """
        From an unticked undesignated biconditional node *n* on a branch *b*, add a
        conjunction undesignated node to *b*, with first conjunct being a conditional
        with the same operands as *n*, and the second conjunct being a conditional
        with the reversed operands of *n*, then tick *n*.
        """

        operator    = 'Biconditional'
        designation = False

        def apply_to_node(self, node, branch):
            s = node.props['sentence']
            branch.add({
                'sentence' : operate('Conjunction', [
                    operate('Conditional', s.operands),
                    operate('Conditional', [s.rhs, s.lhs])
                ]),
                'designated' : False
            })
            branch.tick(node)

    class BiconditionalNegatedUndesignated(logic.TableauxSystem.ConditionalNodeRule):
        """
        From an unticked undesignated negated biconditional node *n* on a branch *b*,
        add a negated conjunction undesignated node to *b*, with the first conjunct being
        a conditional with the same operands as *b*, and the second conjunct being a
        conditional with the reversed operands of *n*, then tick *n*.
        """

        negated     = True
        operator    = 'Biconditional'
        designation = False

        def apply_to_node(self, node, branch):
            s = node.props['sentence'].operand
            branch.add({
                'sentence' : negate(
                    operate('Conjunction', [
                        operate('Conditional', s.operands),
                        operate('Conditional', [s.rhs, s.lhs])
                    ])
                ),
                'designated' : False
            })
            branch.tick(node)

    rules = [

        fde.TableauxRules.Closure,
        k3.TableauxRules.Closure,

        # non-branching rules

        fde.TableauxRules.AssertionDesignated,
        fde.TableauxRules.AssertionUndesignated,
        fde.TableauxRules.AssertionNegatedDesignated,
        fde.TableauxRules.AssertionNegatedUndesignated,
        fde.TableauxRules.ConjunctionDesignated, 
        fde.TableauxRules.DisjunctionNegatedDesignated,
        fde.TableauxRules.DisjunctionUndesignated,
        fde.TableauxRules.DisjunctionNegatedUndesignated,
        fde.TableauxRules.MaterialConditionalNegatedDesignated,
        fde.TableauxRules.MaterialConditionalUndesignated,
        fde.TableauxRules.ConditionalNegatedDesignated,
        BiconditionalDesignated,
        BiconditionalNegatedDesignated,
        BiconditionalUndesignated,
        BiconditionalNegatedUndesignated,
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

        # branching rules

        fde.TableauxRules.ConjunctionNegatedDesignated,
        fde.TableauxRules.ConjunctionUndesignated,
        fde.TableauxRules.ConjunctionNegatedUndesignated,
        fde.TableauxRules.DisjunctionDesignated,
        fde.TableauxRules.MaterialConditionalDesignated,
        fde.TableauxRules.MaterialConditionalNegatedUndesignated,
        fde.TableauxRules.MaterialBiconditionalDesignated,
        fde.TableauxRules.MaterialBiconditionalNegatedDesignated,
        fde.TableauxRules.MaterialBiconditionalUndesignated,
        fde.TableauxRules.MaterialBiconditionalNegatedUndesignated,
        ConditionalDesignated,
        ConditionalUndesignated,
        fde.TableauxRules.ConditionalNegatedUndesignated
    ]