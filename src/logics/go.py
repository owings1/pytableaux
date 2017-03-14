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
# pytableaux - Gappy Object 3-valued Logic

name = 'GO'
description = 'Gappy Object 3-valued Logic'

def example_validities():
    return {
        'Addition'       : [[ 'a'     ], 'Aab'  ],
        'Simplification' : [[ 'Kab'   ], 'a'    ],
        'DeMorgan 3'     : [[ 'KNaNb' ], 'NAab' ],
        'DeMorgan 4'     : [[ 'ANaNb' ], 'NKab' ],
        'Contraction'    : [[ 'CaCab' ], 'Cab'  ],
    }

def example_invalidities():
    import cfol
    args = cfol.example_invalidities()
    args.update({
        'DeMorgan 1' : [[ 'NAab' ], 'KNaNb' ],
        'DeMorgan 2' : [[ 'NKab' ], 'ANaNb' ],
    })
    return args

import logic, fde, k3
from logic import negate, operate

class TableauxSystem(fde.TableauxSystem):
    pass

class TableauxRules(object):

    class ConjunctionUndesignated(logic.TableauxSystem.ConditionalNodeRule):

        operator    = 'Conjunction'
        designation = False

        def apply_to_node(self, node, branch):
            branch.add({ 'sentence': negate(node.props['sentence']), 'designated' : True }).tick(node)

    class ConjunctionNegatedDesignated(logic.TableauxSystem.ConditionalNodeRule):

        negated     = True
        operator    = 'Conjunction'
        designation = True

        def apply_to_node(self, node, branch):
            newBranches = self.tableau.branch_multi(branch, 2)
            s = node.props['sentence'].operand
            newBranches[0].add({ 'sentence' : s.lhs, 'designated' : False }).tick(node)
            newBranches[1].add({ 'sentence' : s.rhs, 'designated' : False }).tick(node)

    class ConjunctionNegatedUndesignated(ConjunctionUndesignated):

        negated = True

    class DisjunctionNegatedDesignated(logic.TableauxSystem.ConditionalNodeRule):

        negated     = True
        operator    = 'Disjunction'
        designation = True

        def apply_to_node(self, node, branch):
            s = node.props['sentence'].operand
            branch.update([
                { 'sentence': s.lhs, 'designated' : False },
                { 'sentence': s.rhs, 'designated' : False }
            ]).tick(node)

    class DisjunctionUndesignated(ConjunctionUndesignated):

        operator = 'Disjunction'

    class DisjunctionNegatedUndesignated(ConjunctionNegatedUndesignated):

        operator = 'Disjunction'

    class MaterialConditionalNegatedDesignated(logic.TableauxSystem.ConditionalNodeRule):

        negated     = True
        operator    = 'Material Conditional'
        designation = True

        def apply_to_node(self, node, branch):
            s = node.props['sentence'].operand
            branch.update([
                { 'sentence' : negate(s.lhs) , 'designated' : False },
                { 'sentence' :        s.rhs  , 'designated' : False }
            ]).tick(node)

    class MaterialConditionalUndesignated(ConjunctionUndesignated):

        operator = 'Material Conditional'

    class MaterialConditionalNegatedUndesignated(ConjunctionNegatedUndesignated):

        operator = 'Material Conditional'

    class MaterialBiconditionalNegatedDesignated(logic.TableauxSystem.ConditionalNodeRule):

        negated     = True
        operator    = 'Material Biconditional'
        designation = True

        def apply_to_node(self, node, branch):
            newBranches = self.tableau.branch_multi(branch, 2)
            s = node.props['sentence'].operand
            newBranches[0].update([
                { 'sentence' : negate(s.lhs) , 'designated' : False },
                { 'sentence' :        s.rhs  , 'designated' : False },
            ]).tick(node)
            newBranches[1].update([
                { 'sentence' : negate(s.rhs) , 'designated' : False },
                { 'sentence' :        s.lhs  , 'designated' : False }
            ]).tick(node)

    class MaterialBiconditionalUndesignated(ConjunctionUndesignated):

        operator = 'Material Biconditional'

    class MaterialBiconditionalNegatedUndesignated(ConjunctionNegatedUndesignated):

        operator = 'Material Biconditional'

    class ConditionalDesignated(logic.TableauxSystem.ConditionalNodeRule):

        operator    = 'Conditional'
        designation = True

        def apply_to_node(self, node, branch):
            newBranches = self.tableau.branch_multi(branch, 2)
            s = node.props['sentence']
            disj = operate('Disjunction', [negate(s.lhs), s.rhs])
            newBranches[0].add({ 'sentence' : disj, 'designated' : True }).tick(node)
            newBranches[1].update([
                { 'sentence' :        s.lhs  , 'designated' : False },
                { 'sentence' :        s.rhs  , 'designated' : False },
                { 'sentence' : negate(s.lhs) , 'designated' : False },
                { 'sentence' : negate(s.rhs) , 'designated' : False }
            ]).tick(node)

    class ConditionalNegatedDesignated(logic.TableauxSystem.ConditionalNodeRule):

        negated     = True
        operator    = 'Conditional'
        designation = True

        def apply_to_node(self, node, branch):
            newBranches = self.tableau.branch_multi(branch, 2)
            s = node.props['sentence'].operand
            newBranches[0].update([
                { 'sentence' : s.lhs, 'designated' : True  },
                { 'sentence' : s.rhs, 'designated' : False }
            ]).tick(node)
            newBranches[1].update([
                { 'sentence' : negate(s.rhs), 'designated' : True  },
                { 'sentence' : negate(s.lhs), 'designated' : False }
            ]).tick(node)

    class ConditionalUndesignated(ConjunctionUndesignated):

        operator = 'Conditional'

    class ConditionalNegatedUndesignated(ConjunctionNegatedUndesignated):

        operator = 'Conditional'

    class BiconditionalDesignated(logic.TableauxSystem.ConditionalNodeRule):

        operator    = 'Biconditional'
        designation = True

        def apply_to_node(self, node, branch):
            s = node.props['sentence']
            branch.update([
                { 'sentence' : operate('Conditional', [s.lhs, s.rhs]), 'designated' : True },
                { 'sentence' : operate('Conditional', [s.rhs, s.lhs]), 'designated' : True }
            ]).tick(node)

    class BiconditionalNegatedDesignated(logic.TableauxSystem.ConditionalNodeRule):

        negated     = True
        operator    = 'Biconditional'
        designation = True

        def apply_to_node(self, node, branch):
            newBranches = self.tableau.branch_multi(branch, 2)
            s = node.props['sentence'].operand
            newBranches[0].add({ 'sentence' : negate(operate('Conditional', [s.lhs, s.rhs])), 'designated': True }).tick(node)
            newBranches[1].add({ 'sentence' : negate(operate('Conditional', [s.rhs, s.lhs])), 'designated': True }).tick(node)

    class BiconditionalUndesignated(ConjunctionUndesignated):

        operator = 'Biconditional'

    class BiconditionalNegatedUndesignated(ConjunctionNegatedUndesignated):

        operator = 'Biconditional'

    class ExistentialUndesignated(ConjunctionUndesignated):

        operator   = None
        quantifier = 'Existential'

    class UniversalUndesignated(ExistentialUndesignated):

        quantifier = 'Universal'

    fderules = fde.TableauxRules
    k3rules = k3.TableauxRules

    rules = [

        # closure rules
        fderules.Closure,
        k3rules.Closure,

        # non-branching rules
        fderules.ConjunctionDesignated,
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
        fderules.UniversalDesignated,
        fderules.ExistentialDesignated,
        UniversalUndesignated,
        ExistentialUndesignated,
        fderules.DoubleNegationDesignated,
        fderules.DoubleNegationUndesignated,

        # branching rules
        fderules.DisjunctionDesignated,
        ConjunctionNegatedDesignated,
        fderules.MaterialConditionalDesignated,
        fderules.MaterialBiconditionalDesignated,
        MaterialBiconditionalNegatedDesignated,
        ConditionalDesignated,
        ConditionalNegatedDesignated,
        BiconditionalNegatedDesignated

    ]