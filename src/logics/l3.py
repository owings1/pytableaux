# -*- coding: utf-8 -*-
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
# pytableaux - Lukasiewicz 3-valued Logic

"""
Semantics
=========
Ł3 is a three-valued logic with values **T**, **F**, and **N**. It is
similar to K3, but with a different, primitive conditional 
operator that respects the Law of Conditional Identity (P{A $ A}).

Truth Tables
------------

**Truth-functional operators** are defined via truth tables below. Note the
value of the Conditional operator when both operands have the value **N**.

/truth_tables/

Predication
-----------

**Predicate Sentences** are handled as in `K3 Predication`_.

Quantification
--------------

**Quantification** is handled as in `K3 Quantification`_.

Logical Consequence
-------------------

**Logical Consequence** is defined just like in `CPL`_ and `K3`_:

- *C* is a **Logical Consequence** of *A* iff all cases where the value of *A* is **T**
  are cases where *C* also has the value **T**.

.. _K3: k3.html

.. _K3 Predication: k3.html#predication

.. _K3 Quantification: k3.html#quantification

.. _FDE: fde.html

.. _CPL: cpl.html
"""
name = 'L3'
title = u'Łukasiewicz 3-valued Logic'
description = 'Three-valued logic (True, False, Neither) with a primitive Conditional operator'
tags_list = ['many-valued', 'gappy', 'non-modal', 'first-order']
tags = set(tags_list)
category = 'Many-valued'
category_display_order = 6

from . import fde, k3
import logic
from logic import operate, negate

class Model(k3.Model):

    def truth_function(self, operator, a, b=None):
        if operator == 'Conditional' or operator == 'Biconditional':
            if a == self.char_values['N'] and b == self.char_values['N']:
                return self.char_values['T']
        return super(Model, self).truth_function(operator, a, b)

class TableauxSystem(fde.TableauxSystem):
    """
    Ł3's Tableaux System inherits directly from `FDE`_'s, employing designation markers,
    and building the trunk in the same way.
    """
    pass

class TableauxRules(object):
    """
    The closure rules for Ł3 are the `FDE closure rule`_, and the `K3 closure rule`_.
    The operator rules for Ł3 are mostly the rules for `FDE`_, with the exception
    of the rules for the conditional and biconditional operators.

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

    class AssertionNegatedDesignated(fde.TableauxRules.AssertionNegatedDesignated):
        """
        This rule is the same as the `FDE AssertionNegatedDesignated rule`_.

        .. _FDE AssertionNegatedDesignated rule: fde.html#logics.fde.TableauxRules.AssertionNegatedDesignated
        """
        pass

    class AssertionUndesignated(fde.TableauxRules.AssertionUndesignated):
        """
        This rule is the same as the `FDE AssertionUndesignated rule`_.

        .. _FDE AssertionUndesignated rule: fde.html#logics.fde.TableauxRules.AssertionUndesignated
        """
        pass

    class AssertionNegatedUndesignated(fde.TableauxRules.AssertionNegatedUndesignated):
        """
        This rule is the same as the `FDE AssertionNegatedUndesignated rule`_.

        .. _FDE AssertionNegatedUndesignated rule: fde.html#logics.fde.TableauxRules.AssertionNegatedUndesignated
        """
        pass

    class ConjunctionDesignated(fde.TableauxRules.ConjunctionDesignated):
        """
        This rule is the same as the `FDE ConjunctionDesignated rule`_.

        .. _FDE ConjunctionDesignated rule: fde.html#logics.fde.TableauxRules.ConjunctionDesignated
        """
        pass

    class ConjunctionNegatedDesignated(fde.TableauxRules.ConjunctionNegatedDesignated):
        """
        This rule is the same as the `FDE ConjunctionNegatedDesignated rule`_.

        .. _FDE ConjunctionNegatedDesignated rule: fde.html#logics.fde.TableauxRules.ConjunctionNegatedDesignated
        """
        pass

    class ConjunctionUndesignated(fde.TableauxRules.ConjunctionUndesignated):
        """
        This rule is the same as the `FDE ConjunctionUndesignated rule`_.

        .. _FDE ConjunctionUndesignated rule: fde.html#logics.fde.TableauxRules.ConjunctionUndesignated
        """
        pass

    class ConjunctionNegatedUndesignated(fde.TableauxRules.ConjunctionNegatedUndesignated):
        """
        This rule is the same as the `FDE ConjunctionNegatedUndesignated rule`_.

        .. _FDE ConjunctionNegatedUndesignated rule: fde.html#logics.fde.TableauxRules.ConjunctionNegatedUndesignated
        """
        pass

    class DisjunctionDesignated(fde.TableauxRules.DisjunctionDesignated):
        """
        This rule is the same as the `FDE DisjunctionDesignated rule`_.

        .. _FDE DisjunctionDesignated rule: fde.html#logics.fde.TableauxRules.DisjunctionDesignated
        """
        pass

    class DisjunctionNegatedDesignated(fde.TableauxRules.DisjunctionNegatedDesignated):
        """
        This rule is the same as the `FDE DisjunctionNegatedDesignated rule`_.

        .. _FDE DisjunctionNegatedDesignated rule: fde.html#logics.fde.TableauxRules.DisjunctionNegatedDesignated
        """
        pass

    class DisjunctionUndesignated(fde.TableauxRules.DisjunctionUndesignated):
        """
        This rule is the same as the `FDE DisjunctionUndesignated rule`_.

        .. _FDE DisjunctionUndesignated rule: fde.html#logics.fde.TableauxRules.DisjunctionUndesignated
        """
        pass

    class DisjunctionNegatedUndesignated(fde.TableauxRules.DisjunctionNegatedUndesignated):
        """
        This rule is the same as the `FDE DisjunctionNegatedUndesignated rule`_.

        .. _FDE DisjunctionNegatedUndesignated rule: fde.html#logics.fde.TableauxRules.DisjunctionNegatedUndesignated
        """
        pass

    class MaterialConditionalDesignated(fde.TableauxRules.MaterialConditionalDesignated):
        """
        This rule is the same as the `FDE MaterialConditionalDesignated rule`_.

        .. _FDE MaterialConditionalDesignated rule: fde.html#logics.fde.TableauxRules.MaterialConditionalDesignated
        """
        pass

    class MaterialConditionalNegatedDesignated(fde.TableauxRules.MaterialConditionalNegatedDesignated):
        """
        This rule is the same as the `FDE MaterialConditionalNegatedDesignated rule`_.

        .. _FDE MaterialConditionalNegatedDesignated rule: fde.html#logics.fde.TableauxRules.MaterialConditionalNegatedDesignated
        """
        pass

    class MaterialConditionalNegatedUndesignated(fde.TableauxRules.MaterialConditionalNegatedUndesignated):
        """
        This rule is the same as the `FDE MaterialConditionalNegatedUndesignated rule`_.

        .. _FDE MaterialConditionalNegatedUndesignated rule: fde.html#logics.fde.TableauxRules.MaterialConditionalNegatedUndesignated
        """
        pass

    class MaterialConditionalUndesignated(fde.TableauxRules.MaterialConditionalUndesignated):
        """
        This rule is the same as the `FDE MaterialConditionalUndesignated rule`_.

        .. _FDE MaterialConditionalUndesignated rule: fde.html#logics.fde.TableauxRules.MaterialConditionalUndesignated
        """
        pass

    class MaterialBiconditionalDesignated(fde.TableauxRules.MaterialBiconditionalDesignated):
        """
        This rule is the same as the `FDE MaterialBiconditionalDesignated rule`_.

        .. _FDE MaterialBiconditionalDesignated rule: fde.html#logics.fde.TableauxRules.MaterialBiconditionalDesignated
        """
        pass

    class MaterialBiconditionalNegatedDesignated(fde.TableauxRules.MaterialBiconditionalNegatedDesignated):
        """
        This rule is the same as the `FDE MaterialBiconditionalNegatedDesignated rule`_.

        .. _FDE MaterialBiconditionalNegatedDesignated rule: fde.html#logics.fde.TableauxRules.MaterialBiconditionalNegatedDesignated
        """
        pass

    class MaterialBiconditionalUndesignated(fde.TableauxRules.MaterialBiconditionalUndesignated):
        """
        This rule is the same as the `FDE MaterialBiconditionalUndesignated rule`_.

        .. _FDE MaterialBiconditionalUndesignated rule: fde.html#logics.fde.TableauxRules.MaterialBiconditionalUndesignated
        """
        pass

    class MaterialBiconditionalNegatedUndesignated(fde.TableauxRules.MaterialBiconditionalNegatedUndesignated):
        """
        This rule is the same as the `FDE MaterialBiconditionalNegatedUndesignated rule`_.

        .. _FDE MaterialBiconditionalNegatedUndesignated rule: fde.html#logics.fde.TableauxRules.MaterialBiconditionalNegatedUndesignated
        """
        pass


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

    class ConditionalNegatedDesignated(fde.TableauxRules.ConditionalNegatedDesignated):
        """
        This rule is the same as the `FDE ConditionalNegatedDesignated rule`_.

        .. _FDE ConditionalNegatedDesignated rule: fde.html#logics.fde.TableauxRules.ConditionalNegatedDesignated
        """
        pass

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

    class ConditionalNegatedUndesignated(fde.TableauxRules.ConditionalNegatedUndesignated):
        """
        This rule is the same as the `FDE ConditionalNegatedUndesignated rule`_.

        .. _FDE ConditionalNegatedUndesignated rule: fde.html#logics.fde.TableauxRules.ConditionalNegatedUndesignated
        """
        pass
        
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

    class ExistentialDesignated(fde.TableauxRules.ExistentialDesignated):
        """
        This rule is the same as the `FDE ExistentialDesignated rule`_.

        .. _FDE ExistentialDesignated rule: fde.html#logics.fde.TableauxRules.ExistentialDesignated
        """
        pass

    class ExistentialNegatedDesignated(fde.TableauxRules.ExistentialNegatedDesignated):
        """
        This rule is the same as the `FDE ExistentialNegatedDesignated rule`_.

        .. _FDE ExistentialNegatedDesignated rule: fde.html#logics.fde.TableauxRules.ExistentialNegatedDesignated
        """
        pass

    class ExistentialUndesignated(fde.TableauxRules.ExistentialUndesignated):
        """
        This rule is the same as the `FDE ExistentialUndesignated rule`_.

        .. _FDE ExistentialUndesignated rule: fde.html#logics.fde.TableauxRules.ExistentialUndesignated
        """
        pass

    class ExistentialNegatedUndesignated(fde.TableauxRules.ExistentialNegatedUndesignated):
        """
        This rule is the same as the `FDE ExistentialNegatedUndesignated rule`_.

        .. _FDE ExistentialNegatedUndesignated rule: fde.html#logics.fde.TableauxRules.ExistentialNegatedUndesignated
        """
        pass

    class UniversalDesignated(fde.TableauxRules.UniversalDesignated):
        """
        This rule is the same as the `FDE UniversalDesignated rule`_.

        .. _FDE UniversalDesignated rule: fde.html#logics.fde.TableauxRules.UniversalDesignated
        """
        pass

    class UniversalNegatedDesignated(fde.TableauxRules.UniversalNegatedDesignated):
        """
        This rule is the same as the `FDE UniversalNegatedDesignated rule`_.

        .. _FDE UniversalNegatedDesignated rule: fde.html#logics.fde.TableauxRules.UniversalNegatedDesignated
        """
        pass

    class UniversalUndesignated(fde.TableauxRules.UniversalUndesignated):
        """
        This rule is the same as the `FDE UniversalUndesignated rule`_.

        .. _FDE UniversalUndesignated rule: fde.html#logics.fde.TableauxRules.UniversalUndesignated
        """
        pass

    class UniversalNegatedUndesignated(fde.TableauxRules.UniversalNegatedUndesignated):
        """
        This rule is the same as the `FDE UniversalNegatedUndesignated rule`_.

        .. _FDE UniversalNegatedUndesignated rule: fde.html#logics.fde.TableauxRules.UniversalNegatedUndesignated
        """
        pass

    rules = [

        fde.TableauxRules.Closure,
        k3.TableauxRules.Closure,

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
        ConditionalNegatedDesignated,
        BiconditionalDesignated,
        BiconditionalNegatedDesignated,
        BiconditionalUndesignated,
        BiconditionalNegatedUndesignated,
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
        ConditionalUndesignated,
        ConditionalNegatedUndesignated,
    ]