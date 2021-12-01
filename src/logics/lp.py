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
# pytableaux - Logic of Paradox
name = 'LP'

class Meta(object):
    title    = 'Logic of Paradox'
    category = 'Many-valued'
    description = 'Three-valued logic (T, F, B)'
    tags = ['many-valued', 'glutty', 'non-modal', 'first-order']
    category_display_order = 100

from lexicals import Atomic
from proof.rules import ClosureRule
from . import fde
from utils import UniqueList

class Model(fde.Model):
    """
    An LP model is like an `FDE model`_ without the :m:`N` value, which yields an
    exhaustion restraint an predicate's extension/anti-extension.

    .. _FDE model: fde.html#logics.fde.Model
    """

    #: The admissible values
    truth_values = UniqueList(('F', 'B', 'T'))#set(truth_values_list)

    unassigned_value = 'F'

    nvals = {
        'F': 0    ,
        'B': 0.75 ,
        'T': 1    ,
    }
    cvals = {
        0    : 'F',
        0.75 : 'B',
        1    : 'T',
    }

    def value_of_operated(self, sentence, **kw):
        """
        The value of a sentence with a truth-functional operator is determined by
        the values of its operands according to the following tables.

        //truth_tables//lp//
        """
        return super().value_of_operated(sentence, **kw)

class TableauxSystem(fde.TableauxSystem):
    """
    LP's Tableaux System inherits directly from the `FDE system`_, employing
    designation markers, and building the trunk in the same way.

    .. _FDE system: fde.html#logics.fde.TableauxSystem
    """
    pass

class TableauxRules(object):
    """
    The Tableaux System for LP contains all the rules from :ref:`FDE <FDE>`, as well as an additional
    closure rule.
    """

    class GapClosure(ClosureRule):
        """
        A branch closes when a sentence and its negation both appear as undesignated nodes.
        This rule is **in addition to** the `FDE closure rule`_.

        .. _FDE closure Rule: fde.html#logics.fde.TableauxRules.DesignationClosure
        """

        # tracker implementation

        def check_for_target(self, node, branch):
            nnode = self.__find_closing_node(node, branch)
            if nnode:
                return {'nodes': {node, nnode}}

        # rule implementation

        def node_will_close_branch(self, node, branch):
            if self.__find_closing_node(node, branch):
                return True
            return False

        def applies_to_branch(self, branch):
            # Delegate to tracker
            return self.ntch.cached_target(branch)

        def example_nodes(self, branch = None):
            a = Atomic.first()
            return (
                {'sentence': a         , 'designated': False},
                {'sentence': a.negate(), 'designated': False},
            )

        # private util

        def __find_closing_node(self, node, branch):
            if node.has('sentence', 'designated') and not node['designated']:
                return branch.find({
                    'sentence'   : node['sentence'].negative(),
                    'designated' : False
                })

    class DesignationClosure(fde.TableauxRules.DesignationClosure):
        pass

    class DoubleNegationDesignated(fde.TableauxRules.DoubleNegationDesignated):
        pass

    class DoubleNegationUndesignated(fde.TableauxRules.DoubleNegationUndesignated):
        pass

    class AssertionDesignated(fde.TableauxRules.AssertionDesignated):
        pass

    class AssertionNegatedDesignated(fde.TableauxRules.AssertionNegatedDesignated):
        pass

    class AssertionUndesignated(fde.TableauxRules.AssertionUndesignated):
        pass

    class AssertionNegatedUndesignated(fde.TableauxRules.AssertionNegatedUndesignated):
        pass

    class ConjunctionDesignated(fde.TableauxRules.ConjunctionDesignated):
        pass

    class ConjunctionNegatedDesignated(fde.TableauxRules.ConjunctionNegatedDesignated):
        pass

    class ConjunctionUndesignated(fde.TableauxRules.ConjunctionUndesignated):
        pass

    class ConjunctionNegatedUndesignated(fde.TableauxRules.ConjunctionNegatedUndesignated):
        pass

    class DisjunctionDesignated(fde.TableauxRules.DisjunctionDesignated):
        pass

    class DisjunctionNegatedDesignated(fde.TableauxRules.DisjunctionNegatedDesignated):
        pass

    class DisjunctionUndesignated(fde.TableauxRules.DisjunctionUndesignated):
        pass

    class DisjunctionNegatedUndesignated(fde.TableauxRules.DisjunctionNegatedUndesignated):
        pass

    class MaterialConditionalDesignated(fde.TableauxRules.MaterialConditionalDesignated):
        pass

    class MaterialConditionalNegatedDesignated(fde.TableauxRules.MaterialConditionalNegatedDesignated):
        pass

    class MaterialConditionalUndesignated(fde.TableauxRules.MaterialConditionalUndesignated):
        pass

    class MaterialConditionalNegatedUndesignated(fde.TableauxRules.MaterialConditionalNegatedUndesignated):
        pass

    class MaterialBiconditionalDesignated(fde.TableauxRules.MaterialBiconditionalDesignated):
        pass

    class MaterialBiconditionalNegatedDesignated(fde.TableauxRules.MaterialBiconditionalNegatedDesignated):
        pass

    class MaterialBiconditionalUndesignated(fde.TableauxRules.MaterialBiconditionalUndesignated):
        pass

    class MaterialBiconditionalNegatedUndesignated(fde.TableauxRules.MaterialBiconditionalNegatedUndesignated):
        pass

    class ConditionalDesignated(fde.TableauxRules.ConditionalDesignated):
        pass

    class ConditionalNegatedDesignated(fde.TableauxRules.ConditionalNegatedDesignated):
        pass

    class ConditionalUndesignated(fde.TableauxRules.ConditionalUndesignated):
        pass

    class ConditionalNegatedUndesignated(fde.TableauxRules.ConditionalNegatedUndesignated):
        pass
        
    class BiconditionalDesignated(fde.TableauxRules.BiconditionalDesignated):
        pass

    class BiconditionalNegatedDesignated(fde.TableauxRules.BiconditionalNegatedDesignated):
        pass

    class BiconditionalUndesignated(fde.TableauxRules.BiconditionalUndesignated):
        pass

    class BiconditionalNegatedUndesignated(fde.TableauxRules.BiconditionalNegatedUndesignated):
        pass

    class ExistentialDesignated(fde.TableauxRules.ExistentialDesignated):
        pass

    class ExistentialNegatedDesignated(fde.TableauxRules.ExistentialNegatedDesignated):
        pass

    class ExistentialUndesignated(fde.TableauxRules.ExistentialUndesignated):
        pass

    class ExistentialNegatedUndesignated(fde.TableauxRules.ExistentialNegatedUndesignated):
        pass

    class UniversalDesignated(fde.TableauxRules.UniversalDesignated):
        pass

    class UniversalNegatedDesignated(fde.TableauxRules.UniversalNegatedDesignated):
        pass

    class UniversalUndesignated(fde.TableauxRules.UniversalUndesignated):
        pass

    class UniversalNegatedUndesignated(fde.TableauxRules.UniversalNegatedUndesignated):
        pass

    closure_rules = [
        GapClosure,
        DesignationClosure,
    ]

    rule_groups = [
        [
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
            ConditionalUndesignated, 
            ConditionalNegatedDesignated,
            ExistentialNegatedDesignated,
            ExistentialNegatedUndesignated,
            UniversalNegatedDesignated,
            UniversalNegatedUndesignated,
            DoubleNegationDesignated,
            DoubleNegationUndesignated,
        ],
        [
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
            ConditionalNegatedUndesignated,
            BiconditionalDesignated,
            BiconditionalNegatedDesignated,
            BiconditionalUndesignated,
            BiconditionalNegatedUndesignated,
        ],
        [
            ExistentialDesignated,
            ExistentialUndesignated,
        ],
        [
            UniversalDesignated,
            UniversalUndesignated,
        ],
    ]