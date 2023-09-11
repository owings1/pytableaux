# pytableaux, a multi-logic proof generator.
# Copyright (C) 2014-2023 Doug Owings.
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
# pytableaux.logics.knownargs
from __future__ import annotations

from collections import defaultdict
from types import MappingProxyType as MapProxy
from typing import Any, Callable, Collection, Iterable, Mapping, TypeVar

from pytableaux.examples import arguments as examples
from pytableaux.lang import Argument
from pytableaux.logics import LogicType, registry, LogicSet
from pytableaux.proof import Tableau
from pytableaux.tools import qset, qsetf, wraps

_F = TypeVar('_F', bound=Callable)


validities = {}
invalidities = {}

def L(name, valid=(), invalid=()):
    validities[name] = valid
    invalidities[name] = invalid

arguments = dict(examples)
arguments.update((key, Argument(value, title=key)) for key, value in dict.items({
    'Test Arrow Negation 1': 'NUbc:a:UaNUbc',
    'Test Arrow Negation 2': 'NUab:a:UaNUbc',
    'Test Biarrow Negation 1': 'NBab:c:BcNUab',
    'Test Contradiction Arrow 1': 'NUab:a:Na:Nb',
}))


L('*',
    valid = (
        'Disjunction Idempotence 1',
        'Disjunction Idempotence 2',
        'Modal Platitude 1',
        'Modal Platitude 2',
        'Modal Platitude 3',
    ),
    invalid = (
        'Affirming a Disjunct 1',
        'Affirming a Disjunct 2',
        'Affirming the Consequent',
        'Conditional Equivalence',
        'Denying the Antecedent',
        'Extracting a Disjunct 1',
        'Extracting a Disjunct 2',
        'Extracting the Antecedent',
        'Extracting the Consequent',
        'Possibility Distribution',
        'Triviality 1',
        'Triviality 2',
        'Test Arrow Negation 2',
        'Universal from Existential',
    ))

# ---------------------------------------------------------------------------

L('CPL',
    valid = (
        'Addition',
        'Asserted Addition',
        'Assertion Elimination 1',
        'Assertion Elimination 2',
        'Biconditional Elimination 1',
        'Biconditional Elimination 2',
        'Biconditional Elimination 3',
        'Biconditional Identity',
        'Biconditional Introduction 1',
        'Biconditional Introduction 2',
        'Biconditional Introduction 3',
        'Conditional Contraction',
        'Conditional Contraposition 1',
        'Conditional Contraposition 2',
        'Conditional Double Negation',
        'Conditional Identity',
        'Conditional Law of Excluded Middle',
        'Conditional Modus Ponens',
        'Conditional Modus Tollens',
        'Conditional Pseudo Contraction',
        'Conditional Pseudo Contraposition',
        'Conjunction Commutativity',
        'Conjunction Elimination',
        'Conjunction Idempotence 1',
        'Conjunction Idempotence 2',
        'Conjunction Introduction',
        'Conjunction Pseudo Commutativity',
        'DeMorgan 1',
        'DeMorgan 2',
        'DeMorgan 3',
        'DeMorgan 4',
        'DeMorgan 5',
        'DeMorgan 6',
        'DeMorgan 7',
        'DeMorgan 8',
        'Disjunction Commutativity',
        'Disjunction Pseudo Commutativity',
        'Disjunctive Syllogism 1',
        'Disjunctive Syllogism 2',
        'Existential to Conditional Identity',
        'Existential to Material Identity',
        'Explosion',
        'Identity Indiscernability 1',
        'Identity Indiscernability 2',
        'Law of Excluded Middle',
        'Law of Non-contradiction',
        'Material Biconditional Elimination 1',
        'Material Biconditional Elimination 2',
        'Material Biconditional Elimination 3',
        'Material Biconditional Identity',
        'Material Biconditional Introduction 1',
        'Material Contraction',
        'Material Contraposition 1',
        'Material Contraposition 2',
        'Material Identity',
        'Material Modus Ponens',
        'Material Modus Tollens',
        'Material Pseudo Contraction',
        'Material Pseudo Contraposition',
        'Self Identity 1',
        'Test Arrow Negation 1',
        'Test Biarrow Negation 1',
        'Test Contradiction Arrow 1',
    ),
    invalid = (
        'Existential Syllogism',
        'Existential from Universal',
        'Quantifier Interdefinability 1',
        'Quantifier Interdefinability 2',
        'Quantifier Interdefinability 3',
        'Quantifier Interdefinability 4',
        'Self Identity 2',
        'Syllogism',
        'Universal Predicate Syllogism',
        # moved from suite
        'Nb:Bab',
        'Nb:NBab',
    ))

# ---------------------------------------------------------------------------

L('CFOL',
    valid = (
        'Existential from Universal',
        'Existential Syllogism',
        'Quantifier Interdefinability 1',
        'Quantifier Interdefinability 2',
        'Quantifier Interdefinability 3',
        'Quantifier Interdefinability 4',
        'Self Identity 2',
        'Syllogism',
        'Universal Predicate Syllogism',
        Argument('b:VxKFxKaNa', title='cfol_regression_efq_univeral_with_contradiction_no_constants'),
    ),
    invalid = (
        'KFDE Distribution Inference 1',
        'Modal Transformation 1',
        'Modal Transformation 2',
        'Modal Transformation 3',
        'Modal Transformation 4',
        'Necessity Distribution 1',
        'Necessity Distribution 2',
        'NP Conditional Modus Ponens',
    ))

L('K',
    valid = (

    ),
    invalid = (        
        'Serial Inference 1',
        'Serial Inference 2',
    ))

L('D',
    valid = (
        'Serial Inference 1',
        'Serial Inference 2',
    ),
    invalid = (        
        'Necessity Elimination',
        'NP Collapse 1',
        'Possibility Addition',
        'Possibility Distribution',
        'Reflexive Inference 1',
        'S4 Conditional Inference 2',
    ))

L('T',
    valid = (
        'Necessity Elimination',
        'NP Collapse 1',
        'Possibility Addition',
        'Reflexive Inference 1',
    ),
    invalid = (
        'S4 Conditional Inference 1',
        'S4 Conditional Inference 2',
        'S4 Material Inference 1',
        'S4 Material Inference 2',
    ))

L('S4',
    valid = (
        'S4 Conditional Inference 1',
        'S4 Conditional Inference 2',
        'S4 Material Inference 1',
        'S4 Material Inference 2',
    ),
    invalid = (
        'S5 Conditional Inference 1',
        'S5 Inference 1',
        'S5 Material Inference 1',
    ))

L('S5',
    valid = (
        'S5 Conditional Inference 1',
        'S5 Material Inference 1',
    ),
    invalid = (
        Argument('KMNbc:LCaMNb:Ma', title='nested_diamond_within_box1'),
    ))

# ---------------------------------------------------------------------------


L('K3WQ',
    valid = (
        'Assertion Elimination 1',
        'Assertion Elimination 2',
        'Biconditional Elimination 1',
        'Biconditional Elimination 2',
        'Biconditional Elimination 3',
        'Biconditional Introduction 1',
        'Biconditional Introduction 2',
        'Biconditional Introduction 3',
        'Conditional Contraction',
        'Conditional Contraposition 1',
        'Conditional Contraposition 2',
        'Conditional Modus Ponens',
        'Conditional Modus Tollens',
        'Conjunction Commutativity',
        'Conjunction Elimination',
        'Conjunction Idempotence 1',
        'Conjunction Idempotence 2',
        'Conjunction Introduction',
        'DeMorgan 1',
        'DeMorgan 2',
        'DeMorgan 3',
        'DeMorgan 4',
        'DeMorgan 5',
        'DeMorgan 6',
        'DeMorgan 7',
        'DeMorgan 8',
        'Disjunction Commutativity',
        'Disjunctive Syllogism 1',
        'Disjunctive Syllogism 2',
        'Existential from Universal',
        'Existential Syllogism',
        'Existential to Conditional Identity',
        'Existential to Material Identity',
        'Law of Non-contradiction',
        'Material Biconditional Elimination 1',
        'Material Biconditional Elimination 2',
        'Material Biconditional Elimination 3',
        'Material Biconditional Introduction 1',
        'Material Contraction',
        'Material Contraposition 1',
        'Material Contraposition 2',
        'Material Modus Ponens',
        'Material Modus Tollens',
        'Quantifier Interdefinability 1',
        'Quantifier Interdefinability 2',
        'Quantifier Interdefinability 3',
        'Quantifier Interdefinability 4',
        'Syllogism',
        'Test Arrow Negation 1',
        'Test Biarrow Negation 1',
        'Test Contradiction Arrow 1',
        'Universal Predicate Syllogism',
    ),
    invalid = (
        'Addition',
        'Asserted Addition',
        'Biconditional Identity',
        'Conditional Double Negation',
        'Conditional Identity',
        'Conditional Law of Excluded Middle',
        'Conditional Pseudo Contraction',
        'Conditional Pseudo Contraposition',
        'Conjunction Pseudo Commutativity',
        'Disjunction Pseudo Commutativity',
        'Identity Indiscernability 1',
        'Identity Indiscernability 2',
        'Law of Excluded Middle',
        'Material Biconditional Identity',
        'Material Identity',
        'Material Pseudo Contraction',
        'Material Pseudo Contraposition',
        'Necessity Distribution 1',
        'Reflexive Inference 1',
        'S4 Conditional Inference 1',
        'S4 Material Inference 1',
        'S5 Conditional Inference 1',
        'S5 Material Inference 1',
        'Self Identity 1',
        'Self Identity 2',
        'Serial Inference 1',
        
    ))

L('MH',
    valid = (
        'Addition',
        'Asserted Addition',
        'Assertion Elimination 1',
        'Assertion Elimination 2',
        'Biconditional Elimination 1',
        'Biconditional Identity',
        'Biconditional Introduction 1',
        'Biconditional Introduction 2',
        'Biconditional Introduction 3',
        'Conditional Contraction',
        'Conditional Double Negation',
        'Conditional Identity',
        'Conditional Law of Excluded Middle',
        'Conditional Modus Ponens',
        'Conditional Pseudo Contraction',
        'Conjunction Commutativity',
        'Conjunction Elimination',
        'Conjunction Idempotence 1',
        'Conjunction Idempotence 2',
        'Conjunction Introduction',
        'Conjunction Pseudo Commutativity',
        'DeMorgan 2',
        'DeMorgan 3',
        'DeMorgan 4',
        'DeMorgan 5',
        'DeMorgan 6',
        'DeMorgan 7',
        'Disjunction Commutativity',
        'Disjunction Pseudo Commutativity',
        'Disjunctive Syllogism 1',
        'Disjunctive Syllogism 2',
        'Existential from Universal',
        'Existential Syllogism',
        'Existential to Conditional Identity',
        'Explosion',
        'Material Biconditional Elimination 1',
        'Material Biconditional Elimination 2',
        'Material Biconditional Elimination 3',
        'Material Biconditional Introduction 1',
        'Material Contraction',
        'Material Contraposition 1',
        'Material Contraposition 2',
        'Material Modus Ponens',
        'Material Modus Tollens',
        'Quantifier Interdefinability 1',
        'Quantifier Interdefinability 2',
        'Quantifier Interdefinability 3',
        'Syllogism',
        'Test Arrow Negation 1',
        'Test Biarrow Negation 1',
        'Test Contradiction Arrow 1',
        'Universal Predicate Syllogism',
        Argument('UaUba', title='hmh_axiom01'),
        Argument('UUaUbcUUabUac', title='hmh_axiom02'),
        Argument('UKaba', title='hmh_axiom03'),
        Argument('UKabb', title='hmh_axiom04'),
        Argument('UUabUUacUaKbc', title='hmh_axiom05'),
        Argument('UaAab', title='hmh_axiom06'),
        Argument('UbAab', title='hmh_axiom07'),
        Argument('UUacUUbcUAabc', title='hmh_axiom08'),
        Argument('BNNaa', title='hmh_axiom09'),
        Argument('AAaNaNAaNa', title='hmh_axiom10'),
        # Argument('AUabNUab', title='hmh_axiom11'), # Conditional LEM
        Argument('UAaNaUUabUNbNa', title='hmh_axiom12'),
        Argument('BNKabANaNb', title='hmh_axiom13'),
        Argument('BNAabAKNaNbKNAaNaNAbNb', title='hmh_axiom14'),
        Argument('UANaNAaNaUab', title='hmh_axiom15'),
        Argument('UKaANbNAbNbNUab', title='hmh_axiom16'),
        Argument('BNAaNaNANaNNa', title='ifn'),
    ),
    invalid = (
        'Biconditional Elimination 2',
        'Biconditional Elimination 3',
        'Conditional Contraposition 1',
        'Conditional Contraposition 2',
        'Conditional Modus Tollens',
        'Conditional Pseudo Contraposition',
        'DeMorgan 1',
        'DeMorgan 8',
        'Existential to Material Identity',
        'Identity Indiscernability 1',
        'Identity Indiscernability 2',
        'Law of Excluded Middle',
        'Material Biconditional Identity',
        'Material Identity',
        'Material Pseudo Contraction',
        'Material Pseudo Contraposition',
        'Quantifier Interdefinability 4',
        'Self Identity 1',
        'Self Identity 2',
        Argument('UNbNa:NAaNa:Uab', title='p_from_article'),
    ))

# -----------------

L('NH',
    valid = (
        'Addition',
        'Asserted Addition',
        'Assertion Elimination 1',
        'Assertion Elimination 2',
        'Biconditional Elimination 1',
        'Biconditional Elimination 3',
        'Biconditional Identity',
        'Biconditional Introduction 1',
        'Conditional Contraction',
        'Conditional Double Negation',
        'Conditional Identity',
        'Conditional Law of Excluded Middle',
        'Conditional Modus Ponens',
        'Conditional Pseudo Contraction',
        'Conjunction Commutativity',
        'Conjunction Elimination',
        'Conjunction Idempotence 1',
        'Conjunction Idempotence 2',
        'Conjunction Introduction',
        'Conjunction Pseudo Commutativity',
        'DeMorgan 1',
        'DeMorgan 2',
        'DeMorgan 3',
        'DeMorgan 6',
        'DeMorgan 7',
        'DeMorgan 8',
        'Disjunction Commutativity',
        'Disjunction Pseudo Commutativity',
        'Existential from Universal',
        'Existential from Universal',
        'Existential to Conditional Identity',
        'Existential to Material Identity',
        'Law of Excluded Middle',
        'Material Biconditional Identity',
        'Material Biconditional Introduction 1',
        'Material Contraction',
        'Material Contraposition 1',
        'Material Contraposition 2',
        'Material Identity',
        'Material Pseudo Contraction',
        'Material Pseudo Contraposition',
        'Quantifier Interdefinability 1',
        'Quantifier Interdefinability 2',
        'Quantifier Interdefinability 4',
        'Test Arrow Negation 1',
        'Test Biarrow Negation 1',
        Argument('UaUba', title='hnh_axiom01'),
        Argument('UUaUbcUUabUac', title='hnh_axiom02'),
        Argument('UKaba', title='hnh_axiom03'),
        Argument('UKabb', title='hnh_axiom04'),
        Argument('UUabUUacUaKbc', title='hnh_axiom05'),
        Argument('UaAab', title='hnh_axiom06'),
        Argument('UbAab', title='hnh_axiom07'),
        Argument('UUacUUbcUAabc', title='hnh_axiom08'),
        Argument('BNNaa', title='hnh_axiom09'),
        Argument('NKKaNaNKaNa', title='hnh_axiom17'),
        Argument('NKUabNUab', title='hnh_axiom18'),
        Argument('UNKaNaUUbaUNaNb', title='hnh_axiom19'),
        Argument('BKNaNbNAab', title='hnh_axiom20'),
        Argument('BANaNbANKabKKaNaKbNb', title='hnh_axiom21'),
        Argument('UKNKaNaNaUab', title='hnh_axiom22'),
        Argument('UKaKNKbNbNbNUab', title='hnh_axiom23'),
    ),
    invalid = (
        'Biconditional Elimination 2',
        'Biconditional Introduction 2',
        'Biconditional Introduction 3',
        'Conditional Contraposition 1',
        'Conditional Contraposition 2',
        'Conditional Modus Tollens',
        'Conditional Pseudo Contraposition',
        'DeMorgan 4',
        'DeMorgan 5',
        'Disjunctive Syllogism 1',
        'Disjunctive Syllogism 2',
        'Existential Syllogism',
        'Explosion',
        'Identity Indiscernability 1',
        'Identity Indiscernability 2',
        'Law of Non-contradiction',
        'Material Biconditional Elimination 1',
        'Material Biconditional Elimination 2',
        'Material Biconditional Elimination 3',
        'Material Modus Ponens',
        'Material Modus Tollens',
        'Quantifier Interdefinability 3',
        'Self Identity 1',
        'Self Identity 2',
        'Syllogism',
        'Test Contradiction Arrow 1',
        'Universal Predicate Syllogism',
    ))

L('P3',
    valid = (
        'Addition',
        'Asserted Addition',
        'Assertion Elimination 1',
        'Assertion Elimination 2',
        'Biconditional Elimination 1',
        'Biconditional Elimination 2',
        'Biconditional Introduction 3',
        'Conditional Contraction',
        'Conditional Modus Ponens',
        'Conditional Modus Tollens',
        'Conjunction Commutativity',
        'DeMorgan 6',
        'DeMorgan 8',
        'Disjunction Commutativity',
        'Disjunctive Syllogism 2',
        'Disjunctive Syllogism 1',
        'Explosion',
        'Material Biconditional Elimination 1',
        'Material Biconditional Elimination 2',
        'Material Contraction',
        'Material Modus Ponens',
        'Material Modus Tollens',
        'Test Arrow Negation 1',
        'Test Biarrow Negation 1',
        'Test Contradiction Arrow 1',
    ),
    invalid = (
        'Biconditional Elimination 3',
        'Biconditional Identity',
        'Biconditional Introduction 1',
        'Biconditional Introduction 2',
        'Conditional Contraposition 1',
        'Conditional Contraposition 2',
        'Conditional Double Negation',
        'Conditional Identity',
        'Conditional Law of Excluded Middle',
        'Conditional Pseudo Contraction',
        'Conditional Pseudo Contraposition',
        'Conjunction Elimination',
        'Conjunction Idempotence 1',
        'Conjunction Idempotence 2',
        'Conjunction Introduction',
        'Conjunction Pseudo Commutativity',
        'DeMorgan 1',
        'DeMorgan 2',
        'DeMorgan 3',
        'DeMorgan 4',
        'DeMorgan 5',
        'DeMorgan 7',
        'Disjunction Pseudo Commutativity',
        'Existential from Universal',
        'Existential Syllogism',
        'Existential to Conditional Identity',
        'Existential to Material Identity',
        'Identity Indiscernability 1',
        'Identity Indiscernability 2',
        'KFDE Distribution Inference 1',
        'Law of Excluded Middle',
        'Material Biconditional Elimination 3',
        'Material Biconditional Identity',
        'Material Biconditional Introduction 1',
        'Material Contraposition 1',
        'Material Contraposition 2',
        'Material Identity',
        'Material Pseudo Contraction',
        'Material Pseudo Contraposition',
        'Modal Transformation 1',
        'Modal Transformation 2',
        'Modal Transformation 3',
        'Modal Transformation 4',
        'Necessity Distribution 1',
        'Necessity Distribution 2',
        'Necessity Elimination',
        'NP Collapse 1',
        'NP Conditional Modus Ponens',
        'Possibility Addition',
        'Quantifier Interdefinability 1',
        'Quantifier Interdefinability 2',
        'Quantifier Interdefinability 3',
        'Quantifier Interdefinability 4',
        'Reflexive Inference 1',
        'S4 Conditional Inference 1',
        'S4 Conditional Inference 2',
        'S4 Material Inference 1',
        'S4 Material Inference 2',
        'S5 Conditional Inference 1',
        'S5 Inference 1',
        'S5 Material Inference 1',
        'Self Identity 1',
        'Self Identity 2',
        'Serial Inference 1',
        'Serial Inference 2',
        'Syllogism',
        'Universal Predicate Syllogism',
    ))

# ---------------------------------------------------------------------------

L('FDE',
    valid = (
        'Asserted Addition',
        'Conditional Contraposition 1',
        'Conditional Contraposition 2',
        'Conjunction Commutativity',
        'Conjunction Elimination',
        'Conjunction Idempotence 1',
        'Conjunction Idempotence 2',
        'Conjunction Introduction',
        'Disjunction Commutativity',
        'Existential from Universal',
        'Material Biconditional Introduction 1',
        'Material Contraposition 1',
        'Material Contraposition 2',
        'Quantifier Interdefinability 1',
        'Quantifier Interdefinability 2',
        'Quantifier Interdefinability 3',
        'Addition',
        'Assertion Elimination 1',
        'Assertion Elimination 2',
        'Biconditional Introduction 1',
        'Biconditional Introduction 2',
        'Biconditional Introduction 3',
        'Conditional Contraction',
        'DeMorgan 1',
        'DeMorgan 2',
        'DeMorgan 3',
        'DeMorgan 4',
        'DeMorgan 5',
        'DeMorgan 6',
        'DeMorgan 7',
        'DeMorgan 8',
        'Material Contraction',
        'Quantifier Interdefinability 4',
        'Test Contradiction Arrow 1',
    ),
    invalid = (

    ))

L('KFDE',
    valid = (
        'KFDE Distribution Inference 1',
        'Modal Transformation 1',
        'Modal Transformation 2',
        'Modal Transformation 3',
        'Modal Transformation 4',
        'Necessity Distribution 2',
    ),
    invalid = (

    ))

L('TFDE',
    valid = (
        'Necessity Elimination',
        'NP Collapse 1',
        'Possibility Addition',
        'Serial Inference 2',
    ),
    invalid = (
    ))

L('S4FDE',
    valid = (
    ),
    invalid = (
    ))

L('S5FDE',
    valid = (
        'S5 Inference 1',
    ),
    invalid = (
        'NP Conditional Modus Ponens',
    ))

# -----------------

L('K3',
    valid = (
        'Biconditional Elimination 1',
        'Biconditional Elimination 2',
        'Biconditional Elimination 3',
        'Conditional Modus Ponens',
        'Conditional Modus Tollens',
        'Disjunctive Syllogism 2',
        'Disjunctive Syllogism 1',
        'Existential Syllogism',
        'Explosion',
        'Law of Non-contradiction',
        'Material Biconditional Elimination 1',
        'Material Biconditional Elimination 2',
        'Material Biconditional Elimination 3',
        'Material Modus Ponens',
        'Material Modus Tollens',
        'Syllogism',
        'Universal Predicate Syllogism',
        'Test Arrow Negation 1',
        'Test Biarrow Negation 1',
    ),
    invalid = (

    ))

L('KK3',
    valid = (
        'NP Conditional Modus Ponens',
    ),
    invalid = (
    ))

L('TK3',
    valid = (
    ),
    invalid = (
    ))

L('S4K3',
    valid = (
        'S4 Conditional Inference 2',
        'S4 Material Inference 2',
    ),
    invalid = (
    ))

L('S5K3',
    valid = (
    ),
    invalid = (
        'Biconditional Identity',
        'Conditional Double Negation',
        'Conditional Identity',
        'Conditional Law of Excluded Middle',
        'Conditional Pseudo Contraction',
        'Conditional Pseudo Contraposition',
        'Conjunction Pseudo Commutativity',
        'Disjunction Pseudo Commutativity',
        'Existential to Conditional Identity',
        'Existential to Material Identity',
        'Identity Indiscernability 1',
        'Identity Indiscernability 2',
        'Law of Excluded Middle',
        'Material Biconditional Identity',
        'Material Identity',
        'Material Pseudo Contraction',
        'Material Pseudo Contraposition',
        'Necessity Distribution 1',
        'Reflexive Inference 1',
        'S4 Conditional Inference 1',
        'S4 Material Inference 1',
        'S5 Conditional Inference 1',
        'S5 Material Inference 1',
        'Self Identity 1',
        'Self Identity 2',
        'Serial Inference 1',
    ))

# -----------------

L('LP',
    valid = (
        'Biconditional Identity',
        'Conditional Double Negation',
        'Conditional Identity',
        'Conditional Law of Excluded Middle',
        'Conditional Pseudo Contraction',
        'Conditional Pseudo Contraposition',
        'Conjunction Pseudo Commutativity',
        'Disjunction Pseudo Commutativity',
        'Existential to Conditional Identity',
        'Existential to Material Identity',
        'Law of Excluded Middle',
        'Material Biconditional Identity',
        'Material Identity',
        'Material Pseudo Contraction',
        'Material Pseudo Contraposition',
    ),
    invalid = (

    ))

L('KLP',
    valid = (
        'Necessity Distribution 1',
    ),
    invalid = (
    ))

L('TLP',
    valid = (
        'Reflexive Inference 1',
        'Serial Inference 1',
    ),
    invalid = (
    ))

L('S4LP',
    valid = (
        'S4 Conditional Inference 1',
        'S4 Material Inference 1',
    ),
    invalid = (
    ))

L('S5LP',
    valid = (
        'S5 Conditional Inference 1',
        'S5 Material Inference 1',
    ),
    invalid = (
        'Biconditional Elimination 1',
        'Biconditional Elimination 2',
        'Biconditional Elimination 3',
        'Conditional Modus Ponens',
        'Conditional Modus Tollens',
        'Disjunctive Syllogism 2',
        'Disjunctive Syllogism 1',
        'Existential Syllogism',
        'Explosion',
        'Identity Indiscernability 1',
        'Identity Indiscernability 2',
        'Law of Non-contradiction',
        'Material Biconditional Elimination 1',
        'Material Biconditional Elimination 2',
        'Material Biconditional Elimination 3',
        'Material Modus Ponens',
        'Material Modus Tollens',
        'NP Conditional Modus Ponens',
        'S4 Conditional Inference 2',
        'S4 Material Inference 2',
        'Self Identity 1',
        'Self Identity 2',
        'Syllogism',
        'Test Arrow Negation 1',
        'Test Biarrow Negation 1',
        'Universal Predicate Syllogism',
    ))

# -----------------

L('L3',
    valid = (
        'Addition',
        'Asserted Addition',
        'Assertion Elimination 1',
        'Assertion Elimination 2',
        'Biconditional Elimination 1',
        'Biconditional Elimination 2',
        'Biconditional Elimination 3',
        'Biconditional Identity',
        'Biconditional Introduction 1',
        'Biconditional Introduction 2',
        'Biconditional Introduction 3',
        'Conditional Contraposition 1',
        'Conditional Contraposition 2',
        'Conditional Double Negation',
        'Conditional Identity',
        'Conditional Modus Ponens',
        'Conditional Modus Tollens',
        'Conditional Pseudo Contraposition',
        'Conjunction Commutativity',
        'Conjunction Elimination',
        'Conjunction Idempotence 1',
        'Conjunction Idempotence 2',
        'Conjunction Introduction',
        'Conjunction Pseudo Commutativity',
        'DeMorgan 1',
        'DeMorgan 2',
        'DeMorgan 3',
        'DeMorgan 4',
        'DeMorgan 5',
        'DeMorgan 6',
        'DeMorgan 7',
        'DeMorgan 8',
        'Disjunction Commutativity',
        'Disjunction Pseudo Commutativity',
        'Disjunctive Syllogism 1',
        'Disjunctive Syllogism 2',
        'Existential from Universal',
        'Existential Syllogism',
        'Existential to Conditional Identity',
        'Law of Non-contradiction',
        'Material Biconditional Elimination 1',
        'Material Biconditional Elimination 2',
        'Material Biconditional Elimination 3',
        'Material Biconditional Introduction 1',
        'Material Contraction',
        'Material Contraposition 1',
        'Material Contraposition 2',
        'Material Modus Ponens',
        'Material Modus Tollens',
        'Quantifier Interdefinability 1',
        'Quantifier Interdefinability 2',
        'Quantifier Interdefinability 3',
        'Quantifier Interdefinability 4',
        'Syllogism',
        'Test Arrow Negation 1',
        'Test Biarrow Negation 1',
        'Test Contradiction Arrow 1',
        'Universal Predicate Syllogism',
    ),
    invalid = (

    ))

L('KL3',
    valid = (
        'KFDE Distribution Inference 1',
        'Modal Transformation 1',
        'Modal Transformation 2',
        'Modal Transformation 3',
        'Modal Transformation 4',
        'NP Conditional Modus Ponens',
        'Necessity Distribution 1',
        'Necessity Distribution 2',
    ),
    invalid = ( 
    ))

L('TL3',
    valid = (
        'NP Collapse 1',
        'Necessity Elimination',
        'Possibility Addition',
        'Serial Inference 1',
        'Serial Inference 2',
    ),
    invalid = (
    ))

L('S4L3',
    valid = (
        'S4 Conditional Inference 1',
        'S4 Conditional Inference 2',
        'S4 Material Inference 2',
    ),
    invalid = (
    ))

L('S5L3',
    valid = (
        'S5 Conditional Inference 1',
        'S5 Inference 1',
    ),
    invalid = (
        'Conditional Contraction',
        'Conditional Law of Excluded Middle',
        'Conditional Pseudo Contraction',
        'Existential to Material Identity',
        'Identity Indiscernability 1',
        'Identity Indiscernability 2',
        'Law of Excluded Middle',
        'Material Biconditional Identity',
        'Material Identity',
        'Material Pseudo Contraction',
        'Material Pseudo Contraposition',
        'Reflexive Inference 1',
        'S4 Material Inference 1',
        'S5 Material Inference 1',
        'Self Identity 1',
        'Self Identity 2',
    ))

# -------------

L('RM3',
    valid = (
        'Addition',
        'Asserted Addition',
        'Assertion Elimination 1',
        'Assertion Elimination 2',
        'Biconditional Elimination 1',
        'Biconditional Elimination 2',
        'Biconditional Identity',
        'Biconditional Introduction 3',
        'Conditional Contraction',
        'Conditional Contraposition 1',
        'Conditional Contraposition 2',
        'Conditional Double Negation',
        'Conditional Identity',
        'Conditional Law of Excluded Middle',
        'Conditional Modus Ponens',
        'Conditional Modus Tollens',
        'Conditional Pseudo Contraction',
        'Conditional Pseudo Contraposition',
        'Conjunction Commutativity',
        'Conjunction Elimination',
        'Conjunction Idempotence 1',
        'Conjunction Idempotence 2',
        'Conjunction Introduction',
        'Conjunction Pseudo Commutativity',
        'DeMorgan 1',
        'DeMorgan 2',
        'DeMorgan 3',
        'DeMorgan 4',
        'DeMorgan 5',
        'DeMorgan 6',
        'DeMorgan 7',
        'DeMorgan 8',
        'Disjunction Commutativity',
        'Disjunction Pseudo Commutativity',
        'Existential from Universal',
        'Existential to Conditional Identity',
        'Existential to Material Identity',
        'Law of Excluded Middle',
        'Material Biconditional Identity',
        'Material Biconditional Introduction 1',
        'Material Contraction',
        'Material Contraposition 1',
        'Material Contraposition 2',
        'Material Identity',
        'Material Pseudo Contraction',
        'Material Pseudo Contraposition',
        'Quantifier Interdefinability 1',
        'Quantifier Interdefinability 2',
        'Quantifier Interdefinability 3',
        'Quantifier Interdefinability 4',
        'Test Arrow Negation 1',
        'Test Biarrow Negation 1',
        'Test Contradiction Arrow 1',
    ),
    invalid = (
    ))

L('KRM3',
    valid = (
        'KFDE Distribution Inference 1',
        'Modal Transformation 1',
        'Modal Transformation 2',
        'Modal Transformation 3',
        'Modal Transformation 4',
        'NP Conditional Modus Ponens',
        'Necessity Distribution 1',
        'Necessity Distribution 2',
    ),
    invalid = (
    ))

L('TRM3',
    valid = (
        'NP Collapse 1',
        'Necessity Elimination',
        'Possibility Addition',
        'Reflexive Inference 1',
        'Serial Inference 1',
        'Serial Inference 2',
    ),
    invalid = (

    ))
L('S4RM3',
    valid = (
        'S4 Conditional Inference 1',
        'S4 Conditional Inference 2',
        'S4 Material Inference 1',
    ),
    invalid = (

    ))
L('S5RM3',
    valid = (
        'S5 Conditional Inference 1',
        'S5 Inference 1',
        'S5 Material Inference 1',
    ),
    invalid = (
        'Biconditional Elimination 3',
        'Biconditional Introduction 1',
        'Biconditional Introduction 2',
        'Disjunctive Syllogism 2',
        'Disjunctive Syllogism 1',
        'Existential Syllogism',
        'Identity Indiscernability 1',
        'Identity Indiscernability 2',
        'Law of Non-contradiction',
        'Material Biconditional Elimination 1',
        'Material Biconditional Elimination 2',
        'Material Biconditional Elimination 3',
        'Material Modus Ponens',
        'Material Modus Tollens',
        'S4 Material Inference 2',
        'Self Identity 1',
        'Self Identity 2',
        'Syllogism',
        'Universal Predicate Syllogism',
    ))

# -------------



L('K3W',
    valid = (
        'Assertion Elimination 1',
        'Assertion Elimination 2',
        'Biconditional Elimination 1',
        'Biconditional Elimination 2',
        'Biconditional Elimination 3',
        'Biconditional Introduction 1',
        'Biconditional Introduction 2',
        'Biconditional Introduction 3',
        'Conditional Contraction',
        'Conditional Contraposition 1',
        'Conditional Contraposition 2',
        'Conditional Modus Ponens',
        'Conditional Modus Tollens',
        'Conjunction Commutativity',
        'Conjunction Elimination',
        'Conjunction Idempotence 1',
        'Conjunction Idempotence 2',
        'Conjunction Introduction',
        'DeMorgan 1',
        'DeMorgan 2',
        'DeMorgan 3',
        'DeMorgan 4',
        'DeMorgan 5',
        'DeMorgan 6',
        'DeMorgan 7',
        'DeMorgan 8',
        'Disjunction Commutativity',
        'Disjunctive Syllogism 2',
        'Disjunctive Syllogism 1',
        'Existential from Universal',
        'Existential Syllogism',
        'Law of Non-contradiction',
        'Material Biconditional Elimination 1',
        'Material Biconditional Elimination 2',
        'Material Biconditional Elimination 3',
        'Material Biconditional Introduction 1',
        'Material Contraction',
        'Material Contraposition 1',
        'Material Contraposition 2',
        'Material Modus Ponens',
        'Material Modus Tollens',
        'Quantifier Interdefinability 1',
        'Quantifier Interdefinability 2',
        'Quantifier Interdefinability 3',
        'Quantifier Interdefinability 4',
        'Syllogism',
        'Universal Predicate Syllogism',
        'Test Arrow Negation 1',
        'Test Biarrow Negation 1',
        'Test Contradiction Arrow 1',
    ),
    invalid = (
        Argument('ANAabNa:Na', title='b3e_prior_rule_defect_1'),
        Argument('AaTb:a'),
        Argument('AaTb:a'),
    ))

L('KK3W',
    valid = (
        'KFDE Distribution Inference 1',
        'Modal Transformation 1',
        'Modal Transformation 2',
        'Modal Transformation 3',
        'Modal Transformation 4',
        'NP Conditional Modus Ponens',
        'Necessity Distribution 2',
    ),
    invalid = (

    ))

L('TK3W',
    valid = (
        'Necessity Elimination',
        'NP Collapse 1',
        'Possibility Addition',
        'Serial Inference 2',
    ),
    invalid = (

    ))

L('S4K3W',
    valid = (
        'S4 Conditional Inference 2',
        'S4 Material Inference 2',
    ),
    invalid = (

    ))

L('S5K3W',
    valid = (
        'S5 Inference 1',
    ),
    invalid = (
        'Addition',
        'Asserted Addition',
        'Biconditional Identity',
        'Conditional Double Negation',
        'Conditional Identity',
        'Conditional Law of Excluded Middle',
        'Conditional Pseudo Contraction',
        'Conditional Pseudo Contraposition',
        'Conjunction Pseudo Commutativity',
        'Disjunction Pseudo Commutativity',
        'Existential to Conditional Identity',
        'Existential to Material Identity',
        'Identity Indiscernability 1',
        'Identity Indiscernability 2',
        'Law of Excluded Middle',
        'Material Biconditional Identity',
        'Material Identity',
        'Material Pseudo Contraction',
        'Material Pseudo Contraposition',
        'Necessity Distribution 1',
        'Reflexive Inference 1',
        'S4 Conditional Inference 1',
        'S4 Material Inference 1',
        'S5 Conditional Inference 1',
        'S5 Material Inference 1',
        'Self Identity 1',
        'Self Identity 2',
        'Serial Inference 1',
    ))

# -------------

L('B3E',
    valid = (
        'Asserted Addition',
        'Assertion Elimination 1',
        'Biconditional Elimination 1',
        'Biconditional Elimination 3',
        'Biconditional Identity',
        'Biconditional Introduction 1',
        'Biconditional Introduction 2',
        'Biconditional Introduction 3',
        'Conditional Contraction',
        'Conditional Double Negation',
        'Conditional Identity',
        'Conditional Law of Excluded Middle',
        'Conditional Modus Ponens',
        'Conditional Pseudo Contraction',
        'Conditional Pseudo Contraposition',
        'Conjunction Commutativity',
        'Conjunction Elimination',
        'Conjunction Idempotence 1',
        'Conjunction Idempotence 2',
        'Conjunction Introduction',
        'Conjunction Pseudo Commutativity',
        'DeMorgan 1',
        'DeMorgan 2',
        'DeMorgan 3',
        'DeMorgan 4',
        'DeMorgan 5',
        'DeMorgan 6',
        'DeMorgan 7',
        'DeMorgan 8',
        'Disjunction Commutativity',
        'Disjunction Pseudo Commutativity',
        'Disjunctive Syllogism 1',
        'Disjunctive Syllogism 2',
        'Existential from Universal',
        'Existential Syllogism',
        'Existential to Conditional Identity',
        'Explosion',
        'Material Biconditional Elimination 1',
        'Material Biconditional Elimination 2',
        'Material Biconditional Elimination 3',
        'Material Biconditional Introduction 1',
        'Material Contraction',
        'Material Contraposition 1',
        'Material Contraposition 2',
        'Material Modus Ponens',
        'Material Modus Tollens',
        'Quantifier Interdefinability 1',
        'Quantifier Interdefinability 2',
        'Quantifier Interdefinability 3',
        'Quantifier Interdefinability 4',
        'Syllogism',
        'Test Arrow Negation 1',
        'Test Biarrow Negation 1',
        'Test Contradiction Arrow 1',
        'Universal Predicate Syllogism',
        Argument('AANaTbNa:Na', title='b3e_prior_rule_defect_2'),
    ),
    invalid = (

    ))

L('KB3E',
    valid = (
        'KFDE Distribution Inference 1',
        'Modal Transformation 1',
        'Modal Transformation 2',
        'Modal Transformation 3',
        'Modal Transformation 4',
        'NP Conditional Modus Ponens',
        'Necessity Distribution 1',
        'Necessity Distribution 2',
    ),
    invalid = (

    ))

L('TB3E',
    valid = (
        'NP Collapse 1',
        'Necessity Elimination',
        'Possibility Addition',
        'Serial Inference 1',
        'Serial Inference 2',
    ),
    invalid = (

    ))

L('S4B3E',
    valid = (
        'S4 Conditional Inference 1',
        'S4 Conditional Inference 2',
        'S4 Material Inference 2',
    ),
    invalid = (

    ))

L('S5B3E',
    valid = (
        'S5 Conditional Inference 1',
        'S5 Inference 1',
    ),
    invalid = (
        'Addition',
        'Assertion Elimination 2',
        'Biconditional Elimination 2',
        'Conditional Contraposition 1',
        'Conditional Contraposition 2',
        'Conditional Modus Tollens',
        'Existential to Material Identity',
        'Identity Indiscernability 1',
        'Identity Indiscernability 2',
        'Law of Excluded Middle',
        'Material Biconditional Identity',
        'Material Identity',
        'Material Pseudo Contraction',
        'Material Pseudo Contraposition',
        'Reflexive Inference 1',
        'S4 Material Inference 1',
        'S5 Material Inference 1',
        'Self Identity 1',
        'Self Identity 2',
        Argument('ANAabNa:Na', title='b3e_prior_rule_defect_1'),
    ))

# -------------

L('G3',
    valid = (
        'Addition',
        'Asserted Addition',
        'Assertion Elimination 1',
        'Assertion Elimination 2',
        'Biconditional Elimination 1',
        'Biconditional Elimination 2',
        'Biconditional Elimination 3',
        'Biconditional Identity',
        'Biconditional Introduction 1',
        'Biconditional Introduction 2',
        'Biconditional Introduction 3',
        'Conditional Contraction',
        'Conditional Contraposition 1',
        'Conditional Identity',
        'Conditional Modus Ponens',
        'Conditional Modus Tollens',
        'Conditional Pseudo Contraction',
        'Conjunction Commutativity',
        'Conjunction Elimination',
        'Conjunction Idempotence 1',
        'Conjunction Idempotence 2',
        'Conjunction Introduction',
        'Conjunction Pseudo Commutativity',
        'DeMorgan 1',
        'DeMorgan 2',
        'DeMorgan 3',
        'DeMorgan 4',
        'DeMorgan 5',
        'DeMorgan 6',
        'Disjunction Commutativity',
        'Disjunction Pseudo Commutativity',
        'Disjunctive Syllogism 1',
        'Disjunctive Syllogism 2',
        'Existential from Universal',
        'Existential Syllogism',
        'Existential to Conditional Identity',
        'Explosion',
        'Material Biconditional Elimination 1',
        'Material Biconditional Elimination 2',
        'Material Biconditional Elimination 3',
        'Material Biconditional Introduction 1',
        'Material Contraction',
        'Material Contraposition 1',
        'Material Modus Ponens',
        'Material Modus Tollens',
        'Quantifier Interdefinability 1',
        'Quantifier Interdefinability 2',
        'Quantifier Interdefinability 3',
        'Quantifier Interdefinability 4',
        'Syllogism',
        'Test Arrow Negation 1',
        'Test Biarrow Negation 1',
        'Test Contradiction Arrow 1',
        'Universal Predicate Syllogism',
        Argument('AUabUba', title='g3_rescher_p45_3'),
        Argument('UUNNaaAaNa', title='g3_rescher_p45_4'),
        Argument('KUabUba:Bab', title='g3_rescher_other_1'),
        Argument('Bab:KUabUba', title='g3_rescher_other_2'),
        Argument('NBab:ANUabNUba', title='g3_rescher_other_3'),
        Argument('ANUabNUba:NBab', title='g3_rescher_other_4'),
    ),
    invalid = (
    ))

L('KG3',
    valid = (
        'KFDE Distribution Inference 1',
        'Modal Transformation 1',
        'Modal Transformation 3',
        'Modal Transformation 4',
        'NP Conditional Modus Ponens',
        'Necessity Distribution 1',
        'Necessity Distribution 2',
    ),
    invalid = (

    ))

L('TG3',
    valid = (
        'NP Collapse 1',
        'Necessity Elimination',
        'Possibility Addition',
        'Serial Inference 1',
        'Serial Inference 2',
    ),
    invalid = (

    ))

L('S4G3',
    valid = (
        'S4 Conditional Inference 1',
        'S4 Conditional Inference 2',
        'S4 Material Inference 2',
    ),
    invalid = (

    ))

L('S5G3',
    valid = (
        'S5 Conditional Inference 1',
        'S5 Inference 1',
    ),
    invalid = (
        'Conditional Contraposition 2',
        'Conditional Double Negation',
        'Conditional Law of Excluded Middle',
        'Conditional Pseudo Contraposition',
        'DeMorgan 7',
        'DeMorgan 8',
        'Existential to Material Identity',
        'Identity Indiscernability 1',
        'Identity Indiscernability 2',
        'Law of Excluded Middle',
        'Material Biconditional Identity',
        'Material Contraposition 2',
        'Material Identity',
        'Material Pseudo Contraction',
        'Material Pseudo Contraposition',
        'Modal Transformation 2',
        'Reflexive Inference 1',
        'S4 Material Inference 1',
        'S5 Material Inference 1',
        'Self Identity 1',
        'Self Identity 2',
        Argument('UNNaa', title='g3_rescher_p45_1'),
        Argument('UUNaNbUba', title='g3_rescher_p45_2'),
    ))

# --------------

L('GO',
    valid = (
        'Addition',
        'Asserted Addition',
        'Assertion Elimination 1',
        'Biconditional Elimination 1',
        'Biconditional Elimination 2',
        'Biconditional Identity',
        'Biconditional Introduction 1',
        'Biconditional Introduction 2',
        'Biconditional Introduction 3',
        'Conditional Contraction',
        'Conditional Contraposition 1',
        'Conditional Contraposition 2',
        'Conditional Double Negation',
        'Conditional Identity',
        'Conditional Law of Excluded Middle',
        'Conditional Modus Ponens',
        'Conditional Modus Tollens',
        'Conditional Pseudo Contraction',
        'Conditional Pseudo Contraposition',
        'Conjunction Commutativity',
        'Conjunction Elimination',
        'Conjunction Idempotence 1',
        'Conjunction Idempotence 2',
        'Conjunction Introduction',
        'Conjunction Pseudo Commutativity',
        'DeMorgan 3',
        'DeMorgan 4',
        'DeMorgan 5',
        'DeMorgan 6',
        'Disjunction Commutativity',
        'Disjunction Pseudo Commutativity',
        'Disjunctive Syllogism 1',
        'Disjunctive Syllogism 2',
        'Existential from Universal',
        'Existential Syllogism',
        'Existential to Conditional Identity',
        'Law of Non-contradiction',
        'Material Biconditional Elimination 1',
        'Material Biconditional Elimination 2',
        'Material Biconditional Introduction 1',
        'Material Contraction',
        'Material Contraposition 1',
        'Material Contraposition 2',
        'Material Modus Ponens',
        'Material Modus Tollens',
        'Material Pseudo Contraction',
        'Material Pseudo Contraposition',
        'Quantifier Interdefinability 1',
        'Quantifier Interdefinability 3',
        'Syllogism',
        'Test Arrow Negation 1',
        'Test Biarrow Negation 1',
        'Test Contradiction Arrow 1',
        'Universal Predicate Syllogism',
        Argument('AANaTbNa:Na', title='b3e_prior_rule_defect_2'),
    ),
    invalid = (
    ))

L('S4GO',
    valid = (
        'Modal Transformation 1',
        'Modal Transformation 4',
        'Necessity Distribution 1',
        'Necessity Distribution 2',
        'Necessity Elimination',
        'NP Collapse 1',
        'NP Conditional Modus Ponens',
        'Possibility Addition',
        'Reflexive Inference 1',
        'S4 Conditional Inference 1',
        'S4 Conditional Inference 2',
        'S4 Material Inference 1',
        'S4 Material Inference 2',
        'Serial Inference 1',
        'Serial Inference 2',
        Argument('La:LLa', title='diss_72'),
        Argument('LLa:La', title='diss_73'),
        Argument('ULMaMa', title='diss_75'),
    ),
    invalid = (
        'Assertion Elimination 2',
        'Biconditional Elimination 3',
        'DeMorgan 1',
        'DeMorgan 2',
        'DeMorgan 7',
        'DeMorgan 8',
        'Existential to Material Identity',
        'Identity Indiscernability 1',
        'Identity Indiscernability 2',
        'KFDE Distribution Inference 1',
        'Law of Excluded Middle',
        'Material Biconditional Elimination 3',
        'Material Biconditional Identity',
        'Material Identity',
        'Modal Transformation 2',
        'Modal Transformation 3',
        'Quantifier Interdefinability 2',
        'Quantifier Interdefinability 4',
        'Self Identity 1',
        'Self Identity 2',
        Argument('KaNa:NAaNa', title='diss_06'),
        Argument('AKaaKNaNa', title='diss_07'),
        Argument('AAaaANaNa', title='diss_08'),
        Argument('LMa:Ma', title='diss_81'),
    ))

del(L)

validities = MapProxy(validities)
invalidities = MapProxy(invalidities)

class ArgSet(qset[Argument]):

    def _hook_cast(self, value):
        return arguments.get(value) or Argument(value)

    def _default_sort_key(self, value):
        return value.title or value.argstr()

def caching(wrapped: _F) -> _F:
    cache = {}
    @wraps(wrapped)
    def wrapper(logic):
        logic = registry(logic)
        try:
            return cache[logic]
        except KeyError:
            return cache.setdefault(logic, wrapped(logic))
    return wrapper

get_extends = caching(registry.get_extends)
get_extensions = caching(registry.get_extensions)

def known_getter(base: Mapping[str, Collection[str|Argument]], getter: Callable[[Any], Iterable[LogicType]]):
    def wrapper(logic: LogicType) -> qsetf[Argument]:
        result = ArgSet()
        result |= base[logic.Meta.name]
        result |= base['*']
        for other in getter(logic):
            result |= base[other.Meta.name]
        result.sort()
        return qsetf(result)
    return caching(wrapper)

get_validities = known_getter(validities, get_extends)
get_invalidities = known_getter(invalidities, get_extensions)

def get_known(logic):
    return get_invalidities(logic), get_validities(logic)

def find_missing(logic):
    logic = registry(logic)
    valids, invalids = get_known(logic)
    exists = valids | invalids
    missing = set(arguments.values()) - exists
    results = defaultdict(set)
    for arg in missing:
        results[Tableau(logic, arg).build().valid].add(arg.title or arg.argstr())
    return {key: sorted(value) for key, value in results.items()}

def find_missing_all():
    logics = LogicSet(registry.all())
    logics.sort()
    for logic in logics:
        missing = find_missing(logic)
        if missing:
            yield logic, missing

del(caching, known_getter)

if __name__ == '__main__':
    import sys
    from textwrap import indent
    args = sys.argv[1:]
    if args:
        it = ((logic, find_missing(logic)) for logic in map(registry, args))
    else:
        it = find_missing_all()
    for logic, results in it:
        print(logic.Meta.name)
        for result, titles in results.items():
            print(indent('valid' if result else 'invalid', '    '))
            for title in titles:
                print(indent(repr(title) + ',', '        '))

