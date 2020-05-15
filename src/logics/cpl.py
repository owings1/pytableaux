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
# pytableaux - Classical Predicate Logic

"""
Semantics
=========

Classical Predicate Logic (CPL) is the standard bivalent logic with
values **T** and **F**, commonly interpretated as 'true' and 'false',
respectively.

Truth Tables
------------

**Truth-functional operators** are defined via the following truth tables.

/truth_tables/

Predication
-----------

**Predicate Sentences** like *P{Fa}* are handled via a predicate's *extension*:

- *P{Fa}* is true iff the object denoted by *a* is in the extension of the predicate *F*.

Quantification
--------------
CPL does not have quantification. See `CFOL`_.

Logical Consequence
-------------------

**Logical Consequence** is defined as follows:

- *C* is a **Logical Consequence** of *A* iff all cases where the value of *A* is **T**
  are cases where *C* also has the value **T**.

.. _CFOL: cfol.html
"""

from . import k, fde

name = 'CPL'
title = 'Classical Predicate Logic'
description = 'Standard bivalent logic with predication, without quantification'
tags = set(['bivalent', 'non-modal'])
tags_list = list(tags)

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
    from . import cfol
    args = cfol.example_invalidities()
    args.update([
        'Existential Syllogism'         ,
        'Syllogism'                     ,
        'Universal Predicate Syllogism' ,
    ])
    return args

import logic, examples
from logic import negate, NotImplementedError

truth_values = k.truth_values
truth_value_chars = k.truth_value_chars
designated_values = k.designated_values
undesignated_values = k.undesignated_values
unassigned_value = k.unassigned_value
truth_functional_operators = fde.truth_functional_operators
truth_function = fde.truth_function

# NB: model semantics are a work in progress
class Model(k.Model):

    def set_atomic_value(self, atomic, value, world=None):
        return super(Model, self).set_atomic_value(atomic, value, 0)

    def set_predicated_value(self, sentence, value, world=None):
        return super(Model, self).set_predicated_value(sentence, value, 0)

    def get_extension(self, predicate, world=None):
        return super(Model, self).get_extension(predicate, 0)

    def value_of(self, sentence, world=None):
        return super(Model, self).value_of(sentence, 0)

    def add_access(self, w1, w2):
        raise NotImplementedError(NotImplemented)

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
            if node.has('sentence'):
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

class NonModal(object):
    modal = False

class TableauxRules(object):
    """
    In general, rules for connectives consist of two rules per connective:
    a "plain" rule, and a negated rule. The special case of negation has only
    one rule for double negation. There is also a special rule for Identity
    predicate.
    """

    class Closure(logic.TableauxSystem.ClosureRule):
        """
        A branch is closed if a sentence and its negation appear on the branch.
        """

        def applies_to_branch(self, branch):
            for node in branch.get_nodes():
                if node.has('sentence'):
                    n = branch.find({ 'sentence' : negate(node.props['sentence']) })
                    if n != None:
                        return { 'nodes': set([node, n]), 'type' : 'Nodes' }
            return False

        def example(self):
            a = logic.atomic(0, 0)
            self.tableau.branch().update([{ 'sentence' : a }, { 'sentence' : negate(a) }])

    class SelfIdentityClosure(NonModal, k.TableauxRules.SelfIdentityClosure):
        """
        A branch is closed if a sentence of the form P{~ a = a} appears on the branch.
        """

        def example(self):
            s = negate(examples.self_identity())
            self.tableau.branch().add({ 'sentence' : s })

    class DoubleNegation(NonModal, k.TableauxRules.DoubleNegation):
        """
        From an unticked double negation node *n* on a branch *b*, add a
        node to *b* with the double-negatum of *n*, then tick *n*.
        """
        pass

    class Assertion(NonModal, k.TableauxRules.Assertion):
        """
        From an unticked assertion node *n* on a branch *b*,
        add a node to *b* with the operand of *n*, then tick *n*.
        """
        pass

    class AssertionNegated(NonModal, k.TableauxRules.AssertionNegated):
        """
        From an unticked, negated assertion node *n* on a branch *b*,
        add a node to *b* with the negation of the assertion of *n*,
        then tick *n*.
        """
        pass

    class Conjunction(NonModal, k.TableauxRules.Conjunction):
        """
        From an unticked conjunction node *n* on a branch *b*, for each conjunct,
        add a node to *b* with the conjunct, then tick *n*.
        """
        pass

    class ConjunctionNegated(NonModal, k.TableauxRules.ConjunctionNegated):
        """
        From an unticked negated conjunction node *n* on a branch *b*, for each
        conjunct, make a new branch *b'* from *b* and add a node with the negation of
        the conjunct to *b*, then tick *n*.
        """
        pass

    class Disjunction(NonModal, k.TableauxRules.Disjunction):
        """
        From an unticked disjunction node *n* on a branch *b*, for each disjunct,
        make a new branch *b'* from *b* and add a node with the disjunct to *b'*,
        then tick *n*.
        """
        pass

    class DisjunctionNegated(NonModal, k.TableauxRules.DisjunctionNegated):
        """
        From an unticked negated disjunction node *n* on a branch *b*, for each
        disjunct, add a node with the negation of the disjunct to *b*, then tick *n*.
        """
        pass

    class MaterialConditional(NonModal, k.TableauxRules.MaterialConditional):
        """
        From an unticked material conditional node *n*on a branch *b*, make two
        new branches *b'* and *b''* from *b*, add a node with the negation of the
        antecedent to *b'*, and add a node with the conequent to *b''*, then tick
        *n*.
        """
        pass

    class MaterialConditionalNegated(NonModal, k.TableauxRules.MaterialConditionalNegated):
        """
        From an unticked negated material conditional node *n* on a branch *b*,
        add two nodes to *b*, one with the antecedent and the other with the negation
        of the consequent, then tick *n*.
        """
        pass

    class MaterialBiconditional(NonModal, k.TableauxRules.MaterialBiconditional):
        """
        From an unticked material biconditional node *n* on a branch *b*, make
        two new branches *b'* and *b''* from *b*, add two nodes to *b'*, one with
        the negation of the antecedent and one with the negation of the consequent,
        and add two nodes to *b''*, one with the antecedent and one with the consequent,
        then tick *n*.
        """
        pass

    class MaterialBiconditionalNegated(NonModal, k.TableauxRules.MaterialBiconditionalNegated):
        """
        From an unticked negated material biconditional node *n* on a branch *b*,
        make two new branches *b'* and *b''* from *b*, add two nodes to *b'*, one with
        the antecedent and the other with the negation of the consequent, and add two nodes
        to *b''*, one with the negation of the antecedent and the other with the consequent,
        then tick *n*.
        """
        pass

    class Conditional(NonModal, k.TableauxRules.Conditional):
        """
        The rule functions the same as the corresponding material conditional rule.

        From an unticked conditional node *n* on a branch *b*, make two
        new branches *b'* and *b''* from *b*, add a node with the negation of the
        antecedent to *b'*, and add a node with the conequent to *b''*, then tick
        *n*.
        """
        pass

    class ConditionalNegated(NonModal, k.TableauxRules.ConditionalNegated):
        """
        The rule functions the same as the corresponding material conditional rule.

        From an unticked negated conditional node *n* on a branch *b*,
        add two nodes to *b*, one with the antecedent and the other with the negation
        of the consequent, then tick *n*.
        """
        pass

    class Biconditional(NonModal, k.TableauxRules.Biconditional):
        """
        The rule functions the same as the corresponding material biconditional rule.

        From an unticked biconditional node *n* on a branch *b*, make
        two new branches *b'* and *b''* from *b*, add two nodes to *b'*, one with
        the negation of the antecedent and one with the negation of the consequent, and add two
        nodes to *b''*, one with the antecedent and one with the consequent, then
        tick *n*.
        """
        pass

    class BiconditionalNegated(NonModal, k.TableauxRules.BiconditionalNegated):
        """
        The rule functions the same as the corresponding material biconditional rule.

        From an unticked negated biconditional node *n* on a branch *b*,
        make two new branches *b'* and *b''* from *b*, add two nodes to *b'*, one with
        the antecedent and the other with the negation of the consequent, and add two nodes
        to *b''*, one with the negation of the antecedent and the other with the consequent,
        then tick *n*.
        """
        pass

    class IdentityIndiscernability(NonModal, k.TableauxRules.IdentityIndiscernability):
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
        Assertion,
        AssertionNegated,
        Conjunction,
        DisjunctionNegated,
        MaterialConditionalNegated,
        ConditionalNegated,
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