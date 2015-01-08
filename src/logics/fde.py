name = 'FDE'
description = 'First Degree Entailment 4-valued logic'
links = {
    'Stanford Encyclopedia' : 'http://plato.stanford.edu/entries/logic-paraconsistent/'
}

def example_validities():
    return {
        'Addition'       : [[ 'a'     ], 'Aab'   ],
        'Simplification' : [[ 'Kab'   ], 'a'     ],
        'DeMorgan 1'     : [[ 'NAab'  ], 'KNaNb' ],
        'DeMorgan 2'     : [[ 'NKab'  ], 'ANaNb' ],
        'DeMorgan 3'     : [[ 'KNaNb' ], 'NAab'  ],
        'DeMorgan 4'     : [[ 'ANaNb' ], 'NKab'  ],
        'Contraction'    : [[ 'CaCab' ], 'Cab'   ],
    }

def example_invalidities():
    """
    Everything invalid in K3 or LP is also invalid in FDE.
    """
    import k3, lp
    args = k3.example_invalidities()
    args.update(lp.example_invalidities())
    return args

import logic
from logic import negate, quantify

class TableauxSystem(logic.TableauxSystem):

    @staticmethod
    def build_trunk(tableau, argument):
        """
        To build the trunk for an argument, write each premise with the *designated* marker,
        followed by the conclusion with the *undesignated* marker.
        """

        branch = tableau.branch()
        for premise in argument.premises:
            branch.add({ 'sentence': premise, 'designated': True })
        branch.add({ 'sentence': argument.conclusion, 'designated': False })

    class UniversalyDesignationRule(logic.TableauxSystem.BranchRule):

        conditions = None

        def applies_to_branch(self, branch):
            if self.conditions == None:
                return False
            q = self.conditions[0]
            d = self.conditions[1]
            constants = branch.constants()
            for n in branch.get_nodes():
                if n.props['sentence'].quantifier == q and n.props['designated'] == d:
                    v = n.props['sentence'].variable
                    s = n.props['sentence'].sentence
                    if not len(constants):
                        c = branch.new_constant()
                        return { 'branch' : branch, 'sentence' : s.substitute(c, v), 'node' : n }
                    for c in constants:
                        r = s.substitute(c, v)
                        if not branch.has({ 'sentence': r, 'designated' : d }):
                            return { 'branch' : branch, 'sentence' : r, 'node' : n }
            return False

        def apply(self, target):
            target['branch'].add({ 'sentence' : target['sentence'], 'designated' : target['node'].props['designated'] })

class TableauxRules:

    class Closure(logic.TableauxSystem.ClosureRule):
        """
        A branch closes when a sentence appears on a node marked *designated*,
        and the same sentence appears on a node marked *undesignated*.
        """

        def applies_to_branch(self, branch):
            for node in branch.get_nodes():
                if branch.has({ 'sentence' : node.props['sentence'], 'designated' : not node.props['designated'] }):
                    return branch
            return False

    # Conjunction Rules

    class ConjunctionDesignated(logic.TableauxSystem.OperatorDesignationRule):
        """
        From an unticked designated conjunction node *n* on a branch *b*, for each conjunct
        *c*, add a designated node with *c* to *b*, then tick *n*.
        """

        conditions = ('Conjunction', True)

        def apply_to_node(self, node, branch):
            for conjunct in node.props['sentence'].operands:
                branch.add({ 'sentence' : conjunct, 'designated' : True })
            branch.tick(node)

    class ConjunctionNegatedDesignated(logic.TableauxSystem.DoubleOperatorDesignationRule):
        """
        From an unticked designated negated conjunction node *n* on a branch *b*, for each conjunct
        *c*, make a new branch *b'* from *b* and add a designated node with the negation of *c* to *b'*,
        then tick *n*.
        """

        conditions = (('Negation', 'Conjunction'), True)

        def apply_to_node(self, node, branch):
            for conjunct in node.props['sentence'].operand.operands:
                self.tableau.branch(branch).add({ 'sentence' : negate(conjunct), 'designated' : True }).tick(node)

    class ConjunctionUndesignated(logic.TableauxSystem.OperatorDesignationRule):
        """
        From an unticked undesignated conjunction node *n* on a branch *b*, for each conjunct
        *c*, make a new branch *b'* from *b* and add an undesignated node with *c* to *b'*,
        then tick *n*.
        """

        conditions = ('Conjunction', False)

        def apply_to_node(self, node, branch):
            for conjunct in node.props['sentence'].operands:
                self.tableau.branch(branch).add({ 'sentence' : conjunct, 'designated' : False }).tick(node)

    class ConjunctionNegatedUndesignated(logic.TableauxSystem.DoubleOperatorDesignationRule):
        """
        From an unticked undesignated negated conjunction node *n* on a branch *b*, for each conjunct
        *c*, add an undesignated node with the negation of *c* to *b*, then tick *n*.
        """

        conditions = (('Negation', 'Conjunction'), False)

        def apply_to_node(self, node, branch):
            for conjunct in node.props['sentence'].operand.operands:
                branch.add({ 'sentence' : negate(conjunct), 'designated' : False }).tick(node)

    # Disjunction Rules

    class DisjunctionDesignated(logic.TableauxSystem.OperatorDesignationRule):
        """
        From an unticked designated disjunction node *n* on a branch *b*, for each disjunt
        *d*, make a new branch *b'* from *b* and add a designated node with *d* to *b'*,
        then tick *n*.
        """

        conditions = ('Disjunction', True)

        def apply_to_node(self, node, branch):
            for disjunct in node.props['sentence'].operands:
                self.tableau.branch(branch).add({ 'sentence' : disjunct, 'designated' : True }).tick(node)

    class DisjunctionNegatedDesignated(logic.TableauxSystem.DoubleOperatorDesignationRule):
        """
        From an unticked designated negated disjunction node *n* on a branch *b*, for each disjunct
        *d*, add a designated node with the negation of *d* to *b*, then tick *n*.
        """

        conditions = (('Negation', 'Disjunction'), True)

        def apply_to_node(self, node, branch):
            for disjunct in node.props['sentence'].operand.operands:
                branch.add({ 'sentence': negate(disjunct), 'designated': True })
            branch.tick(node)

    class DisjunctionUndesignated(logic.TableauxSystem.OperatorDesignationRule):
        """
        From an unticked undesignated disjunction node *n* on a branch *b*, for each disjunct
        *d*, add an undesignated node with *d* to *b*, then tick *n*.
        """

        conditions = ('Disjunction', False)

        def apply_to_node(self, node, branch):
            for disjunct in node.props['sentence'].operands:
                branch.add({ 'sentence': disjunct, 'designated': False })
            branch.tick(node)

    class DisjunctionNegatedUndesignated(logic.TableauxSystem.DoubleOperatorDesignationRule):
        """
        From an unticked undesignated negated disjunction node *n* on a branch *b*, for each disjunct
        *d*, make a new branch *b'* from *b* and add an undesignated node with the negation of *d* to
        *b'*, then tick *n*.
        """

        conditions = (('Negation', 'Disjunction'), False)

        def apply_to_node(self, node, branch):
            for disjunct in node.props['sentence'].operand.operands:
                self.tableau.branch(branch).add({ 'sentence' : negate(disjunct), 'designated' : False }).tick(node)

    # Material Conditional Rules

    class MaterialConditionalDesignated(logic.TableauxSystem.OperatorDesignationRule):
        """
        From an unticked designated material conditional node *n* on a branch *b*, make
        two new branches *b'* and *b''* from *b*, add a designated node with the negation
        of the antecedent to *b'*, add a designated node with the consequent to *b''*,
        then tick *n*.
        """

        conditions = ('Material Conditional', True)

        def apply_to_node(self, node, branch):
            newBranches = self.tableau.branch_multi(branch, 2)
            s = node.props['sentence']
            newBranches[0].add({ 'sentence' : negate(s.lhs), 'designated' : True }).tick(node)
            newBranches[1].add({ 'sentence' : s.rhs,         'designated' : True }).tick(node)

    class MaterialConditionalNegatedDesignated(logic.TableauxSystem.DoubleOperatorDesignationRule):
        """
        From an unticked designated negated material conditional node *n* on a branch *b*, add
        a designated node with the antecedent, and a designated node with the negation of the
        consequent to *b*, then tick *n*.
        """

        conditions = (('Negation', 'Material Conditional'), True)

        def apply_to_node(self, node, branch):
            s = node.props['sentence'].operand
            branch.update([
                { 'sentence' : s.lhs,         'designated' : True },
                { 'sentence' : negate(s.rhs), 'designated' : True }
            ]).tick(node)

    class MaterialConditionalUndesignated(logic.TableauxSystem.OperatorDesignationRule):
        """
        From an unticked undesignated material conditional node *n* on a branch *b*, add
        an undesignated node with the negation of the antecedent and an undesignated node
        with the consequent to *b*, then tick *n*.
        """

        conditions = ('Material Conditional', False)

        def apply_to_node(self, node, branch):
            s = node.props['sentence']
            branch.update([
                { 'sentence': negate(s.lhs), 'designated': False },
                { 'sentence': s.rhs,         'designated': False }
            ]).tick(node)

    class MaterialConditionalNegatedUndesignated(logic.TableauxSystem.DoubleOperatorDesignationRule):
        """
        From an unticked undesignated negated material conditional node *n* on a branch *b*, make
        two new branches *b'* and *b''* from *b*, add an undesignated node with the antecedent to
        *b'*, and add an undesignated node with the negation of the consequent to *b''*, then
        tick *n*.
        """

        conditions = (('Negation', 'Material Conditional'), False)

        def apply_to_node(self, node, branch):
            newBranches = self.tableau.branch_multi(branch, 2)
            s  = node.props['sentence'].operand
            newBranches[0].add({ 'sentence' : s.lhs,         'designated' : False }).tick(node)
            newBranches[1].add({ 'sentence' : negate(s.rhs), 'designated' : False }).tick(node)

    # Material Biconditional Rules

    class MaterialBiconditionalDesignated(logic.TableauxSystem.OperatorDesignationRule):
        """
        From an unticked designated material biconditional node *n* on a branch *b*, make
        two new branches *b'* and *b''* from *b*, add a designated node with the negation
        of the antecedent and a designated node with the negation of the consequent to *b'*,
        and add a designated node with the antecedent and a designated node with the
        consequent to *b''*, then tick *n*.
        """

        conditions = ('Material Biconditional', True)

        def apply_to_node(self, node, branch):
            newBranches = self.tableau.branch_multi(branch, 2)
            s = node.props['sentence']
            newBranches[0].update([
                { 'sentence': negate(s.lhs), 'designated': True },
                { 'sentence': negate(s.rhs), 'designated': True }
            ]).tick(node)
            newBranches[1].update([
                { 'sentence': s.rhs, 'designated': True },
                { 'sentence': s.lhs, 'designated': True }
            ]).tick(node)

    class MaterialBiconditionalNegatedDesignated(logic.TableauxSystem.DoubleOperatorDesignationRule):
        """
        From an unticked designated negated material biconditional node *n* on a branch *b*, make
        two branches *b'* and *b''* from *b*, add a designated node with the antecedent and a
        designated node with the negation of the consequent to *b'*, and add a designated node
        with the negation of the antecedent and a designated node with the consequent to *b''*,
        then tick *n*.
        """

        conditions = (('Negation', 'Material Biconditional'), True)

        def apply_to_node(self, node, branch):
            newBranches = self.tableau.branch_multi(branch, 2)
            s = node.props['sentence'].operand
            newBranches[0].update([
                { 'sentence': s.lhs,         'designated': True },
                { 'sentence': negate(s.rhs), 'designated': True }
            ]).tick(node)
            newBranches[1].update([
                { 'sentence': negate(s.lhs), 'designated': True },
                { 'sentence': s.rhs,         'designated': True }
            ]).tick(node)
                    
    class MaterialBiconditionalUndesignated(logic.TableauxSystem.OperatorDesignationRule):
        """
        From an unticked undesignated material biconditional node *n* on a branch *b*, make
        two new branches *b'* and *b''* from *b*, add an undesignated node with the negation
        of the antecedent and an undesignated node with the consequent to *b'*, and add an
        undesignated node with the antecedent and an undesignated node with the negation of
        the consequent to *b''*, then tick *n*.
        """

        conditions = ('Material Biconditional', False)

        def apply_to_node(self, node, branch):
            newBranches = self.tableau.branch_multi(branch, 2)
            s = node.props['sentence']
            newBranches[0].update([
                { 'sentence' : negate(s.lhs), 'designated' : False },
                { 'sentence' : s.rhs,         'designated' : False }
            ]).tick(node)
            newBranches[1].update([
                { 'sentence' : s.lhs,         'designated' : False },
                { 'sentence' : negate(s.rhs), 'designated' : False }
            ]).tick(node)

    class MaterialBiconditionalNegatedUndesignated(logic.TableauxSystem.DoubleOperatorDesignationRule):
        """
        From an undesignated negated material biconditional node *n* on a branch *b*, make
        two branches *b'* and *b''* from *b*, add an undesignated node with the negation of
        the antecendent and an undesignated node with the negation of the consequent to *b'*,
        and add an undesignated node with the antecedent and an undesignated node with the
        consequent to *b''*, then tick *n*.
        """

        conditions = (('Negation', 'Material Biconditional'), False)

        def apply_to_node(self, node, branch):
            newBranches = self.tableau.branch_multi(branch, 2)
            s = node.props['sentence'].operand
            newBranches[0].update([
                { 'sentence' : negate(s.lhs), 'designated' : False },
                { 'sentence' : negate(s.rhs), 'designated' : False }
            ]).tick(node)
            newBranches[1].update([
                { 'sentence' : s.lhs, 'designated' : False },
                { 'sentence' : s.rhs, 'designated' : False }
            ]).tick(node)

    # Conditional Rules

    class ConditionalDesignated(MaterialConditionalDesignated):
        """
        This rule functions the same as the corresponding material conditional rule.

        From an unticked designated conditional node *n* on a branch *b*, make two new
        branches *b'* and *b''* from *b*, add a designated node with the negation of
        the antecedent to *b'*, add a designated node with the consequent to *b''*,
        then tick *n*.
        """

        conditions = ('Conditional', True)

    class ConditionalNegatedDesignated(MaterialConditionalNegatedDesignated):
        """
        This rule functions the same as the corresponding material conditional rule.

        From an unticked designated negated conditional node *n* on a branch *b*, add a
        designated node with the antecedent, and a designated node with the negation of
        the consequent to *b*, then tick *n*.
        """

        conditions = (('Negation', 'Conditional'), True)

    class ConditionalUndesignated(MaterialConditionalUndesignated):
        """
        This rule functions the same as the corresponding material conditional rule.

        From an unticked undesignated conditional node *n* on a branch *b*, add an
        undesignated node with the negation of the antecedent and an undesignated node
        with the consequent to *b*, then tick *n*.
        """

        conditions = ('Conditional', False)

    class ConditionalNegatedUndesignated(MaterialConditionalNegatedUndesignated):
        """
        This rule functions the same as the corresponding material conditional rule.

        From an unticked undesignated negated conditional node *n* on a branch *b*, make two
        new branches *b'* and *b''* from *b*, add an undesignated node with the antecedent to
        *b'*, and add an undesignated node with the negation of the consequent to *b''*, then
        tick *n*.
        """

        conditions = (('Negation', 'Conditional'), False)

    # Biconditional Rules

    class BiconditionalDesignated(MaterialBiconditionalDesignated):
        """
        This rule functions the same as the corresponding material biconditional rule.

        From an unticked designated biconditional node *n* on a branch *b*, make two new
        branches *b'* and *b''* from *b*, add a designated node with the negation of the
        antecedent and a designated node with the negation of the consequent to *b'*,
        and add a designated node with the antecedent and a designated node with the
        consequent to *b''*, then tick *n*.
        """

        conditions = ('Biconditional', True)

    class BiconditionalNegatedDesignated(MaterialBiconditionalNegatedDesignated):
        """
        This rule functions the same as the corresponding material biconditional rule.

        From an unticked designated negated biconditional node *n* on a branch *b*, make two
        branches *b'* and *b''* from *b*, add a designated node with the antecedent and a
        designated node with the negation of the consequent to *b'*, and add a designated node
        with the negation of the antecedent and a designated node with the consequent to *b''*,
        then tick *n*.
        """

        conditions = (('Negation', 'Biconditional'), True)

    class BiconditionalUndesignated(MaterialBiconditionalUndesignated):
        """
        This rule functions the same as the corresponding material biconditional rule.

        From an unticked undesignated material biconditional node *n* on a branch *b*, make
        two new branches *b'* and *b''* from *b*, add an undesignated node with the negation
        of the antecedent and an undesignated node with the consequent to *b'*, and add an
        undesignated node with the antecedent and an undesignated node with the negation of
        the consequent to *b''*, then tick *n*.
        """

        conditions = ('Biconditional', False)

    class BiconditionalNegatedUndesignated(MaterialBiconditionalNegatedUndesignated):
        """
        This rule functions the same as the corresponding material biconditional rule.

        From an undesignated negated biconditional node *n* on a branch *b*, make two
        branches *b'* and *b''* from *b*, add an undesignated node with the negation of the
        antecendent and an undesignated node with the negation of the consequent to *b'*,
        and add an undesignated node with the antecedent and an undesignated node with the
        consequent to *b''*, then tick *n*.
        """

        conditions = (('Negation', 'Biconditional'), False)

    # Quantification Rules

    class ExistentialDesignated(logic.TableauxSystem.QuantifierDesignationRule):
        """
        From an unticked designated existential node *n* on a branch *b* quantifying over
        variable *v* into sentence *s*, add a designated node to *b* with the substitution
        into *s* of a new constant not yet appearing on *b* for *v*, then tick *n*.
        """

        conditions = ('Existential', True)

        def apply_to_node(self, node, branch):
            s = node.props['sentence'].sentence
            v = node.props['sentence'].variable
            branch.add({ 'sentence' : s.substitute(branch.new_constant(), v), 'designated' : True }).tick(node)

    class ExistentialNegated(logic.TableauxSystem.OperatorQuantifierRule):
        """
        From an unticked negated existential node *n* on a branch *b*, having desigation
        *d* and quantifying over variable *v* into sentence *s*, add a node to *b* of
        designation *d* that universally quantifies over *v* into the negation of *s*
        (i.e. change 'not exists x: A' to 'for all x: not A'), then tick *n*.
        """

        connectives = ('Negation', 'Existential')

        def apply_to_node(self, node, branch):
            s = node.props['sentence'].operand.sentence
            v = node.props['sentence'].operand.variable
            d = node.props['designated']
            branch.add({ 'sentence' : quantify('Universal', v, negate(s)), 'designated' : d }).tick(node)

    class ExistentialUndesignated(TableauxSystem.UniversalyDesignationRule):
        """
        From an undesignated existential node *n* on a branch *b*, for any constant *c* on
        *b* such that the result *r* of substituting *c* for the variable bound by the
        sentence of *n* does not appear on *b*, then add an undesignated node with *r* to *b*.
        If there are no constants yet on *b*, then instantiate with a new constant. The node
        *n* is never ticked.
        """

        conditions = ('Existential', False)

    class UniversalDesignated(TableauxSystem.UniversalyDesignationRule):
        """
        From a designated universal node *n* on a branch *b*, for any constant *c* on *b*
        such that the result *r* of substituting *c* for the variable bound by the sentence
        of *n* does not appear on *b*, then add a designated node with *r* to *b*. If there
        are no constants yet on *b*, then instantiate with a new constant. The node *n* is
        never ticked.
        """

        conditions = ('Universal', True)

    class UniversalNegated(logic.TableauxSystem.OperatorQuantifierRule):
        """
        From an unticked negated universal node *n* on a branch *b*, having designation *d*
        and quantifying over variable *v* into sentence *s*, add a node to *b* having
        designation *d* with the existential quantifier over *v* into the negation of *s*
        (i.e. change 'not all x: A' to 'exists x: not A'), then tick *n*.
        """

        connectives = ('Negation', 'Universal')

        def apply_to_node(self, node, branch):
            s = node.props['sentence'].operand.sentence
            v = node.props['sentence'].operand.variable
            d = node.props['designated']
            branch.add({ 'sentence' : quantify('Existential', v, negate(s)), 'designated' : d }).tick(node)

    class UniversalUndesignated(logic.TableauxSystem.QuantifierDesignationRule):
        """
        From an unticked undesignated universal node *n* on a branch *b* quantifying over *v*
        into sentence *s*, add an undesignated node to *b* with the result of substituting into
        *s* a constant new to *b* for *v*, then tick *n*.
        """

        conditions = ('Universal', False)

        def apply_to_node(self, node, branch):
            s = node.props['sentence'].sentence
            v = node.props['sentence'].variable
            r = s.substitute(branch.new_constant(), v)
            branch.add({ 'sentence' : r, 'designated' : False }).tick(node)

    # Negation Rules

    class DoubleNegationDesignated(logic.TableauxSystem.DoubleOperatorDesignationRule):
        """
        From an unticked designated negated negation node *n* on a branch *b*, add a designated
        node to *b* with the double-negatum of *n*, then tick *n*.
        """

        conditions = (('Negation', 'Negation'), True)

        def apply_to_node(self, node, branch):
            branch.add({ 'sentence' : node.props['sentence'].operand.operand, 'designated' : True }).tick(node)

    class DoubleNegationUndesignated(logic.TableauxSystem.DoubleOperatorDesignationRule):
        """
        From an unticked undesignated negated negation node *n* on a branch *b*, add an
        undesignated node to *b* with the double-negatum of *n*, then tick *n*.
        """

        conditions = (('Negation', 'Negation'), False)

        def apply_to_node(self, node, branch):
            branch.add({ 'sentence' : node.props['sentence'].operand.operand, 'designated' : False }).tick(node)

    rules = [

        Closure,

        # non-branching rules

        ConjunctionDesignated, 
        DisjunctionNegatedDesignated,
        DisjunctionUndesignated,
        DisjunctionNegatedUndesignated,
        MaterialConditionalNegatedDesignated,
        MaterialConditionalUndesignated,
        MaterialConditionalNegatedUndesignated,
        ConditionalUndesignated, 
        ConditionalNegatedDesignated,
        ConditionalNegatedUndesignated,
        ExistentialDesignated,
        ExistentialNegated,
        ExistentialUndesignated,
        UniversalDesignated,
        UniversalNegated,
        UniversalUndesignated,
        DoubleNegationDesignated,
        DoubleNegationUndesignated,

        # branching rules

        ConjunctionNegatedDesignated,
        ConjunctionUndesignated,
        ConjunctionNegatedUndesignated,
        DisjunctionDesignated,
        MaterialConditionalDesignated,
        MaterialBiconditionalDesignated,
        MaterialBiconditionalNegatedDesignated,
        MaterialBiconditionalUndesignated,
        MaterialBiconditionalNegatedUndesignated,
        ConditionalDesignated,
        BiconditionalDesignated,
        BiconditionalNegatedDesignated,
        BiconditionalUndesignated,
        BiconditionalNegatedUndesignated

    ]