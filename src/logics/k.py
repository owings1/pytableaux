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
    title = 'Kripke Normal Modal Logic'
    description = 'Base normal modal logic with no access relation restrictions'
    tags = ['bivalent', 'modal', 'first-order']
    category = 'Bivalent Modal'
    category_display_order = 1

import logic, examples
from logic import negate, negative, operate, quantify, atomic, constant, predicated, NotImplementedError
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

    #: The admissable values
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

    # wip: real domain (fixed)
    domain = set()
    denotation = {}

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
            self.extensions = {Identity: set(), Existence: set()}

            # Track the anti-extensions to ensure integrity
            self.anti_extensions = {}

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

        # TODO: implement real domain and denotation, think of identity necessity
        self.domain = set()
        self.denotation = {}

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

    def get_identicals(self, c, **kw):
        identity_extension = self.get_extension(Identity, **kw)
        identicals = set()
        for params in identity_extension:
            if c in params:
                identicals.update(params)
        if c in identicals:
            identicals.remove(c)
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

# TODO: Make a pattern for the helpers that makes it
#       easier to register their callbacks.

class MaxWorldsTracker(object):

    max_worlds_operators = set(Model.modal_operators)

    def __init__(self, rule):
        self.rule = rule
        # Track the maximum number of worlds that should be on the branch
        # so we can halt on infinite branches.
        self.branch_max_worlds = {}

    def after_trunk_build(self, branches):
        """
        Must be called by rule.
        """
        for branch in branches:
            origin = branch.origin()
            # In most cases, we will have only one origin branch.
            if origin.id in self.branch_max_worlds:
                return
            self.branch_max_worlds[origin.id] = self.compute_max_worlds(branch)

    def compute_max_worlds(self, branch):
        # Project the maximum number of worlds for a branch (origin) as
        # the number of worlds already on the branch + the number of modal
        # operators + 1.
        node_needed_worlds = sum([
            self.compute_needed_worlds_for_node(node, branch)
            for node in branch.get_nodes()
        ])
        return len(branch.worlds()) + node_needed_worlds + 1

    def compute_needed_worlds_for_node(self, node, branch):
        # we only care about unticked nodes, since ticked nodes will have
        # already created any worlds.
        if not branch.is_ticked(node) and node.has('sentence'):
            ops = node.props['sentence'].operators()
            return len([o for o in ops if o in self.max_worlds_operators])
        return 0

    def get_max_worlds(self, branch):
        origin = branch.origin()
        if origin.id in self.branch_max_worlds:
            return self.branch_max_worlds[origin.id]

    def max_worlds_reached(self, branch):
        # If we have already reached or exceeded the max number of worlds
        # projected for the branch (origin).
        max_worlds = self.get_max_worlds(branch)
        return max_worlds != None and len(branch.worlds()) >= max_worlds

    def max_worlds_exceeded(self, branch):
        # If we have exceeded the max number of worlds projected for
        # the branch (origin).
        max_worlds = self.get_max_worlds(branch)
        if max_worlds != None and len(branch.worlds()) > max_worlds:
            print(('max worlds exceeded', self.rule.name, max_worlds))
            return True

class MaxConstantsTracker(object):

    def __init__(self, rule):
        self.rule = rule
        # Track the maximum number of constats that should be on the branch
        # (per world) so we can halt on infinite branches.
        self.branch_max_constants = {}
        # Track the constants at each world
        self.world_constants = {}

    def after_trunk_build(self, branches):
        """
        Must be called by rule implementation.
        """
        for branch in branches:
            origin = branch.origin()
            # In most cases, we will have only one origin branch.
            if origin.id in self.branch_max_constants:
                return
            self.branch_max_constants[origin.id] = self._compute_max_constants(branch)

    def register_branch(self, branch, parent):
        """
        Must be called by rule implementation.
        """
        if parent != None and parent.id in self.world_constants:
            self.world_constants[branch.id] = {
                world : set(self.world_constants[parent.id][world])
                for world in self.world_constants[parent.id]
            }
        else:
            self.world_constants[branch.id] = {}

    def register_node(self, node, branch):
        """
        Must be called by rule implementation.
        """
        if node.has('sentence'):
            world = node.props['world']
            if world == None:
                world = 0
            if world not in self.world_constants[branch.id]:
                self.world_constants[branch.id][world] = set()
            self.world_constants[branch.id][world].update(node.constants())

    def get_max_constants(self, branch):
        """
        Get the projected max number of constants (per world) for the branch.
        """
        origin = branch.origin()
        if origin.id in self.branch_max_constants:
            return self.branch_max_constants[origin.id]
        return 1

    def get_branch_constants_at_world(self, branch, world):
        """
        Get the cached set of constants at a world for the branch.
        """
        if world not in self.world_constants[branch.id]:
            self.world_constants[branch.id][world] = set()
        return self.world_constants[branch.id][world]

    def max_constants_reached(self, branch, world=0):
        """
        Whether we have already reached or exceeded the max number of constants
        projected for the branch (origin) at the given world.
        """
        max_constants = self.get_max_constants(branch)
        world_constants = self.get_branch_constants_at_world(branch, world)
        return max_constants != None and len(world_constants) >= max_constants

    def max_constants_exceeded(self, branch, world=0):
        """
        Whether we have exceeded the max number of constants projected for
        the branch (origin) at the given world.
        """
        max_constants = self.get_max_constants(branch)
        world_constants = self.get_branch_constants_at_world(branch, world)
        if max_constants != None and len(world_constants) > max_constants:
            return True

    def _compute_max_constants(self, branch):
        # Project the maximum number of constants for a branch (origin) as
        # the number of constants already on the branch (min 1) * the number of
        # quantifiers (min 1) + 1.
        node_needed_constants = sum([
            self._compute_needed_constants_for_node(node, branch)
            for node in branch.get_nodes()
        ])
        return max(1, len(branch.constants())) * max(1, node_needed_constants) + 1

    def _compute_needed_constants_for_node(self, node, branch):
        if node.has('sentence'):
            return len(node.props['sentence'].quantifiers())
        return 0

class TableauxRules(object):
    """
    Rules for modal operators employ *world* indexes as well access-type
    nodes. The world indexes are transparent for the rules for classical
    connectives.
    """

    class ContradictionClosure(logic.TableauxSystem.ClosureRule):
        """
        A branch closes when a sentence and its negation both appear on a node **with the
        same world** on the branch.
        """

        def __init__(self, *args, **opts):
            super(TableauxRules.ContradictionClosure, self).__init__(*args, **opts)
            self.safeprop('targets', {})

        def after_node_add(self, branch, node):
            super(TableauxRules.ContradictionClosure, self).after_node_add(branch, node)
            if node.has('sentence'):
                nnode = branch.find({'sentence': negative(self.sentence(node)), 'world': node.props['world']})
                if nnode:
                    self.targets[branch.id] = {'nodes': set([node, nnode]), 'type': 'Nodes'}
                
        def applies_to_branch(self, branch):
            if branch.id in self.targets:
                return self.targets[branch.id]

        def example_nodes(self, branch):
            a = atomic(0, 0)
            return [
                {'sentence':        a , 'world': 0},
                {'sentence': negate(a), 'world': 0},
            ]

    class SelfIdentityClosure(logic.TableauxSystem.ClosureRule):
        """
        A branch closes when a sentence of the form P{~a = a} appears on the branch *at any world*.
        """

        def __init__(self, *args, **opts):
            super(TableauxRules.SelfIdentityClosure, self).__init__(*args, **opts)
            self.safeprop('targets', {})

        def after_node_add(self, branch, node):
            super(TableauxRules.SelfIdentityClosure, self).after_node_add(branch, node)
            if node.has('sentence'):
                s = self.sentence(node)
                if s.operator == 'Negation' and s.operand.predicate == Identity:
                    a, b = s.operand.parameters
                    if a == b:
                        self.targets[branch.id] = {'node': node, 'type': 'Node'}

        def applies_to_branch(self, branch):
            if branch.id in self.targets:
                return self.targets[branch.id]
            return False

        def example_node(self, branch):
            s = negate(examples.self_identity())
            return {'sentence': s, 'world': 0}

    class NonExistenceClosure(logic.TableauxSystem.ClosureRule):
        """
        A branch closes when a sentence of the form P{~!a} appears on the branch *at any world*.
        """

        def __init__(self, *args, **opts):
            super(TableauxRules.NonExistenceClosure, self).__init__(*args, **opts)
            self.safeprop('targets', {})

        def after_node_add(self, branch, node):
            super(TableauxRules.NonExistenceClosure, self).after_node_add(branch, node)
            if node.has('sentence'):
                s = self.sentence(node)
                if s.operator == 'Negation' and s.operand.predicate == Existence:
                    self.targets[branch.id] = {'node': node, 'type': 'Node'}

        def applies_to_branch(self, branch):
            if branch.id in self.targets:
                return self.targets[branch.id]
            return False

        def example_node(self, branch):
            s = logic.parse('NJm')
            return {'sentence': s, 'world': 0}

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

        def __init__(self, *args, **opts):
            super(TableauxRules.Existential, self).__init__(*args, **opts)
            self.safeprop('world_consts', {})
            self.safeprop('max_constants_tracker', MaxConstantsTracker(self))

        def after_trunk_build(self, branches):
            super(TableauxRules.Existential, self).after_trunk_build(branches)
            self.max_constants_tracker.after_trunk_build(branches)

        def register_branch(self, branch, parent):
            super(TableauxRules.Existential, self).register_branch(branch, parent)
            self.max_constants_tracker.register_branch(branch, parent)

        def register_node(self, node, branch):
            super(TableauxRules.Existential, self).register_node(node, branch)
            self.max_constants_tracker.register_node(node, branch)

        def should_apply(self, branch, world):
            return not self.max_constants_tracker.max_constants_exceeded(branch, world)

        def get_target_for_node(self, node, branch):

            w = node.props['world']

            if not self.should_apply(branch, w):
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
            branch.add({'sentence': target['sentence'], 'world': target['world']}).tick(node)

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
            sq = quantify(self.convert_to, v, negate(si))
            branch.add({'sentence': sq, 'world': w}).tick(node)

    class Universal(IsModal, logic.TableauxSystem.FilterNodeRule):
        """
        From a universal node with world *w* on a branch *b*, quantifying over variable *v* into
        sentence *s*, result *r* of substituting a constant *c* on *b* (or a new constant if none
        exists) for *v* into *s* does not appear at *w* on *b*, add a node with *w* and *r* to
        *b*. The node *n* is never ticked.
        """

        quantifier = 'Universal'

        # TODO: support prenexing
        #
        #    ∀x∃y(Fx → Gy) will be infinite, but not ∃y∀x(Fx → Gy)

        def __init__(self, *args, **opts):
            super(TableauxRules.Universal, self).__init__(*args, **opts)
            self.add_timer(
                'in_len_constants'        ,
                'in_get_targets_for_nodes',
                'in_new_constant'         ,
                'in_node_examime'         ,
            )
            self.safeprop('node_states', {})
            self.safeprop('consts', {})
            self.safeprop('max_constants_tracker', MaxConstantsTracker(self))

        # Caching / callbacks

        def after_trunk_build(self, branches):
            super(TableauxRules.Universal, self).after_trunk_build(branches)
            self.max_constants_tracker.after_trunk_build(branches)

        def register_branch(self, branch, parent):
            super(TableauxRules.Universal, self).register_branch(branch, parent)
            self.max_constants_tracker.register_branch(branch, parent)
            if parent != None and parent.id in self.node_states:
                self.consts[branch.id] = set(self.consts[parent.id])
                self.node_states[branch.id] = {
                    node_id : {
                        k : set(self.node_states[parent.id][node_id][k])
                        for k in self.node_states[parent.id][node_id]
                    }
                    for node_id in self.node_states[parent.id]
                }
            else:
                self.node_states[branch.id] = dict()
                self.consts[branch.id] = set()

        def register_node(self, node, branch):
            super(TableauxRules.Universal, self).register_node(node, branch)
            self.max_constants_tracker.register_node(node, branch)
            if self.is_potential_node(node, branch):
                if node.id not in self.node_states[branch.id]:
                    # By tracking per node, we are tracking per world, a fortiori.
                    self.node_states[branch.id][node.id] = {
                        'applied'   : set(),
                        'unapplied' : set(self.consts[branch.id]),
                    }
            for c in node.constants():
                if c not in self.consts[branch.id]:
                    for node_id in self.node_states[branch.id]:
                        self.node_states[branch.id][node_id]['unapplied'].add(c)
                    self.consts[branch.id].add(c)

        def after_apply(self, target):
            super(TableauxRules.Universal, self).after_apply(target)
            branch = target['branch']
            node = target['node']
            c = target['constant']
            idx = self.node_states[branch.id][node.id]
            idx['applied'].add(c)
            idx['unapplied'].discard(c)

        # Implementation

        def get_targets_for_node(self, node, branch):
            with self.timers['in_get_targets_for_nodes']:
                if not self.should_apply(node, branch):
                    return
                with self.timers['in_node_examime']:
                    s = self.sentence(node)
                    si = s.sentence
                    w = node.props['world']
                    v = s.variable
                    constants = self.node_states[branch.id][node.id]['unapplied']
                targets = list()
                if len(constants):
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
            branch.add({'sentence': target['sentence'], 'world': target['world']})

        def example_node(self, branch):
            node = {'sentence': examples.quantified(self.quantifier)}
            if self.modal:
                node['world'] = 0
            return node

        # Util

        def should_apply(self, node, branch):
            if self.max_constants_tracker.max_constants_exceeded(branch, node.props['world']):
                return False
            # Apply if there are no constants on the branch
            if not self.consts[branch.id]:
                return True
            # Apply if we have tracked a constant that we haven't applied to.
            if self.node_states[branch.id][node.id]['unapplied']:
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

        sentence_track = None

        def __init__(self, *args, **opts):
            super(TableauxRules.Possibility, self).__init__(*args, **opts)
            self.safeprop('branch_sentence_track', {})
            self.safeprop('modal_complexities', {})
            self.safeprop('max_worlds_tracker', MaxWorldsTracker(self))

        def after_trunk_build(self, branches):
            super(TableauxRules.Possibility, self).after_trunk_build(branches)
            self.max_worlds_tracker.after_trunk_build(branches)

        # Cache

        def after_apply(self, target):
            super(TableauxRules.Possibility, self).after_apply(target)
            self.sentence_track_inc(target['branch'], target['sentence'])

        def sentence_track_inc(self, branch, sentence):
            self.sentence_track_count(branch, sentence)
            self.branch_sentence_track[branch.id][sentence] += 1

        # Implementation

        def is_potential_node(self, node, branch):
            if self.max_worlds_tracker.max_worlds_exceeded(branch):
                return False
            return super(TableauxRules.Possibility, self).is_potential_node(node, branch)

        def get_target_for_node(self, node, branch):
            if self.max_worlds_tracker.max_worlds_reached(branch):
                return False
            s  = self.sentence(node)
            si = s.operand
            w1 = node.props['world']
            return {'sentence': si, 'world1': w1}

        def apply_to_node_target(self, node, branch, target):
            si = target['sentence']
            w1 = target['world1']
            w2 = branch.new_world()
            branch.update([
                {'sentence': si, 'world': w2},
                {'world1': w1, 'world2': w2},
            ]).tick(node)

        def score_candidate(self, target):
            # override
            branch = target['branch']
            s = self.sentence(target['node'])
            si = s.operand

            # Don't bother checking for closure since we will always have a new world

            track_count = self.sentence_track_count(branch, si)
            if track_count == 0:
                return 1

            return -1 * self.modal_complexity(s) * track_count

        def group_score(self, target):

            if self.score_candidate(target) > 0:
                return 1

            branch = target['branch']
            s = self.sentence(target['node'])
            si = s.operand

            return -1 * self.sentence_track_count(branch, si)

        # Util

        def sentence_track_count(self, branch, sentence):
            if branch.id not in self.branch_sentence_track:
                self.branch_sentence_track[branch.id] = {}
            if sentence not in self.branch_sentence_track[branch.id]:
                self.branch_sentence_track[branch.id][sentence] = 0
            return self.branch_sentence_track[branch.id][sentence]

        def modal_complexity(self, sentence):
            if sentence not in self.modal_complexities:
                ops = sentence.operators()
                modal_ops = [operator for operator in ops if operator in Model.modal_operators]
                self.modal_complexities[sentence] = len(modal_ops)
            return self.modal_complexities[sentence]

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
            sn = operate(self.convert_to, [negate(s.operand)])
            branch.add({'sentence': sn, 'world': w}).tick(node)

    class Necessity(IsModal, logic.TableauxSystem.FilterNodeRule):
        """
        From a necessity node *n* with world *w1* and operand *s* on a branch *b*, for any
        world *w2* such that an access node with w1,w2 is on *b*, if *b* does not have a node
        with *s* at *w2*, add it to *b*. The node *n* is never ticked.
        """

        operator = 'Necessity'

        def __init__(self, *args, **opts):
            super(TableauxRules.Necessity, self).__init__(*args, **opts)
            self.add_timer(
                'get_targets_for_node',
                'make_target'         ,
                'check_target_condtn1',
                'check_target_condtn2',
            )
            self.safeprop('node_worlds_applied', {})
            self.safeprop('max_worlds_tracker', MaxWorldsTracker(self))

        def after_trunk_build(self, branches):
            super(TableauxRules.Necessity, self).after_trunk_build(branches)
            self.max_worlds_tracker.after_trunk_build(branches)

        def should_stop(self, branch):
            return self.max_worlds_tracker.max_worlds_exceeded(branch)

        def is_potential_node(self, node, branch):
            if self.should_stop(branch):
                return False
            return super(TableauxRules.Necessity, self).is_potential_node(node, branch)

        def is_least_applied_to(self, node, branch):
            node_apply_count = self.node_application_count(node.id, branch.id)
            min_apply_count = self.min_application_count(branch.id)
            return min_apply_count >= node_apply_count

        def register_node(self, node, branch):
            super(TableauxRules.Necessity, self).register_node(node, branch)
            #if self.is_potential_node(node, branch):
            if branch.id not in self.node_worlds_applied:
                self.node_worlds_applied[branch.id] = set()

        def after_apply(self, target):
            super(TableauxRules.Necessity, self).after_apply(target)
            branch = target['branch']
            node = target['node']
            world = target['world']
            self.node_worlds_applied[branch.id].add((node.id, world))
            
        def get_targets_for_node(self, node, branch):

            # Check for max worlds reached
            if self.should_stop(branch):
                return

            # Only count least-applied-to nodes
            if not self.is_least_applied_to(node, branch):
                return

            with self.timers['get_targets_for_node']:
                targets = list()
                worlds = branch.worlds()
                s = self.sentence(node)
                si = s.operand
                w1 = node.props['world']
                for anode in branch.find_all({'world1': w1}):
                    w2 = anode.props['world2']
                    if (node.id, w2) in self.node_worlds_applied[branch.id]:
                        #print(self.node_worlds_applied)
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
            branch.add({'sentence': target['sentence'], 'world': target['world']})

        def example_nodes(self, branch):
            s = operate(self.operator, [atomic(0, 0)])
            return [
                {'sentence': s, 'world': 0},
                {'world1': 0, 'world2': 1},
            ]

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

        def __init__(self, *args, **opts):
            super(TableauxRules.IdentityIndiscernability, self).__init__(*args, **opts)
            self.safeprop('predicated_nodes', {})

        def register_branch(self, branch, parent):
            super(TableauxRules.IdentityIndiscernability, self).register_branch(branch, parent)
            if parent != None and parent.id in self.predicated_nodes:
                self.predicated_nodes[branch.id] = set(self.predicated_nodes[parent.id])
            else:
                self.predicated_nodes[branch.id] = set()

        def register_node(self, node, branch):
            super(TableauxRules.IdentityIndiscernability, self).register_node(node, branch)
            if node.has('sentence') and self.sentence(node).is_predicated():
                self.predicated_nodes[branch.id].add(node)

        def get_targets_for_node(self, node, branch):
            pnodes = self.predicated_nodes[branch.id]
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
                s1 = predicated(s.predicate, params)
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
            return [ 
                {'sentence': examples.predicated(), 'world': 0},
                {'sentence': examples.identity(),   'world': 0},
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
            Existential,
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
            Universal,
        ],
    ]