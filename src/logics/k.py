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
# pytableaux - Kripke Normal Modal Logic (Fixed Domain)

"""
Kripke Logic (K) is the foundation of so-called normal modal logics. It is an extension of CFOL,
adding the modal operators for possibility and necessity.

Links
-----

- `Stanford Encyclopedia on Modal Logic`_

.. _Stanford Encyclopedia on Modal Logic: http://plato.stanford.edu/entries/logic-modal/
"""
name = 'K'
description = 'Kripke Normal Modal Logic (Fixed Domain)'

def example_validities():
    import cfol
    args = cfol.example_validities()
    args.update([
        'Necessity Distribution' ,
        'Modal Platitude 1'      ,
        'Modal Platitude 2'      ,
        'Modal Platitude 3'      ,
        'Modal Transformation 1' ,
        'Modal Transformation 2' ,
        'Modal Transformation 3' ,
        'Modal Transformation 4' ,
    ])
    return args

def example_invalidities():
    import t
    args = t.example_invalidities()
    args.update([
        'Reflexive Inference 1' ,
        'Serial Inference 1'    ,
        'Possibility Addition'  ,
        'Necessity Elimination' ,
    ])
    return args

import logic
from logic import negate, operate, quantify, atomic, variable, Vocabulary

class TableauxSystem(logic.TableauxSystem):
    """
    Modal tableaux are similar to classical tableaux, with the addition of a
    *world* index for each sentence node, as well as *access* nodes representing
    "visibility" of worlds. The worlds and access nodes come into play with
    the rules for Possibility and Necessity. All other rules function equivalently
    to their classical counterparts.
    """

    @staticmethod
    def build_trunk(tableau, argument):
        """
        To build the trunk for an argument, add a node with each premise, with
        world *w0*, following be a node with the negation of the conclusion
        with world *w0*.
        """
        branch = tableau.branch()
        for premise in argument.premises:
            branch.add({ 'sentence': premise, 'world': 0 })
        branch.add({ 'sentence': negate(argument.conclusion), 'world': 0 })

    class ConditionalModalNodeRule(logic.TableauxSystem.ConditionalNodeRule):
        modal = True

class TableauxRules(object):
    """
    Rules for modal operators employ *world* indexes as well access-type
    nodes. The world indexes are transparent for the rules for classical
    connectives.
    """

    class Closure(logic.TableauxSystem.ClosureRule):
        """
        A branch closes when a sentence and its negation both appear on a node **with the
        same world** on the branch.
        """

        def applies_to_branch(self, branch):
            for node in branch.get_nodes():
                if 'sentence' in node.props and 'world' in node.props:
                    w = node.props['world']
                    s = negate(node.props['sentence'])
                    if branch.has({ 'sentence': s, 'world': w }):
                        return branch
            return False

        def example(self):
            a = atomic(0, 0)
            self.tableau.branch().update([
                { 'sentence' :        a  , 'world' : 0 },
                { 'sentence' : negate(a) , 'world' : 0 }
            ])

    class Conjunction(TableauxSystem.ConditionalModalNodeRule):
        """
        From an unticked conjunction node *n* with world *w* on a branch *b*, for each conjunct,
        add a node with world *w* to *b* with the conjunct, then tick *n*.
        """

        operator = 'Conjunction'

        def apply_to_node(self, node, branch):
            w = node.props['world']
            for conjunct in node.props['sentence'].operands:
                branch.add({ 'sentence' : conjunct, 'world' : w })
            branch.tick(node)

    class ConjunctionNegated(TableauxSystem.ConditionalModalNodeRule):
        """
        From an unticked negated conjunction node *n* with world *w* on a branch *b*, for each
        conjunct, make a new branch *b'* from *b* and add a node with *w* and the negation of
        the conjunct to *b*, then tick *n*.
        """

        negated  = True
        operator = 'Conjunction'

        def apply_to_node(self, node, branch):
            w = node.props['world']
            for conjunct in node.props['sentence'].operand.operands:
                self.tableau.branch(branch).add({ 'sentence' : negate(conjunct), 'world' : w }).tick(node)

    class Disjunction(TableauxSystem.ConditionalModalNodeRule):
        """
        From an unticked disjunction node *n* with world *w* on a branch *b*, for each disjunct,
        make a new branch *b'* from *b* and add a node with world *w* to *b'*, then tick *n*.
        """

        operator = 'Disjunction'

        def apply_to_node(self, node, branch):
            w = node.props['world']
            for disjunct in node.props['sentence'].operands:
                self.tableau.branch(branch).add({ 'sentence' : disjunct, 'world' : w }).tick(node)


    class DisjunctionNegated(TableauxSystem.ConditionalModalNodeRule):
        """
        From an unticked negated disjunction node *n* with world *w* on a branch *b*, for each
        disjunct, add a node with *w* and the negation of the disjunct to *b*, then tick *n*.
        """

        negated  = True
        operator = 'Disjunction'

        def apply_to_node(self, node, branch):
            w = node.props['world']
            for disjunct in node.props['sentence'].operand.operands:
                branch.add({ 'sentence' : negate(disjunct), 'world' : w })
            branch.tick(node)

    class MaterialConditional(TableauxSystem.ConditionalModalNodeRule):
        """
        From an unticked material conditional node *n* with world *w* on a branch *b*, make two
        new branches *b'* and *b''* from *b*, add a node with world *w* and the negation of the
        antecedent to *b'*, and add a node with world *w* and the conequent to *b''*, then tick
        *n*.
        """

        operator = 'Material Conditional'

        def apply_to_node(self, node, branch):
            newBranches = self.tableau.branch_multi(branch, 2)
            s = node.props['sentence']
            w = node.props['world']
            newBranches[0].add({ 'sentence' : negate(s.lhs) , 'world' : w }).tick(node)
            newBranches[1].add({ 'sentence' :        s.rhs  , 'world' : w }).tick(node)

    class MaterialConditionalNegated(TableauxSystem.ConditionalModalNodeRule):
        """
        From an unticked negated material conditional node *n* with world *w* on a branch *b*,
        add two nodes with *w* to *b*, one with the antecedent and the other with the negation
        of the consequent, then tick *n*.
        """

        negated  = True
        operator = 'Material Conditional'

        def apply_to_node(self, node, branch):
            s = node.props['sentence'].operand
            w = node.props['world']
            branch.update([
                { 'sentence' :        s.lhs  , 'world' : w }, 
                { 'sentence' : negate(s.rhs) , 'world' : w }
            ]).tick(node)

    class MaterialBiconditional(TableauxSystem.ConditionalModalNodeRule):
        """
        From an unticked material biconditional node *n* with world *w* on a branch *b*, make
        two new branches *b'* and *b''* from *b*, add two nodes with world *w* to *b'*, one with
        the negation of the antecedent and one with the negation of the consequent, and add two
        nodes with world *w* to *b''*, one with the antecedent and one with the consequent, then
        tick *n*.
        """

        operator = 'Material Biconditional'

        def apply_to_node(self, node, branch):
            s = node.props['sentence']
            w = node.props['world']
            newBranches = self.tableau.branch_multi(branch, 2)
            newBranches[0].update([
                { 'sentence' : negate(s.lhs), 'world' : w }, 
                { 'sentence' : negate(s.rhs), 'world' : w }
            ]).tick(node)
            newBranches[1].update([
                { 'sentence' : s.rhs, 'world' : w }, 
                { 'sentence' : s.lhs, 'world' : w }
            ]).tick(node)

    class MaterialBiconditionalNegated(TableauxSystem.ConditionalModalNodeRule):
        """
        From an unticked negated material biconditional node *n* with world *w* on a branch *b*,
        make two new branches *b'* and *b''* from *b*, add two nodes with *w* to *b'*, one with
        the antecedent and the other with the negation of the consequent, and add two nodes with
        *w* to *b''*, one with the negation of the antecedent and the other with the consequent,
        then tick *n*.
        """

        negated  = True
        operator = 'Material Biconditional'

        def apply_to_node(self, node, branch):
            newBranches = self.tableau.branch_multi(branch, 2)
            s = node.props['sentence'].operand
            w = node.props['world']
            newBranches[0].update([
                { 'sentence':        s.lhs  , 'world' : w },
                { 'sentence': negate(s.rhs) , 'world' : w }
            ]).tick(node)
            newBranches[1].update([
                { 'sentence': negate(s.rhs) , 'world' : w },
                { 'sentence':        s.lhs  , 'world' : w }
            ]).tick(node)

    class Conditional(MaterialConditional):
        """
        The rule functions the same as the corresponding material conditional rule.

        From an unticked conditional node *n* with world *w* on a branch *b*, make two
        new branches *b'* and *b''* from *b*, add a node with world *w* and the negation of the
        antecedent to *b'*, and add a node with world *w* and the conequent to *b''*, then tick
        *n*.
        """

        operator = 'Conditional'

    class ConditionalNegated(MaterialConditionalNegated):
        """
        The rule functions the same as the corresponding material conditional rule.

        From an unticked negated conditional node *n* with world *w* on a branch *b*,
        add two nodes with *w* to *b*, one with the antecedent and the other with the negation
        of the consequent, then tick *n*.
        """

        operator = 'Conditional'

    class Biconditional(MaterialBiconditional):
        """
        The rule functions the same as the corresponding material biconditional rule.

        From an unticked biconditional node *n* with world *w* on a branch *b*, make
        two new branches *b'* and *b''* from *b*, add two nodes with world *w* to *b'*, one with
        the negation of the antecedent and one with the negation of the consequent, and add two
        nodes with world *w* to *b''*, one with the antecedent and one with the consequent, then
        tick *n*.
        """

        operator = 'Biconditional'

    class BiconditionalNegated(MaterialBiconditionalNegated):
        """
        The rule functions the same as the corresponding material biconditional rule.

        From an unticked negated biconditional node *n* with world *w* on a branch *b*,
        make two new branches *b'* and *b''* from *b*, add two nodes with *w* to *b'*, one with
        the antecedent and the other with the negation of the consequent, and add two nodes with
        *w* to *b''*, one with the negation of the antecedent and the other with the consequent,
        then tick *n*.
        """

        operator = 'Biconditional'

    class Existential(TableauxSystem.ConditionalModalNodeRule):
        """
        From an unticked existential node *n* with world *w* on a branch *b*, quantifying over
        variable *v* into sentence *s*, add a node with world *w* to *b* with the substitution
        into *s* of *v* with a constant new to *b*, then tick *n*.
        """

        quantifier = 'Existential'

        def apply_to_node(self, node, branch):
            w = node.props['world']
            s = node.props['sentence']
            v = node.props['sentence'].variable
            branch.add({ 'sentence' : s.substitute(branch.new_constant(), v), 'world': w }).tick(node)

    class ExistentialNegated(TableauxSystem.ConditionalModalNodeRule):
        """
        From an unticked negated existential node *n* with world *w* on a branch *b*,
        quantifying over variable *v* into sentence *s*, add a universally quantified
        node to *b* with world *w* over *v* into the negation of *s*, then tick *n*.
        """

        negated    = True
        quantifier = 'Existential'
        convert_to = 'Universal'

        def apply_to_node(self, node, branch):
            w = node.props['world']
            v = node.props['sentence'].operand.variable
            s = node.props['sentence'].operand.sentence
            # keep conversion neutral for inheritance below
            branch.add({ 'sentence' : quantify(self.convert_to, v, negate(s)), 'world' : w }).tick(node)

    class Universal(logic.TableauxSystem.BranchRule):
        """
        From a universal node with world *w* on a branch *b*, quantifying over variable *v* into
        sentence *s*, result *r* of substituting a constant *c* on *b* (or a new constant if none
        exists) for *v* into *s* does not appear at *w* on *b*, add a node with *w* and *r* to
        *b*. The node *n* is never ticked.
        """

        quantifier = 'Universal'

        def applies_to_branch(self, branch):
            constants = branch.constants()
            for node in branch.get_nodes():
                if 'sentence' in node.props and 'world' in node.props and node.props['sentence'].quantifier == self.quantifier:
                    w = node.props['world']
                    v = node.props['sentence'].variable
                    s = node.props['sentence']
                    if len(constants):
                        for c in constants:
                            r = s.substitute(c, v)
                            if not branch.has({ 'sentence' : r, 'world' : w }):
                                return { 'branch' : branch, 'sentence' : r, 'node' : node, 'world' : w }
                        continue
                    return { 'branch' : branch, 'sentence' : s.substitute(branch.new_constant(), v), 'world' : w }
            return False

        def apply(self, target):
            target['branch'].add({ 'sentence' : target['sentence'], 'world' : target['world'] })

        def example(self):
            self.tableau.branch().add({ 'sentence' : Vocabulary.get_example_quantifier_sentence(self.quantifier), 'world' : 0 })

    class UniversalNegated(ExistentialNegated):
        """
        From an unticked negated universal node *n* with world *w* on a branch *b*,
        quantifying over variable *v* into sentence *s*, add an existentially
        quantified node to *b* with world *w* over *v* into the negation of *s*,
        then tick *n*.
        """

        quantifier = 'Universal'
        convert_to = 'Existential'

    class DoubleNegation(TableauxSystem.ConditionalModalNodeRule):
        """
        From an unticked double negation node *n* with world *w* on a branch *b*, add a
        node to *b* with *w* and the double-negatum of *n*, then tick *n*.
        """

        negated  = True
        operator = 'Negation'

        def apply_to_node(self, node, branch):
            w = node.props['world']
            branch.add({ 'sentence' : node.props['sentence'].operand.operand, 'world' : w }).tick(node)

    class Possibility(TableauxSystem.ConditionalModalNodeRule):
        """
        From an unticked possibility node with world *w* on a branch *b*, add a node with a
        world *w'* new to *b* with the operand of *n*, and add an access-type node with
        world1 *w* and world2 *w'* to *b*, then tick *n*.
        """

        operator = 'Possibility'

        def apply_to_node(self, node, branch):
            s  = node.props['sentence'].operand
            w1 = node.props['world']
            w2 = branch.new_world()
            branch.update([{ 'sentence' : s, 'world' : w2 }, { 'world1' : w1, 'world2' : w2 }]).tick(node)

    class PossibilityNegated(TableauxSystem.ConditionalModalNodeRule):
        """
        From an unticked negated possibility node *n* with world *w* on a branch *b*, add a
        necessity node to *b* with *w*, whose operand is the negation of the negated 
        possibilium of *n*, then tick *n*.
        """

        negated    = True
        operator   = 'Possibility'
        convert_to = 'Necessity'

        def apply_to_node(self, node, branch):
            w = node.props['world']
            s = operate(self.convert_to, [negate(node.props['sentence'].operand.operand)])
            branch.add({ 'sentence' : s, 'world' : w }).tick(node)

    class Necessity(logic.TableauxSystem.BranchRule):
        """
        From a necessity node *n* with world *w1* and operand *s* on a branch *b*, for any
        world *w2* such that an access node with w1,w2 is on *b*, if *b* does not have a node
        with *s* at *w2*, add it to *b*. The node *n* is never ticked.
        """

        operator = 'Necessity'

        def applies_to_branch(self, branch):
            worlds = branch.worlds()
            for node in branch.get_nodes():
                if ('world' in node.props and
                    'sentence' in node.props and
                    node.props['sentence'].operator == self.operator):                    
                    s = node.props['sentence'].operand
                    w1 = node.props['world']
                    for w2 in worlds:
                        if (branch.has({ 'world1': w1, 'world2': w2 }) and
                            not branch.has({ 'sentence': s, 'world': w2 })):
                            return { 'node': node, 'sentence' : s, 'world': w2, 'branch': branch }
            return False

        def apply(self, target):
            target['branch'].add({ 'sentence': target['sentence'], 'world': target['world'] })

        def example(self):
            s = operate(self.operator, [atomic(0, 0)])
            self.tableau.branch().update([{ 'sentence' : s, 'world' : 0 }, { 'world1' : 0, 'world2' : 1 }])

    class NecessityNegated(PossibilityNegated):
        """
        From an unticked negated necessity node *n* with world *w* on a branch *b*, add a
        possibility node whose operand is the negation of the negated necessitatum of *n*,
        then tick *n*.
        """

        operator   = 'Necessity'
        convert_to = 'Possibility'

    rules = [

        Closure,

        # non-branching rules
        Conjunction, 
        DisjunctionNegated, 
        MaterialConditionalNegated,
        ConditionalNegated,
        Existential,
        ExistentialNegated,
        Universal,
        UniversalNegated,
        DoubleNegation,
        PossibilityNegated,
        NecessityNegated,

        # branching rules
        ConjunctionNegated,
        Disjunction, 
        MaterialConditional, 
        MaterialBiconditional,
        MaterialBiconditionalNegated,
        Conditional,
        Biconditional,
        BiconditionalNegated,

        # world creation rules
        Possibility,
        Necessity

    ]