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
# pytableaux - Weak Kleene Logic
name = 'K3W'
title = 'Weak Kleene 3-valued logic'
description = 'Three-valued logic with values T, F, and N'
tags_list = ['many-valued', 'gappy', 'non-modal', 'first-order']
tags = set(tags_list)
category = 'Many-valued'
category_display_order = 3

import logic
from logic import negate, operate
from . import fde, k3

class Model(k3.Model):
    """
    A K3W model is just like a `K3 model`_ with different tables for some of the connectives.

    .. _K3 model: k3.html#logics.k3.Model
    """

    def value_of_operated(self, sentence, **kw):
        """
        The value of a sentence with a truth-functional operator is determined by
        the values of its operands according to the following tables.

        Note that, for the binary connectives, if either operand has the value **N**,
        then the whole sentence has the value **N**. Hence the saying, "one bit of rat's
        dung spoils the soup."

        //truth_tables//k3w//
        """
        return super(Model, self).value_of_operated(sentence, **kw)

    def truth_function(self, operator, a, b=None):
        if logic.arity(operator) == 2 and (a == self.char_values['N'] or b == self.char_values['N']):
            return self.char_values['N']
        return super(Model, self).truth_function(operator, a, b)

class TableauxSystem(fde.TableauxSystem):
    """
    K3W's Tableaux System inherits directly from the `FDE system`_, employing
    designation markers, and building the trunk in the same way.

    .. _FDE system: fde.html#logics.fde.TableauxSystem
    """
    pass
        
class TableauxRules(object):
    """
    The Tableaux System for K3W contains the `FDE closure rule`_, and the
    `K3 closure rule`_. Several of the operator rules are the same as `FDE`_.
    However, many rules for K3W are different from `FDE`_, given
    the behavior of the *N* value.
    
    .. _FDE closure rule: fde.html#logics.fde.TableauxRules.Closure
    .. _K3 closure rule: k3.html#logics.k3.TableauxRules.Closure
    .. _FDE: fde.html
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

    class ConjunctionUndesignated(fde.TableauxRules.ConjunctionUndesignated):
        """
        This rule is the same as the `FDE ConjunctionUndesignated rule`_.

        .. _FDE ConjunctionUndesignated rule: fde.html#logics.fde.TableauxRules.ConjunctionUndesignated
        """
        pass

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

    class DisjunctionNegatedDesignated(fde.TableauxRules.DisjunctionNegatedDesignated):
        """
        This rule is the same as the `FDE DisjunctionNegatedDesignated rule`_.

        .. _FDE DisjunctionNegatedDesignated rule: fde.html#logics.fde.TableauxRules.DisjunctionNegatedDesignated
        """
        pass

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
        one disjunct is True and the other False, or at least one of the dijuncts is Neither. So, from an
        unticked, undesignated, negated disjunction node *n*, on a branch *b*, make five branches
        *b'*, *b''*, *b'''*, *b''''*, *b'''''* from *b*. On *b'*, add a designated node for each disjunct.
        On *b''* add a designated node for the first disjunct, an undesignated node for the second
        disjunct, and a designated node for the negation of the second disjunct. On *b'''* do the
        same as before, except with the second and first disjuncts, respectively. On
        *b''''*, add undesignated nodes for the first disjunct and its negation, and on *b'''''*,
        add undesignated nodes for the other disjunction and its negation. Then, tick *n*.
        """

        def apply_to_node(self, node, branch):
            s = self.sentence(node)
            b1 = branch
            b2 = self.tableau.branch(branch)
            b3 = self.tableau.branch(branch)
            b4 = self.tableau.branch(branch)
            b5 = self.tableau.branch(branch)
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
            ]).tick(node)
            b5.update([
                { 'sentence' :        s.rhs,  'designated' : False },
                { 'sentence' : negate(s.rhs), 'designated' : False }
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

    class MaterialConditionalUndesignated(MaterialConditionalDesignated):
        """
        This rule reduces to a disjunction.
        """

        designation = False

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

    class MaterialBiconditionalUndesignated(MaterialBiconditionalDesignated):
        """
        This rule reduces to a conjunction of material conditionals.
        """

        designation = False

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

    class ConditionalNegatedDesignated(MaterialConditionalNegatedDesignated):
        """
        Same as for the negated material conditional designated.
        """

        operator = 'Conditional'

    class ConditionalUndesignated(MaterialConditionalUndesignated):
        """
        Same as for the material conditional undesignated.
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

    class BiconditionalNegatedDesignated(MaterialBiconditionalNegatedDesignated):
        """
        Same as for the negated material biconditional designated.
        """

        operator = 'Biconditional'

    class BiconditionalUndesignated(MaterialBiconditionalUndesignated):
        """
        Same as for the material biconditional undesignated.
        """

        operator = 'Biconditional'

    class BiconditionalNegatedUndesignated(MaterialBiconditionalNegatedUndesignated):
        """
        Same as for the negated material biconditional undesignated.
        """

        operator = 'Biconditional'

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

        k3.TableauxRules.Closure,
        fde.TableauxRules.Closure,

        # non-branching rules

        AssertionDesignated,
        AssertionUndesignated,
        AssertionNegatedDesignated,
        AssertionNegatedUndesignated,
        ConjunctionDesignated, 
        DisjunctionNegatedDesignated,
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
        ConjunctionUndesignated,

        # three-branching rules
        DisjunctionDesignated,
        DisjunctionUndesignated,
        ConjunctionNegatedDesignated,
        ConjunctionNegatedUndesignated,

        # five-branching rules
        DisjunctionNegatedUndesignated
    ]