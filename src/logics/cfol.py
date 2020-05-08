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
# pytableaux - Classical First-Order Logic

"""
Classical First-Order Logic (CFOL) augments CPL with the quantifiers: Universal and Existential.

Semantics
---------

The semantics for CFOL is the same as CPL, except we add two operators for quantification.

**Quantification** can be thought of along these lines:

- **Universal Quantifier**: *P{LxFx}* has the value:

    - **true** iff everything is in the extension of *F*.
    - **false** iff not everything is in the extension of *F*.

- **Existential Quantifier**: *P{XxFx}* is equivalent to *P{~Lx~Fx}*.

*C* is a **Logical Consequence** of *A* iff all cases where the value of *A* is **true**
are cases where *C* also has the value **true**.
"""

from . import k, cpl

name = 'CFOL'
title = 'Classical First Order Logic'

def example_validities():
    # Everything valid in CPL, K3, K3W, GO, or LP is valid in CFOL
    from . import cpl, k3, k3w, go, lp
    args = k3.example_validities()
    args.update(lp.example_validities())
    args.update(cpl.example_validities())
    args.update(k3w.example_validities())
    args.update(go.example_validities())
    return args

def example_invalidities():
    args = k.example_invalidities()
    args.update([
        'Necessity Distribution'     ,
        'Necessity Elimination'      ,
        'Possibility Addition'       ,
        'Possibility Distribution'   ,
        'Reflexive Inference 1'      ,
    ])
    return args

import logic, examples
from logic import negate

truth_values = cpl.truth_values
truth_value_chars = cpl.truth_value_chars
designated_values = cpl.designated_values
undesignated_values = cpl.undesignated_values
unassigned_value = cpl.unassigned_value
truth_functional_operators = cpl.truth_functional_operators
truth_function = cpl.truth_function

class Model(cpl.Model):
    # """
    # A CFOL model is the same as
    # """
    pass

class TableauxSystem(cpl.TableauxSystem):
    """
    CFOL's Tableaux System inherits directly from CPL's.
    """

class TableauxRules(object):
    """
    The Tableaux System for CFOL contains all the rules from CPL, as well as
    additional rules for the quantifiers.
    """

    class Existential(cpl.NonModal, k.TableauxRules.Existential):
        """
        From an unticked existential node *n* on a branch *b*, quantifying over
        variable *v* into sentence *s*, add a node to *b* with the substitution
        into *s* of *v* with a constant new to *b*, then tick *n*.
        """
        pass

    class ExistentialNegated(cpl.NonModal, k.TableauxRules.ExistentialNegated):
        """
        From an unticked negated existential node *n* on a branch *b*,
        quantifying over variable *v* into sentence *s*, add a universally quantified
        node to *b* over *v* into the negation of *s*, then tick *n*.
        """
        pass

    class Universal(cpl.NonModal, k.TableauxRules.Universal):
        """
        From a universal node on a branch *b*, quantifying over variable *v* into
        sentence *s*, result *r* of substituting a constant *c* on *b* (or a new constant if none
        exists) for *v* into *s* does not appear on *b*, add a node with *r* to
        *b*. The node *n* is never ticked.
        """
        pass

    class UniversalNegated(cpl.NonModal, k.TableauxRules.UniversalNegated):
        """
        From an unticked negated universal node *n* on a branch *b*,
        quantifying over variable *v* into sentence *s*, add an existentially
        quantified node to *b* over *v* into the negation of *s*,
        then tick *n*.
        """
        pass

    rules = [

        cpl.TableauxRules.Closure,
        cpl.TableauxRules.SelfIdentityClosure,

        # non-branching rules

        cpl.TableauxRules.IdentityIndiscernability,
        cpl.TableauxRules.Assertion,
        cpl.TableauxRules.AssertionNegated,
        cpl.TableauxRules.Conjunction,
        cpl.TableauxRules.DisjunctionNegated,
        cpl.TableauxRules.MaterialConditionalNegated,
        cpl.TableauxRules.ConditionalNegated,
        Existential,
        ExistentialNegated,
        Universal,
        UniversalNegated,
        cpl.TableauxRules.DoubleNegation,

        # branching rules

        cpl.TableauxRules.ConjunctionNegated,
        cpl.TableauxRules.Disjunction,
        cpl.TableauxRules.MaterialConditional,
        cpl.TableauxRules.MaterialBiconditional,
        cpl.TableauxRules.MaterialBiconditionalNegated,
        cpl.TableauxRules.Conditional,
        cpl.TableauxRules.Biconditional,
        cpl.TableauxRules.BiconditionalNegated

    ]