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
# pytableaux - Gappy Object 3-valued Logic
name = 'GO'
title = 'Gappy Object 3-valued Logic'
description = 'Three-valued logic (True, False, Neither) with classical-like binary operators'
tags_list = ['many-valued', 'gappy', 'non-modal', 'first-order']
tags = set(tags_list)
category = 'Many-valued'
category_display_order = 5

import logic, math, examples
from . import fde, k3, b3e
from logic import negate, negative, operate, quantify

def gap(v):
    return min(v, 1 - v)

def crunch(v):
    return v - gap(v)

class Model(k3.Model):
    """
    A GO model is like a `K3 model`_, but with different tables for some of the connectives,
    as well as a different behavior for the quantifiers.

    .. _K3 model: k3.html#logics.k3.Model
    """

    def value_of_operated(self, sentence, **kw):
        """
        The value of a sentence with a truth-functional operator is determined by
        the values of its operands according to the following tables.

        //truth_tables//go//

        Note that, given the tables above, conjunctions and disjunctions always have a classical
        value (**T** or **F**). This means that only atomic sentences (with zero or more negations)
        can have the non-classical **N** value.

        This property of "classical containment" means, that we can define a conditional operator
        that satisfies Identity P{A $ A}. It also allows us to give a formal description of
        a subset of sentences that obey all principles of classical logic. For example, although
        the Law of Excluded Middle fails for atomic sentences P{A V ~A}, complex sentences -- those
        with at least one binary connective -- do obey the law: P{(A V A) V ~(A V A)}.
        """
        return super(Model, self).value_of_operated(sentence, **kw)

    def value_of_existential(self, sentence, **kw):
        """
        The value of an existential sentence is the maximum of the *crunched
        values* of the sentences that result from replacing each constant for the
        quantified variable.

        The *crunched value* of *v* is 1 (**T**) if *v* is 1, else 0 (**F**).

        Note that this is in accord with interpreting the existential quantifier
        in terms of generalized disjunction.
        """
        values = {self.value_of(sentence.substitute(c, sentence.variable), **kw) for c in self.constants}
        crunched = {crunch(self.nvals[v]) for v in values}
        return max(crunched)

    def value_of_universal(self, sentence, **kw):
        """
        The value of an universal sentence is the minimum of the *crunched values*
        of the sentences that result from replacing each constant for the quantified
        variable.

        The *crunched value* of *v* is 1 (**T**) if *v* is 1, else 0 (**F**).

        Note that this is in accord with interpreting the universal quantifier
        in terms of generalized conjunction.
        """
        values = {self.value_of(sentence.substitute(c, sentence.variable), **kw) for c in self.constants}
        crunched = {crunch(self.nvals[v]) for v in values}
        return min(crunched)

    def truth_function(self, operator, a, b=None):
        if operator == 'Assertion':
            return self.cvals[crunch(self.nvals[a])]
        elif operator == 'Disjunction':
            return self.cvals[max(crunch(self.nvals[a]), crunch(self.nvals[b]))]
        elif operator == 'Conjunction':
            return self.cvals[min(crunch(self.nvals[a]), crunch(self.nvals[b]))]
        elif operator == 'Conditional':
            return self.cvals[crunch(max(1 - self.nvals[a], self.nvals[b], gap(self.nvals[a]) + gap(self.nvals[b])))]
        return super(Model, self).truth_function(operator, a, b)

class TableauxSystem(fde.TableauxSystem):
    """
    GO's Tableaux System inherits directly from the `FDE system`_, employing
    designation markers, and building the trunk in the same way.

    .. _FDE system: fde.html#logics.fde.TableauxSystem
    """
    pass

class TableauxRules(object):
    """
    The closure rules for GO are the `FDE closure rule`_, and the `K3 closure rule`_.
    Most of the operators rules are unique to GO, with a few rules that are
    the same as `FDE`_. The rules for assertion mirror those of `B3E`_.
    
    .. _FDE closure rule: fde.html#logics.fde.TableauxRules.Closure
    .. _K3 closure rule: k3.html#logics.k3.TableauxRules.Closure
    """

    class DoubleNegationDesignated(k3.TableauxRules.DoubleNegationDesignated):
        """
        This rule is the same as the `FDE DoubleNegationDesignated rule`_.

        .. _FDE DoubleNegationDesignated rule: fde.html#logics.fde.TableauxRules.DoubleNegationDesignated
        """
        pass

    class DoubleNegationUndesignated(k3.TableauxRules.DoubleNegationUndesignated):
        """
        This rule is the same as the `FDE DoubleNegationUndesignated rule`_.

        .. _FDE DoubleNegationUndesignated rule: fde.html#logics.fde.TableauxRules.DoubleNegationUndesignated
        """
        pass

    class AssertionDesignated(k3.TableauxRules.AssertionDesignated):
        """
        This rule is the same as the `FDE AssertionDesignated rule`_.

        .. _FDE AssertionDesignated rule: fde.html#logics.fde.TableauxRules.AssertionDesignated
        """
        pass

    class AssertionNegatedDesignated(b3e.TableauxRules.AssertionNegatedDesignated):
        """
        This rule is the same as the `B3E AssertionDesignated rule`_.

        .. _B3E AssertionDesignated rule: b3e.html#logics.b3e.TableauxRules.AssertionDesignated
        """
        pass

    class AssertionUndesignated(b3e.TableauxRules.AssertionUndesignated):
        """
        This rule is the same as the `B3E AssertionUndesignated rule`_.

        .. _B3E AssertionUndesignated rule: b3e.html#logics.b3e.TableauxRules.AssertionUndesignated
        """
        pass

    class AssertionNegatedUndesignated(b3e.TableauxRules.AssertionNegatedUndesignated):
        """
        This rule is the same as the `B3E AssertionNegatedUndesignated rule`_.

        .. _B3E AssertionNegatedUndesignated rule: b3e.html#logics.b3e.TableauxRules.AssertionNegatedUndesignated
        """
        pass

    class ConjunctionDesignated(k3.TableauxRules.ConjunctionDesignated):
        """
        This rule is the same as the `FDE ConjunctionDesignated rule`_.

        .. _FDE ConjunctionDesignated rule: fde.html#logics.fde.TableauxRules.ConjunctionDesignated
        """
        pass

    class ConjunctionNegatedDesignated(logic.TableauxSystem.ConditionalNodeRule):
        """
        From an unticked, designated, negated conjunction node *n* on a branch *b*,
        make two new branches *b'* and *b''* from *b*, add an undesignated node to
        *b'* with one conjunct, and an undesignated node to *b''* with the other
        conjunct, then tick *n*.
        """

        negated     = True
        operator    = 'Conjunction'
        designation = True

        def apply_to_node(self, node, branch):
            b1 = branch
            b2 = self.branch(branch)
            s = self.sentence(node)
            b1.add({'sentence': s.lhs, 'designated': False}).tick(node)
            b2.add({'sentence': s.rhs, 'designated': False}).tick(node)

        def score_target_map(self, target):
            branch = target['branch']
            s = self.sentence(target['node'])
            return {
                'b1': branch.has_any([
                    # FDE closure
                    {'sentence': s.lhs, 'designated': True},
                    # K3 closure n/a
                ]),
                'b2': branch.has_any([
                    # FDE closure
                    {'sentence': s.rhs, 'designated': True},
                    # K3 closure n/a
                ]),
            }
            
    class ConjunctionUndesignated(logic.TableauxSystem.ConditionalNodeRule):
        """
        From an unticked, undesignated conjunction node *n* on a branch *b*, add a
        designated node to *b* with the negation of the conjunction, then tick *n*.
        """

        operator    = 'Conjunction'
        designation = False

        def apply_to_node(self, node, branch):
            s = self.sentence(node)
            branch.add({'sentence': negate(s), 'designated': True}).tick(node)

    class ConjunctionNegatedUndesignated(logic.TableauxSystem.ConditionalNodeRule):
        """
        From an unticked, undesignated, negated conjunction node *n* on a branch *b*,
        add a designated node to *b* with the (un-negated) conjuction, then tick *n*.
        """

        negated     = True
        operator    = 'Conjunction'
        designation = False

        def apply_to_node(self, node, branch):
            s = self.sentence(node)
            branch.add({'sentence': s, 'designated': True}).tick(node)

    class DisjunctionDesignated(k3.TableauxRules.DisjunctionDesignated):
        """
        This rule is the same as the `FDE DisjunctionDesignated rule`_.

        .. _FDE DisjunctionDesignated rule: fde.html#logics.fde.TableauxRules.DisjunctionDesignated
        """
        pass
        
    class DisjunctionNegatedDesignated(logic.TableauxSystem.ConditionalNodeRule):
        """
        From an unticked, designated, negated disjunction node *n* on a branch *b*,
        add an undesignated node to *b* for each disjunct, then tick *n*.
        """

        negated     = True
        operator    = 'Disjunction'
        designation = True

        def apply_to_node(self, node, branch):
            s = self.sentence(node)
            branch.update([
                {'sentence': s.lhs, 'designated': False},
                {'sentence': s.rhs, 'designated': False},
            ]).tick(node)

    class DisjunctionUndesignated(ConjunctionUndesignated):
        """
        From an unticked, undesignated disjunction node *n* on a branch *b*, add a
        designated node to *b* with the negation of the disjunction, then tick *n*.
        """

        operator = 'Disjunction'

    class DisjunctionNegatedUndesignated(ConjunctionNegatedUndesignated):
        """
        From an unticked, undesignated, negated disjunction node *n* on a branch *b*,
        add a designated node to *b* with the (un-negated) disjunction, then tick *n*.
        """

        operator = 'Disjunction'

    class MaterialConditionalDesignated(k3.TableauxRules.MaterialConditionalDesignated):
        """
        This rule is the same as the `FDE MaterialConditionalDesignated rule`_.

        .. _FDE MaterialConditionalDesignated rule: fde.html#logics.fde.TableauxRules.MaterialConditionalDesignated
        """
        pass
        
    class MaterialConditionalNegatedDesignated(logic.TableauxSystem.ConditionalNodeRule):
        """
        From an unticked, designated, negated material conditional node *n* on a branch
        *b*, add an undesignated node with the negation of the antecedent, and an
        undesignated node with the consequent to *b*, then tick *n*.
        """

        negated     = True
        operator    = 'Material Conditional'
        designation = True

        def apply_to_node(self, node, branch):
            s = self.sentence(node)
            branch.update([
                {'sentence': negate(s.lhs), 'designated': False},
                {'sentence':        s.rhs , 'designated': False},
            ]).tick(node)

    class MaterialConditionalUndesignated(ConjunctionUndesignated):
        """
        From an unticked, undesignated, material conditional node *n* on a branch *b*,
        add a designated node to *b* with the negation of the conditional, then tick *n*.
        """

        operator = 'Material Conditional'

    class MaterialConditionalNegatedUndesignated(ConjunctionNegatedUndesignated):
        """
        From an unticked, undesignated, negated material conditional node *n* on a branch
        *b*, add a designated node with the (un-negated) conditional to *b*, then tick *n*.
        """

        operator = 'Material Conditional'

    class MaterialBiconditionalDesignated(k3.TableauxRules.MaterialBiconditionalDesignated):
        """
        This rule is the same as the `FDE MaterialBiconditionalDesignated rule`_.

        .. _FDE MaterialBiconditionalDesignated rule: fde.html#logics.fde.TableauxRules.MaterialBiconditionalDesignated
        """
        pass
        
    class MaterialBiconditionalNegatedDesignated(logic.TableauxSystem.ConditionalNodeRule):
        """
        From an unticked, designated, negated, material biconditional node *n* on a branch
        *b*, make two branches *b'* and *b''* from *b*. On *b'* add undesignated nodes for
        the negation of the antecent, and for the consequent. On *b''* add undesignated
        nodes for the antecedent, and for the negation of the consequent. Then tick *n*.
        """

        negated     = True
        operator    = 'Material Biconditional'
        designation = True

        def apply_to_node(self, node, branch):
            s = self.sentence(node)
            b1 = branch
            b2 = self.branch(branch)
            b1.update([
                {'sentence': negate(s.lhs), 'designated': False},
                {'sentence':        s.rhs , 'designated': False},
            ]).tick(node)
            b2.update([
                {'sentence':        s.lhs , 'designated': False},
                {'sentence': negate(s.rhs), 'designated': False},
            ]).tick(node)

        def score_target_map(self, target):
            branch = target['branch']
            s = self.sentence(target['node'])
            return {
                'b1': branch.has_any([
                    # FDE closure
                    {'sentence': negative(s.lhs), 'designated': True},
                    {'sentence':          s.rhs , 'designated': True},
                    # K3 closure n/a
                ]),
                'b2': branch.has_any([
                    # FDE closure
                    {'sentence':          s.lhs , 'designated': True},
                    {'sentence': negative(s.rhs), 'designated': True},
                    # K3 closure n/a
                ]),
            }

    class MaterialBiconditionalUndesignated(ConjunctionUndesignated):
        """
        From an unticked, undesignated, material biconditional node *n* on a branch *b*,
        add a designated node to *b* with the negation of the biconditional, then tick *n*.
        """

        operator = 'Material Biconditional'

    class MaterialBiconditionalNegatedUndesignated(ConjunctionNegatedUndesignated):
        """
        From an unticked, undesignated, negated material biconditional node *n* on a branch
        *b*, add a designated node to *b* with the (un-negated) biconditional, then tick *n*.
        """

        operator = 'Material Biconditional'

    class ConditionalDesignated(logic.TableauxSystem.ConditionalNodeRule):
        """
        From an unticked, designated, conditional node *n* on a branch *b*, make two branches
        *b'* and *b''* from *b*. On *b'* add a designated node with a disjunction of the
        negated antecedent and the consequent. On *b''* add undesignated nodes for the
        antecedent, consequent, and their negations. Then tick *n*.
        """

        operator    = 'Conditional'
        designation = True

        def apply_to_node(self, node, branch):
            s = self.sentence(node)
            disj = operate('Disjunction', [negate(s.lhs), s.rhs])
            b1 = branch
            b2 = self.branch(branch)
            b1.add({'sentence': disj, 'designated': True}).tick(node)
            b2.update([
                {'sentence':        s.lhs , 'designated': False},
                {'sentence':        s.rhs , 'designated': False},
                {'sentence': negate(s.lhs), 'designated': False},
                {'sentence': negate(s.rhs), 'designated': False},
            ]).tick(node)

        def score_target_map(self, target):
            branch = target['branch']
            s = self.sentence(target['node'])
            disj = operate('Disjunction', [negative(s.lhs), s.rhs])
            return {
                'b1': branch.has_any([
                    # FDE closure
                    {'sentence': disj, 'designated': False},
                    # K3 closure
                    {'sentence': negative(disj), 'designated': True},
                ]),
                'b2': branch.has_any([
                    # FDE closure
                    {'sentence':          s.lhs , 'designated': True},
                    {'sentence':          s.rhs , 'designated': True},
                    {'sentence': negative(s.lhs), 'designated': True},
                    {'sentence': negative(s.rhs), 'designated': True},
                    # K3 closure n/a
                ]),
            }

    class ConditionalNegatedDesignated(logic.TableauxSystem.ConditionalNodeRule):
        """
        From an unticked, designated, negated conditional node *n* on a branch *b*, make
        two branches *b'* and *b''* from *b*. On *b'* add a designated node with the
        antecedent, and an undesignated node with the consequent. On *b''* add an
        undesignated node with the negation of the antencedent, and a designated node
        with the negation of the consequent. Then tick *n*.
        """

        negated     = True
        operator    = 'Conditional'
        designation = True

        def apply_to_node(self, node, branch):
            s = self.sentence(node)
            b1 = branch
            b2 = self.branch(branch)
            b1.update([
                {'sentence': s.lhs,'designated' : True },
                {'sentence': s.rhs,'designated' : False},
            ]).tick(node)
            b2.update([
                {'sentence': negate(s.lhs), 'designated': False},
                {'sentence': negate(s.rhs), 'designated': True },
            ]).tick(node)

        def score_target_map(self, target):
            branch = target['branch']
            s = self.sentence(target['node'])
            return {
                'b1': branch.has_any([
                    # FDE closure
                    {'sentence': s.lhs,'designated' : False},
                    {'sentence': s.rhs,'designated' : True },
                    # K3 closure
                    {'sentence': negative(s.lhs),'designated' : True},
                ]),
                'b2': branch.has_any([
                    # FDE closure
                    {'sentence': negative(s.lhs), 'designated': True },
                    {'sentence': negative(s.rhs), 'designated': False},
                    # K3 closure
                    {'sentence': s.rhs, 'designated': True},
                ]),
            }

    class ConditionalUndesignated(ConjunctionUndesignated):
        """
        From an unticked, undesignated conditional node *n* on a branch *b*, add a
        designated node to *b* with the negation of the conditional, then tick *n*.
        """

        operator = 'Conditional'

    class ConditionalNegatedUndesignated(ConjunctionNegatedUndesignated):
        """
        From an unticked, undesignated, negated conditional node *n* on a branch *b*,
        add a designated node to *b* with the (un-negated) conditional, then tick *n*.
        """

        operator = 'Conditional'

    class BiconditionalDesignated(logic.TableauxSystem.ConditionalNodeRule):
        """
        From an unticked, designated biconditional node *n* on a branch *b*, add two
        designated conditional nodes to *b*, one with the operands of the biconditional,
        and the other with the reversed operands. Then tick *n*.
        """

        operator    = 'Biconditional'
        designation = True

        def apply_to_node(self, node, branch):
            s = self.sentence(node)
            branch.update([
                {'sentence': operate('Conditional', [s.lhs, s.rhs]), 'designated': True},
                {'sentence': operate('Conditional', [s.rhs, s.lhs]), 'designated': True},
            ]).tick(node)

    class BiconditionalNegatedDesignated(logic.TableauxSystem.ConditionalNodeRule):
        """
        From an unticked, designated, negated biconditional node *n* on a branch *b*, make
        two branches *b'* and *b''* from *b*. On *b'* add a designated negated conditional
        node with the operands of the biconditional. On *b''* add a designated negated
        conditional node with the reversed operands of the biconditional. Then tick *n*.
        """

        negated     = True
        operator    = 'Biconditional'
        designation = True

        def apply_to_node(self, node, branch):
            s = self.sentence(node)
            b1 = branch
            b2 = self.branch(branch)
            cond1 = operate('Conditional', [s.lhs, s.rhs])
            cond2 = operate('Conditional', [s.rhs, s.lhs])
            b1.add({'sentence': negate(cond1), 'designated': True}).tick(node)
            b2.add({'sentence': negate(cond2), 'designated': True}).tick(node)

        def score_target_map(self, target):
            branch = target['branch']
            s = self.sentence(target['node'])
            cond1 = operate('Conditional', [s.lhs, s.rhs])
            cond2 = operate('Conditional', [s.rhs, s.lhs])
            return {
                'b1': branch.has_any([
                    # FDE closure
                    {'sentence': negative(cond1), 'designated': False},
                    # K3 closure
                    {'sentence': cond1, 'designated': True},
                ]),
                'b2': branch.has_any([
                    # FDE closure
                    {'sentence': negative(cond2), 'designated': False},
                    # K3 closure
                    {'sentence': cond2, 'designated': True},
                ]),
            }

    class BiconditionalUndesignated(ConjunctionUndesignated):
        """
        From an unticked, undesignated biconditional node *n* on a branch *b*, add a
        designated node to *b* with the negation of the biconditional, then tick *n*.
        """

        operator = 'Biconditional'

    class BiconditionalNegatedUndesignated(ConjunctionNegatedUndesignated):
        """
        From an unticked, undesignated, negated biconditional node *n* on a branch *b*,
        add a designated node to *b* with the (un-negated) biconditional, then tick *n*.
        """

        operator = 'Biconditional'

    class ExistentialDesignated(k3.TableauxRules.ExistentialDesignated):
        """
        This rule is the same as the `FDE ExistentialDesignated rule`_.

        .. _FDE ExistentialDesignated rule: fde.html#logics.fde.TableauxRules.ExistentialDesignated
        """
        pass
        
    class ExistentialNegatedDesignated(logic.TableauxSystem.ConditionalNodeRule):
        """
        From an unticked, designated negated existential node *n* on a branch *b*,
        add a designated node *n'* to *b* with a universal sentence consisting of
        disjunction, whose first disjunct is the negated inner sentence of *n*,
        and whose second disjunct is the negation of a disjunction *d*, where the
        first disjunct of *d* is the inner sentence of *n*, and the second disjunct
        of *d* is the negation of the inner setntence of *n*. Then tick *n*.
        """
        quantifier  = 'Existential'
        negated     = True
        designation = True
        convert_to  = 'Universal'

        def apply_to_node(self, node, branch):
            s = self.sentence(node)
            d = self.designation
            v = s.variable
            si = s.sentence

            si_lem_fail = negate(operate('Disjunction', [si, negate(si)]))
            si_disj = operate('Disjunction', [negate(si), si_lem_fail])
            branch.add({'sentence': quantify(self.convert_to, v, si_disj), 'designated': d}).tick(node)

    class ExistentialUndesignated(ConjunctionUndesignated):
        """
        From an unticked, undesignated existential node *n* on a branch *b*, add a designated
        node to *b* with the negation of the existential sentence, then tick *n*.
        """

        operator   = None
        quantifier = 'Existential'

    class ExistentialNegatedUndesignated(ConjunctionNegatedUndesignated):
        """
        From an unticked, undesignated negated existential node *n* on a branch *b*, add a designated
        node to *b* with the negated existential sentence (negatum), then tick *n*.
        """

        operator   = None
        quantifier = 'Existential'

    class UniversalDesignated(k3.TableauxRules.UniversalDesignated):
        """
        This rule is the same as the `FDE UniversalDesignated rule`_.

        .. _FDE UniversalDesignated rule: fde.html#logics.fde.TableauxRules.UniversalDesignated
        """
        pass
        
    class UniversalNegatedDesignated(logic.TableauxSystem.ConditionalNodeRule):
        """
        From an unticked, designated universal existential node *n* on a branch *b*, make two branches
        *b'* and *b''* from *b*. On *b'*, add a designtated node with the standard 
        translation of the sentence on *b*. For *b''*, substitute a new constant *c* for
        the quantified variable, and add two undesignated nodes to *b''*, one with the
        substituted inner sentence, and one with its negation, then tick *n*.
        """
        quantifier  = 'Universal'
        designation = True
        negated     = True
        convert_to  = 'Existential'

        # NB: since the rule always uses a new constant, scoring the targets
        # would require complex predicting of whether the branch might close,
        # e.g. by checking for universal statements that might result in closure.

        def apply_to_node(self, node, branch):
            s = self.sentence(node)
            d = self.designation
            v = s.variable

            c = branch.new_constant()
            si = s.sentence
            ss = s.substitute(c, v)
            sq = quantify(self.convert_to, v, negate(si))

            b1 = branch
            b2 = self.branch(branch)
            b1.add({'sentence': sq, 'designated': d}).tick(node)
            b2.update([
                {'sentence':        ss , 'designated': not d},
                {'sentence': negate(ss), 'designated': not d},
            ]).tick(node)
            
    class UniversalUndesignated(ExistentialUndesignated):
        """
        From an unticked, undesignated universal node *n* on a branch *b*, add a designated
        node to *b* with the negation of the universal sentence, then tick *n*.
        """

        quantifier = 'Universal'

    class UniversalNegatedUndesignated(ExistentialNegatedUndesignated):
        """
        From an unticked, undesignated negated universal node *n* on a branch *b*, add a designated
        node to *b* with the negated universal sentence (negatum), then tick *n*.
        """

        quantifier = 'Universal'

    closure_rules = list(k3.TableauxRules.closure_rules)

    rule_groups = [
        [
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
        ],
        [
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
        ],
    ]