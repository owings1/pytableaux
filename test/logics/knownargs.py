from __future__ import annotations

from collections import defaultdict
from types import MappingProxyType as MapProxy
from typing import Any, Callable, Collection, Mapping, TypeVar

from pytableaux import examples
from pytableaux.lang import Argument, Parser
from pytableaux.logics import LogicType, registry
from pytableaux.proof import Tableau
from pytableaux.tools import qset, qsetf, wraps

_F = TypeVar('_F', bound=Callable)

arg = Parser('polish', examples.preds).argument

validities = {}
invalidities = {}

def L(name, valid=(), invalid=()):
    validities[name] = valid
    invalidities[name] = invalid

L('*',
    valid = (
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
        'Disjunctive Syllogism 2',
        'Disjunctive Syllogism',
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
        'Simplification',
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
    ))

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
        arg('b', ('VxKFxKaNa',), title='regression_efq_univeral_with_contradiction_no_constants'),
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

# ---------------------------------------------------------------------------

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
        arg('KMNbc', ('LCaMNb', 'Ma'), title='nested_diamond_within_box1'),
    ))
# ---------------------------------------------------------------------------

L('FDE',
    valid = (
        'Asserted Addition',
        'Conditional Contraposition 1',
        'Conditional Contraposition 2',
        'Conjunction Commutativity',
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
        'Simplification',
    ),
    invalid = (

    ))

L('K3',
    valid = (
        'Biconditional Elimination 1',
        'Biconditional Elimination 2',
        'Biconditional Elimination 3',
        'Conditional Modus Ponens',
        'Conditional Modus Tollens',
        'Disjunctive Syllogism 2',
        'Disjunctive Syllogism',
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
    ),
    invalid = (

    ))

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
        'Disjunctive Syllogism',
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
        'Self Identity 1',
        'Self Identity 2',
    ))

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
        'Disjunctive Syllogism',
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
    ),
    invalid = (
        
    ))

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
        'Disjunctive Syllogism 2',
        'Disjunctive Syllogism',
        'Existential from Universal',
        'Existential Syllogism',
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
        'Universal Predicate Syllogism',
    ),
    invalid = (
        'Addition',
        'Assertion Elimination 2',
        'Biconditional Elimination 2',
        'Conditional Contraposition 1',
        'Conditional Contraposition 2',
        'Conditional Modus Tollens',
        'Identity Indiscernability 1',
        'Identity Indiscernability 2',
        'Law of Excluded Middle',
        'Material Biconditional Identity',
        'Material Identity',
        'Material Pseudo Contraction',
        'Material Pseudo Contraposition',
        'Self Identity 1',
        'Self Identity 2',
    ))

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
        'Conjunction Introduction',
        'Conjunction Pseudo Commutativity',
        'DeMorgan 3',
        'DeMorgan 4',
        'DeMorgan 5',
        'DeMorgan 6',
        'Disjunction Commutativity',
        'Disjunction Pseudo Commutativity',
        'Disjunctive Syllogism 2',
        'Disjunctive Syllogism',
        'Existential from Universal',
        'Existential Syllogism',
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
        'Universal Predicate Syllogism',
    ),
    invalid = (        
        'Assertion Elimination 2',
        'Biconditional Elimination 3',
        'DeMorgan 1',
        'DeMorgan 2',
        'DeMorgan 7',
        'DeMorgan 8',
        'Identity Indiscernability 1',
        'Identity Indiscernability 2',
        'Law of Excluded Middle',
        'Material Biconditional Elimination 3',
        'Material Biconditional Identity',
        'Material Identity',
        'Quantifier Interdefinability 2',
        'Quantifier Interdefinability 4',
        'Self Identity 1',
        'Self Identity 2',
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
        'Conditional Modus Ponens',
        'Conditional Pseudo Contraction',
        'Conjunction Commutativity',
        'Conjunction Elimination',
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
        'Disjunctive Syllogism 2',
        'Disjunctive Syllogism',
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
        arg('UaUba', title='hmh_axiom01'),
        arg('UUaUbcUUabUac', title='hmh_axiom02'),
        arg('UKaba', title='hmh_axiom03'),
        arg('UKabb', title='hmh_axiom04'),
        arg('UUabUUacUaKbc', title='hmh_axiom05'),
        arg('UaAab', title='hmh_axiom06'),
        arg('UbAab', title='hmh_axiom07'),
        arg('UUacUUbcUAabc', title='hmh_axiom08'),
        arg('BNNaa', title='hmh_axiom09'),
        arg('AAaNaNAaNa', title='hmh_axiom10'),
        arg('AUabNUab', title='hmh_axiom11'),
        arg('UAaNaUUabUNbNa', title='hmh_axiom12'),
        arg('BNKabANaNb', title='hmh_axiom13'),
        arg('BNAabAKNaNbKNAaNaNAbNb', title='hmh_axiom14'),
        arg('UANaNAaNaUab', title='hmh_axiom15'),
        arg('UKaANbNAbNbNUab', title='hmh_axiom16'),
        arg('BNAaNaNANaNNa', title='ifn'),
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
        'Existential from Universal',
        'Existential Syllogism',
        'Identity Indiscernability 1',
        'Identity Indiscernability 2',
        'Law of Excluded Middle',
        'Material Biconditional Identity',
        'Material Identity',
        'Material Pseudo Contraction',
        'Material Pseudo Contraposition',
        'Quantifier Interdefinability 1',
        'Quantifier Interdefinability 2',
        'Quantifier Interdefinability 3',
        'Quantifier Interdefinability 4',
        'Self Identity 1',
        'Self Identity 2',
        'Syllogism',
        'Universal Predicate Syllogism',
        arg('UNbNa', ('NAaNa', 'Uab'), title='p_from_article'),
    ))

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
        'Disjunctive Syllogism 2',
        'Disjunctive Syllogism',
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
        'Simplification',
        'Syllogism',
        'Universal Predicate Syllogism',
    ),
    invalid = (

    ))

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
        'Disjunctive Syllogism 2',
        'Disjunctive Syllogism',
        'Existential from Universal',
        'Existential Syllogism',
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
        'Universal Predicate Syllogism',
    ),
    invalid = (
        'Conditional Contraposition 2',
        'Conditional Double Negation',
        'Conditional Law of Excluded Middle',
        'Conditional Pseudo Contraposition',
        'DeMorgan 7',
        'DeMorgan 8',
        'Identity Indiscernability 1',
        'Identity Indiscernability 2',
        'Law of Excluded Middle',
        'Material Biconditional Identity',
        'Material Contraposition 2',
        'Material Identity',
        'Material Pseudo Contraction',
        'Material Pseudo Contraposition',
        'Self Identity 1',
        'Self Identity 2',
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
        'Law of Excluded Middle',
        'Material Biconditional Identity',
        'Material Identity',
        'Material Pseudo Contraction',
        'Material Pseudo Contraposition',
    ),
    invalid = (

    ))

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
        'Law of Excluded Middle',
        'Material Biconditional Identity',
        'Material Biconditional Introduction 1',
        'Material Contraction',
        'Material Contraposition 1',
        'Material Contraposition 2',
        'Material Identity',
        'Material Pseudo Contraction',
        'Material Pseudo Contraposition',
        arg('UaUba', title='hnh_axiom01'),
        arg('UUaUbcUUabUac', title='hnh_axiom02'),
        arg('UKaba', title='hnh_axiom03'),
        arg('UKabb', title='hnh_axiom04'),
        arg('UUabUUacUaKbc', title='hnh_axiom05'),
        arg('UaAab', title='hnh_axiom06'),
        arg('UbAab', title='hnh_axiom07'),
        arg('UUacUUbcUAabc', title='hnh_axiom08'),
        arg('BNNaa', title='hnh_axiom09'),
        arg('NKKaNaNKaNa', title='hnh_axiom17'),
        arg('NKUabNUab', title='hnh_axiom18'),
        arg('UNKaNaUUbaUNaNb', title='hnh_axiom19'),
        arg('BKNaNbNAab', title='hnh_axiom20'),
        arg('BANaNbANKabKKaNaKbNb', title='hnh_axiom21'),
        arg('UKNKaNaNaUab', title='hnh_axiom22'),
        arg('UKaKNKbNbNbNUab', title='hnh_axiom23'),
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
        'Disjunctive Syllogism 2',
        'Disjunctive Syllogism',
        'Existential from Universal',
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
        'Quantifier Interdefinability 1',
        'Quantifier Interdefinability 2',
        'Quantifier Interdefinability 3',
        'Quantifier Interdefinability 4',
        'Self Identity 1',
        'Self Identity 2',
        'Syllogism',
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
        'Disjunctive Syllogism',
        'Explosion',
        'Material Biconditional Elimination 1',
        'Material Biconditional Elimination 2',
        'Material Contraction',
        'Material Modus Ponens',
        'Material Modus Tollens',
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
        'Simplification',
    ),
    invalid = (
    ))

# ---------------------------------------------------------------------------

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
        'Disjunctive Syllogism',
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
        'Universal Predicate Syllogism',
    ))

# -----------------

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
        'Biconditional Elimination 3',
        'Biconditional Introduction 1',
        'Biconditional Introduction 2',
        'Disjunctive Syllogism 2',
        'Disjunctive Syllogism',
        'Existential Syllogism',
        'Identity Indiscernability 1',
        'Identity Indiscernability 2',
        'Law of Non-contradiction',
        'Material Biconditional Elimination 1',
        'Material Biconditional Elimination 2',
        'Material Biconditional Elimination 3',
        'Material Modus Ponens',
        'Material Modus Tollens',
        'Self Identity 1',
        'Self Identity 2',
        'Syllogism',
        'Universal Predicate Syllogism',
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
        'Conditional Contraction',
        'Conditional Law of Excluded Middle',
        'Conditional Pseudo Contraction',
        'Identity Indiscernability 1',
        'Identity Indiscernability 2',
        'Law of Excluded Middle',
        'Material Biconditional Identity',
        'Material Identity',
        'Material Pseudo Contraction',
        'Material Pseudo Contraposition',
        'Self Identity 1',
        'Self Identity 2',        
    ))

class ArgSet(qset[Argument]):

    _hook_cast = staticmethod(examples.argument)

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

@caching
def get_extends(logic) -> qsetf[LogicType]:
    return registry.get_extends(logic)

@caching
def get_extensions(logic) -> qsetf[LogicType]:
    return registry.get_extensions(logic)

def known_getter(base: Mapping[str, Collection[str|Argument]]):
    if base is validities:
        getter = get_extends
    elif base is invalidities:
        getter = get_extensions
    else:
        raise ValueError
    def decorator(wrapped):
        @caching
        @wraps(wrapped)
        def wrapper(logic: LogicType) -> qsetf[Argument]:
            result = ArgSet()
            result |= base[logic.Meta.name]
            result |= base['*']
            for other in getter(logic):
                result |= base[other.Meta.name]
            result.sort()
            return qsetf(result)
        return wrapper
    return decorator

@known_getter(validities)
def get_validities(logic): ...

@known_getter(invalidities)
def get_invalidities(logic): ...

def get_known(logic):
    return get_invalidities(logic), get_validities(logic)

def find_missing(logic):
    logic = registry(logic)
    exists = get_invalidities(logic) | get_validities(logic)
    missing = set(examples.arguments()) - exists
    results = defaultdict(set)
    for arg in missing:
        results[Tableau(logic, arg).build().valid].add(arg.title)
    return {key: sorted(value) for key, value in results.items()}

def find_missing_all():
    registry.import_all()
    for name in sorted(registry):
        missing = find_missing(name)
        if missing:
            yield name, find_missing(name)

validities = MapProxy(validities)
invalidities = MapProxy(invalidities)

del(caching, known_getter, L)