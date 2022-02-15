# pytableaux, a multi-logic proof generator.
# Copyright (C) 2014-2022 Doug Owings.
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
# pytableaux - Paracomplete Hybrid 3-valued Logic
name = 'MH'

class Meta(object):
    title    = 'Paracomplete Hybrid Logic'
    category = 'Many-valued'
    description = ' '.join((
        'Three-valued logic (True, False, Neither) with non-standard disjunction,',
        'and a classical-like conditional',
    ))
    tags = 'many-valued', 'gappy', 'non-modal', 'first-order'
    category_display_order = 70

from lexicals import Operator as Oper, Sentence, Quantified
from proof.common import Node
from . import fde as FDE, k3 as K3
from .fde import sdnode, adds, group

class Model(K3.Model):

    def is_sentence_opaque(self, s: Sentence, /):
        return isinstance(s, Quantified) or super().is_sentence_opaque(s)

    def truth_function(self, oper: Oper, a, b = None, /):
        oper = Oper(oper)
        Value = self.Value
        if oper is Oper.Disjunction:
            if Value[a] is Value.N and Value[b] is Value.N:
                return Value.F
        elif oper is Oper.Conditional:
            if Value[a] is Value.T and Value[b] is not Value.T:
                return Value.F
            return Value.T
        return super().truth_function(oper, a, b)

class TableauxSystem(FDE.TableauxSystem):
    """
    MH's Tableaux System inherits directly from the `FDE system`_, employing
    designation markers, and building the trunk in the same way.

    .. _FDE system: fde.html#logics.fde.TableauxSystem
    """
    # operator => negated => designated
    branchables = {
        Oper.Negation: {
            True  : {True: 0, False: 0}
        },
        Oper.Assertion: {
            False : {True: 0, False: 0},
            True  : {True: 0, False: 0},
        },
        Oper.Conjunction: {
            False : {True: 0, False: 1},
            True  : {True: 1, False: 0},
        },
        Oper.Disjunction: {
            False : {True: 1, False: 0},
            True  : {True: 1, False: 3},
        },
        # for now, reduce to negated disjunction
        Oper.MaterialConditional: {
            False : {True: 0, False: 0},
            True  : {True: 0, False: 0},
        },
        # for now, reduce to conjunction
        Oper.MaterialBiconditional: {
            False : {True: 0, False: 0},
            True  : {True: 0, False: 0},
        },
        Oper.Conditional: {
            False : {True: 1, False: 0},
            True  : {True: 0, False: 1},
        },
        # for now, reduce to conjunction
        Oper.Biconditional: {
            False : {True: 0, False: 0},
            True  : {True: 0, False: 0},
        },
    }

class TabRules:
    """
    The closure rules for MH are the `FDE closure rule`_, and the `K3 closure rule`_.
    ...
    
    .. _FDE closure rule: fde.html#logics.fde.TabRules.DesignationClosure
    .. _K3 closure rule: k3.html#logics.k3.TabRules.GlutClosure
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
    class AssertionNegatedDesignated(FDE.TabRules.AssertionNegatedDesignated):
        pass
    class AssertionUndesignated(FDE.TabRules.AssertionUndesignated):
        pass
    class AssertionNegatedUndesignated(FDE.TabRules.AssertionNegatedUndesignated):
        pass

    class ConjunctionDesignated(FDE.TabRules.ConjunctionDesignated):
        pass
    class ConjunctionNegatedDesignated(FDE.TabRules.ConjunctionNegatedDesignated):
        pass
    class ConjunctionUndesignated(FDE.TabRules.ConjunctionUndesignated):
        pass
    class ConjunctionNegatedUndesignated(FDE.TabRules.ConjunctionNegatedUndesignated):
        pass

    class DisjunctionDesignated(FDE.TabRules.DisjunctionDesignated):
        pass

    class DisjunctionNegatedDesignated(FDE.OperatorNodeRule):
        """
        From an unticked, negated, designated disjunction node *n* on a branch *b*,
        make two branches *b'* and *b''* from *b*. On *b'* add four undesignated
        nodes, one for each disjunct and its negation. On *b''* add two designated
        nodes, one for the negation of each disjunct. Then tick *n*.
        """
        designation  = True
        negated      = True
        operator     = Oper.Disjunction
        branch_level = 2

        def _get_node_targets(self, node: Node, _, /):
            s = self.sentence(node)
            lhs, rhs = s
            d = self.designation
            return adds(
                group(
                    sdnode( lhs, not d),
                    sdnode(~lhs, not d),
                    sdnode( rhs, not d),
                    sdnode(~rhs, not d),
                ),
                group(
                    sdnode(~lhs, d),
                    sdnode(~rhs, d),
                )
            )

    class DisjunctionUndesignated(FDE.TabRules.DisjunctionUndesignated):
        pass

    class DisjunctionNegatedUndesignated(FDE.OperatorNodeRule):
        """
        From an unticked, negated, undesignated disjunction node *n* on a branch
        *b*, make four branches from *b*: *b'*, *b''*, *b'''*, and *b''''*. On *b'*,
        add a designated node with the first disjunct, and on *b''*, add a designated
        node with the second disjunct.

        On *b'''* add three nodes:

        - An undesignated node with the first disjunct.
        - An undesignated node with the negation of the first disjunct.
        - A designated node with the negation of the second disjunct.

        On *b''''* add three nodes:

        - An undesignated node with the second disjunct.
        - An undesignated node with the negation of the second disjunct.
        - A designated node with the negation of the first disjunct.

        Then tick *n*.
        """
        designation  = False
        negated      = True
        operator     = Oper.Disjunction
        branch_level = 4

        def _get_node_targets(self, node: Node, _):
            lhs, rhs = self.sentence(node)
            d = self.designation
            return adds(
                group(
                    sdnode(lhs, not d)
                ),
                group(
                    sdnode(rhs, not d)
                ),
                group(
                    sdnode(lhs, d), sdnode(~lhs, d), sdnode(~rhs, not d)
                ),
                group(
                    sdnode(rhs, d), sdnode(~rhs, d), sdnode(~lhs, not d)
                ),
            )

    class MaterialConditionalDesignated(FDE.OperatorNodeRule):
        """
        This rule reduces to a disjunction.
        """
        designation  = True
        operator     = Oper.MaterialConditional
        branch_level = 1

        def _get_node_targets(self, node: Node, _):
            lhs, rhs = self.sentence(node)
            return adds(
                group(sdnode(~lhs | rhs, self.designation))
            )

    class MaterialConditionalNegatedDesignated(FDE.OperatorNodeRule):
        """
        This rule reduces to a negated disjunction.
        """
        designation  = True
        negated      = True
        operator     = Oper.MaterialConditional
        branch_level = 1

        def _get_node_targets(self, node: Node, _):
            lhs, rhs = self.sentence(node)
            return adds(
                group(sdnode(~(~lhs | rhs), self.designation))
            )

    class MaterialConditionalUndesignated(MaterialConditionalDesignated):
        """
        This rule reduces to a disjunction.
        """
        designation = False
        negated     = False

    class MaterialConditionalNegatedUndesignated(MaterialConditionalNegatedDesignated):
        """
        This rule reduces to a negated disjunction.
        """
        designation = False
        negated     = True

    class MaterialBiconditionalDesignated(FDE.ConjunctionReducingRule):
        """
        This rule reduces to a conjunction of material conditionals.
        """
        designation  = True
        operator     = Oper.MaterialBiconditional
        conjunct_op  = Oper.MaterialConditional

    class MaterialBiconditionalNegatedDesignated(MaterialBiconditionalDesignated):
        """
        This rule reduces to a negated conjunction of material conditionals.
        """
        negated = True

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

    class ConditionalDesignated(FDE.OperatorNodeRule):
        """
        From an unticked, designated conditional node *n* on a branch *b*, make
        two branches *b'* and *b''* from *b*. On *b'* add an undesignated node
        with the antecedent, and on *b''* add a designated node with the consequent.
        Then tick *n*.
        """
        designation  = True
        operator     = Oper.Conditional
        branch_level = 2

        def _get_node_targets(self, node: Node, _):
            lhs, rhs = self.sentence(node)
            # Keep designation fixed for inheritance below.
            return adds(
                group(sdnode(lhs, False)),
                group(sdnode(rhs, True)),
            )

    class ConditionalNegatedDesignated(FDE.OperatorNodeRule):
        """
        From an unticked, negated, desigated conditional node *n* on a branch *b*,
        add two nodes to *b*:

        - A designated node with the antecedent.
        - An undesignated node with the consequent.

        Then tick *n*.
        """
        designation  = True
        negated      = True
        operator     = Oper.Conditional
        branch_level = 1

        def _get_node_targets(self, node: Node, _):
            lhs, rhs = self.sentence(node)
            # Keep designation fixed for inheritance below.
            return adds(
                group(sdnode(lhs, True), sdnode(rhs, False))
            )

    class ConditionalUndesignated(ConditionalNegatedDesignated):
        """
        From an unticked, undesignated conditional node *n* on a branch *b*, add
        two nodes to *b*:

        - A designated node with the antecedent.
        - An undesignated node with the consequent.

        Then tick *n*.

        Note that the nodes added are the same as for the above
        *ConditionalNegatedDesignated* rule.
        """
        designation = False
        negated     = False

    class ConditionalNegatedUndesignated(ConditionalDesignated):
        """
        From an unticked, negated, undesignated conditional node *n* on a branch *b*,
        make two branches *b'* and *b''* from *b*. On *b'* add an undesignated node
        with the antecedent, and on *b''* add a designated node with the consequent.
        Then tick *n*.

        Note that the result is the same as for the above *ConditionalDesignated* rule.
        """
        designation = False
        negated     = True

    class BiconditionalDesignated(FDE.ConjunctionReducingRule):
        """
        This rule reduces to a conjunction of conditionals.
        """
        designation = True
        operator    = Oper.Biconditional
        conjunct_op = Oper.Conditional

    class BiconditionalNegatedDesignated(BiconditionalDesignated):
        """
        This rule reduces to a negated conjunction of conditionals.
        """
        negated = True

    class BiconditionalUndesignated(BiconditionalDesignated):
        """
        This rule reduces to a conjunction of conditionals.
        """
        designation = False

    class BiconditionalNegatedUndesignated(BiconditionalNegatedDesignated):
        """
        This rule reduces to a negated conjunction of conditionals.
        """
        designation = False

    closure_rules = (
        GlutClosure,
        DesignationClosure,
    )

    rule_groups = (
        # Non-branching rules.
        (
            AssertionDesignated,
            AssertionUndesignated,
            AssertionNegatedDesignated,
            AssertionNegatedUndesignated,
            ConjunctionDesignated,
            ConjunctionNegatedUndesignated,
            DisjunctionUndesignated,
            MaterialConditionalDesignated,
            MaterialConditionalNegatedDesignated,
            MaterialConditionalUndesignated,
            MaterialConditionalNegatedUndesignated,
            MaterialBiconditionalDesignated,
            MaterialBiconditionalNegatedDesignated,
            MaterialBiconditionalUndesignated,
            MaterialBiconditionalNegatedUndesignated,
            ConditionalUndesignated,
            ConditionalNegatedDesignated,
            BiconditionalDesignated,
            BiconditionalNegatedDesignated,
            BiconditionalUndesignated,
            BiconditionalNegatedUndesignated,
            DoubleNegationDesignated,
            DoubleNegationUndesignated,
        ),
        # 1-branching rules.
        (
            ConjunctionUndesignated,
            ConjunctionNegatedDesignated,
            DisjunctionDesignated,
            DisjunctionNegatedDesignated,
            ConditionalDesignated,
            ConditionalNegatedUndesignated,
        ),
        # 3-branching rules.
        (
            DisjunctionNegatedUndesignated,
        ),
    )

