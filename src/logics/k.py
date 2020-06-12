# -*- coding: utf-8 -*-
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

class Meta(object):

    title    = 'Kripke Normal Modal Logic'
    category = 'Bivalent Modal'

    description = 'Base normal modal logic with no access relation restrictions'

    tags = ['bivalent', 'modal', 'first-order']
    
    category_display_order = 1

import logic, examples, helpers
from logic import negate, negative, NotImplementedError
from . import fde

Identity  = logic.get_system_predicate('Identity')
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

    #: The admissible values
    truth_values = set(['F', 'T'])

    #: A set of pairs of worlds.
    access = set()

    #: The domain of constants.
    constants = set()

    #: A map from worlds to their frame.
    frames = {}

    truth_values_list = ['F', 'T']

    unassigned_value = 'F'

    nvals = {
        'F': 0,
        'T': 1,
    }
    cvals = {
        1: 'T',
        0: 'F',
    }

    # WIP - Generating "objects" like k-constants for a domain, dentation, and
    #       predicate "property" extensions.
    #
    #       With the current implemtation of how values are set and checked
    #       dynamically for integrity, we can't easily generate a useful
    #       domain until we know the model is finished.
    #
    #       For now, the purpose of this WIP feature is merely informational.

    class Denotum(object):
        pass

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

        # TODO: WIP
        domain = set()
        denotation = {}

        def __init__(self, world):

            self.world = world
            self.atomics = {}
            self.opaques = {}
            self.extensions = {Identity: set(), Existence: set()}
            # Track the anti-extensions to ensure integrity
            self.anti_extensions = {}

            # TODO: WIP
            self.denotation = {}
            self.domain = set()
            self.property_classes = {Identity: set(), Existence: set()}

        def get_data(self):
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
                                'output' : self.atomics[sentence]
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
                                'output' : self.opaques[sentence],
                            }
                            for sentence in sorted(list(self.opaques.keys()))
                        ]
                    },
                    # TODO: include (instead?) domain and property class data
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
                                        'output' : self.extensions[predicate],
                                    }
                                ]
                            }
                            for predicate in sorted(list(self.extensions.keys()))
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
            #return cmp(self.world, other.world)
            return (self.world > other.world) - (self.world < other.world)

    def __init__(self):

        super(Model, self).__init__()

        self.frames = {}
        self.access = set()

        self.predicates = set([Identity, Existence])
        self.constants = set()
        self.fde = fde.Model()

        # ensure there is a w0
        self.world_frame(0)

    def value_of_operated(self, sentence, **kw):
        """
        The value of a sentence with a truth-functional operator `w` is determined by
        the values of its operands at `w` according to the following tables.

        //truth_tables//k//
        """
        if self.is_sentence_opaque(sentence):
            return self.value_of_opaque(sentence, **kw)
        elif sentence.operator in self.modal_operators:
            return self.value_of_modal(sentence, **kw)
        return super(Model, self).value_of_operated(sentence, **kw)

    def value_of_predicated(self, sentence, **kw):
        """
        A sentence for predicate `P` is true at `w` iff the tuple of the parameters
        is in the extension of `P` at `w`.
        """
        for param in sentence.parameters:
            if param not in self.constants:
                raise Model.DenotationError('Parameter {0} is not in the constants'.format(str(param)))
        if tuple(sentence.parameters) in self.get_extension(sentence.predicate, **kw):
            return 'T'
        return 'F'

    def value_of_existential(self, sentence, **kw):
        """
        An existential sentence is true at `w`, just when the sentence resulting in the
        subsitution of some constant in the domain for the variable is true at `w`.
        """
        si = sentence.sentence
        v = sentence.variable
        for c in self.constants:
            r = si.substitute(c, v)
            if self.value_of(r, **kw) == 'T':
                return 'T'
        return 'F'

    def value_of_universal(self, sentence, **kw):
        """
        A universal sentence is true at `w`, just when the sentence resulting in the
        subsitution of each constant in the domain for the variable is true at `w`.
        """
        si = sentence.sentence
        v = sentence.variable
        for c in self.constants:
            r = si.substitute(c, v)
            if self.value_of(r, **kw) == 'F':
                return 'F'
        return 'T'

    def value_of_possibility(self, sentence, world=0, **kw):
        """
        A possibility sentence is true at `w` iff its operand is true at `w'` for
        some `w'` such that `<w, w'>` in the access relation.
        """
        for w2 in self.visibles(world):
            if self.value_of(sentence.operand, world=w2, **kw) == 'T':
                return 'T'
        return 'F'

    def value_of_necessity(self, sentence, world=0, **kw):
        """
        A possibility sentence is true at `w` iff its operand is true at `w'` for
        each `w'` such that `<w, w'>` is in the access relation.
        """
        for w2 in self.visibles(world):
            if self.value_of(sentence.operand, world=w2, **kw) == 'F':
                return 'F'
        return 'T'

    def is_countermodel_to(self, argument):
        """
        A model is a countermodel for an argument iff the value of each premise
        is **T** at `w0` and the value of the conclusion is **F** at `w0`.
        """
        for premise in argument.premises:
            if self.value_of(premise, world=0) != 'T':
                return False
        return self.value_of(argument.conclusion, world=0) == 'F'

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
                'values'          : [frame.get_data() for frame in sorted(self.frames.values())]
            }
        }

    def read_branch(self, branch):
        for node in branch.get_nodes():
            self.read_node(node)
        self.finish()

    def read_node(self, node):
        if node.has('sentence'):
            sentence = node.props['sentence']
            world = node.props['world']
            if world == None:
                world = 0
            if self.is_sentence_opaque(sentence):
                self.set_opaque_value(sentence, 'T', world=world)
            elif self.is_sentence_literal(sentence):
                self.set_literal_value(sentence, 'T', world=world)
            self.predicates.update(node.predicates())
        elif node.has('world1') and node.has('world2'):
            self.add_access(node.props['world1'], node.props['world2'])

    def finish(self):
        # track all atomics and opaques
        atomics = set()
        opaques = set()

        for world in self.frames:

            frame = self.world_frame(world)
            atomics.update(frame.atomics.keys())
            opaques.update(frame.opaques.keys())

            # TODO: WIP
            self.generate_denotation(world)
            self.generate_property_classes(world)

            for predicate in self.predicates:
                self.agument_extension_with_identicals(predicate, world)
            self.ensure_self_identity(world)
            self.ensure_self_existence(world)

        # make sure each atomic and opaque is assigned a value in each frame
        for world in self.frames:
            frame = self.world_frame(world)
            for s in atomics:
                if s not in frame.atomics:
                    self.set_literal_value(s, self.unassigned_value, world=world)
            for s in opaques:
                if s not in frame.opaques:
                    self.set_opaque_value(s, self.unassigned_value, world=world)

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

    def generate_denotation(self, world):
        #: TODO: WIP
        frame = self.world_frame(world)
        todo = set(self.constants)
        for c1 in self.constants:
            if c1 in todo:
                o = Model.Denotum()
                frame.domain.add(o)
                frame.denotation[c1] = o
                todo.remove(c1)
                for c2 in self.get_identicals(c1, world=world):
                    frame.denotation[c2] = o
                    todo.remove(c2)
        assert not todo

    def generate_property_classes(self, world):
        # TODO: WIP
        frame = self.world_frame(world)
        for predicate in self.predicates:
            # Skip identity
            if predicate == Identity:
                continue
            frame.property_classes[predicate] = set()
            property_class = frame.property_classes[predicate]
            for params in self.get_extension(predicate, world=world):
                ptuple = tuple(self.get_denotum(param, world=world) for param in params)
                property_class.add(ptuple)

    def get_identicals(self, c, **kw):
        identity_extension = self.get_extension(Identity, **kw)
        identicals = set()
        for params in identity_extension:
            if c in params:
                identicals.update(params)
        identicals.discard(c)
        return identicals

    def is_sentence_literal(self, sentence):
        if sentence.operator == 'Negation' and self.is_sentence_opaque(sentence.operand):
            return True
        return sentence.is_literal()

    def set_literal_value(self, sentence, value, **kw):
        if self.is_sentence_opaque(sentence):
            self.set_opaque_value(sentence, value, **kw)
        elif sentence.is_operated() and sentence.operator == 'Negation':
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
        # We might have a quantified opaque sentence, in which case we will need
        # to still check every subsitution, so we want the constants.
        # NB: in FDE we added the atomics to all_atomics, but we don't have that
        #     here since we do frames -- will that be a problem?
        self.constants.update(sentence.constants())
        self.predicates.update(sentence.predicates())
        frame.opaques[sentence] = value

    def set_atomic_value(self, sentence, value, world=0, **kw):
        frame = self.world_frame(world)
        if sentence in frame.atomics and frame.atomics[sentence] != value:
            raise Model.ModelValueError('Inconsistent value for sentence {0}'.format(str(sentence)))
        frame.atomics[sentence] = value

    def set_predicated_value(self, sentence, value, **kw):
        predicate = sentence.predicate
        if predicate not in self.predicates:
            self.predicates.add(predicate)
        params = tuple(sentence.parameters)
        for param in params:
            if param.is_constant():
                self.constants.add(param)
        extension = self.get_extension(predicate, **kw)
        anti_extension = self.get_anti_extension(predicate, **kw)
        if value == 'F':
            if params in extension:
                raise Model.ModelValueError('Cannot set value {0} for tuple {1} already in extension'.format(str(value), str(params)))
            anti_extension.add(params)
        if value == 'T':
            if params in anti_extension:
                raise Model.ModelValueError('Cannot set value {0} for tuple {1} already in anti-extension'.format(str(value), str(params)))
            extension.add(params)

    def get_extension(self, predicate, world=0, **kw):
        frame = self.world_frame(world)
        if predicate not in self.predicates:
            self.predicates.add(predicate)
        if predicate not in frame.extensions:
            frame.extensions[predicate] = set()
        if predicate not in frame.anti_extensions:
            frame.anti_extensions[predicate] = set()
        return frame.extensions[predicate]

    def get_anti_extension(self, predicate, world=0, **kw):
        frame = self.world_frame(world)
        if predicate not in self.predicates:
            self.predicates.add(predicate)
        if predicate not in frame.extensions:
            frame.extensions[predicate] = set()
        if predicate not in frame.anti_extensions:
            frame.anti_extensions[predicate] = set()
        return frame.anti_extensions[predicate]

    def get_domain(self, world=0, **kw):
        # TODO: wip
        return self.world_frame(world).domain

    def get_denotation(self, world=0, **kw):
        # TODO: wip
        return self.world_frame(world).denotation

    def get_denotum(self, c, world=0, **kw):
        # TODO: wip
        den = self.get_denotation(world=world)
        try:
            return den[c]
        except KeyError:
            raise Model.DenotationError('Constant {0} does not have a reference at w{1}'.format(str(c), str(world)))

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

    def value_of_modal(self, sentence, **kw):
        operator = sentence.operator
        if operator == 'Possibility':
            return self.value_of_possibility(sentence, **kw)
        elif operator == 'Necessity':
            return self.value_of_necessity(sentence, **kw)
        else:
            raise NotImplementedError(NotImplemented)

    def value_of_quantified(self, sentence, **kw):
        q = sentence.quantifier
        if q == 'Existential':
            return self.value_of_existential(sentence, **kw)
        elif q == 'Universal':
            return self.value_of_universal(sentence, **kw)
        return super(Model, self).value_of_quantified(sentence, **kw)

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

    neg_branchable = set(['Conjunction', 'Material Biconditional', 'Biconditional'])
    pos_branchable = set(['Disjunction', 'Material Conditional', 'Conditional'])

    @classmethod
    def build_trunk(cls, tableau, argument):
        """
        To build the trunk for an argument, add a node with each premise, with
        world *w0*, followed by a node with the negation of the conclusion
        with world *w0*.
        """
        branch = tableau.branch()
        for premise in argument.premises:
            branch.add({'sentence': premise, 'world': 0})
        branch.add({'sentence': negate(argument.conclusion), 'world': 0})

    @classmethod
    def branching_complexity(cls, node):
        if not node.has('sentence'):
            return 0
        sentence = node.props['sentence']
        operators = list(sentence.operators())
        last_is_negated = False
        complexity = 0
        while len(operators):
            operator = operators.pop(0)
            if operator == 'Assertion':
                continue
            if operator == 'Negation':
                if last_is_negated:
                    last_is_negated = False
                    continue
                last_is_negated = True
            elif last_is_negated:
                if operator in cls.neg_branchable:
                    complexity += 1
                    last_is_negated = False
            elif operator in cls.pos_branchable:
                complexity += 1
        return complexity

class IsModal(object):
    modal = True

class TableauxRules(object):
    """
    Rules for modal operators employ *world* indexes as well access-type
    nodes. The world indexes are transparent for the rules for classical
    connectives.
    """

    class ContradictionClosure(IsModal, logic.TableauxSystem.ClosureRule):
        """
        A branch closes when a sentence and its negation both appear on a node **with the
        same world** on the branch.
        """

        def setup(self):
            self.add_helper('checker', helpers.NodeTargetCheckHelper(self))

        def check_for_target(self, node, branch):
            if node.has('sentence'):
                nnode = branch.find({'sentence': negative(self.sentence(node)), 'world': node.props['world']})
                if nnode:
                    return {'nodes': set([node, nnode]), 'type': 'Nodes'}
                
        def applies_to_branch(self, branch):
            return self.checker.cached_target(branch)

        def example_nodes(self, branch):
            a = logic.atomic(0, 0)
            w = 0 if self.modal else None
            return [
                {'sentence':        a , 'world': w},
                {'sentence': negate(a), 'world': w},
            ]

    class SelfIdentityClosure(IsModal, logic.TableauxSystem.ClosureRule):
        """
        A branch closes when a sentence of the form P{~a = a} appears on the branch *at any world*.
        """

        def setup(self):
            self.add_helper('checker', helpers.NodeTargetCheckHelper(self))

        def check_for_target(self, node, branch):
            if node.has('sentence'):
                s = self.sentence(node)
                if s.operator == 'Negation' and s.operand.predicate == Identity:
                    a, b = s.operand.parameters
                    if a == b:
                        return {'node': node, 'type': 'Node'}

        def applies_to_branch(self, branch):
            return self.checker.cached_target(branch)

        def example_node(self, branch):
            s = negate(examples.self_identity())
            w = 0 if self.modal else None
            return {'sentence': s, 'world': w}

    class NonExistenceClosure(IsModal, logic.TableauxSystem.ClosureRule):
        """
        A branch closes when a sentence of the form P{~!a} appears on the branch *at any world*.
        """

        def setup(self):
            self.add_helper('checker', helpers.NodeTargetCheckHelper(self))

        def check_for_target(self, node, branch):
            if node.has('sentence'):
                s = self.sentence(node)
                if s.operator == 'Negation' and s.operand.predicate == Existence:
                    return {'node': node, 'type': 'Node'}

        def applies_to_branch(self, branch):
            return self.checker.cached_target(branch)

        def example_node(self, branch):
            s = negate(examples.existence())
            w = 0 if self.modal else None
            return {'sentence': s, 'world': w}

    class DoubleNegation(IsModal, logic.TableauxSystem.FilterNodeRule):
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

    class Assertion(IsModal, logic.TableauxSystem.FilterNodeRule):
        """
        From an unticked assertion node *n* with world *w* on a branch *b*,
        add a node to *b* with the operand of *n* and world *w*, then tick *n*.
        """

        operator = 'Assertion'

        def apply_to_node(self, node, branch):
            w = node.props['world']
            s = self.sentence(node)
            branch.add({'sentence': s.operand, 'world': w}).tick(node)

    class AssertionNegated(IsModal, logic.TableauxSystem.FilterNodeRule):
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

    class Conjunction(IsModal, logic.TableauxSystem.FilterNodeRule):
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

    class ConjunctionNegated(IsModal, logic.TableauxSystem.FilterNodeRule):
        """
        From an unticked negated conjunction node *n* with world *w* on a branch *b*, for each
        conjunct, make a new branch *b'* from *b* and add a node with *w* and the negation of
        the conjunct to *b*, then tick *n*.
        """

        negated  = True
        operator = 'Conjunction'

        branch_level = 2

        def apply_to_node(self, node, branch):
            s = self.sentence(node)
            w = node.props['world']
            b1 = branch
            b2 = self.branch(branch)
            b1.add({'sentence': negate(s.lhs), 'world': w}).tick(node)
            b2.add({'sentence': negate(s.rhs), 'world': w}).tick(node)

        def score_candidate_map(self, target):
            branch = target['branch']
            node = target['node']
            s = self.sentence(node)
            w = node.props['world']
            return {
                'b1': branch.has({'sentence': s.lhs, 'world': w}),
                'b2': branch.has({'sentence': s.rhs, 'world': w}),
            }

    class Disjunction(IsModal, logic.TableauxSystem.FilterNodeRule):
        """
        From an unticked disjunction node *n* with world *w* on a branch *b*, for each disjunct,
        make a new branch *b'* from *b* and add a node with the disjunct and world *w* to *b'*,
        then tick *n*.
        """

        operator = 'Disjunction'

        branch_level = 2

        def apply_to_node(self, node, branch):
            s = self.sentence(node)
            w = node.props['world']
            b1 = branch
            b2 = self.branch(branch)
            b1.add({'sentence': s.lhs, 'world': w}).tick(node)
            b2.add({'sentence': s.rhs, 'world': w}).tick(node)

        def score_candidate_map(self, target):
            branch = target['branch']
            node = target['node']
            s = self.sentence(node)
            w = node.props['world']
            return {
                'b1': branch.has({'sentence': negative(s.lhs), 'world': w}),
                'b2': branch.has({'sentence': negative(s.rhs), 'world': w}),
            }

    class DisjunctionNegated(IsModal, logic.TableauxSystem.FilterNodeRule):
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

    class MaterialConditional(IsModal, logic.TableauxSystem.FilterNodeRule):
        """
        From an unticked material conditional node *n* with world *w* on a branch *b*, make two
        new branches *b'* and *b''* from *b*, add a node with world *w* and the negation of the
        antecedent to *b'*, and add a node with world *w* and the conequent to *b''*, then tick
        *n*.
        """

        operator = 'Material Conditional'

        branch_level = 2

        def apply_to_node(self, node, branch):
            s = self.sentence(node)
            w = node.props['world']
            b1 = branch
            b2 = self.branch(branch)
            b1.add({'sentence': negate(s.lhs), 'world': w}).tick(node)
            b2.add({'sentence':        s.rhs , 'world': w}).tick(node)

        def score_candidate_map(self, target):
            branch = target['branch']
            node = target['node']
            s = self.sentence(node)
            w = node.props['world']
            return {
                'b1': branch.has({'sentence':          s.lhs , 'world': w}),
                'b2': branch.has({'sentence': negative(s.rhs), 'world': w}),
            }

    class MaterialConditionalNegated(IsModal, logic.TableauxSystem.FilterNodeRule):
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

    class MaterialBiconditional(IsModal, logic.TableauxSystem.FilterNodeRule):
        """
        From an unticked material biconditional node *n* with world *w* on a branch *b*, make
        two new branches *b'* and *b''* from *b*, add two nodes with world *w* to *b'*, one with
        the negation of the antecedent and one with the negation of the consequent, and add two
        nodes with world *w* to *b''*, one with the antecedent and one with the consequent, then
        tick *n*.
        """

        operator = 'Material Biconditional'

        branch_level = 2

        def apply_to_node(self, node, branch):
            s = self.sentence(node)
            w = node.props['world']
            b1 = branch
            b2 = self.branch(branch)
            b1.update([
                {'sentence': negate(s.lhs), 'world': w}, 
                {'sentence': negate(s.rhs), 'world': w},
            ]).tick(node)
            b2.update([
                {'sentence': s.rhs, 'world': w}, 
                {'sentence': s.lhs, 'world': w},
            ]).tick(node)

        def score_candidate_map(self, target):
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

    class MaterialBiconditionalNegated(IsModal, logic.TableauxSystem.FilterNodeRule):
        """
        From an unticked negated material biconditional node *n* with world *w* on a branch *b*,
        make two new branches *b'* and *b''* from *b*, add two nodes with *w* to *b'*, one with
        the antecedent and the other with the negation of the consequent, and add two nodes with
        *w* to *b''*, one with the negation of the antecedent and the other with the consequent,
        then tick *n*.
        """

        negated  = True
        operator = 'Material Biconditional'

        branch_level = 2

        def apply_to_node(self, node, branch):
            s = self.sentence(node)
            w = node.props['world']
            b1 = branch
            b2 = self.branch(branch)
            b1.update([
                {'sentence':        s.lhs , 'world': w},
                {'sentence': negate(s.rhs), 'world': w},
            ]).tick(node)
            b2.update([
                {'sentence': negate(s.rhs), 'world': w},
                {'sentence':        s.lhs , 'world': w},
            ]).tick(node)

        def score_candidate_map(self, target):
            branch = target['branch']
            node = target['node']
            s = self.sentence(node)
            w = node.props['world']
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

    class Existential(IsModal, logic.TableauxSystem.FilterNodeRule):
        """
        From an unticked existential node *n* with world *w* on a branch *b*, quantifying over
        variable *v* into sentence *s*, add a node with world *w* to *b* with the substitution
        into *s* of *v* with a constant new to *b*, then tick *n*.
        """

        quantifier = 'Existential'

        def setup(self):
            self.add_helper('max_constants', helpers.MaxConstantsTracker(self))
            self.add_helper('quit_flagger', helpers.QuitFlagHelper(self))

        def get_target_for_node(self, node, branch):

            w = node.props['world']

            if not self._should_apply(branch, w):
                if not self.quit_flagger.has_flagged(branch):
                    return {'flag': True}
                return

            s = self.sentence(node)
            v = s.variable
            c = branch.new_constant()
            si = s.sentence
            r = si.substitute(c, v)

            return {
                'sentence' : r,
                'world'    : w,
                'constant' : c,
            }

        def apply_to_node_target(self, node, branch, target):
            if 'flag' in target and target['flag']:
                branch.add(self.max_constants.quit_flag(branch))
            else:
                branch.add({'sentence': target['sentence'], 'world': target['world']}).tick(node)

        # private util

        def _should_apply(self, branch, world):
            return not self.max_constants.max_constants_exceeded(branch, world)

        # this actually hurts
        #def score_candidate(self, target):
        #    return -1 * len(self.sentence(target['node']).quantifiers())

    class ExistentialNegated(IsModal, logic.TableauxSystem.FilterNodeRule):
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
            sq = logic.quantify(self.convert_to, v, negate(si))
            branch.add({'sentence': sq, 'world': w}).tick(node)

    class Universal(IsModal, logic.TableauxSystem.FilterNodeRule):
        """
        From a universal node with world *w* on a branch *b*, quantifying over variable *v* into
        sentence *s*, result *r* of substituting a constant *c* on *b* (or a new constant if none
        exists) for *v* into *s* does not appear at *w* on *b*, add a node with *w* and *r* to
        *b*. The node *n* is never ticked.
        """

        quantifier = 'Universal'

        
        def setup(self):
            self.add_timer(
                'in_len_constants'        ,
                'in_get_targets_for_nodes',
                'in_new_constant'         ,
                'in_node_examime'         ,
                'in_should_apply'         ,
            )
            self.add_helper('max_constants', helpers.MaxConstantsTracker(self))
            self.add_helper('applied_constants', helpers.NodeAppliedConstants(self))
            self.add_helper('quit_flagger', helpers.QuitFlagHelper(self))

        def get_targets_for_node(self, node, branch):
            w = node.props['world']
            with self.timers['in_should_apply']:
                should_apply = self._should_apply(node, branch)
            if not should_apply:
                if self.max_constants.max_constants_exceeded(branch, w):
                    if not self.quit_flagger.has_flagged(branch):
                        return [{'flag': True}]
                return
            with self.timers['in_get_targets_for_nodes']:
                with self.timers['in_node_examime']:
                    s = self.sentence(node)
                    si = s.sentence
                    v = s.variable
                    constants = self.applied_constants.get_unapplied(node, branch)
                targets = list()
                if constants:
                    # if the branch already has a constant, find all the substitutions not
                    # already on the branch.
                    with self.timers['in_len_constants']:
                        for c in constants:
                            r = si.substitute(c, v)
                            target = {'sentence': r, 'world': w}
                            if not branch.has(target):
                                target['constant'] = c
                                targets.append(target)
                else:
                    # if the branch does not have any constants, pick a new one
                    with self.timers['in_new_constant']:
                        c = branch.new_constant()
                        r = si.substitute(c, v)
                        target = {'sentence': r, 'world': w, 'constant': c}
                        targets.append(target)
            return targets

        def score_candidate(self, target):
            node_apply_count = self.node_application_count(target['node'], target['branch'])
            return float(1 / (node_apply_count + 1))

        def apply_to_node_target(self, node, branch, target):
            if 'flag' in target and target['flag']:
                branch.add(self.max_constants.quit_flag(branch))
            else:
                branch.add({'sentence': target['sentence'], 'world': target['world']})

        def example_node(self, branch):
            s = examples.quantified(self.quantifier)
            w = 0 if self.modal else None
            return {'sentence': s, 'world': w}

        # private util

        def _should_apply(self, node, branch):
            if self.max_constants.max_constants_exceeded(branch, node.props['world']):
                return False
            # Apply if there are no constants on the branch
            if not branch.constants():
                return True
            # Apply if we have tracked a constant that we haven't applied to.
            if self.applied_constants.get_unapplied(node, branch):
                return True

    class UniversalNegated(ExistentialNegated):
        """
        From an unticked negated universal node *n* with world *w* on a branch *b*,
        quantifying over variable *v* into sentence *s*, add an existentially
        quantified node to *b* with world *w* over *v* into the negation of *s*,
        then tick *n*.
        """

        quantifier = 'Universal'
        convert_to = 'Existential'

    class Possibility(IsModal, logic.TableauxSystem.FilterNodeRule):
        """
        From an unticked possibility node with world *w* on a branch *b*, add a node with a
        world *w'* new to *b* with the operand of *n*, and add an access-type node with
        world1 *w* and world2 *w'* to *b*, then tick *n*.
        """

        operator = 'Possibility'

        def setup(self):
            self.add_helper('applied_sentences', helpers.AppliedSentenceCounter(self))
            self.add_helper('max_worlds', helpers.MaxWorldsTracker(self))
            self.add_helper('quit_flagger', helpers.QuitFlagHelper(self))

        def is_potential_node(self, node, branch):
            if self.quit_flagger.has_flagged(branch):
                return False
            return super(TableauxRules.Possibility, self).is_potential_node(node, branch)

        def get_target_for_node(self, node, branch):
            if not self._should_apply(branch):
                if not self.quit_flagger.has_flagged(branch):
                    return {'flag': True}
                return
            s  = self.sentence(node)
            si = s.operand
            w1 = node.props['world']
            return {'sentence': si, 'world1': w1}

        def apply_to_node_target(self, node, branch, target):
            if 'flag' in target and target['flag']:
                branch.add(self.max_worlds.quit_flag(branch))
            else:
                si = target['sentence']
                w1 = target['world1']
                w2 = branch.new_world()
                branch.update([
                    {'sentence': si, 'world': w2},
                    {'world1': w1, 'world2': w2},
                ]).tick(node)

        def score_candidate(self, target):
            if 'flag' in target and target['flag']:
                return 1
            # override
            branch = target['branch']
            s = self.sentence(target['node'])
            si = s.operand

            # Don't bother checking for closure since we will always have a new world

            track_count = self.applied_sentences.get_count(si, branch)
            if track_count == 0:
                return 1

            return -1 * self.max_worlds.modal_complexity(s) * track_count

        def group_score(self, target):

            if self.score_candidate(target) > 0:
                return 1

            branch = target['branch']
            s = self.sentence(target['node'])
            si = s.operand

            return -1 * self.applied_sentences.get_count(si, branch)

        # private util

        def _should_apply(self, branch):
            return not self.max_worlds.max_worlds_exceeded(branch)

    class PossibilityNegated(IsModal, logic.TableauxSystem.FilterNodeRule):
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
            sn = logic.operate(self.convert_to, [negate(s.operand)])
            branch.add({'sentence': sn, 'world': w}).tick(node)

    class Necessity(IsModal, logic.TableauxSystem.FilterNodeRule):
        """
        From a necessity node *n* with world *w1* and operand *s* on a branch *b*, for any
        world *w2* such that an access node with w1,w2 is on *b*, if *b* does not have a node
        with *s* at *w2*, add it to *b*. The node *n* is never ticked.
        """

        operator = 'Necessity'

        def setup(self):
            self.add_timer(
                'get_targets_for_node',
                'make_target'         ,
                'check_target_condtn1',
                'check_target_condtn2',
            )
            self.add_helper('max_worlds', helpers.MaxWorldsTracker(self))
            self.add_helper('node_worlds_applied', helpers.AppliedNodesWorldsTracker(self))
            self.add_helper('quit_flagger', helpers.QuitFlagHelper(self))

        def is_potential_node(self, node, branch):
            if self.quit_flagger.has_flagged(branch):
                return False
            return super(TableauxRules.Necessity, self).is_potential_node(node, branch)
            
        def get_targets_for_node(self, node, branch):

            # Check for max worlds reached
            if not self._should_apply(branch):
                if not self.quit_flagger.has_flagged(branch):
                    return [{'flag': True}]
                return

            # Only count least-applied-to nodes
            if not self._is_least_applied_to(node, branch):
                return

            with self.timers['get_targets_for_node']:
                targets = list()
                worlds = branch.worlds()
                s = self.sentence(node)
                si = s.operand
                w1 = node.props['world']
                for anode in branch.find_all({'world1': w1}):
                    w2 = anode.props['world2']
                    if self.node_worlds_applied.is_applied(node, w2, branch):
                        continue
                    with self.timers['check_target_condtn1']:
                        meets_condtn = branch.has_access(w1, w2)
                    if not meets_condtn:
                        continue
                    with self.timers['check_target_condtn2']:
                        meets_condtn = not branch.has({'sentence': si, 'world': w2})
                    if meets_condtn:
                        with self.timers['make_target']:
                            anode = branch.find({'world1': w1, 'world2': w2})
                            targets.append({
                                'sentence' : si,
                                'world'    : w2,
                                'nodes'    : set([node, anode]),
                                'type'     : 'Nodes',
                            })
            return targets

        def score_candidate(self, target):

            if 'flag' in target and target['flag']:
                return 1
            # We are already restricted to least-applied-to nodes by ``get_targets_for_node()``

            # Check for closure
            if target['branch'].has({'sentence': negative(target['sentence']), 'world': target['world']}):
                return 1

            # not applied to yet
            node_apply_count = self.node_application_count(target['node'].id, target['branch'].id)
            if node_apply_count == 0:
                return 1

            # Pick the least branching complexity
            return -1 * self.branching_complexity(target['node'])

            # greatest world?
            # / max(1, target['world'])

            # Modal complexity?
            #return -1 * len(target['sentence'].operators())

        def group_score(self, target):

            if self.score_candidate(target) > 0:
                return 1

            return -1 * self.node_application_count(target['node'].id, target['branch'].id)
            #return -1 * min(target['track_count'], self.branching_complexity(target['node']))

        def apply_to_node_target(self, node, branch, target):
            if 'flag' in target and target['flag']:
                branch.add(self.max_worlds.quit_flag(branch))
            else:
                branch.add({'sentence': target['sentence'], 'world': target['world']})

        def example_nodes(self, branch):
            s = logic.operate(self.operator, [logic.atomic(0, 0)])
            return [
                {'sentence': s, 'world': 0},
                {'world1': 0, 'world2': 1},
            ]

        # private util

        def _should_apply(self, branch):
            return not self.max_worlds.max_worlds_exceeded(branch)

        def _is_least_applied_to(self, node, branch):
            node_apply_count = self.node_application_count(node.id, branch.id)
            min_apply_count = self.min_application_count(branch.id)
            return min_apply_count >= node_apply_count

    class NecessityNegated(PossibilityNegated):
        """
        From an unticked negated necessity node *n* with world *w* on a branch *b*, add a
        possibility node whose operand is the negation of the negated necessitatum of *n*,
        then tick *n*.
        """

        operator   = 'Necessity'
        convert_to = 'Possibility'

    class IdentityIndiscernability(IsModal, logic.TableauxSystem.FilterNodeRule):
        """
        From an unticked node *n* having an Identity sentence *s* at world *w* on an open branch *b*,
        and a predicated node *n'* whose sentence *s'* has a constant that is a parameter of *s*,
        if the replacement of that constant for the other constant of *s* is a sentence that does
        not appear on *b* at *w*, then add it.
        """

        predicate = 'Identity'

        def setup(self):
            self.add_helper('predicated_nodes', helpers.PredicatedNodesTracker(self))

        def get_targets_for_node(self, node, branch):
            pnodes = self.predicated_nodes.get_predicated(branch)
            targets = list()
            w = node.props['world']
            pa, pb = node.props['sentence'].parameters
            # find a node n with a sentence s having one of those parameters p.
            for n in pnodes:
                s = n.props['sentence']
                if pa in s.parameters:
                    p = pa
                    p1 = pb
                elif pb in s.parameters:
                    p = pb
                    p1 = pa
                else:
                    # This continue statement does not register as covered. this line is covered
                    # by test_identity_indiscernability_not_applies
                    continue # pragma: no cover
                # let s1 be the replacement of p with the other parameter p1 into s.
                params = [p1 if param == p else param for param in s.parameters]
                s1 = logic.predicated(s.predicate, params)
                # since we have SelfIdentityClosure, we don't need a = a
                if s.predicate != Identity or params[0] != params[1]:
                    # if <s1,w> does not yet appear on b, ...
                    if not branch.has({'sentence': s1, 'world': w}):
                        # then the rule applies to <s',w,b>
                        target = {'sentence': s1, 'world': w, 'nodes': set([node, n]), 'type': 'Nodes'}
                        targets.append(target)
            return targets

        def apply_to_node_target(self, node, branch, target):
            branch.add({'sentence': target['sentence'], 'world': target['world']})

        def example_nodes(self, branch):
            world = 0 if self.modal else None
            return [
                {'sentence': examples.predicated(), 'world': world},
                {'sentence': examples.identity(),   'world': world},
            ]

    closure_rules = [
        ContradictionClosure,
        SelfIdentityClosure,
        NonExistenceClosure,
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
            DoubleNegation,
            PossibilityNegated,
            NecessityNegated,
            ExistentialNegated,
            UniversalNegated,
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
            # modal operator rules
            Necessity,
            Possibility,
        ],
        [
            Existential,
            Universal,
        ],
    ]