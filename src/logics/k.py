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

# LCaMNb
# Ma
# KMNbc

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

    @staticmethod
    def build_trunk(tableau, argument):
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

class MaxWorldTrackingFilterRule(IsModal, logic.TableauxSystem.FilterNodeRule):

    def __init__(self, *args, **opts):
        super(MaxWorldTrackingFilterRule, self).__init__(*args, **opts)
        # Track the maximum number of worlds that should be on the branch
        # so we can halt on infinite branches.
        self.branch_max_worlds = {}

    def after_trunk_build(self, branches):
        super(MaxWorldTrackingFilterRule, self).after_trunk_build(branches)
        for branch in branches:
            # Project the maximum number of worlds for a branch (origin) as
            # the number of worlds already on the branch + the number of modal
            # operators + 1.
            origin = branch.origin()
            # In most cases, we will have only one origin branch.
            if origin.id in self.branch_max_worlds:
                return
            branch_modal_operators_list = list()
            # we only care about unticked nodes, since ticked nodes will have
            # already created any worlds.
            for node in branch.get_nodes(ticked=False):
                if node.has('sentence'):
                    ops = self.sentence(node).operators()
                    branch_modal_operators_list.extend(
                        [o for o in ops if o in Model.modal_operators]
                    )
            self.branch_max_worlds[origin.id] = len(branch.worlds()) + len(branch_modal_operators_list) + 1

    def get_max_worlds(self, branch):
        origin = branch.origin()
        if origin.id in self.branch_max_worlds:
            return self.branch_max_worlds[origin.id]

    def max_worlds_reached(self, branch):
        # TODO: should this logic move to the possibility rule instead?
        #       after all, it's the one that will add a new world.
        #
        # If we have already reached the max number of worlds projected for
        # the branch (origin), return the empty list.
        max_worlds = self.get_max_worlds(branch)
        return max_worlds != None and len(branch.worlds()) > max_worlds

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

        def applies_to_branch(self, branch):
            for node in branch.get_nodes():
                if node.has('sentence') and node.has('world'):
                    n = branch.find({'sentence': negate(node.props['sentence']), 'world': node.props['world']})
                    if n != None:
                        return {'nodes': set([node, n]), 'type': 'Nodes'}
            #for node in branch.find_all({'_operator': 'Negation'}):
            #    if node.has('sentence') and node.has('world'):
            #        n = branch.find({'sentence': node.props['sentence'].operand, 'world': node.props['world']})
            #        if n != None:
            #            return {'nodes': set([node, n]), 'type': 'Nodes'}
            return False

        def example(self):
            a = atomic(0, 0)
            self.branch().update([
                {'sentence':        a , 'world': 0},
                {'sentence': negate(a), 'world': 0},
            ])

    class SelfIdentityClosure(logic.TableauxSystem.ClosureRule):
        """
        A branch closes when a sentence of the form P{~a = a} appears on the branch *at any world*.
        """

        def applies_to_branch(self, branch):
            #for node in branch.find_all({'_operator': 'Negation'}):
            #    s = self.sentence(node).operand
            #    if s.predicate == Identity:
            #        a, b = s.parameters
            #        if a == b:
            #            return {'node': node, 'type': 'Node'}
            for node in branch.get_nodes():
                if node.has('sentence'):
                    s = self.sentence(node)
                    if s.operator == 'Negation' and s.operand.predicate == Identity:
                        a, b = s.operand.parameters
                        if a == b:
                            return {'node': node, 'type': 'Node'}
            return False

        def example(self):
            s = negate(examples.self_identity())
            self.branch().add({'sentence': s, 'world': 0})

    class NonExistenceClosure(logic.TableauxSystem.ClosureRule):
        """
        A branch closes when a sentence of the form P{~!a} appears on the branch *at any world*.
        """

        def applies_to_branch(self, branch):
            #for node in branch.find_all({'_operator': 'Negation'}):
            #    s = self.sentence(node).operand
            #    if s.predicate == Existence:
            #        return {'node': node, 'type': 'Node'}
            for node in branch.get_nodes():
                if node.has('sentence'):
                    s = self.sentence(node)
                    if s.operator == 'Negation' and s.operand.predicate == Existence:
                        return {'node': node, 'type': 'Node'}

        def example(self):
            s = logic.parse('NJm')
            self.branch().add({'sentence': s, 'world': 0})

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

        def apply_to_node(self, node, branch):
            w = node.props['world']
            s = self.sentence(node)
            v = node.props['sentence'].variable
            c = branch.new_constant()
            si = s.sentence
            r = si.substitute(c, v)
            branch.add({'sentence': r, 'world': w}).tick(node)

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

        def get_targets_for_node(self, node, branch):
            s = self.sentence(node)
            si = s.sentence
            w = node.props['world']
            v = s.variable
            constants = branch.constants()
            targets = list()
            if len(constants):
                # if the branch already has a constant, find all the substitutions not
                # already on the branch.
                for c in constants:
                    r = si.substitute(c, v)
                    target = {'sentence': r, 'world': w}
                    if not branch.has(target):
                        targets.append(target)
            else:
                # if the branch does not have any constants, pick a new one
                c = branch.new_constant()
                r = si.substitute(c, v)
                target = {'sentence': r, 'world': w}
                targets.append(target)
            return targets

        def score_candidate(self, target):
            node_apply_count = self.node_application_count(target['node'], target['branch'])
            return float(1 / (node_apply_count + 1))

        def apply_to_target(self, target):
            branch = target['branch']
            branch.add({'sentence': target['sentence'], 'world': target['world']})

        def example(self):
            self.branch().add({'sentence': examples.quantified(self.quantifier), 'world': 0})

    class UniversalNegated(ExistentialNegated):
        """
        From an unticked negated universal node *n* with world *w* on a branch *b*,
        quantifying over variable *v* into sentence *s*, add an existentially
        quantified node to *b* with world *w* over *v* into the negation of *s*,
        then tick *n*.
        """

        quantifier = 'Universal'
        convert_to = 'Existential'

    class Possibility(MaxWorldTrackingFilterRule):
        """
        From an unticked possibility node with world *w* on a branch *b*, add a node with a
        world *w'* new to *b* with the operand of *n*, and add an access-type node with
        world1 *w* and world2 *w'* to *b*, then tick *n*.
        """

        operator = 'Possibility'

        sentence_track = None

        def __init__(self, *args, **opts):
            super(TableauxRules.Possibility, self).__init__(*args, **opts)
            self.branch_sentence_track = {}
            self.modal_complexities = {}

        def is_potential_node(self, node, branch):
            if self.max_worlds_reached(branch):
                return False
            return super(TableauxRules.Possibility, self).is_potential_node(node, branch)

        def applies_to_node(self, node, branch):
            if self.max_worlds_reached(branch):
                return False
            return super(TableauxRules.Possibility, self).applies_to_node(node, branch)

        def apply_to_node(self, node, branch):
            s  = self.sentence(node)
            si = s.operand
            w1 = node.props['world']
            w2 = branch.new_world()
            branch.update([
                {'sentence': si, 'world': w2},
                {'world1': w1, 'world2': w2},
            ]).tick(node)
            self.sentence_track_inc(branch, si)

        # override
        def score_candidate(self, target):

            branch = target['branch']
            s = self.sentence(target['node'])
            si = s.operand

            # Don't bother checking for closure since we will always have a new world

            track_count = self.sentence_track_count(branch, si)

            # Make sure we apply once for each sentence.
            #
            # TODO: Consider flanking quantifiers like XxPLyFxy. In this case PLyFac, PLyFab, etc.
            #       will always be new sentences. This could lead to a failure to close.
            #
            #       1. PNLxFx
            #       2. XxPSy(Fx & ~Fy)
            #
            #       In S5 these are unsatisfiable, so the tree would go (ignoring extra access nodes):
            #                                |           :
            #       1. PNLxFx , w0           |  (4,5)    :
            #       2. XxPXy(Fx & ~Fy) , w0  |  (3)      :
            #                                |           :
            #       3. PXy(Fa & ~Fy) , w0    |  (6,7)    :   Existential (2) 
            #                                |           :
            #       4. NLxFx , w1            |           :
            #       5. w0,w1                 |           :   Possibility (1)    -- since track_count of NLxFx is 0
            #                                |           :
            #       6. Xy(Fa & ~Fy), w2      |  (8)      :
            #       7. w0,w2                 |           :   Possibility (3)    -- since track_count of Xy(Fa & ~Fy) is 0
            #                                |           :
            #       8. Fa & ~Fb , w2         |  (9,10)   :   Existenial (6)
            #                                |           :
            #       9. Fa , w2               |           :
            #      10. ~Fb , w2              |           :   Conjunction (8)
            #                                |           :
            #      11  w2,w0                 |           :   Symmetric (7)
            #      12. w2,w1                 |           :   Transitive (11,5)
            #      13. w1,w2                 |           :   Symmetric (12)
            #                                |           :
            #      14. LxFx , w2             |           :   Necessity (4,13)
            #                                |           :
            #      15. Fb , w2               |           :   Universal (14)
            #                                |           :
            #          X                     |           :   ContradictionClosure (10,15)
            #
            #      OK, this closes, but what about:
            #
            #       1. PNLxFx , w0                (3,4)
            #       2. NXxPXy(Fx & ~Fy) , w0     
            #                                    
            #       3. NLxFx , w1                
            #       4. w0,w1                                   Possibility (1)    -- since sentence track_count of NLxFx is 0
            #                                    
            #       5. XxPXy(Fx & ~Fy) , w1       (5)          Necessity (2,4)    -- could have been 3 since node track_count = 0
            #                                    
            #       6. PXy(Fa & ~Fy) , w1         (8)          Existential (5)
            #
            #       7. w1,w1                                   Reflexive (4)
            #
            #       now we have group competition between Necessity and Possibility.
            #
            # TODO: redesign this group/candidate scoring
            #
            #       Necessity will check for:
            #         - node must be one of the least-applied-to
            #            - if candidate score > 0, then group score is 1
            #               - if branch will close with this candidate, the candidate score is 1
            #               - else candidate score is -1 * node branching complexity
            #            - else group score is -1 * node track_count
            #       Possibility will check for:
            #            - if candidate score > 0, then group score is 1
            #               - if sentence track_count is 0, then candidate score is 1
            #               - else candidate score is -1 * sentence modal complexity * sentence track_count
            #            - else group score is -1 * sentence track_count
            #
            #       Necessity will check 2 and 3
            #           - the node track_count of 2 is 1, and of 3 is 0.
            #           - the only least-applied-to node is 3.
            #           - having LxFx , w1 on the branch will not immediately close it.
            #           - thus the candidate score of 3 is -1 * 0 == 0.
            #           - since the candidate score is less than 1, the group score is
            #             -1 * node track_count, which is 0.
            #
            #       Possibility will check 6
            #           - sentence track count is 0, so candidate score is 1.
            #           - thus group score is 1.
            #
            #       8. Xy(Fa & ~Fy) , w1         (9)            Possibility (6)
            #
            #       9. Fa & ~Fb , w1             (10,11)        Existential (8)
            #
            #      10. Fa , w1
            #      11. ~Fb, w1                                  Conjunction (9)
            #
            #      12. LxFx , w1                                Necessity (3,7)
            #
            #      13. Fa , w1                                  Universal (12)
            #      14. Fb , w1                                  Universal (12)
            #
            #          X                                        ContradictionClosure (11, 14)
            #
            #       Whew!
            #
            if track_count == 0:
                return 1
            return -1 * self.modal_complexity(s) * track_count

            # Other ideas ....

            # Apply to the simplest possibility sentence, so we don't get stuck
            #ops = s.operators()
            # use full modal complexity, not just possbility NPNA vs NPA
            #modal_ops = [operator for operator in ops if operator in Model.modal_operators]
            #return -1 * len(modal_ops) * track_count

            #possibility_ops = [operator for operator in ops if operator == self.operator]
            #return -1 * len(possibility_ops) # * len(ops) # Also rank by simplest?
            #return -1 * (len(possibility_ops) + self.branching_complexity(self.sentence(target['node']).operand))

        def modal_complexity(self, sentence):
            if sentence not in self.modal_complexities:
                ops = sentence.operators()
                modal_ops = [operator for operator in ops if operator in Model.modal_operators]
                self.modal_complexities[sentence] = len(modal_ops)
            return self.modal_complexities[sentence]

        def group_score(self, target):
            if target['candidate_score'] > 0:
                return 1
            branch = target['branch']
            s = self.sentence(target['node'])
            si = s.operand
            #self.branching_complexity(target['node']), 
            return -1 * self.sentence_track_count(branch, si)

        def sentence_track_count(self, branch, sentence):
            if branch.id not in self.branch_sentence_track:
                self.branch_sentence_track[branch.id] = {}
            if sentence not in self.branch_sentence_track[branch.id]:
                self.branch_sentence_track[branch.id][sentence] = 0
            return self.branch_sentence_track[branch.id][sentence]

        def sentence_track_inc(self, branch, sentence):
            self.sentence_track_count(branch, sentence)
            self.branch_sentence_track[branch.id][sentence] += 1

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

    class Necessity(MaxWorldTrackingFilterRule):
        """
        From a necessity node *n* with world *w1* and operand *s* on a branch *b*, for any
        world *w2* such that an access node with w1,w2 is on *b*, if *b* does not have a node
        with *s* at *w2*, add it to *b*. The node *n* is never ticked.
        """

        operator = 'Necessity'

        def is_potential_node(self, node, branch):
            if self.max_worlds_reached(branch):
                return False
            return super(TableauxRules.Necessity, self).is_potential_node(node, branch)

        def is_least_applied_to(self, node, branch):
            node_apply_count = self.node_application_count(node.id, branch.id)
            min_apply_count = self.min_application_count(branch.id)
            return min_apply_count >= node_apply_count

        def get_targets_for_node(self, node, branch):

            # Check for max worlds reached
            if self.max_worlds_reached(branch):
                return

            # Only count least-applied-to nodes
            if not self.is_least_applied_to(node, branch):
                return

            targets = list()
            worlds = branch.worlds()
            s = self.sentence(node)
            si = s.operand
            w1 = node.props['world']
            for w2 in worlds:
                anode = branch.find({'world1': w1, 'world2': w2})
                if anode != None and not branch.has({'sentence': si, 'world': w2}):
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

            # Modal complexity?
            #return -1 * len(target['sentence'].operators())

        def group_score(self, target):
            if target['candidate_score'] > 0:
                return 1
            return -1 * self.node_application_count(target['node'].id, target['branch'].id)
            #return -1 * min(target['track_count'], self.branching_complexity(target['node']))

        def apply_to_target(self, target):
            branch = target['branch']
            branch.add({'sentence': target['sentence'], 'world': target['world']})

        def example(self):
            s = operate(self.operator, [atomic(0, 0)])
            self.branch().update([
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

    class IdentityIndiscernability(IsModal, logic.TableauxSystem.Rule):
        """
        From an unticked node *n* having an Identity sentence *s* at world *w* on an open branch *b*,
        and a predicated node *n'* whose sentence *s'* has a constant that is a parameter of *s*,
        if the replacement of that constant for the other constant of *s* is a sentence that does
        not appear on *b* at *w*, then add it.
        """

        def get_candidate_targets(self, branch):
            #nodes = set(branch.find_all({'_is_predicated': True}, ticked = False))
            nodes = {
                node for node in branch.get_nodes(ticked = False)
                if node.has('sentence') and self.sentence(node).is_predicated()
            }
            #inodes = set(branch.search_nodes({'_predicate': Identity}, nodes))
            inodes = {
                node for node in nodes if self.sentence(node).predicate == Identity and
                # checking length of the set excludes self-identity sentences.
                len(set(self.sentence(node).parameters)) == 2
            }
            cands = list()
            for inode in inodes:
                w = inode.props['world']
                pa, pb = inode.props['sentence'].parameters
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
                        # this continue statements does not register as covered. this line is covered
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
                            target = {'sentence': s1, 'world': w, 'branch': branch}
                            cands.append(target)
            return cands

        def select_best_target(self, targets, branch):
            # TODO optimize
            return targets[0]
            #raise NotImplementedError(NotImplemented)

        def apply(self, target):
            target['branch'].add({'sentence': target['sentence'], 'world': target['world']})

        def example(self):
            self.branch().update([ 
                {'sentence': examples.predicated(), 'world': 0},
                {'sentence': examples.identity(),   'world': 0},
            ])

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
            Universal,
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
            # world creation rules 2
            Necessity,
        #],
        #[
            # world creation rules 1
            Possibility,
        ],
    ]