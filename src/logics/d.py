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
# pytableaux - Deonitic Normal Modal Logic

"""
Deontic logic, also known as the Logic of Obligation, is an extension of K, with
a *serial* accessibility relation, which states that for every world *w*, there is
a world *w'* such that *w* accesses *w'*.

Links
-----

- `Stanford Encyclopedia on Deontic Logic`_

.. _Stanford Encyclopedia on Deontic Logic: http://plato.stanford.edu/entries/logic-deontic/

"""
name = 'D'
description = 'Deontic Normal Modal Logic'

def example_validities():
    import k
    args = k.example_validities()
    args.update([
        'Serial Inference 1',
    ])
    return args
    
def example_invalidities():
    import t
    args = t.example_invalidities()
    args.update([
    	'Reflexive Inference 1' ,
        'Necessity Elimination' ,
        'Possibility Addition'  ,
    ])
    return args
    
import logic, k
from logic import atomic

class TableauxSystem(k.TableauxSystem):
    """
    D's Tableaux System inherits directly from K's.
    """
    pass

class TableauxRules:
    """
    The Tableaux Rules for D contain the rules for K, as well as an additional
    Serial rule, which operates on the accessibility relation for worlds.
    """
    class Serial(logic.TableauxSystem.BranchRule):
        """
        The Serial rule applies to a an open branch *b* when there is a world *w* that
        appears on *b*, but there is no world *w'* such that *w* accesses *w'*. The exception
        to this is when the Serial rule was the last rule to apply to the branch. This
        prevents infinite repetition of the Serial rule for open branches that are otherwise
        finished. For this reason, even though the Serial rule is non-branching, it is ordered
        last in the rules, so that all other rules are checked before it.

        For a node *n* on an open branch *b* on which appears a world *w* for which there is
        no world *w'* on *b* such that *w* accesses *w'*, add a node to *b* with *w* as world1,
        and *w1* as world2, where *w1* does not yet appear on *b*.
        """

        def applies_to_branch(self, branch):
            if len(self.tableau.history) and self.tableau.history[-1]['rule'] == self:
                return False
            serial_worlds = {node.props['world1'] for node in branch.get_nodes() if 'world1' in node.props}
            worlds = branch.worlds() - serial_worlds
            if len(worlds):
                world = worlds.pop()
                return { 'branch' : branch, 'world' : world, 'node' : branch.find({ 'world1' : world }) }
            return False

        def apply(self, target):
            target['branch'].add({ 
                'world1': target['world'], 
                'world2': target['branch'].new_world()
            })

        def example(self):
            self.tableau.branch().add({ 'sentence' : atomic(0, 0), 'world' : 0 })

    class IdentityIndiscernability(k.TableauxRules.IdentityIndiscernability):
        """
        The rule for identity indiscernability is the same as for K, with the exception that
        the rule does not apply if the Serial rule was the last rule to apply to the branch.
        This prevents infinite repetition (back and forth) of the Serial and IdentityIndiscernability
        rules.
        """

        def applies_to_branch(self, branch):
            if len(self.tableau.history) and isinstance(self.tableau.history[-1]['rule'], TableauxRules.Serial):
                return False
            return super(TableauxRules.IdentityIndiscernability, self).applies_to_branch(branch)
        
    rules = [

        k.TableauxRules.Closure,
        k.TableauxRules.SelfIdentityClosure,

        # non-branching rules
        k.TableauxRules.Conjunction, 
        k.TableauxRules.DisjunctionNegated, 
        k.TableauxRules.MaterialConditionalNegated,
        k.TableauxRules.ConditionalNegated,
        k.TableauxRules.Existential,
        k.TableauxRules.ExistentialNegated,
        k.TableauxRules.Universal,
        k.TableauxRules.UniversalNegated,
        k.TableauxRules.DoubleNegation,
        k.TableauxRules.PossibilityNegated,
        k.TableauxRules.NecessityNegated,

        # branching rules
        k.TableauxRules.ConjunctionNegated,
        k.TableauxRules.Disjunction, 
        k.TableauxRules.MaterialConditional, 
        k.TableauxRules.MaterialBiconditional,
        k.TableauxRules.MaterialBiconditionalNegated,
        k.TableauxRules.Conditional,
        k.TableauxRules.Biconditional,
        k.TableauxRules.BiconditionalNegated,

        # world creation rules
        k.TableauxRules.Possibility,
        k.TableauxRules.Necessity,

        # special ordering of serial rule
        IdentityIndiscernability,
        Serial
    ]