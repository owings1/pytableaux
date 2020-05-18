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
# pytableaux - R-mingle 3 logic
"""
Semantics
=========

R-mingle 3 (RM3) is a three-valued logic with values **T**, **F**, and **B**.
It is similar to `LP`_, with a different conditional operator.

Truth Tables
------------

**Truth-functional operators** are defined via truth tables below. Note the
distinct treatment of the conditional (and thus the biconditional) operators.

/truth_tables/

Predication
-----------

**Predicate Sentences** are handled the same way as in `LP Predication`_.

Quantification
--------------

**Quantification** is handled as in `LP Quantification`_.

Logical Consequence
-------------------

**Logical Consequence** is defined, just as in `FDE`_, in terms of *designated* values **T**
and **B**:

- *C* is a **Logical Consequence** of *A* iff all cases where *A* has a *designated*
  value (**T** or **B**) are cases where *C* also has a *designated* value.

.. _LP: lp.html

.. _LP Predication: lp.html#predication

.. _LP Quantification: lp.html#quantification

.. _FDE: fde.html

.. _L3: l3.html
"""
name = 'RM3'
title = 'R-mingle 3'
description = 'Three-valued logic (True, False, Both) with a primitive Conditional operator'
tags = set(['many-valued', 'glutty', 'non-modal', 'first-order'])
tags_list = list(tags)

import logic
from logic import negate, operate
from . import fde, lp, l3

class Model(lp.Model):

    def truth_function(self, operator, a, b=None):
        if operator == 'Conditional' and a > b:
            return self.char_values['F']
        return super(Model, self).truth_function(operator, a, b)

class TableauxSystem(fde.TableauxSystem):
    """
    RM3 tableaux behave just like `FDE`_'s using designation markers. The trunk
    is built in the same way.
    """
    pass

class TableauxRules(object):
    """
    The closure rules for RM3 are the `FDE closure rule`_, and the `LP closure rule`_.
    Most of the operator rules are the same as `FDE`_, except for the conditional
    rules. The biconditional rules are borrowed from `L3_`, since they are
    simplification rules.

    .. _FDE closure rule: fde.html#logics.fde.TableauxRules.Closure
    .. _LP closure rule: lp.html#logics.lp.TableauxRules.Closure
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

    class ConditionalDesignated(fde.TableauxRules.ConditionalDesignated):
        """
        From an unticked, designated conditional node *n* on a branch *b*, make
        three branches *b'*, *b''*, and *b'''* from *b*. On *b'*, add an undesignated
        node with the antecedent, and a designated node with the negation of the
        antecedent. On *b''*, add a designated node with the consequent, and an
        undesignated node with the negation of the consequent. On *b'''*, add
        four designated nodes, with the antecedent, the negation of the antecedent,
        the consequent, and the negation of the consequent, respecitively. Then tick *n*.
        """
        def apply_to_node(self, node, branch):
            lhs, rhs = self.sentence(node).operands
            b1 = branch
            b2 = self.tableau.branch(branch)
            b3 = self.tableau.branch(branch)
            b1.update([
                {'sentence': lhs, 'designated': False},
                {'sentence': negate(lhs), 'designated': True}
            ]).tick(node)
            b2.update([
                {'sentence': rhs, 'designated': True},
                {'sentence': negate(rhs), 'designated': False}
            ]).tick(node)
            b3.update([
                {'sentence': lhs, 'designated': True},
                {'sentence': negate(lhs), 'designated': True},
                {'sentence': rhs, 'designated': True},
                {'sentence': negate(rhs), 'designated': True}
            ]).tick(node)

    class ConditionalNegatedDesignated(fde.TableauxRules.ConditionalNegatedDesignated):
        """
        This rule is the same as the `FDE ConditionalNegatedDesignated rule`_.

        .. _FDE ConditionalNegatedDesignated rule: fde.html#logics.fde.TableauxRules.ConditionalNegatedDesignated
        """
        pass

    class ConditionalUndesignated(fde.TableauxRules.ConditionalUndesignated):
        """
        From an unticked, undesignated conditional node *n* on a branch *b*, make
        two branches *b'* and *b''* from *b*. On *b'*, add a designated node
        with the antecedent, and an undesignated node with with consequent.
        On *b''*, add an undesignated node with the negation of the antecedent,
        and a designated node with the negation of the consequent. Then tick *n*.
        """
        def apply_to_node(self, node, branch):
            lhs, rhs = self.sentence(node).operands
            b1 = branch
            b2 = self.tableau.branch(branch)
            b1.update([
                {'sentence': lhs, 'designated': True},
                {'sentence': rhs, 'designated': False}
            ]).tick(node)
            b2.update([
                {'sentence': negate(lhs), 'designated': False},
                {'sentence': negate(rhs), 'designated': True}
            ]).tick(node)

    class ConditionalNegatedUndesignated(fde.TableauxRules.ConditionalNegatedUndesignated):
        """
        From an unticked, undesignated, negated conditional node *n* on a branch *b*,
        make two branches *b'* and *b''* from *b*. On *b'*, add an undesignated node
        with the antecedent. On *b''*, add an undesignated node with the negation of
        the consequent. Then tick *n*.
        """
        def apply_to_node(self, node, branch):
            lhs, rhs = self.sentence(node).operands
            b1 = branch
            b2 = self.tableau.branch(branch)
            b1.add({'sentence': lhs, 'designated': False}).tick(node)
            b2.add({'sentence': negate(rhs), 'designated': False}).tick(node)
        
    class BiconditionalDesignated(l3.TableauxRules.BiconditionalDesignated):
        """
        This rule is the same as the `L3 BiconditionalDesignated rule`_.

        .. _L3 BiconditionalDesignated rule: l3.html#logics.l3.TableauxRules.BiconditionalDesignated
        """
        pass

    class BiconditionalNegatedDesignated(l3.TableauxRules.BiconditionalNegatedDesignated):
        """
        This rule is the same as the `L3 BiconditionalNegatedDesignated rule`_.

        .. _L3 BiconditionalNegatedDesignated rule: l3.html#logics.l3.TableauxRules.BiconditionalNegatedDesignated
        """
        pass

    class BiconditionalUndesignated(l3.TableauxRules.BiconditionalUndesignated):
        """
        This rule is the same as the `L3 BiconditionalUndesignated rule`_.

        .. _L3 BiconditionalUndesignated rule: l3.html#logics.l3.TableauxRules.BiconditionalUndesignated
        """
        pass

    class BiconditionalNegatedUndesignated(l3.TableauxRules.BiconditionalNegatedUndesignated):
        """
        This rule is the same as the `L3 BiconditionalNegatedUndesignated rule`_.

        .. _L3 BiconditionalNegatedUndesignated rule: l3.html#logics.l3.TableauxRules.BiconditionalNegatedUndesignated
        """
        pass

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
        lp.TableauxRules.Closure,

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
        BiconditionalDesignated,
        BiconditionalNegatedDesignated,
        BiconditionalUndesignated,
        BiconditionalNegatedUndesignated,

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
        ConditionalNegatedUndesignated,
        ConditionalUndesignated,

        # 3-branching rules
        ConditionalDesignated,

    ]