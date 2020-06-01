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
# pytableaux - Kripke Normal Modal Logic
name = 'K'
title = 'Kripke Normal Modal Logic'
description = 'Base normal modal logic with no access relation restrictions'
tags_list = ['bivalent', 'modal', 'first-order']
tags = set(tags_list)
category = 'Bivalent Modal'
category_display_order = 1

import logic, examples
from logic import negate, negative, operate, quantify, atomic, constant, predicated, NotImplementedError
from . import fde

Identity = logic.get_system_predicate('Identity')
Existence = logic.get_system_predicate('Existence')

def substitute_params(params, old_value, new_value):
    new_params = []
    for p in params:
        if p == old_value:
            new_params.append(new_value)
        else:
            new_params.append(p)
    return tuple(new_params)

class Model(logic.Model):
    """
    A K-model comprises a non-empty collection of K-frames, a world access
    relation, and a set of constants (the domain).
    """

    class Frame(object):
        """
        A K-frame comprises the interpretation of sentences and predicates at a world.
        """

        #: The world of the frame.
        world = 0

        #: An assignment of each atomic sentence to a value.
        atomics = {}

        #: An assignment of each opaque (un-interpreted) sentence to a value.
        opaques = {}

        #: A map of predicates to their extension.
        extensions = {}

        def __init__(self, world):
            self.world = world
            self.atomics = {}
            self.opaques = {}
            self.extensions = {}
            self.predicates = set()
            self.extensions.update({'Identity': set(), 'Existence': set()})

        def get_data(self, model):
            return {
                'description' : 'frame at world {0}'.format(str(self.world)),
                'datatype'    : 'map',
                'typehint'    : 'frame',
                'value'       : {
                    'world'   : {
                        'description' : 'world',
                        'datatype'    : 'int',
                        'typehint'    : 'world', 
                        'value'       : self.world,
                        'symbol'      : 'w',
                    },
                    'Atomics' : {
                        'description'     : 'atomic values',
                        'datatype'        : 'function',
                        'typehint'        : 'truth_function',
                        'input_datatype'  : 'sentence',
                        'output_datatype' : 'string',
                        'output_typehint' : 'truth_value',
                        'symbol'          : 'v',
                        'values'          : [
                            {
                                'input'  : sentence,
                                'output' : model.truth_value_chars[self.atomics[sentence]]
                            }
                            for sentence in sorted(list(self.atomics.keys()))
                        ]
                    },
                    'Opaques' : {
                        'description'     : 'opaque values',
                        'datatype'        : 'function',
                        'typehint'        : 'truth_function',
                        'input_datatype'  : 'sentence',
                        'output_datatype' : 'string',
                        'output_typehint' : 'truth_value',
                        'symbol'          : 'v',
                        'values'          : [
                            {
                                'input'  : sentence,
                                'output' : model.truth_value_chars[self.opaques[sentence]],
                            }
                            for sentence in sorted(list(self.opaques.keys()))
                        ]
                    },
                    'Predicates' : {
                        'description' : 'predicate extensions',
                        'datatype'    : 'list',
                        'values'      : [
                            {
                                'description'     : 'predicate extension for {0}'.format(predicate.name),
                                'datatype'        : 'function',
                                'typehint'        : 'extension',
                                'input_datatype'  : 'predicate',
                                'output_datatype' : 'set',
                                'output_typehint' : 'extension',
                                'symbol'          : 'P',
                                'values'          : [
                                    {
                                        'input'  : predicate,
                                        'output' : self.extensions[predicate.name],
                                    }
                                ]
                            }
                            for predicate in sorted(list(model.predicates)) if predicate.name in self.extensions
                        ]
                    }
                }
            }

        def is_equivalent_to(self, other):
            # check for informational equivalence, ignoring world
            # check atomic keys
            akeys_a = set(self.atomics.keys())
            akeys_b = set(other.atomics.keys())
            if len(akeys_a.difference(akeys_b)) or len(akeys_b.difference(akeys_a)):
                return False
            # check opaque keys
            okeys_a = set(self.opaques.keys())
            okeys_b = set(other.opaques.keys())
            if len(okeys_a.difference(okeys_b)) or len(okeys_b.difference(okeys_a)):
                return False
            # check extensions keys
            ekeys_a = set(self.extensions.keys())
            ekeys_b = set(other.extensions.keys())
            if len(ekeys_a.difference(ekeys_b)) or len(ekeys_b.difference(ekeys_a)):
                return False
            # check atomic values
            for s in self.atomics:
                if other.atomics[s] != self.atomics[s]:
                    return False
            # check opaque values
            for s in self.opaques:
                if other.opaques[s] != self.opaques[s]:
                    return False
            # check extensions values
            for p in self.extensions:
                ext_a = self.extensions[p]
                ext_b = other.extensions[p]
                if len(ext_a.difference(ext_b)) or len(ext_b.difference(ext_a)):
                    return False
            return True

        def __eq__(self, other):
            return other != None and self.__dict__ == other.__dict__

        def __ne__(self, other):
            return other == None or self.__dict__ != other.__dict__

        def __lt__(self, other):
            return self.world < other.world

        def __le__(self, other):
            return self.world <= other.world

        def __gt__(self, other):
            return self.world > other.world

        def __ge__(self, other):
            return self.world >= other.world

        def __cmp__(self, other):
            # Python 2 only
            return cmp(self.world, other.world)

    truth_values = [0, 1]
    truth_functional_operators = fde.Model.truth_functional_operators
    modal_operators = set(['Possibility', 'Necessity'])

    unassigned_value = 0
    char_values = {
        'F' : 0,
        'T' : 1
    }
    truth_value_chars = {
        0 : 'F',
        1 : 'T'
    }

    #: A map from worlds to their frame.
    frames = {}

    #: A set of pairs of worlds.
    access = set()

    #: The domain of constants.
    constants = set()

    # wip: real domain (fixed)
    domain = set()
    denotation = {}

    def __init__(self):
        super(Model, self).__init__()
        self.frames = {}
        self.access = set()
        self.predicates = set([
            Identity,
            Existence,
        ])
        self.constants = set()
        self.fde = fde.Model()
        # ensure there is a w0
        self.world_frame(0)
        # TODO: implement real domain and denotation, think of identity necessity
        self.domain = set()
        self.denotation = {}

    def value_of_operated(self, sentence, world=0, **kw):
        """
        The value of a sentence with a truth-functional operator `w` is determined by
        the values of its operands at `w` according to the following tables.

        //truth_tables//k//
        """
        if sentence.operator in self.modal_operators:
            return self.value_of_modal(sentence, world=world, **kw)
        return super(Model, self).value_of_operated(sentence, world=world, **kw)

    def value_of_predicated(self, sentence, **kw):
        """
        A sentence for predicate `P` is true at `w` iff the tuple of the parameters
        is in the extension of `P` at `w`.
        """
        if tuple(sentence.parameters) in self.get_extension(sentence.predicate, **kw):
            return self.char_values['T']
        return self.char_values['F']

    def value_of_existential(self, sentence, world=0, **kw):
        """
        An existential sentence is true at `w`, just when the sentence resulting in the
        subsitution of some constant in the domain for the variable is true at `w`.
        """
        for c in self.constants:
            r = sentence.substitute(c, sentence.variable)
            if self.value_of(r, world=world, **kw) == self.char_values['T']:
                return self.char_values['T']
        return self.char_values['F']

    def value_of_universal(self, sentence, world=0, **kw):
        """
        A universal sentence is true at `w`, just when the sentence resulting in the
        subsitution of each constant in the domain for the variable is true at `w`.
        """
        for c in self.constants:
            r = sentence.substitute(c, sentence.variable)
            if self.value_of(r, world=world, **kw) == self.char_values['F']:
                return self.char_values['F']
        return self.char_values['T']

    def value_of_possibility(self, sentence, world=0, **kw):
        """
        A possibility sentence is true at `w` iff its operand is true at `w'` for
        some `w'` such that `<w, w'>` in the access relation.
        """
        for w2 in self.visibles(world):
            if self.value_of(sentence.operand, world=w2, **kw) == self.char_values['T']:
                return self.char_values['T']
        return self.char_values['F']

    def value_of_necessity(self, sentence, world=0, **kw):
        """
        A possibility sentence is true at `w` iff its operand is true at `w'` for
        each `w'` such that `<w, w'>` is in the access relation.
        """
        for w2 in self.visibles(world):
            if self.value_of(sentence.operand, world=w2, **kw) == self.char_values['F']:
                return self.char_values['F']
        return self.char_values['T']

    def is_countermodel_to(self, argument):
        """
        A model is a countermodel for an argument iff the value of each premise
        is **T** at `w0` and the value of the conclusion is **F** at `w0`.
        """
        for premise in argument.premises:
            if self.value_of(premise, world=0) != self.char_values['T']:
                return False
        return self.value_of(argument.conclusion, world=0) == self.char_values['F']

    def get_data(self):
        return {
            'Worlds': {
                'description'     : 'set of worlds',
                'in_summary'      : True,
                'datatype'        : 'set',
                'member_datatype' : 'int',
                'member_typehint' : 'world',
                'symbol'          : 'W',
                'values'          : sorted(list(self.frames.keys())),
            },
            'Access': {
                'description'     : 'access relation',
                'in_summary'      : True,
                'datatype'        : 'set',
                'typehint'        : 'access_relation',
                'member_datatype' : 'tuple',
                'member_typehint' : 'access',
                'symbol'          : 'R',
                'values'          : sorted(list(self.access)),
            },
            'Frames': {
                'description'     : 'world frames',
                'datatype'        : 'list',
                'typehint'        : 'frames',
                'member_datatype' : 'map',
                'member_typehint' : 'frame',
                'symbol'          : 'F',
                'values'          : [frame.get_data(self) for frame in sorted(self.frames.values())]
            }
        }

    def read_branch(self, branch):
        # TODO: write docs
    #    """
    #    To read a model from a branch *b*, every atomic sentence at a world *w* on *b*
    #    is True at *w*, and every negated atomic is False at *w*. For every predicate
    #    sentence Fa0...an at a world *w* on *b*, the tuple <a0,...,an> is in the extension
    #    of F at *w*.
    #    """
        for node in branch.nodes:
            self.read_node(node)
        self.finish()

    def read_node(self, node):
        if node.has('sentence'):
            sentence = node.props['sentence']
            world = node.props['world']
            if self.is_sentence_opaque(sentence):
                self.set_opaque_value(sentence, self.char_values['T'], world=world)
            elif sentence.is_literal():
                self.set_literal_value(sentence, self.char_values['T'], world=world)
            self.predicates.update(node.predicates())
        elif node.has('world1') and node.has('world2'):
            self.add_access(node.props['world1'], node.props['world2'])

    def finish(self):
        # track all atomics
        atomics = set()
        for world in self.frames:
            frame = self.world_frame(world)
            atomics.update(frame.atomics.keys())
            for predicate in self.predicates:
                self.agument_extension_with_identicals(predicate, world)
            self.ensure_self_identity(world)
            self.ensure_self_existence(world)
        # make sure each atomic is assigned a value in each frame
        for world in self.frames:
            frame = self.world_frame(world)
            for s in atomics:
                if s not in frame.atomics:
                    self.set_literal_value(s, self.unassigned_value, world=world)

    def ensure_self_identity(self, world):
        identity_extension = self.get_extension(Identity, world=world)
        for c in self.constants:
            # make sure each constant is self-identical
            identity_extension.add((c, c))

    def ensure_self_existence(self, world):
        existence_extension = self.get_extension(Existence, world=world)
        for c in self.constants:
            # make sure each constant exists
            existence_extension.add((c,))

    def agument_extension_with_identicals(self, predicate, world):
        extension = self.get_extension(predicate, world=world)
        for c in self.constants:
            identicals = self.get_identicals(c, world=world)
            to_add = set()
            for params in extension:
                if c in params:
                    for new_c in identicals:
                        new_params = substitute_params(params, c, new_c)
                        to_add.add(new_params)
            extension.update(to_add)

    def get_identicals(self, c, world=0, **kw):
        identity_extension = self.get_extension(Identity, world=world, **kw)
        identicals = set()
        for params in identity_extension:
            if c in params:
                identicals.update(params)
        if c in identicals:
            identicals.remove(c)
        return identicals

    def set_literal_value(self, sentence, value, **kw):
        if sentence.is_operated() and sentence.operator == 'Negation':
            self.set_literal_value(sentence.operand, self.truth_function('Negation', value), **kw)
        elif sentence.is_atomic():
            self.set_atomic_value(sentence, value, **kw)
        elif sentence.is_predicated():
            self.set_predicated_value(sentence, value, **kw)
        else:
            raise NotImplementedError(NotImplemented)

    def set_opaque_value(self, sentence, value, world=0, **kw):
        frame = self.world_frame(world)
        if sentence in frame.opaques and frame.opaques[sentence] != value:
            raise Model.ModelValueError('Inconsistent value for sentence {0}'.format(str(sentence)))
        frame.opaques[sentence] = value

    def set_atomic_value(self, sentence, value, world=0, **kw):
        frame = self.world_frame(world)
        if sentence in frame.atomics and frame.atomics[sentence] != value:
            raise Model.ModelValueError('Inconsistent value for sentence {0}'.format(str(sentence)))
        frame.atomics[sentence] = value

    def set_predicated_value(self, sentence, value, world=0, **kw):
        predicate = sentence.predicate
        if predicate not in self.predicates:
            self.predicates.add(predicate)
        params = tuple(sentence.parameters)
        for param in params:
            if param.is_constant():
                self.constants.add(param)
        extension = self.get_extension(predicate, world=world, **kw)
        if value == self.char_values['F']:
            if params in extension:
                raise Model.ModelValueError('Cannot set value {0} for tuple {1} already in extension'.format(str(value), str(params)))
        if value == self.char_values['T']:
            extension.add(params)

    def get_extension(self, predicate, world=0, **kw):
        name = predicate.name
        frame = self.world_frame(world)
        if predicate not in self.predicates:
            self.predicates.add(predicate)
        if predicate not in frame.predicates:
            frame.predicates.add(predicate)
        if name not in frame.extensions:
            frame.extensions[name] = set()
        return frame.extensions[name]

    def add_access(self, w1, w2):
        self.access.add((w1, w2))
        self.world_frame(w1)
        self.world_frame(w2)

    def has_access(self, w1, w2):
        return (w1, w2) in self.access

    def visibles(self, world):
        return {w for w in self.frames if (world, w) in self.access}

    def world_frame(self, world):
        if world not in self.frames:
            self.frames[world] = self.__class__.Frame(world)
        return self.frames[world]

    def value_of_opaque(self, sentence, world=0, **kw):
        frame = self.world_frame(world)
        if sentence in frame.opaques:
            return frame.opaques[sentence]
        return self.unassigned_value

    def value_of_atomic(self, sentence, world=0, **kw):
        frame = self.world_frame(world)
        if sentence in frame.atomics:
            return frame.atomics[sentence]
        return self.unassigned_value

    def value_of_modal(self, sentence, world=0, **kw):
        operator = sentence.operator
        if operator == 'Possibility':
            return self.value_of_possibility(sentence, world=world, **kw)
        elif operator == 'Necessity':
            return self.value_of_necessity(sentence, world=world, **kw)
        else:
            raise NotImplementedError(NotImplemented)

    def value_of_quantified(self, sentence, world=0, **kw):
        q = sentence.quantifier
        if q == 'Existential':
            return self.value_of_existential(sentence, world=world, **kw)
        elif q == 'Universal':
            return self.value_of_universal(sentence, world=world, **kw)
        return super(Model, self).value_of_quantified(sentence, world=world, **kw)

    def truth_function(self, operator, a, b=None):
        return self.fde.truth_function(operator, a, b)

class TableauxSystem(logic.TableauxSystem):
    """
    Modal tableaux are similar to classical tableaux, with the addition of a
    *world* index for each sentence node, as well as *access* nodes representing
    "visibility" of worlds. The worlds and access nodes come into play with
    the rules for Possibility and Necessity. All other rules function equivalently
    to their classical counterparts.
    """

    @staticmethod
    def build_trunk(tableau, argument):
        """
        To build the trunk for an argument, add a node with each premise, with
        world *w0*, followed by a node with the negation of the conclusion
        with world *w0*.
        """
        branch = tableau.branch()
        for premise in argument.premises:
            branch.add({ 'sentence': premise, 'world': 0 })
        branch.add({ 'sentence': negate(argument.conclusion), 'world': 0 })

class IsModal(object):
    modal = True

class TableauxRules(object):
    """
    Rules for modal operators employ *world* indexes as well access-type
    nodes. The world indexes are transparent for the rules for classical
    connectives.
    """

    class Closure(logic.TableauxSystem.ClosureRule):
        """
        A branch closes when a sentence and its negation both appear on a node **with the
        same world** on the branch.
        """

        def applies_to_branch(self, branch):
            for node in branch.get_nodes():
                if node.has('sentence') and node.has('world'):
                    n = branch.find({'sentence': negate(node.props['sentence']), 'world': node.props['world']})
                    if n != None:
                        return {'nodes': set([node, n]), 'type': 'Nodes'}
            return False

        def node_will_close_branch(self, node, branch):
            return node.has('sentence') and node.has('world') and branch.has({
                'sentence': negative(node.props['sentence']), 'world': node.props['world']
            })

        def example(self):
            a = atomic(0, 0)
            self.tableau.branch().update([
                {'sentence':        a , 'world': 0},
                {'sentence': negate(a), 'world': 0},
            ])

    class SelfIdentityClosure(logic.TableauxSystem.ClosureRule):
        """
        A branch closes when a sentence of the form P{~a = a} appears on the branch *at any world*.
        """

        def applies_to_branch(self, branch):
            for node in branch.get_nodes():
                if node.has('sentence'):
                    s = node.props['sentence']
                    if s.is_operated() and s.operator == 'Negation':
                        o = s.operand
                        if o.is_predicated() and o.predicate.name == 'Identity':
                            a, b = o.parameters
                            if a == b:
                                return {'node': node, 'type': 'Node'}
            return False

        def example(self):
            s = negate(examples.self_identity())
            self.tableau.branch().add({'sentence': s, 'world': 0})

    class DoubleNegation(IsModal, logic.TableauxSystem.ConditionalNodeRule):
        """
        From an unticked double negation node *n* with world *w* on a branch *b*, add a
        node to *b* with *w* and the double-negatum of *n*, then tick *n*.
        """

        negated  = True
        operator = 'Negation'

        def apply_to_node(self, node, branch):
            w = node.props['world']
            s = self.sentence(node)
            branch.add({'sentence': s.operand, 'world': w}).tick(node)

    class Assertion(IsModal, logic.TableauxSystem.ConditionalNodeRule):
        """
        From an unticked assertion node *n* with world *w* on a branch *b*,
        add a node to *b* with the operand of *n* and world *w*, then tick *n*.
        """

        operator = 'Assertion'

        def apply_to_node(self, node, branch):
            w = node.props['world']
            s = self.sentence(node)
            branch.add({'sentence': s.operand, 'world': w}).tick(node)

    class AssertionNegated(IsModal, logic.TableauxSystem.ConditionalNodeRule):
        """
        From an unticked, negated assertion node *n* with world *w* on a branch *b*,
        add a node to *b* with the negation of the assertion of *n* and world *w*,
        then tick *n*.
        """

        operator = 'Assertion'
        negated  = True

        def apply_to_node(self, node, branch):
            w = node.props['world']
            s = self.sentence(node)
            branch.add({'sentence': negate(s.operand), 'world': w}).tick(node)

    class Conjunction(IsModal, logic.TableauxSystem.ConditionalNodeRule):
        """
        From an unticked conjunction node *n* with world *w* on a branch *b*, for each conjunct,
        add a node with world *w* to *b* with the conjunct, then tick *n*.
        """

        operator = 'Conjunction'

        def apply_to_node(self, node, branch):
            s = self.sentence(node)
            w = node.props['world']
            for conjunct in s.operands:
                branch.add({'sentence': conjunct, 'world': w})
            branch.tick(node)

    class ConjunctionNegated(IsModal, logic.TableauxSystem.ConditionalNodeRule):
        """
        From an unticked negated conjunction node *n* with world *w* on a branch *b*, for each
        conjunct, make a new branch *b'* from *b* and add a node with *w* and the negation of
        the conjunct to *b*, then tick *n*.
        """

        negated  = True
        operator = 'Conjunction'

        def apply_to_node(self, node, branch):
            s = self.sentence(node)
            w = node.props['world']
            b1 = branch
            b2 = self.tableau.branch(branch)
            b1.add({'sentence': negate(s.lhs), 'world': w}).tick(node)
            b2.add({'sentence': negate(s.rhs), 'world': w}).tick(node)

        def score_target_map(self, target):
            branch = target['branch']
            node = target['node']
            s = self.sentence(node)
            w = node.props['world']
            return {
                'b1': branch.has({'sentence': s.lhs, 'world': w}),
                'b2': branch.has({'sentence': s.rhs, 'world': w}),
            }

    class Disjunction(IsModal, logic.TableauxSystem.ConditionalNodeRule):
        """
        From an unticked disjunction node *n* with world *w* on a branch *b*, for each disjunct,
        make a new branch *b'* from *b* and add a node with the disjunct and world *w* to *b'*,
        then tick *n*.
        """

        operator = 'Disjunction'

        def apply_to_node(self, node, branch):
            s = self.sentence(node)
            w = node.props['world']
            b1 = branch
            b2 = self.tableau.branch(branch)
            b1.add({'sentence': s.lhs, 'world': w}).tick(node)
            b2.add({'sentence': s.rhs, 'world': w}).tick(node)

        def score_target_map(self, target):
            branch = target['branch']
            node = target['node']
            s = self.sentence(node)
            w = node.props['world']
            return {
                'b1': branch.has({'sentence': negative(s.lhs), 'world': w}),
                'b2': branch.has({'sentence': negative(s.rhs), 'world': w}),
            }

    class DisjunctionNegated(IsModal, logic.TableauxSystem.ConditionalNodeRule):
        """
        From an unticked negated disjunction node *n* with world *w* on a branch *b*, for each
        disjunct, add a node with *w* and the negation of the disjunct to *b*, then tick *n*.
        """

        negated  = True
        operator = 'Disjunction'

        def apply_to_node(self, node, branch):
            s = self.sentence(node)
            w = node.props['world']
            for disjunct in s.operands:
                branch.add({'sentence': negate(disjunct), 'world': w})
            branch.tick(node)

    class MaterialConditional(IsModal, logic.TableauxSystem.ConditionalNodeRule):
        """
        From an unticked material conditional node *n* with world *w* on a branch *b*, make two
        new branches *b'* and *b''* from *b*, add a node with world *w* and the negation of the
        antecedent to *b'*, and add a node with world *w* and the conequent to *b''*, then tick
        *n*.
        """

        operator = 'Material Conditional'

        def apply_to_node(self, node, branch):
            s = self.sentence(node)
            w = node.props['world']
            b1 = branch
            b2 = self.tableau.branch(branch)
            b1.add({'sentence': negate(s.lhs), 'world': w}).tick(node)
            b2.add({'sentence':        s.rhs , 'world': w}).tick(node)

        def score_target_map(self, target):
            branch = target['branch']
            node = target['node']
            s = self.sentence(node)
            w = node.props['world']
            return {
                'b1': branch.has({'sentence':          s.lhs , 'world': w}),
                'b2': branch.has({'sentence': negative(s.rhs), 'world': w}),
            }

    class MaterialConditionalNegated(IsModal, logic.TableauxSystem.ConditionalNodeRule):
        """
        From an unticked negated material conditional node *n* with world *w* on a branch *b*,
        add two nodes with *w* to *b*, one with the antecedent and the other with the negation
        of the consequent, then tick *n*.
        """

        negated  = True
        operator = 'Material Conditional'

        def apply_to_node(self, node, branch):
            s = self.sentence(node)
            w = node.props['world']
            branch.update([
                {'sentence':        s.lhs , 'world': w}, 
                {'sentence': negate(s.rhs), 'world': w},
            ]).tick(node)

    class MaterialBiconditional(IsModal, logic.TableauxSystem.ConditionalNodeRule):
        """
        From an unticked material biconditional node *n* with world *w* on a branch *b*, make
        two new branches *b'* and *b''* from *b*, add two nodes with world *w* to *b'*, one with
        the negation of the antecedent and one with the negation of the consequent, and add two
        nodes with world *w* to *b''*, one with the antecedent and one with the consequent, then
        tick *n*.
        """

        operator = 'Material Biconditional'

        def apply_to_node(self, node, branch):
            s = self.sentence(node)
            w = node.props['world']
            b1 = branch
            b2 = self.tableau.branch(branch)
            b1.update([
                { 'sentence' : negate(s.lhs), 'world' : w }, 
                { 'sentence' : negate(s.rhs), 'world' : w }
            ]).tick(node)
            b2.update([
                { 'sentence' : s.rhs, 'world' : w }, 
                { 'sentence' : s.lhs, 'world' : w }
            ]).tick(node)

        def score_target_map(self, target):
            branch = target['branch']
            node = target['node']
            s = self.sentence(node)
            w = node.props['world']
            return {
                'b1': branch.has_any([
                    {'sentence': s.lhs, 'world': w},
                    {'sentence': s.rhs, 'world': w},
                ]),
                'b2': branch.has_any([
                    {'sentence': negative(s.lhs), 'world': w},
                    {'sentence': negative(s.rhs), 'world': w},
                ]),
            }

    class MaterialBiconditionalNegated(IsModal, logic.TableauxSystem.ConditionalNodeRule):
        """
        From an unticked negated material biconditional node *n* with world *w* on a branch *b*,
        make two new branches *b'* and *b''* from *b*, add two nodes with *w* to *b'*, one with
        the antecedent and the other with the negation of the consequent, and add two nodes with
        *w* to *b''*, one with the negation of the antecedent and the other with the consequent,
        then tick *n*.
        """

        negated  = True
        operator = 'Material Biconditional'

        def apply_to_node(self, node, branch):
            s = self.sentence(node)
            w = node.props['world']
            b1 = branch
            b2 = self.tableau.branch(branch)
            b1.update([
                { 'sentence':        s.lhs  , 'world' : w },
                { 'sentence': negate(s.rhs) , 'world' : w }
            ]).tick(node)
            b2.update([
                { 'sentence': negate(s.rhs) , 'world' : w },
                { 'sentence':        s.lhs  , 'world' : w }
            ]).tick(node)

        def score_target_map(self, target):
            branch = target['branch']
            node = target['node']
            s = self.sentence(node)
            w = node.props['world']
            score = 0
            return {
                'b1': branch.has_any([
                    {'sentence': negative(s.lhs), 'world': w},
                    {'sentence':          s.rhs , 'world': w},
                ]),
                'b2': branch.has_any([
                    {'sentence':          s.lhs , 'world': w},
                    {'sentence': negative(s.rhs), 'world': w},
                ]),
            }

    class Conditional(MaterialConditional):
        """
        The rule functions the same as the corresponding material conditional rule.

        From an unticked conditional node *n* with world *w* on a branch *b*, make two
        new branches *b'* and *b''* from *b*, add a node with world *w* and the negation of the
        antecedent to *b'*, and add a node with world *w* and the conequent to *b''*, then tick
        *n*.
        """

        operator = 'Conditional'

    class ConditionalNegated(MaterialConditionalNegated):
        """
        The rule functions the same as the corresponding material conditional rule.

        From an unticked negated conditional node *n* with world *w* on a branch *b*,
        add two nodes with *w* to *b*, one with the antecedent and the other with the negation
        of the consequent, then tick *n*.
        """

        operator = 'Conditional'

    class Biconditional(MaterialBiconditional):
        """
        The rule functions the same as the corresponding material biconditional rule.

        From an unticked biconditional node *n* with world *w* on a branch *b*, make
        two new branches *b'* and *b''* from *b*, add two nodes with world *w* to *b'*, one with
        the negation of the antecedent and one with the negation of the consequent, and add two
        nodes with world *w* to *b''*, one with the antecedent and one with the consequent, then
        tick *n*.
        """

        operator = 'Biconditional'

    class BiconditionalNegated(MaterialBiconditionalNegated):
        """
        The rule functions the same as the corresponding material biconditional rule.

        From an unticked negated biconditional node *n* with world *w* on a branch *b*,
        make two new branches *b'* and *b''* from *b*, add two nodes with *w* to *b'*, one with
        the antecedent and the other with the negation of the consequent, and add two nodes with
        *w* to *b''*, one with the negation of the antecedent and the other with the consequent,
        then tick *n*.
        """

        operator = 'Biconditional'

    class Existential(IsModal, logic.TableauxSystem.ConditionalNodeRule):
        """
        From an unticked existential node *n* with world *w* on a branch *b*, quantifying over
        variable *v* into sentence *s*, add a node with world *w* to *b* with the substitution
        into *s* of *v* with a constant new to *b*, then tick *n*.
        """

        quantifier = 'Existential'

        def apply_to_node(self, node, branch):
            w = node.props['world']
            s = self.sentence(node)
            v = node.props['sentence'].variable
            c = branch.new_constant()
            r = s.substitute(c, v)
            branch.add({'sentence': r, 'world': w}).tick(node)

    class ExistentialNegated(IsModal, logic.TableauxSystem.ConditionalNodeRule):
        """
        From an unticked negated existential node *n* with world *w* on a branch *b*,
        quantifying over variable *v* into sentence *s*, add a universally quantified
        node to *b* with world *w* over *v* into the negation of *s*, then tick *n*.
        """

        negated    = True
        quantifier = 'Existential'
        convert_to = 'Universal'

        def apply_to_node(self, node, branch):
            w = node.props['world']
            s = self.sentence(node)
            v = s.variable
            si = s.sentence
            # keep conversion neutral for inheritance below
            sq = quantify(self.convert_to, v, negate(si))
            branch.add({'sentence': sq, 'world': w}).tick(node)

    class Universal(IsModal, logic.TableauxSystem.SelectiveTrackingBranchRule):
        """
        From a universal node with world *w* on a branch *b*, quantifying over variable *v* into
        sentence *s*, result *r* of substituting a constant *c* on *b* (or a new constant if none
        exists) for *v* into *s* does not appear at *w* on *b*, add a node with *w* and *r* to
        *b*. The node *n* is never ticked.
        """

        quantifier = 'Universal'

        def get_candidate_targets_for_branch(self, branch):
            cands = list()
            constants = branch.constants()
            for node in branch.get_nodes():
                if not node.has('sentence'):
                    continue
                s = self.sentence(node)
                if s.quantifier == self.quantifier:
                    w = node.props['world']
                    v = s.variable
                    if len(constants):
                        # if the branch already has a constant, find all the substitutions not
                        # already on the branch.
                        for c in constants:
                            r = s.substitute(c, v)
                            if not branch.has({'sentence': r, 'world': w}):
                                cands.append({
                                    'branch'   : branch,
                                    'sentence' : r,
                                    'node'     : node,
                                    'world'    : w,
                                })
                    else:
                        # if the branch does not have any constants, pick a new one
                        c = branch.new_constant()
                        r = s.substitute(c, v)
                        cands.append({
                            'branch'   : branch,
                            'sentence' : r,
                            'node'     : node,
                            'world'    : w,
                        })
            return cands

        def apply_to_target(self, target):
            branch = target['branch']
            branch.add({'sentence': target['sentence'], 'world': target['world']})

        def example(self):
            self.tableau.branch().add({'sentence': examples.quantified(self.quantifier), 'world': 0})

    class UniversalNegated(ExistentialNegated):
        """
        From an unticked negated universal node *n* with world *w* on a branch *b*,
        quantifying over variable *v* into sentence *s*, add an existentially
        quantified node to *b* with world *w* over *v* into the negation of *s*,
        then tick *n*.
        """

        quantifier = 'Universal'
        convert_to = 'Existential'

    class Possibility(IsModal, logic.TableauxSystem.ConditionalNodeRule):
        """
        From an unticked possibility node with world *w* on a branch *b*, add a node with a
        world *w'* new to *b* with the operand of *n*, and add an access-type node with
        world1 *w* and world2 *w'* to *b*, then tick *n*.
        """

        operator = 'Possibility'

        def apply_to_node(self, node, branch):
            s  = self.sentence(node)
            w1 = node.props['world']
            w2 = branch.new_world()
            branch.update([
                {'sentence': s.operand, 'world': w2},
                {'world1': w1, 'world2': w2},
            ]).tick(node)

    class PossibilityNegated(IsModal, logic.TableauxSystem.ConditionalNodeRule):
        """
        From an unticked negated possibility node *n* with world *w* on a branch *b*, add a
        necessity node to *b* with *w*, whose operand is the negation of the negated 
        possibilium of *n*, then tick *n*.
        """

        negated    = True
        operator   = 'Possibility'
        convert_to = 'Necessity'

        def apply_to_node(self, node, branch):
            w = node.props['world']
            s = self.sentence(node)
            sn = operate(self.convert_to, [negate(s.operand)])
            branch.add({'sentence': sn, 'world': w}).tick(node)

    class Necessity(IsModal, logic.TableauxSystem.SelectiveTrackingBranchRule):
        """
        From a necessity node *n* with world *w1* and operand *s* on a branch *b*, for any
        world *w2* such that an access node with w1,w2 is on *b*, if *b* does not have a node
        with *s* at *w2*, add it to *b*. The node *n* is never ticked.
        """

        operator = 'Necessity'

        def get_candidate_targets_for_branch(self, branch):
            cands = list()
            worlds = branch.worlds()
            for node in branch.get_nodes():
                if not node.has('sentence') or not node.has('world'):
                    continue
                s = self.sentence(node)
                if s.operator == self.operator:                    
                    s = s.operand
                    w1 = node.props['world']
                    for w2 in worlds:
                        anode = branch.find({'world1': w1, 'world2': w2})
                        if anode != None and not branch.has({'sentence': s, 'world': w2}):
                            cands.append({
                                'node'     : node,
                                'sentence' : s,
                                'world'    : w2,
                                'branch'   : branch,
                                'nodes'    : set([node, anode]),
                                'type'     : 'Nodes',
                            })
            return cands

        def apply_to_target(self, target):
            branch = target['branch']
            branch.add({'sentence': target['sentence'], 'world': target['world']})

        def example(self):
            s = operate(self.operator, [atomic(0, 0)])
            self.tableau.branch().update([
                {'sentence': s, 'world': 0},
                {'world1': 0, 'world2': 1},
            ])

    class NecessityNegated(PossibilityNegated):
        """
        From an unticked negated necessity node *n* with world *w* on a branch *b*, add a
        possibility node whose operand is the negation of the negated necessitatum of *n*,
        then tick *n*.
        """

        operator   = 'Necessity'
        convert_to = 'Possibility'

    class IdentityIndiscernability(IsModal, logic.TableauxSystem.BranchRule):
        """
        From an unticked node *n* having an Identity sentence *s* at world *w* on an open branch *b*,
        and a predicated node *n'* whose sentence *s'* has a constant that is a parameter of *s*,
        if the replacement of that constant for the other constant of *s* is a sentence that does
        not appear on *b* at *w*, then add it.
        """

        def applies_to_branch(self, branch):
            nodes = {
                n for n in branch.get_nodes(ticked = False) if (
                    'sentence' in n.props and
                    n.props['sentence'].is_predicated()
                )
            }
            inodes = {
                n for n in nodes if (
                    n.props['sentence'].predicate.name == 'Identity' and
                    len(set(n.props['sentence'].parameters)) == 2
                )
            }
            for node in inodes:
                w = node.props['world']
                pa, pb = node.props['sentence'].parameters
                # find a node n with a sentence s having one of those parameters p.
                for n in nodes:
                    s = n.props['sentence']
                    if pa in s.parameters:
                        p = pa
                        p1 = pb
                    elif pb in s.parameters:
                        p = pb
                        p1 = pa
                    else:
                        continue
                    # let s1 be the replacement of p with the other parameter p1 into s.
                    params = [p1 if param == p else param for param in s.parameters]
                    s1 = predicated(s.predicate, params)
                    # since we have SelfIdentityClosure, we don't need a = a
                    if s.predicate.name != 'Identity' or params[0] != params[1]:
                        # if <s1,w> does not yet appear on b, ...
                        if not branch.has({'sentence': s1, 'world': w}):
                            # then the rule applies to <s',w,b>
                            return {'sentence': s1, 'world': w, 'branch': branch}
            return False

        def apply(self, target):
            target['branch'].add({'sentence': target['sentence'], 'world': target['world']})

        def example(self):
            self.tableau.branch().update([ 
                {'sentence' : examples.predicated(), 'world': 0},
                {'sentence' : examples.identity(),   'world': 0},
            ])

    closure_rules = [
        Closure,
        SelfIdentityClosure,
    ]

    rule_groups = [
        [
            # non-branching rules
            IdentityIndiscernability,
            Assertion,
            AssertionNegated,
            Conjunction, 
            DisjunctionNegated, 
            MaterialConditionalNegated,
            ConditionalNegated,
            Existential,
            ExistentialNegated,
            Universal,
            UniversalNegated,
            DoubleNegation,
            PossibilityNegated,
            NecessityNegated,
        ],
        [
            # branching rules
            ConjunctionNegated,
            Disjunction, 
            MaterialConditional, 
            MaterialBiconditional,
            MaterialBiconditionalNegated,
            Conditional,
            Biconditional,
            BiconditionalNegated,
        ],
        [
            # world creation rules 1
            Possibility,
        ],
        [
            # world creation rules 2
            Necessity,
        ],
    ]