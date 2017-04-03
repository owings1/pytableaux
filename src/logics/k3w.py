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
# pytableaux - Weak Kleene Logic

"""
K3W is a 3-valued logic (True, False, and Neither), just like Strong Kleene (K3),
with different treatment of conjunction and disjunction. This logic is also known
as Bochvar Internal (B3).

Semantics
---------

The truth-functional operators are defined via truth tables below.
Negation is the same as K3, but the table for disjunction does not admit a sentence
with the value **N** for *either* disjunct to be true. Likewise for the other
binary connectives. Hence the saying "one bit of rat's dung spoils the soup," or something.

**Predicate Sentences** and **Quantification** are handled the same as in FDE.

**Logical Consequence** is defined the same as in K3.

"""
name = 'K3W'
description = 'Weak Kleene 3-valued logic'

import fde, k3

def example_validities():
    args = set([
        'Biconditional Elimination 1'   ,
        'Biconditional Elimination 2'   ,
        'Conditional Contraction'       ,
        'Conditional Modus Ponens'      ,
        'Conditional Modus Tollens'     ,
        'DeMorgan 1'                    ,
        'DeMorgan 2'                    ,
        'DeMorgan 3'                    ,
        'DeMorgan 4'                    ,
        'Disjunctive Syllogism'         ,
        'Existential Syllogism'         ,
        'Law of Non-contradiction'      ,
        'Material Contraction'          ,
        'Material Modus Ponens'         ,
        'Material Modus Tollens'        ,
        'Modal Platitude 1'             ,
        'Modal Platitude 2'             ,
        'Modal Platitude 3'             ,
        'Simplification'                ,
        'Syllogism'                     ,
        'Universal Predicate Syllogism' ,
    ])
    return args
    
def example_invalidities():
    args = k3.example_invalidities()
    args.update([
        'Addition',
    ])
    return args
    
import logic
from logic import negate, operate

truth_values = k3.truth_values
truth_value_chars = k3.truth_value_chars
designated_values = k3.designated_values
undesignated_values = k3.undesignated_values
unassigned_value = k3.unassigned_value
truth_functional_operators = fde.truth_functional_operators

def truth_function(operator, a, b=None):
    if logic.arity(operator) == 2 and (a == 0.5 or b == 0.5):
        return 0.5
    return fde.truth_function(operator, a, b)

class TableauxSystem(fde.TableauxSystem):
    """
    K3W's Tableaux System inherits directly from FDE's.
    """
    pass
        
class TableauxRules(object):
    """
    The Tableaux System for K3W contains the closure rules from FDE and K3, and all of
    the designated rules for FDE. The undesignated rules for K3W are different, given
    the behavior of disjunction when both disjuncts have the value *N*.
    """

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

    class MaterialConditionalUndesignated(MaterialConditionalDesignated):
        """
        This rule reduces to a disjunction.
        """

        designation = False

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

    class MaterialBiconditionalUndesignated(MaterialBiconditionalDesignated):
        """
        This rule reduces to a conjunction of material conditionals.
        """

        designation = False

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

    class ConditionalUndesignated(MaterialConditionalUndesignated):
        """
        Same as for the material conditional undesignated.
        """

        operator = 'Conditional'

    class ConditionalNegatedDesignated(MaterialConditionalNegatedDesignated):
        """
        Same as for the negated material conditional designated.
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

    class BiconditionalUndesignated(MaterialBiconditionalUndesignated):
        """
        Same as for the material biconditional undesignated.
        """

        operator = 'Biconditional'

    class BiconditionalNegatedDesignated(MaterialBiconditionalNegatedDesignated):
        """
        Same as for the negated material biconditional designated.
        """

        operator = 'Biconditional'

    class BiconditionalNegatedUndesignated(MaterialBiconditionalNegatedUndesignated):
        """
        Same as for the negated material biconditional undesignated.
        """

        operator = 'Biconditional'

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
        fde.TableauxRules.ConjunctionUndesignated,

        # three-branching rules
        DisjunctionDesignated,
        DisjunctionUndesignated,
        ConjunctionNegatedDesignated,
        ConjunctionNegatedUndesignated,

        # four-branching rules
        DisjunctionNegatedUndesignated
    ]