from pytableaux.lang import Parser
from pytableaux.tools import qset, qsetf
from pytableaux import examples
arg = Parser('polish', examples.preds).argument

validities = {}
invalidities = {}
validities[...] = qsetf([
    'Modal Platitude 1',
    'Modal Platitude 2',
    'Modal Platitude 3',
])
validities['FDE'] = validities[...] | [
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
    # 'Self Identity 1',
    'Quantifier Interdefinability 4',
    'Simplification',
]
validities['K3'] = validities['FDE'] | [
    'Biconditional Elimination 1',
    'Biconditional Elimination 2',
    'Biconditional Elimination 3',
    'Conditional Modus Ponens',
    'Conditional Modus Tollens',
    'Disjunctive Syllogism',
    'Disjunctive Syllogism 2',
    'Explosion',
    'Law of Non-contradiction',
    'Material Modus Ponens',
    'Material Modus Tollens',
]
validities['LP'] = validities['FDE'] | [
    'Biconditional Identity',
    'Conditional Double Negation',
    'Conditional Identity',
    'Conditional Law of Excluded Middle',
    'Law of Excluded Middle',
    'Material Identity',
]

validities['RM3'] = validities[...] | [
    'Conditional Identity',
    'Conditional Modus Ponens',
    'Biconditional Elimination 1',
    'Biconditional Introduction 3',
    'Biconditional Identity',
    'DeMorgan 1',
    'DeMorgan 2',
    'DeMorgan 3',
    'DeMorgan 4',
    'DeMorgan 5',
    'DeMorgan 6',
    'DeMorgan 7',
    'DeMorgan 8',
    'Law of Excluded Middle',
    
]
validities['L3'] = validities[...] | [
    'Conditional Identity',
    'Conditional Modus Ponens',
    'Biconditional Elimination 1',
    'Biconditional Elimination 3',
    'Biconditional Introduction 3',
    'Biconditional Identity',
    'DeMorgan 1',
    'DeMorgan 2',
    'DeMorgan 3',
    'DeMorgan 4',
    'DeMorgan 5',
    'DeMorgan 6',
    'DeMorgan 7',
    'DeMorgan 8',
    'Law of Non-contradiction',
]
validities['B3E'] = validities[...] | [
    'Biconditional Introduction 1',
    'Biconditional Elimination 3',
    'Biconditional Elimination 1',
    'Conditional Contraction',
    arg('AaTb', ('a',), title='Asserted Addition'),
    arg('AUabNUab', title='Conditional LEM')
]
validities['G3'] = validities[...] | [
    'Biconditional Identity',
    'DeMorgan 6',
]
validities['GO'] = validities[...] | [
    'DeMorgan 3',
    'Quantifier Interdefinability 1',
    'Quantifier Interdefinability 3',
]
validities['K3W'] = validities[...] | [
    'Conditional Contraction',
    'DeMorgan 1',
    'DeMorgan 2',
    'DeMorgan 3',
    'DeMorgan 4',
    'DeMorgan 5',
    'DeMorgan 6',
    'DeMorgan 7',
    'DeMorgan 8',
    'Law of Non-contradiction',
    
]
validities['K3WQ'] = validities[...] | [
    'Conditional Contraction',
    'DeMorgan 1',
    'DeMorgan 2',
    'DeMorgan 3',
    'DeMorgan 4',
    'DeMorgan 5',
    'DeMorgan 6',
    'DeMorgan 7',
    'DeMorgan 8',
    'Law of Non-contradiction',
    'Quantifier Interdefinability 1',
    'Quantifier Interdefinability 2',
    'Quantifier Interdefinability 3',
    'Quantifier Interdefinability 4',
]
validities['MH'] = validities[...] | [
    'Conditional Identity',
    'Conditional Modus Ponens',
    'Conjunction Introduction',
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
    'DeMorgan 2',
    'Law of Excluded Middle',
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
    'DeMorgan 6',
]

validities['CPL'] = validities[...] | [
    'Addition',
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
    'NP Collapse 1',
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
    'Serial Inference 1',
    'Serial Inference 2',
    'Syllogism',
    'Universal Predicate Syllogism',
]

invalidities['K3'] = invalidities['CFOL'] | [
    'Conditional Double Negation',
    'Law of Excluded Middle',
    'Conditional Pseudo Contraction',
    'Conditional Law of Excluded Middle',

]
invalidities['LP'] = invalidities['CFOL'] | [
    'Explosion',
    'Law of Non-contradiction',
    'Biconditional Elimination 1',
    'Biconditional Elimination 2',
    'Biconditional Elimination 3',
    'Conditional Modus Ponens',
    'Conditional Modus Tollens',
    'Disjunctive Syllogism 2',
    'Disjunctive Syllogism',
    'Material Biconditional Elimination 3',
    'Material Modus Ponens',
    'Material Modus Tollens',
    
]
invalidities['FDE'] = invalidities['K3'] | invalidities['LP'] | [
]

invalidities['RM3'] = invalidities['CFOL'] | [
    'Biconditional Elimination 3',
    'Law of Non-contradiction',
]
invalidities['L3'] = invalidities['CFOL'] | [
    'Conditional Contraction',
    'Conditional Law of Excluded Middle',
    'Conditional Pseudo Contraction',
    'Law of Excluded Middle',
    'Material Identity',
]
invalidities['B3E'] = invalidities['CFOL'] | [
    'Law of Excluded Middle',
]
invalidities['G3'] = invalidities['CFOL'] | [
    'Conditional Double Negation',
    'DeMorgan 8',
    'Law of Excluded Middle',
]
invalidities['GO'] = invalidities['CFOL'] | [
    'DeMorgan 1',
    'Law of Excluded Middle',
    'Quantifier Interdefinability 2',
    'Quantifier Interdefinability 4',
]
invalidities['K3W'] = invalidities['CFOL'] | [
    'Addition',
    'Law of Excluded Middle',
]
invalidities['K3WQ'] = invalidities['CFOL'] | [
    'Addition',
    'Law of Excluded Middle',

]
invalidities['MH'] = invalidities['CFOL'] | [
    'Law of Excluded Middle',
   arg('UNbNa', ('NAaNa', 'Uab'), title='p_from_article'),
]
invalidities['NH'] = invalidities['CFOL'] | [
    'Explosion',
    'Law of Non-contradiction',
]
invalidities['P3'] = invalidities[...] | [
    'DeMorgan 1',
    'DeMorgan 2',
    'DeMorgan 3',
    'DeMorgan 4',
    'DeMorgan 5',
    'Law of Excluded Middle',
]