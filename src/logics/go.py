# pytableaux, a multi-logic proof generator.
# Copyright (C) 2014-2021 Doug Owings.
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
# pytableaux - Gappy Object 3-valued Logic
from __future__ import annotations
name = 'GO'

class Meta:
    title    = 'Gappy Object 3-valued Logic'
    category = 'Many-valued'
    description = 'Three-valued logic (True, False, Neither) with classical-like binary operators'
    tags = ['many-valued', 'gappy', 'non-modal', 'first-order']
    category_display_order = 60

from lexicals import Operated, Quantified, Operator as Oper, Quantifier
from proof.common import Branch, Node
from . import fde as FDE, k3 as K3, b3e as B3E

def gap(v):
    return min(v, 1 - v)

def crunch(v):
    return v - gap(v)

class Model(K3.Model):
    """
    A GO model is like a :ref:`K3 model <k3-model>`, but with different tables
    for some of the connectives, as well as a different behavior for the quantifiers.
    """

    def truth_function(self, oper: Oper, a, b=None):
        if oper == Oper.Assertion:
            return self.cvals[crunch(self.nvals[a])]
        elif oper == Oper.Disjunction:
            return self.cvals[max(crunch(self.nvals[a]), crunch(self.nvals[b]))]
        elif oper == Oper.Conjunction:
            return self.cvals[min(crunch(self.nvals[a]), crunch(self.nvals[b]))]
        elif oper == Oper.Conditional:
            return self.cvals[crunch(max(1 - self.nvals[a], self.nvals[b], gap(self.nvals[a]) + gap(self.nvals[b])))]
        return super().truth_function(oper, a, b)

    def value_of_existential(self, sentence: Quantified, **kw):
        """
        The value of an existential sentence is the maximum of the *crunched
        values* of the sentences that result from replacing each constant for the
        quantified variable.

        The *crunched value* of *v* is 1 (:m:`T`) if *v* is 1, else 0 (:m:`F`).

        Note that this is in accord with interpreting the existential quantifier
        in terms of `generalized disjunction`.
        """
        si = sentence.sentence
        v = sentence.variable
        values = {self.value_of(si.substitute(c, v), **kw) for c in self.constants}
        crunched = {crunch(self.nvals[val]) for val in values}
        return self.cvals[max(crunched)]

    def value_of_universal(self, sentence: Quantified, **kw):
        """
        The value of an universal sentence is the minimum of the *crunched values*
        of the sentences that result from replacing each constant for the quantified
        variable.

        The *crunched value* of *v* is 1 (:m:`T`) if *v* is 1, else 0 (:m:`F`).

        Note that this is in accord with interpreting the universal quantifier
        in terms of generalized conjunction.
        """
        si = sentence.sentence
        v = sentence.variable
        values = {self.value_of(si.substitute(c, v), **kw) for c in self.constants}
        crunched = {crunch(self.nvals[val]) for val in values}
        return self.cvals[min(crunched)]

class TableauxSystem(FDE.TableauxSystem):
    """
    GO's Tableaux System inherits directly from the :ref:`FDE system <fde-system>`,
    employing designation markers, and building the trunk in the same way.
    """
    # operator => negated => designated
    branchables = {
        Oper.Negation: {
            True: {True: 0, False: 0},
        },
        Oper.Assertion: {
            False : {True: 0, False: 0},
            True  : {True: 0, False: 0},
        },
        Oper.Conjunction: {
            False : {True: 0, False: 0},
            True  : {True: 1, False: 0},
        },
        Oper.Disjunction: {
            False : {True: 1, False: 0},
            True  : {True: 0, False: 0},
        },
        Oper.MaterialConditional: {
            False : {True: 1, False: 0},
            True  : {True: 0, False: 0},
        },
        Oper.MaterialBiconditional: {
            False : {True: 1, False: 0},
            True  : {True: 1, False: 0},
        },
        Oper.Conditional: {
            False : {True: 1, False: 0},
            True  : {True: 1, False: 0},
        },
        Oper.Biconditional: {
            False : {True: 0, False: 0},
            True  : {True: 1, False: 0},
        },
    }

class TabRules:
    """
    The closure rules for GO are the FDE closure rule, and the K3 closure rule.
    Most of the operators rules are unique to GO, with a few rules that are
    the same as :ref:`FDE <FDE>`. The rules for assertion mirror those of
    :ref:`B3E <B3E>`.
    """

    class GlutClosure(K3.TabRules.GlutClosure):
        pass
    class DesignationClosure(FDE.TabRules.DesignationClosure):
        pass

    class DoubleNegationDesignated(FDE.TabRules.DoubleNegationDesignated):
        pass
    class DoubleNegationUndesignated(FDE.TabRules.DoubleNegationUndesignated):
        pass

    class AssertionDesignated(FDE.TabRules.AssertionDesignated):
        pass
    class AssertionNegatedDesignated(B3E.TabRules.AssertionNegatedDesignated):
        pass
    class AssertionUndesignated(B3E.TabRules.AssertionUndesignated):
        pass
    class AssertionNegatedUndesignated(B3E.TabRules.AssertionNegatedUndesignated):
        pass

    class ConjunctionDesignated(FDE.TabRules.ConjunctionDesignated):
        pass

    class ConjunctionNegatedDesignated(FDE.OperatorNodeRule):
        """
        From an unticked, designated, negated conjunction node *n* on a branch *b*,
        make two new branches *b'* and *b''* from *b*, add an undesignated node to
        *b'* with one conjunct, and an undesignated node to *b''* with the other
        conjunct, then tick *n*.
        """
        designation = True
        negated     = True
        operator    = Oper.Conjunction
        branch_level = 2

        def _get_node_targets(self, node: Node, _):
            s: Operated = self.sentence(node)
            lhs, rhs = s
            d = self.designation
            return {
                'adds': (
                    ({'sentence': lhs, 'designated': not d},),
                    ({'sentence': rhs, 'designated': not d},),
                )
            }
            
    class ConjunctionUndesignated(FDE.OperatorNodeRule):
        """
        From an unticked, undesignated conjunction node *n* on a branch *b*, add a
        designated node to *b* with the negation of the conjunction, then tick *n*.
        """
        designation = False
        operator    = Oper.Conjunction
        branch_level = 1

        def _get_node_targets(self, node: Node, _):
            s: Operated = self.sentence(node)
            d = self.designation
            return {
                'adds': (({'sentence': s.negate(), 'designated': not d},),),
            }

    class ConjunctionNegatedUndesignated(FDE.OperatorNodeRule):
        """
        From an unticked, undesignated, negated conjunction node *n* on a branch *b*,
        add a designated node to *b* with the (un-negated) conjuction, then tick *n*.
        """
        designation = False
        negated     = True
        operator    = Oper.Conjunction
        branch_level = 1

        def _get_node_targets(self, node: Node, _):
            s: Operated = self.sentence(node)
            d = self.designation
            return {
                'adds': (({'sentence': s, 'designated': not d},),),
            }

    class DisjunctionDesignated(FDE.TabRules.DisjunctionDesignated):
        pass
        
    class DisjunctionNegatedDesignated(FDE.OperatorNodeRule):
        """
        From an unticked, designated, negated disjunction node *n* on a branch *b*,
        add an undesignated node to *b* for each disjunct, then tick *n*.
        """
        designation = True
        negated     = True
        operator    = Oper.Disjunction
        branch_level = 1

        def _get_node_targets(self, node: Node, _):
            s: Operated = self.sentence(node)
            lhs, rhs = s
            d = self.designation
            return {
                'adds': (
                    (
                        {'sentence': lhs, 'designated': not d},
                        {'sentence': rhs, 'designated': not d},
                    ),
                ),
            }

    class DisjunctionUndesignated(ConjunctionUndesignated):
        """
        From an unticked, undesignated disjunction node *n* on a branch *b*, add a
        designated node to *b* with the negation of the disjunction, then tick *n*.
        """
        operator = Oper.Disjunction

    class DisjunctionNegatedUndesignated(ConjunctionNegatedUndesignated):
        """
        From an unticked, undesignated, negated disjunction node *n* on a branch *b*,
        add a designated node to *b* with the (un-negated) disjunction, then tick *n*.
        """
        operator = Oper.Disjunction

    class MaterialConditionalDesignated(FDE.TabRules.MaterialConditionalDesignated):
        pass
        
    class MaterialConditionalNegatedDesignated(FDE.OperatorNodeRule):
        """
        From an unticked, designated, negated material conditional node *n* on a branch
        *b*, add an undesignated node with the negation of the antecedent, and an
        undesignated node with the consequent to *b*, then tick *n*.
        """
        negated     = True
        operator    = Oper.MaterialConditional
        designation = True
        branch_level = 1

        def _get_node_targets(self, node: Node, _):
            s: Operated = self.sentence(node)
            lhs, rhs = s
            d = self.designation
            return {
                'adds': (
                    (
                        {'sentence': lhs.negate(), 'designated': not d},
                        {'sentence': rhs         , 'designated': not d},
                    ),
                ),
            }

    class MaterialConditionalUndesignated(ConjunctionUndesignated):
        """
        From an unticked, undesignated, material conditional node *n* on a branch *b*,
        add a designated node to *b* with the negation of the conditional, then tick *n*.
        """
        operator = Oper.MaterialConditional

    class MaterialConditionalNegatedUndesignated(ConjunctionNegatedUndesignated):
        """
        From an unticked, undesignated, negated material conditional node *n* on a branch
        *b*, add a designated node with the (un-negated) conditional to *b*, then tick *n*.
        """
        operator = Oper.MaterialConditional

    class MaterialBiconditionalDesignated(FDE.TabRules.MaterialBiconditionalDesignated):
        pass
        
    class MaterialBiconditionalNegatedDesignated(FDE.OperatorNodeRule):
        """
        From an unticked, designated, negated, material biconditional node *n* on a branch
        *b*, make two branches *b'* and *b''* from *b*. On *b'* add undesignated nodes for
        the negation of the antecent, and for the consequent. On *b''* add undesignated
        nodes for the antecedent, and for the negation of the consequent. Then tick *n*.
        """
        designation = True
        negated     = True
        operator    = Oper.MaterialBiconditional
        branch_level = 2

        def _get_node_targets(self, node: Node, _):
            s: Operated = self.sentence(node)
            lhs, rhs = s
            d = self.designation
            return {
                'adds': (
                    (
                        {'sentence': lhs.negate(), 'designated': not d},
                        {'sentence': rhs         , 'designated': not d},
                    ),
                    (
                        {'sentence': lhs         , 'designated': not d},
                        {'sentence': rhs.negate(), 'designated': not d},
                    ),
                ),
            }

    class MaterialBiconditionalUndesignated(ConjunctionUndesignated):
        """
        From an unticked, undesignated, material biconditional node *n* on a branch *b*,
        add a designated node to *b* with the negation of the biconditional, then tick *n*.
        """
        operator = Oper.MaterialBiconditional

    class MaterialBiconditionalNegatedUndesignated(ConjunctionNegatedUndesignated):
        """
        From an unticked, undesignated, negated material biconditional node *n* on a branch
        *b*, add a designated node to *b* with the (un-negated) biconditional, then tick *n*.
        """
        operator = Oper.MaterialBiconditional

    class ConditionalDesignated(FDE.OperatorNodeRule):
        """
        From an unticked, designated, conditional node *n* on a branch *b*, make two branches
        *b'* and *b''* from *b*. On *b'* add a designated node with a disjunction of the
        negated antecedent and the consequent. On *b''* add undesignated nodes for the
        antecedent, consequent, and their negations. Then tick *n*.
        """
        designation = True
        operator    = Oper.Conditional
        branch_level = 2

        def _get_node_targets(self, node: Node, _):
            s: Operated = self.sentence(node)
            lhs, rhs = s
            disj = lhs.negate().disjoin(rhs)
            d = self.designation
            return {
                'adds': (
                    ({'sentence': disj, 'designated': d},),
                    (
                        {'sentence': lhs         , 'designated': not d},
                        {'sentence': rhs         , 'designated': not d},
                        {'sentence': lhs.negate(), 'designated': not d},
                        {'sentence': rhs.negate(), 'designated': not d},
                    ),
                ),
            }

    class ConditionalNegatedDesignated(FDE.OperatorNodeRule):
        """
        From an unticked, designated, negated conditional node *n* on a branch *b*, make
        two branches *b'* and *b''* from *b*. On *b'* add a designated node with the
        antecedent, and an undesignated node with the consequent. On *b''* add an
        undesignated node with the negation of the antencedent, and a designated node
        with the negation of the consequent. Then tick *n*.
        """
        designation = True
        negated     = True
        operator    = Oper.Conditional
        branch_level = 2

        def _get_node_targets(self, node: Node, _):
            s: Operated = self.sentence(node)
            lhs, rhs = s
            d = self.designation
            return {
                'adds': (
                    (
                        {'sentence': lhs, 'designated': d},
                        {'sentence': rhs, 'designated': not d},
                    ),
                    (
                        {'sentence': lhs.negate(), 'designated': not d},
                        {'sentence': rhs.negate(), 'designated': d},
                    ),
                ),
            }

    class ConditionalUndesignated(ConjunctionUndesignated):
        """
        From an unticked, undesignated conditional node *n* on a branch *b*, add a
        designated node to *b* with the negation of the conditional, then tick *n*.
        """
        designation = False
        negated     = False
        operator    = Oper.Conditional

    class ConditionalNegatedUndesignated(ConjunctionNegatedUndesignated):
        """
        From an unticked, undesignated, negated conditional node *n* on a branch *b*,
        add a designated node to *b* with the (un-negated) conditional, then tick *n*.
        """
        designation = False
        negated     = True
        operator    = Oper.Conditional

    class BiconditionalDesignated(FDE.OperatorNodeRule):
        """
        From an unticked, designated biconditional node *n* on a branch *b*, add two
        designated conditional nodes to *b*, one with the operands of the biconditional,
        and the other with the reversed operands. Then tick *n*.
        """
        designation = True
        operator    = Oper.Biconditional
        branch_level = 1

        def _get_node_targets(self, node: Node, _):
            lhs, rhs = self.sentence(node)
            cond1 = Oper.Conditional((lhs, rhs))
            cond2 = Oper.Conditional((rhs, lhs))
            d = self.designation
            return {
                'adds': (
                    (
                        {'sentence': cond1, 'designated': d},
                        {'sentence': cond2, 'designated': d},
                    ),
                ),
            }

    class BiconditionalNegatedDesignated(FDE.OperatorNodeRule):
        """
        From an unticked, designated, negated biconditional node *n* on a branch *b*, make
        two branches *b'* and *b''* from *b*. On *b'* add a designated negated conditional
        node with the operands of the biconditional. On *b''* add a designated negated
        conditional node with the reversed operands of the biconditional. Then tick *n*.
        """
        designation = True
        negated     = True
        operator    = Oper.Biconditional
        branch_level = 2

        def _get_node_targets(self, node: Node, _):
            lhs, rhs = self.sentence(node)
            cond1 = Oper.Conditional((lhs, rhs))
            cond2 = Oper.Conditional((rhs, lhs))
            d = self.designation
            return {
                'adds': (
                    ({'sentence': cond1.negate(), 'designated': d},),
                    ({'sentence': cond2.negate(), 'designated': d},),
                ),
            }

    class BiconditionalUndesignated(ConjunctionUndesignated):
        """
        From an unticked, undesignated biconditional node *n* on a branch *b*, add a
        designated node to *b* with the negation of the biconditional, then tick *n*.
        """
        operator = Oper.Biconditional

    class BiconditionalNegatedUndesignated(ConjunctionNegatedUndesignated):
        """
        From an unticked, undesignated, negated biconditional node *n* on a branch *b*,
        add a designated node to *b* with the (un-negated) biconditional, then tick *n*.
        """
        operator = Oper.Biconditional

    class ExistentialDesignated(FDE.TabRules.ExistentialDesignated):
        pass
        
    class ExistentialNegatedDesignated(FDE.QuantifiedSentenceRule, FDE.DefaultNodeRule):
        """
        From an unticked, designated negated existential node *n* on a branch *b*,
        add a designated node *n'* to *b* with a universal sentence consisting of
        disjunction, whose first disjunct is the negated inner sentence of *n*,
        and whose second disjunct is the negation of a disjunction *d*, where the
        first disjunct of *d* is the inner sentence of *n*, and the second disjunct
        of *d* is the negation of the inner setntence of *n*. Then tick *n*.
        """
        designation = True
        negated     = True
        quantifier  = Quantifier.Existential
        convert_to  = Quantifier.Universal
        branch_level = 1

        def _get_node_targets(self, node: Node, _):
            s = self.sentence(node)
            v = s.variable
            si = s.sentence
            si_lem_fail = si.disjoin(si.negate()).negate()
            si_disj = si.negate().disjoin(si_lem_fail)
            sq = Quantified(self.convert_to, v, si_disj)
            return {
                'adds': [
                    [
                        {'sentence': sq, 'designated': self.designation},
                    ],
                ],
            }

    class ExistentialUndesignated(ConjunctionUndesignated):
        """
        From an unticked, undesignated existential node *n* on a branch *b*, add a
        designated node to *b* with the negation of the existential sentence, then
        tick *n*.
        """
        designation = False
        negated     = False
        operator    = None
        quantifier  = Quantifier.Existential

    class ExistentialNegatedUndesignated(ConjunctionNegatedUndesignated):
        """
        From an unticked, undesignated negated existential node *n* on a branch *b*,
        add a designated node to *b* with the negated existential sentence (negatum),
        then tick *n*.
        """
        designation = False
        negated     = True
        operator    = None
        quantifier  = Quantifier.Existential

    class UniversalDesignated(FDE.TabRules.UniversalDesignated):
        pass
        
    class UniversalNegatedDesignated(FDE.QuantifierSkinnyRule):
        """
        From an unticked, designated universal existential node *n* on a branch *b*,
        make two branches *b'* and *b''* from *b*. On *b'*, add a designtated node
        with the standard translation of the sentence on *b*. For *b''*, substitute
        a new constant *c* for the quantified variable, and add two undesignated
        nodes to *b''*, one with the substituted inner sentence, and one with its
        negation, then tick *n*.
        """
        designation = True
        negated     = True
        quantifier  = Quantifier.Universal
        convert_to  = Quantifier.Existential
        branch_level = 2

        def _get_node_targets(self, node: Node, branch: Branch):
            s: Quantified = self.sentence(node)
            r = s.unquantify(branch.new_constant())
            sq = self.convert_to(s.variable, s.sentence.negate())
            d = self.designation
            return {
                'adds': (
                    (
                        {'sentence': sq, 'designated': d},
                    ),
                    (
                        {'sentence': r         , 'designated': not d},
                        {'sentence': r.negate(), 'designated': not d},
                    ),
                ),
            }
            
    class UniversalUndesignated(ExistentialUndesignated):
        """
        From an unticked, undesignated universal node *n* on a branch *b*, add a designated
        node to *b* with the negation of the universal sentence, then tick *n*.
        """
        designation = False
        negated     = False
        quantifier  = Quantifier.Universal

    class UniversalNegatedUndesignated(ExistentialNegatedUndesignated):
        """
        From an unticked, undesignated negated universal node *n* on a branch *b*,
        add a designated node to *b* with the negated universal sentence (negatum),
        then tick *n*.
        """
        designation = False
        negated     = True
        quantifier  = Quantifier.Universal

    closure_rules = (
        GlutClosure,
        DesignationClosure,
    )

    rule_groups = (
        (
            # non-branching rules
            AssertionDesignated,
            AssertionUndesignated,
            AssertionNegatedDesignated,
            AssertionNegatedUndesignated,
            ConjunctionDesignated,
            ConjunctionUndesignated,
            ConjunctionNegatedUndesignated,
            DisjunctionNegatedDesignated,
            DisjunctionUndesignated,
            DisjunctionNegatedUndesignated,
            MaterialConditionalNegatedDesignated,
            MaterialConditionalUndesignated,
            MaterialConditionalNegatedUndesignated,
            MaterialBiconditionalUndesignated,
            MaterialBiconditionalNegatedUndesignated,
            ConditionalUndesignated,
            ConditionalNegatedUndesignated,
            BiconditionalUndesignated,
            BiconditionalNegatedUndesignated,
            BiconditionalDesignated,
            ExistentialDesignated,
            ExistentialNegatedDesignated,
            ExistentialUndesignated,
            ExistentialNegatedUndesignated,
            UniversalDesignated,
            UniversalUndesignated,
            UniversalNegatedUndesignated,
            DoubleNegationDesignated,
            DoubleNegationUndesignated,
        ),
        (
            # branching rules
            DisjunctionDesignated,
            ConjunctionNegatedDesignated,
            MaterialConditionalDesignated,
            MaterialBiconditionalDesignated,
            MaterialBiconditionalNegatedDesignated,
            ConditionalDesignated,
            ConditionalNegatedDesignated,
            BiconditionalNegatedDesignated,
            UniversalNegatedDesignated,
        ),
    )
