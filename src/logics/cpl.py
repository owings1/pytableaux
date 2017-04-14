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
# pytableaux - Classical Predicate Logic

"""
Classical Predicate Logic (CPL) is the standard bivalent logic (True, False).

Semantics
---------

Truth functional operators are defined via truth tables (below).

**Predicate Sentences** like *P{Fa}* are handled via a predicate's *extension*:

- *P{Fa}* is true iff the object denoted by the constant *a* is in the extension of the predicate *F*.

*C* is a **Logical Consequence** of *A* iff all cases where the value of *A* is true
are cases where *C* also has the value true.
"""

import k, fde

name = 'CPL'
description = 'Classical Predicate Logic'

def example_validities():
    # Everything valid in K3 or LP is valid in CPL, except quantifier validities
    args = set([
        'Addition'                        ,
        'Biconditional Elimination 1'     ,
        'Biconditional Elimination 2'     ,
        'Biconditional Identity'          ,
        'Conditional Contraction'         ,
        'Conditional Identity'            ,
        'Conditional Modus Ponens'        ,
        'Conditional Modus Tollens'       ,
        'Conditional Pseudo Contraction'  ,
        'DeMorgan 1'                      ,
        'DeMorgan 2'                      ,
        'DeMorgan 3'                      ,
        'DeMorgan 4'                      ,
        'Disjunctive Syllogism'           ,
        'Law of Excluded Middle'          ,
        'Law of Non-contradiction'        ,
        'Material Biconditional Identity' ,
        'Material Contraction'            ,
        'Material Identity'               ,
        'Material Modus Ponens'           ,
        'Material Modus Tollens'          ,
        'Material Pseudo Contraction'     ,
        'Modal Platitude 1'               ,
        'Modal Platitude 2'               ,
        'Modal Platitude 3'               ,
        'Simplification'                  ,
    ])
    return args

def example_invalidities():
    import cfol
    args = cfol.example_invalidities()
    args.update([
        'Existential Syllogism'         ,
        'Syllogism'                     ,
        'Universal Predicate Syllogism' ,
    ])
    return args

import logic, examples
from logic import negate

truth_values = k.truth_values
truth_value_chars = k.truth_value_chars
designated_values = k.designated_values
undesignated_values = k.undesignated_values
unassigned_value = k.unassigned_value
truth_functional_operators = fde.truth_functional_operators
truth_function = fde.truth_function

class Model(k.Model):

    def set_atomic_value(self, atomic, value):
        return super(Model, self).set_atomic_value(atomic, value, 0)

    def get_atomic_value(self, atomic):
        return super(Model, self).get_atomic_value(atomic, 0)

    def set_predicated_value(self, sentence, value):
        return super(Model, self).set_predicated_value(sentence, value, 0)

    def get_extension(self, predicate):
        return super(Model, self).get_extension(predicate, 0)
        
    def add_access(self, w1, w2):
        raise Exception(NotImplemented)

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

    @staticmethod
    def read_model(model, branch):
        """
        To read a model from a branch *b*, every atomic sentence on *b* is True,
        every negated atomic is False. For every predicate sentence Fa0...an on *b*,
        the tuple <a0,...,an> is in the extension of F.
        """
        for node in branch.get_nodes():
            if 'sentence' in node.props:
                s = node.props['sentence']
                if s.is_literal():
                    if s.is_operated():
                        assert s.operator == 'Negation'
                        value = 0
                        s = s.operand
                    else:
                        value = 1
                    if s.is_atomic():
                        model.set_atomic_value(s, value)
                    else:
                        assert s.is_predicated()
                        model.set_predicated_value(s, value)

class TableauxRules(object):
    """
    The Tableaux System for CPL contains all the operator rules from K, except for
    the rules for the modal operators (Necessity, Possibility), and the quantifiers
    (Universal, Existential).
    """

    class Closure(logic.TableauxSystem.ClosureRule):
        """
        A branch is closed if a sentence and its negation appear on the branch.
        """

        def applies_to_branch(self, branch):
            for node in branch.get_nodes():
                n = branch.find({ 'sentence' : negate(node.props['sentence']) })
                if n:
                    return { 'nodes': set([node, n]), 'type' : 'Nodes' }
            return False

        def example(self):
            a = logic.atomic(0, 0)
            self.tableau.branch().update([{ 'sentence' : a }, { 'sentence' : negate(a) }])

    class SelfIdentityClosure(k.TableauxRules.SelfIdentityClosure):
        """
        A branch is closed if a sentence of the form *~ a = a* appears on the branch.
        """

        def example(self):
            s = negate(examples.self_identity())
            self.tableau.branch().add({ 'sentence' : s })

    class IdentityIndiscernability(k.TableauxRules.IdentityIndiscernability):
        """
        From an unticked node *n* having an Identity sentence *s* on an open branch *b*,
        and a predicated node *n'* whose sentence *s'* has a constant that is a parameter of *s*,
        if the replacement of that constant for the other constant of *s* is a sentence that does
        not appear on *b*, then add it.
        """

        def example(self):
            self.tableau.branch().update([
                { 'sentence' : examples.predicated() },
                { 'sentence' : examples.identity()   }
            ])

    rules = [

        Closure,
        SelfIdentityClosure,

        # non-branching rules
        IdentityIndiscernability,
        k.TableauxRules.Assertion,
        k.TableauxRules.AssertionNegated,
        k.TableauxRules.Conjunction,
        k.TableauxRules.DisjunctionNegated,
        k.TableauxRules.MaterialConditionalNegated,
        k.TableauxRules.ConditionalNegated,
        k.TableauxRules.DoubleNegation,

        # branching rules

        k.TableauxRules.ConjunctionNegated,
        k.TableauxRules.Disjunction,
        k.TableauxRules.MaterialConditional,
        k.TableauxRules.MaterialBiconditional,
        k.TableauxRules.MaterialBiconditionalNegated,
        k.TableauxRules.Conditional,
        k.TableauxRules.Biconditional,
        k.TableauxRules.BiconditionalNegated

    ]