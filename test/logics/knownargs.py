from pytableaux.lang import Parser
from pytableaux.tools import qsetf
from pytableaux import examples
arg = Parser('polish', examples.preds).argument

validities = {}

validities[...] = qsetf([
    'Modal Platitude 1',
    'Modal Platitude 2',
    'Modal Platitude 3',
])

validities['FDE'] = validities[...] | [
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
]

validities['K3'] = validities['FDE'] | [
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
]

validities['LP'] = validities['FDE'] | [
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
]

validities['RM3'] = validities[...] | [
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
]

validities['L3'] = validities[...] | [
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
]

validities['B3E'] = validities[...] | [
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
]

validities['G3'] = validities[...] | [
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
]

validities['GO'] = validities[...] | [
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
]

validities['K3W'] = validities[...] | [
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
]

validities['K3WQ'] = validities[...] | [
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
]

validities['MH'] = validities[...] | [
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
]

validities['NH'] = validities[...] | [
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
]

validities['P3'] = validities[...] | [
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
]

validities['CPL'] = validities[...] | [
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
]

validities['CFOL'] = validities['K3'] | validities['LP'] | validities['L3'] | validities['RM3'] | validities['CPL'] | [
    'Existential from Universal',
    'Existential Syllogism',
    'Quantifier Interdefinability 1',
    'Quantifier Interdefinability 2',
    'Quantifier Interdefinability 3',
    'Quantifier Interdefinability 4',
    'Self Identity 2',
    'Syllogism',
    'Universal Predicate Syllogism',
]
validities['K'] = validities['CFOL'] | [
    'Modal Transformation 1',
    'Modal Transformation 2',
    'Modal Transformation 3',
    'Modal Transformation 4',
    'Necessity Distribution 1',
    'Necessity Distribution 2',
]
validities['D'] = validities['K'] | [
    'Serial Inference 1',
    'Serial Inference 2',
]
validities['T'] = validities['D'] | [
    'Necessity Elimination',
    'NP Collapse 1',
    'Possibility Addition',
    'Reflexive Inference 1',
]
validities['S4'] = validities['T'] | [
    'S4 Conditional Inference 1',
    'S4 Conditional Inference 2',
    'S4 Material Inference 1',
    'S4 Material Inference 2',
]
validities['S5'] = validities['S4'] | [
    'S5 Conditional Inference 1',
    'S5 Material Inference 1',
]


invalidities = {}

invalidities[...] = qsetf([
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
])

invalidities['S5'] = invalidities[...] | [

]

invalidities['S4'] = invalidities['S5'] | [
    'S5 Conditional Inference 1',
    'S5 Material Inference 1',
]

invalidities['T'] = invalidities['S4'] | [
    'S4 Conditional Inference 1',
    'S4 Conditional Inference 2',
    'S4 Material Inference 1',
    'S4 Material Inference 2',
]

invalidities['D'] = invalidities['T'] | [
    'Necessity Elimination',
    'NP Collapse 1',
    'Possibility Addition',
    'Possibility Distribution',
    'Reflexive Inference 1',
    'S4 Conditional Inference 2',
]

invalidities['K'] = invalidities['D'] | [
    'Serial Inference 1',
    'Serial Inference 2',

]

invalidities['CFOL'] = invalidities['K'] | [
    'Modal Transformation 1',
    'Modal Transformation 2',
    'Modal Transformation 3',
    'Modal Transformation 4',
    'Necessity Distribution 1',
    'Necessity Distribution 2',
]

invalidities['CPL'] = invalidities['CFOL'] | [
    'Existential Syllogism',
    'Existential from Universal',
    'Quantifier Interdefinability 1',
    'Quantifier Interdefinability 2',
    'Quantifier Interdefinability 3',
    'Quantifier Interdefinability 4',
    'Self Identity 2',
    'Syllogism',
    'Universal Predicate Syllogism',
]

invalidities['K3'] = invalidities['CFOL'] | [
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
]

invalidities['LP'] = invalidities['CFOL'] | [
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
    'Self Identity 1',
    'Self Identity 2',
    'Syllogism',
    'Universal Predicate Syllogism',
]

invalidities['FDE'] = invalidities['K3'] | invalidities['LP']

invalidities['RM3'] = invalidities['CFOL'] | [
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
]

invalidities['L3'] = invalidities['CFOL'] | [
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
]

invalidities['B3E'] = invalidities['CFOL'] | [
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
]

invalidities['G3'] = invalidities['CFOL'] | [
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
]

invalidities['GO'] = invalidities['CFOL'] | [
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
]

invalidities['K3W'] = invalidities['CFOL'] | [
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
]

invalidities['K3WQ'] = invalidities['K3W'] | [

]

invalidities['MH'] = invalidities['CFOL'] | [
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
]

invalidities['NH'] = invalidities['CFOL'] | [
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
]

invalidities['P3'] = invalidities[...] | [
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
    'S5 Material Inference 1',
    'Self Identity 1',
    'Self Identity 2',
    'Serial Inference 1',
    'Serial Inference 2',
    'Syllogism',
    'Universal Predicate Syllogism',
]

def find_missing(logic):
    from collections import defaultdict
    from pytableaux.logics import registry
    from pytableaux.proof import Tableau
    logic = registry(logic)
    exists = invalidities[logic.Meta.name] | validities[logic.Meta.name]
    exists = set(map(examples.argument, exists))
    missing = set(examples.arguments()) - exists
    results = defaultdict(set)
    for arg in missing:
        results[Tableau(logic, arg).build().valid].add(arg.title)
    return {key: sorted(value) for key, value in results.items()}

