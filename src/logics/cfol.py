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

import k, cpl

name = 'CFOL'
description = 'Classical First Order Logic'

def example_validities():
    # Everything valid in CPL, K3, K3W, GO, or LP is valid in CFOL
    import cpl, k3, k3w, go, lp
    args = k3.example_validities()
    args.update(lp.example_validities())
    args.update(cpl.example_validities())
    args.update(k3w.example_validities())
    args.update(go.example_validities())
    return args

def example_invalidities():
    import k
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
    """
    A CFOL model is the same as
    """
class TableauxSystem(cpl.TableauxSystem):
    """
    CFOL's Tableaux System inherits directly from CPL's.
    """

class TableauxRules(object):
    """
    The Tableaux System for CFOL contains the closure and identity rules from CPL, and all the operator
    rules from K, except for the rules for the modal operators (Necessity, Possibility).
    """

    rules = [

        cpl.TableauxRules.Closure,
        cpl.TableauxRules.SelfIdentityClosure,

        # non-branching rules

        cpl.TableauxRules.IdentityIndiscernability,
        k.TableauxRules.Assertion,
        k.TableauxRules.AssertionNegated,
        k.TableauxRules.Conjunction,
        k.TableauxRules.DisjunctionNegated,
        k.TableauxRules.MaterialConditionalNegated,
        k.TableauxRules.ConditionalNegated,
        k.TableauxRules.Existential,
        k.TableauxRules.ExistentialNegated,
        k.TableauxRules.Universal,
        k.TableauxRules.UniversalNegated,
        k.TableauxRules.DoubleNegation,

        # branching rules

        k.TableauxRules.ConjunctionNegated,
        k.TableauxRules.Disjunction,
        k.TableauxRules.MaterialConditional,
        k.TableauxRules.MaterialBiconditional,
        k.TableauxRules.MaterialBiconditionalNegated,
        k.TableauxRules.Conditional,
        k.TableauxRules.Biconditional,
        k.TableauxRules.BiconditionalNegated

    ]