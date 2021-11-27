# -*- coding: utf-8 -*-
# pytableaux, a multi-logic proof generator.
# Copyright (C) 2014-2021 Doug Owings.
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

from lexicals import Predicate, Atomic, Constant, Operated, Predicated, Quantified, \
    Operator as Oper, Quantifier, Argument, Sentence, Predicates
from models import BaseModel

from proof.tableaux import TableauxSystem as BaseSystem, Rule, Tableau
from proof.rules import ClosureRule
from proof.common import Access, Annotate, Branch, Filters, Node, Target
from proof.helpers import AppliedNodesWorlds, AppliedSentenceCounter, \
    MaxWorldsTracker, PredicatedNodesTracker, AppliedQuitFlag, AdzHelper, \
    FilterHelper, AppliedNodeCount, VisibleWorldsIndex

from errors import DenotationError, ModelValueError

from . import fde as FDE

Identity: Predicate  = Predicates.System.Identity
Existence: Predicate = Predicates.System.Existence

def substitute_params(params, old_value, new_value):
    return tuple(new_value if p == old_value else p for p in params)

class Model(BaseModel):
    """
    A K model comprises a non-empty collection of K-frames, a world access
    relation, and a set of constants (the domain).
    """

    truth_values_list = ['F', 'T']

    #: The set of admissible values for sentences in a model.
    #:
    #: :type: set
    #: :value: {T, F}
    #: :meta hide-value:
    truth_values = frozenset(truth_values_list)

    unassigned_value = 'F'

    nvals = {
        'F': 0,
        'T': 1,
    }
    cvals = {
        1: 'T',
        0: 'F',
    }

    def __init__(self):

        super().__init__()

        #: A map from worlds to their frame. Worlds are reprented as integers.
        #:
        #: :type: dict
        self.frames: dict[int, Frame] = {}

        #: A set of pairs of worlds, which functions as an `access` relation.
        #:
        #: :type: set
        self.access = set()

        #: The fixed domain of constants, common to all worlds in the model.
        #:
        #: :type: set
        self.constants = set()

        self.predicates = {Identity, Existence}
        self.fde = FDE.Model()

        # ensure there is a w0
        self.world_frame(0)

    def value_of_operated(self, sentence: Operated, **kw):
        if self.is_sentence_opaque(sentence):
            return self.value_of_opaque(sentence, **kw)
        if sentence.operator in self.modal_operators:
            return self.value_of_modal(sentence, **kw)
        return super().value_of_operated(sentence, **kw)

    def value_of_predicated(self, sentence: Predicated, **kw):
        """
        A sentence for predicate `P` is true at :m:`w` iff the tuple of the parameters
        is in the extension of `P` at :m:`w`.
        """
        pred = sentence.predicate
        params = sentence.params
        for param in params:
            if param not in self.constants:
                raise DenotationError(
                    'Parameter {0} is not in the constants'.format(param)
                )
        if params in self.get_extension(pred, **kw):
            return 'T'
        return 'F'

    def value_of_existential(self, sentence: Quantified, **kw):
        """
        An existential sentence is true at :m:`w`, just when the sentence resulting in the
        subsitution of some constant in the domain for the variable is true at :m:`w`.
        """
        si = sentence.sentence
        v = sentence.variable
        for c in self.constants:
            r = si.substitute(c, v)
            if self.value_of(r, **kw) == 'T':
                return 'T'
        return 'F'

    def value_of_universal(self, sentence: Quantified, **kw):
        """
        A universal sentence is true at :m:`w`, just when the sentence resulting in the
        subsitution of each constant in the domain for the variable is true at :m:`w`.
        """
        si = sentence.sentence
        v = sentence.variable
        for c in self.constants:
            r = si.substitute(c, v)
            if self.value_of(r, **kw) == 'F':
                return 'F'
        return 'T'

    def value_of_possibility(self, sentence: Operated, world=0, **kw):
        """
        A possibility sentence is true at :m:`w` iff its operand is true at :m:`w'` for
        some :m:`w'` such that :m:`<w, w'>` in the access relation.
        """
        for w2 in self.visibles(world):
            if self.value_of(sentence.operand, world=w2, **kw) == 'T':
                return 'T'
        return 'F'

    def value_of_necessity(self, sentence: Operated, world=0, **kw):
        """
        A necessity sentence is true at :m:`w` iff its operand is true at :m:`w'` for
        each :m:`w'` such that :m:`<w, w'>` is in the access relation.
        """
        for w2 in self.visibles(world):
            if self.value_of(sentence.operand, world=w2, **kw) == 'F':
                return 'F'
        return 'T'

    def is_countermodel_to(self, argument: Argument):
        """
        A model is a countermodel for an argument iff the value of each premise
        is :m:`T` at `w0` and the value of the conclusion is :m:`F` at :m:`w0`.
        """
        for premise in argument.premises:
            if self.value_of(premise, world=0) != 'T':
                return False
        return self.value_of(argument.conclusion, world=0) == 'F'

    def get_data(self) -> dict:
        return {
            'Worlds': {
                'description'     : 'set of worlds',
                'in_summary'      : True,
                'datatype'        : 'set',
                'member_datatype' : 'int',
                'member_typehint' : 'world',
                'symbol'          : 'W',
                'values'          : sorted(self.frames),
            },
            'Access': {
                'description'     : 'access relation',
                'in_summary'      : True,
                'datatype'        : 'set',
                'typehint'        : 'access_relation',
                'member_datatype' : 'tuple',
                'member_typehint' : 'access',
                'symbol'          : 'R',
                'values'          : sorted(self.access),
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

    def read_branch(self, branch: Branch):
        for node in branch:
            self.read_node(node)
        self.finish()
        return self

    def read_node(self, node: Node):
        s: Sentence = node.get('sentence')
        if s:
            w = node.get('world')
            if w == None:
                w = 0
            if self.is_sentence_opaque(s):
                self.set_opaque_value(s, 'T', world = w)
            elif self.is_sentence_literal(s):
                self.set_literal_value(s, 'T', world = w)
            self.predicates.update(s.predicates)
        elif node.is_access:
            self.add_access(node['world1'], node['world2'])

    def finish(self):
        # track all atomics and opaques
        atomics = set()
        opaques = set()

        for w in self.frames:

            frame = self.world_frame(w)
            atomics.update(frame.atomics.keys())
            opaques.update(frame.opaques.keys())

            # TODO: WIP
            self.generate_denotation(w)
            self.generate_property_classes(w)

            for pred in self.predicates:
                self.agument_extension_with_identicals(pred, w)
            self.ensure_self_identity(w)
            self.ensure_self_existence(w)

        # make sure each atomic and opaque is assigned a value in each frame
        unval = self.unassigned_value
        for w in self.frames:
            frame = self.world_frame(w)
            for s in atomics:
                if s not in frame.atomics:
                    self.set_literal_value(s, unval, world = w)
            for s in opaques:
                if s not in frame.opaques:
                    self.set_opaque_value(s, unval, world = w)

    def ensure_self_identity(self, w):
        ext = self.get_extension(Identity, world = w)
        for c in self.constants:
            # make sure each constant is self-identical
            ext.add((c, c))

    def ensure_self_existence(self, w):
        ext = self.get_extension(Existence, world = w)
        for c in self.constants:
            # make sure each constant exists
            ext.add((c,))

    def agument_extension_with_identicals(self, pred: Predicate, w):
        extension = self.get_extension(pred, world = w)
        for c in self.constants:
            identicals = self.get_identicals(c, world = w)
            to_add = set()
            for params in extension:
                if c in params:
                    for new_c in identicals:
                        new_params = substitute_params(params, c, new_c)
                        to_add.add(new_params)
            extension.update(to_add)

    def generate_denotation(self, w):
        frame = self.world_frame(w)
        w = frame.world
        todo = set(self.constants)
        for c in self.constants:
            if c in todo:
                denotum = Denotum()
                frame.domain.add(denotum)
                denoters = {c}.union(self.get_identicals(c, world = w))
                frame.denotation.update({c: denotum for c in denoters})
                todo -= denoters
        assert not todo

    def generate_property_classes(self, w):
        frame = self.world_frame(w)
        w = frame.world
        for pred in self.predicates:
            # Skip identity and existence
            if pred in (Identity, Existence):
                continue
            frame.property_classes[pred] = {
                tuple(self.get_denotum(p, world = w) for p in params)
                for params in self.get_extension(pred, world = w)
            }

    def get_identicals(self, c, **kw):
        ext = self.get_extension(Identity, **kw)
        identicals = set()
        for params in ext:
            if c in params:
                identicals.update(params)
        identicals.discard(c)
        return identicals

    def is_sentence_literal(self, sentence: Sentence):
        if sentence.is_negated and self.is_sentence_opaque(sentence.operand):
            return True
        return sentence.is_literal

    def set_literal_value(self, sentence: Sentence, value, **kw):
        if self.is_sentence_opaque(sentence):
            self.set_opaque_value(sentence, value, **kw)
        elif sentence.is_negated:
            negval = self.truth_function(sentence.operator, value)
            self.set_literal_value(sentence.operand, negval, **kw)
        elif sentence.is_atomic:
            self.set_atomic_value(sentence, value, **kw)
        elif sentence.is_predicated:
            self.set_predicated_value(sentence, value, **kw)
        else:
            raise NotImplementedError()

    def set_opaque_value(self, sentence: Sentence, value, world = 0, **kw):
        frame = self.world_frame(world)
        # if sentence in frame.opaques and frame.opaques[sentence] != value:
        if frame.opaques.get(sentence, value) != value:
            raise ModelValueError('Inconsistent value for sentence {0}'.format(sentence))
        # We might have a quantified opaque sentence, in which case we will need
        # to still check every subsitution, so we want the constants.
        # NB: in FDE we added the atomics to all_atomics, but we don't have that
        #     here since we do frames -- will that be a problem?
        self.constants.update(sentence.constants)
        self.predicates.update(sentence.predicates)
        frame.opaques[sentence] = value

    def set_atomic_value(self, sentence: Atomic, value, world = 0, **kw):
        frame = self.world_frame(world)
        if sentence in frame.atomics and frame.atomics[sentence] != value:
            raise ModelValueError('Inconsistent value for sentence {0}'.format(str(sentence)))
        frame.atomics[sentence] = value

    def set_predicated_value(self, sentence: Predicated, value, **kw):
        pred = sentence.predicate
        params = sentence.params
        if pred not in self.predicates:
            self.predicates.add(pred)
        for param in params:
            if param.is_constant:
                self.constants.add(param)
        extension = self.get_extension(pred, **kw)
        anti_extension = self.get_anti_extension(pred, **kw)
        if value == 'F':
            if params in extension:
                raise ModelValueError(
                    'Cannot set value {0} for tuple {1} already in extension'.format(
                        value, params
                    )
                )
            anti_extension.add(params)
        if value == 'T':
            if params in anti_extension:
                raise ModelValueError(
                    'Cannot set value {0} for tuple {1} already in anti-extension'.format(
                        value, params
                    )
                )
            extension.add(params)

    def get_extension(self, pred, world = 0, **kw):
        frame = self.world_frame(world)
        if pred not in self.predicates:
            self.predicates.add(pred)
        if pred not in frame.extensions:
            frame.extensions[pred] = set()
        if pred not in frame.anti_extensions:
            frame.anti_extensions[pred] = set()
        return frame.extensions[pred]

    def get_anti_extension(self, pred, world = 0, **kw):
        frame = self.world_frame(world)
        if pred not in self.predicates:
            self.predicates.add(pred)
        if pred not in frame.extensions:
            frame.extensions[pred] = set()
        if pred not in frame.anti_extensions:
            frame.anti_extensions[pred] = set()
        return frame.anti_extensions[pred]

    def get_domain(self, world = 0, **kw):
        # TODO: wip
        return self.world_frame(world).domain

    def get_denotation(self, world = 0, **kw):
        # TODO: wip
        return self.world_frame(world).denotation

    def get_denotum(self, c: Constant, world = 0, **kw):
        # TODO: wip
        frame = self.world_frame(world)
        world = frame.world
        den = self.get_denotation(world = world)
        try:
            return den[c]
        except KeyError:
            raise DenotationError(
                'Constant {0} does not have a reference at w{1}'.format(
                    c, world
                )
            )

    def add_access(self, w1, w2):
        self.access.add((w1, w2))
        self.world_frame(w1)
        self.world_frame(w2)

    def has_access(self, w1, w2):
        return (w1, w2) in self.access

    def visibles(self, world):
        return {w for w in self.frames if (world, w) in self.access}

    def world_frame(self, world):
        if world == None:
            world = 0
        if not isinstance(world, int):
            raise TypeError(world)
        if world not in self.frames:
            self.frames[world] = Frame(world)
        return self.frames[world]

    def value_of_opaque(self, sentence: Sentence, world=0, **kw):
        frame = self.world_frame(world)
        world = frame.world
        if sentence in frame.opaques:
            return frame.opaques[sentence]
        return self.unassigned_value

    def value_of_atomic(self, sentence: Atomic, world=0, **kw):
        frame = self.world_frame(world)
        world = frame.world
        if sentence in frame.atomics:
            return frame.atomics[sentence]
        return self.unassigned_value

    def value_of_modal(self, sentence: Operated, **kw):
        operator = sentence.operator
        if operator == Oper.Possibility:
            return self.value_of_possibility(sentence, **kw)
        elif operator == Oper.Necessity:
            return self.value_of_necessity(sentence, **kw)
        else:
            raise NotImplementedError()

    def value_of_quantified(self, sentence: Quantified, **kw):
        q = sentence.quantifier
        if q == Quantifier.Existential:
            return self.value_of_existential(sentence, **kw)
        elif q == Quantifier.Universal:
            return self.value_of_universal(sentence, **kw)
        return super().value_of_quantified(sentence, **kw)

    def truth_function(self, operator: Oper, a, b=None):
        return self.fde.truth_function(operator, a, b)

class Denotum(object):
    # WIP - Generating "objects" like k-constants for a domain, dentation, and
    #       predicate "property" extensions.
    #
    #       With the current implemtation of how values are set and checked
    #       dynamically for integrity, we can't easily generate a useful
    #       domain until we know the model is finished.
    #
    #       For now, the purpose of this WIP feature is merely informational.
    pass

class Frame(object):
    """
    A K-frame comprises the interpretation of sentences and predicates at a world.
    """

    def __init__(self, world):

        #: The world of the frame.
        #:
        #: :type: int
        self.world = world

        #: An assignment of each atomic sentence to a truth value.
        #:
        #: :type: dict
        self.atomics = {}

        #: An assignment of each opaque (un-interpreted) sentence to a value.
        self.opaques = {}

        #: A map of predicates to their extension. An extension for an
        #: *n*-ary predicate is a set of *n*-tuples of constants.
        #:
        #: :type: dict
        #: :meta hide-value:
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
                            'description'     : 'predicate extension for {0}'.format(pred.name),
                            'datatype'        : 'function',
                            'typehint'        : 'extension',
                            'input_datatype'  : 'predicate',
                            'output_datatype' : 'set',
                            'output_typehint' : 'extension',
                            'symbol'          : 'P',
                            'values'          : [
                                {
                                    'input'  : pred,
                                    'output' : self.extensions[pred],
                                }
                            ]
                        }
                        for pred in sorted(list(self.extensions.keys()))
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

class TableauxSystem(BaseSystem):
    """
    Modal tableaux are similar to classical tableaux, with the addition of a
    *world* index for each sentence node, as well as *access* nodes representing
    "visibility" of worlds. The worlds and access nodes come into play with
    the rules for Possibility and Necessity. All other rules function equivalently
    to their classical counterparts.
    """

    neg_branchable = {Oper.Conjunction, Oper.MaterialBiconditional, Oper.Biconditional}
    pos_branchable = {Oper.Disjunction, Oper.MaterialConditional, Oper.Conditional}

    @classmethod
    def build_trunk(cls, tableau: Tableau, argument: Argument):
        """
        To build the trunk for an argument, add a node with each premise, with
        world :m:`*w0*`, followed by a node with the negation of the conclusion
        with world :m:`*w0*`.
        """
        branch = tableau.branch()
        for premise in argument.premises:
            branch.add({'sentence': premise, 'world': 0})
        branch.add({'sentence': argument.conclusion.negate(), 'world': 0})

    @classmethod
    def branching_complexity(cls, node: Node) -> int:
        s: Sentence = node.get('sentence')
        if not s:
            return 0
        last_is_negated = False
        complexity = 0
        for oper in s.operators:
            if oper == Oper.Assertion:
                continue
            if oper == Oper.Negation:
                if last_is_negated:
                    last_is_negated = False
                    continue
                last_is_negated = True
            elif last_is_negated:
                if oper in cls.neg_branchable:
                    complexity += 1
                    last_is_negated = False
            elif oper in cls.pos_branchable:
                complexity += 1
        return complexity

@FilterHelper.clsfilters(
    sentence = Filters.Node.Sentence,
    modal    = Filters.Node.Modal,
)
class DefaultRule(FilterHelper.Sentence, FilterHelper.ExampleNodes, Rule):

    nf: FilterHelper = Annotate.HelperAttr

    ignore_ticked = True

    # Filters.Node.Sentence
    negated    : bool = None
    operator   : Oper = None
    quantifier : Quantifier = None
    predicate  : Predicate = None

    # Filters.Node.Modal
    modal  : bool = True
    access : bool = None

class DefaultNodeRule(DefaultRule, AdzHelper.ClosureScore, AdzHelper.Apply):

    adz: AdzHelper = Annotate.HelperAttr

    @FilterHelper.node_targets
    def _get_targets(self, node: Node, branch: Branch):
        return self._get_node_targets(node, branch)

    def _get_node_targets(self, node: Node, branch: Branch):
        raise NotImplementedError()

class TabRules(object):
    """
    Rules for modal operators employ *world* indexes as well access-type
    nodes. The world indexes are transparent for the rules for classical
    connectives.
    """

    class ContradictionClosure(ClosureRule):
        """
        A branch closes when a sentence and its negation both appear on a node **with the
        same world** on the branch.
        """
        modal = True

        # tracker implementation

        def check_for_target(self, node: Node, branch: Branch):
            nnode = self._find_closing_node(node, branch)
            if nnode:
                return {'nodes': {node, nnode}}

        # rule implementation

        def node_will_close_branch(self, node: Node, branch: Branch) -> bool:
            if self._find_closing_node(node, branch):
                return True
            return False

        def example_nodes(self) -> tuple[dict]:
            a: Atomic = Atomic.first()
            w = 0 if self.modal else None
            return (
                {'sentence': a         , 'world': w},
                {'sentence': a.negate(), 'world': w},
            )

        def applies_to_branch(self, branch: Branch):
            # Delegate to tracker
            return self.ntch.cached_target(branch)

        # private util

        def _find_closing_node(self, node: Node, branch: Branch):
            s: Sentence = node.get('sentence')
            if s:
                return branch.find({
                    'sentence' : s.negative(),
                    'world'    : node.get('world'),
                })

    class SelfIdentityClosure(ClosureRule):
        """
        A branch closes when a sentence of the form :s:`~a = a` appears on the
        branch *at any world*.
        """
        modal = True

        # tracker implementation

        def check_for_target(self, node: Node, branch: Branch):
            if self.node_will_close_branch(node, branch):
                return {'node': node}

        # rule implementation

        def node_will_close_branch(self, node: Node, branch: Branch) -> bool:
            s: Operated = node.get('sentence')
            if s:
                if s.is_negated and s.negatum.predicate == Identity:
                    a, b = s.negatum
                    return a == b

        def applies_to_branch(self, branch: Branch):
            # Delegate to tracker
            return self.ntch.cached_target(branch)

        def example_nodes(self):
            c = Constant.first()
            s = Identity((c, c)).negate()
            w = 0 if self.modal else None
            return ({'sentence': s, 'world': w},)

    class NonExistenceClosure(ClosureRule):
        """
        A branch closes when a sentence of the form :s:`~!a` appears on the branch
        *at any world*.
        """
        modal = True

        # tracker implementation

        def check_for_target(self, node: Node, branch: Branch):
            if self.node_will_close_branch(node, branch):
                return {'node': node}

        # rule implementation

        def node_will_close_branch(self, node: Node, branch: Branch) -> bool:
            s: Operated = node.get('sentence')
            if s:
                return s.is_negated and s.negatum.predicate == Existence

        def applies_to_branch(self, branch):
            # Delegate to tracker
            return self.ntch.cached_target(branch)

        def example_nodes(self):
            s = Predicated.first(Existence).negate()
            w = 0 if self.modal else None
            return ({'sentence': s, 'world': w},)

    class DoubleNegation(DefaultNodeRule):
        """
        From an unticked double negation node *n* with world *w* on a branch *b*, add a
        node to *b* with *w* and the double-negatum of *n*, then tick *n*.
        """
        negated  = True
        operator = Oper.Negation
        branch_level = 1

        def _get_node_targets(self, node: Node, branch: Branch):
            s: Operated = self.sentence(node)
            w = node.get('world')
            return {
                'adds': (
                    ({'sentence': s.operand, 'world': w},),
                ),
            }

    class Assertion(DefaultNodeRule):
        """
        From an unticked assertion node *n* with world *w* on a branch *b*,
        add a node to *b* with the operand of *n* and world *w*, then tick *n*.
        """
        operator = Oper.Assertion
        branch_level = 1

        def _get_node_targets(self, node: Node, branch: Branch):
            s: Operated = self.sentence(node)
            w = node.get('world')
            return {
                'adds': (
                    ({'sentence': s.operand, 'world': w},),
                ),
            }

    class AssertionNegated(DefaultNodeRule):
        """
        From an unticked, negated assertion node *n* with world *w* on a branch *b*,
        add a node to *b* with the negation of the assertion of *n* and world *w*,
        then tick *n*.
        """
        negated  = True
        operator = Oper.Assertion
        branch_level = 1

        def _get_node_targets(self, node: Node, branch: Branch):
            s: Operated = self.sentence(node)
            w = node.get('world')
            return {
                'adds': (
                    ({'sentence': s.operand.negate(), 'world': w},),
                ),
            }

    class Conjunction(DefaultNodeRule):
        """
        From an unticked conjunction node *n* with world *w* on a branch *b*, for each conjunct,
        add a node with world *w* to *b* with the conjunct, then tick *n*.
        """
        operator = Oper.Conjunction
        branch_level = 1

        def _get_node_targets(self, node: Node, branch: Branch):
            w = node.get('world')
            return {
                'adds': (
                    tuple(
                        {'sentence': s, 'world': w}
                        for s in self.sentence(node)
                    ),
                ),
            }

    class ConjunctionNegated(DefaultNodeRule):
        """
        From an unticked negated conjunction node *n* with world *w* on a branch *b*, for each
        conjunct, make a new branch *b'* from *b* and add a node with *w* and the negation of
        the conjunct to *b*, then tick *n*.
        """
        negated  = True
        operator = Oper.Conjunction
        branch_level = 2

        def _get_node_targets(self, node: Node, branch: Branch):
            w = node.get('world')
            return {
                'adds': tuple(
                    ({'sentence': s.negate(), 'world': w},)
                    for s in self.sentence(node)
                ),
            }

    class Disjunction(DefaultNodeRule):
        """
        From an unticked disjunction node *n* with world *w* on a branch *b*, for each disjunct,
        make a new branch *b'* from *b* and add a node with the disjunct and world *w* to *b'*,
        then tick *n*.
        """
        operator = Oper.Disjunction
        branch_level = 2

        def _get_node_targets(self, node: Node, branch: Branch):
            w = node.get('world')
            return {
                'adds': tuple(
                    ({'sentence': s, 'world': w},)
                    for s in self.sentence(node)
                ),
            }

    class DisjunctionNegated(DefaultNodeRule):
        """
        From an unticked negated disjunction node *n* with world *w* on a branch *b*, for each
        disjunct, add a node with *w* and the negation of the disjunct to *b*, then tick *n*.
        """
        negated  = True
        operator = Oper.Disjunction
        branch_level = 1

        def _get_node_targets(self, node: Node, branch: Branch):
            s: Operated = self.sentence(node)
            lhs, rhs = s
            w = node.get('world')
            return {
                'adds': (
                    (
                        {'sentence': lhs.negate(), 'world': w},
                        {'sentence': rhs.negate(), 'world': w},
                    ),
                ),
            }

    class MaterialConditional(DefaultNodeRule):
        """
        From an unticked material conditional node *n* with world *w* on a branch *b*, make two
        new branches *b'* and *b''* from *b*, add a node with world *w* and the negation of the
        antecedent to *b'*, and add a node with world *w* and the conequent to *b''*, then tick
        *n*.
        """
        operator = Oper.MaterialConditional
        branch_level = 2

        def _get_node_targets(self, node: Node, branch: Branch):
            s: Operated = self.sentence(node)
            lhs, rhs = s
            w = node.get('world')
            return {
                'adds': (
                    ({'sentence': lhs.negate(), 'world': w},),
                    ({'sentence': rhs         , 'world': w},),
                ),
            }

    class MaterialConditionalNegated(DefaultNodeRule):
        """
        From an unticked negated material conditional node *n* with world *w* on a branch *b*,
        add two nodes with *w* to *b*, one with the antecedent and the other with the negation
        of the consequent, then tick *n*.
        """
        negated  = True
        operator = Oper.MaterialConditional
        branch_level = 1

        def _get_node_targets(self, node: Node, branch: Branch):
            s: Operated = self.sentence(node)
            lhs, rhs = s
            w = node.get('world')
            return {
                'adds': (
                    (
                        {'sentence': lhs         , 'world': w}, 
                        {'sentence': rhs.negate(), 'world': w},
                    ),
                ),
            }

    class MaterialBiconditional(DefaultNodeRule):
        """
        From an unticked material biconditional node *n* with world *w* on a branch *b*, make
        two new branches *b'* and *b''* from *b*, add two nodes with world *w* to *b'*, one with
        the negation of the antecedent and one with the negation of the consequent, and add two
        nodes with world *w* to *b''*, one with the antecedent and one with the consequent, then
        tick *n*.
        """
        operator = Oper.MaterialBiconditional
        branch_level = 2

        def _get_node_targets(self, node: Node, branch: Branch):
            s: Operated = self.sentence(node)
            lhs, rhs = s
            w = node.get('world')
            return {
                'adds': (
                    (
                        {'sentence': lhs.negate(), 'world': w},
                        {'sentence': rhs.negate(), 'world': w},
                    ),
                    (
                        {'sentence': rhs, 'world': w},
                        {'sentence': lhs, 'world': w},
                    ),
                ),
            }

    class MaterialBiconditionalNegated(DefaultNodeRule):
        """
        From an unticked negated material biconditional node *n* with world *w* on a branch *b*,
        make two new branches *b'* and *b''* from *b*, add two nodes with *w* to *b'*, one with
        the antecedent and the other with the negation of the consequent, and add two nodes with
        *w* to *b''*, one with the negation of the antecedent and the other with the consequent,
        then tick *n*.
        """
        negated  = True
        operator = Oper.MaterialBiconditional
        branch_level = 2

        def _get_node_targets(self, node: Node, branch: Branch):
            s: Operated = self.sentence(node)
            lhs, rhs = s
            nrhs = rhs.negate()
            w = node.get('world')
            return {
                'adds': (
                    (
                        {'sentence': lhs , 'world': w},
                        {'sentence': nrhs, 'world': w},
                    ),
                    (
                        {'sentence': nrhs, 'world': w},
                        {'sentence': lhs , 'world': w},
                    ),
                ),
            }

    class Conditional(MaterialConditional):
        """
        The rule functions the same as the corresponding material conditional rule.

        From an unticked conditional node *n* with world *w* on a branch *b*, make two
        new branches *b'* and *b''* from *b*, add a node with world *w* and the negation of the
        antecedent to *b'*, and add a node with world *w* and the conequent to *b''*, then tick
        *n*.
        """
        negated  = False
        operator = Oper.Conditional

    class ConditionalNegated(MaterialConditionalNegated):
        """
        The rule functions the same as the corresponding material conditional rule.

        From an unticked negated conditional node *n* with world *w* on a branch *b*,
        add two nodes with *w* to *b*, one with the antecedent and the other with the negation
        of the consequent, then tick *n*.
        """
        negated  = True
        operator = Oper.Conditional

    class Biconditional(MaterialBiconditional):
        """
        The rule functions the same as the corresponding material biconditional rule.

        From an unticked biconditional node *n* with world *w* on a branch *b*, make
        two new branches *b'* and *b''* from *b*, add two nodes with world *w* to *b'*, one with
        the negation of the antecedent and one with the negation of the consequent, and add two
        nodes with world *w* to *b''*, one with the antecedent and one with the consequent, then
        tick *n*.
        """
        negated  = False
        operator = Oper.Biconditional

    class BiconditionalNegated(MaterialBiconditionalNegated):
        """
        The rule functions the same as the corresponding material biconditional rule.

        From an unticked negated biconditional node *n* with world *w* on a branch *b*,
        make two new branches *b'* and *b''* from *b*, add two nodes with *w* to *b'*, one with
        the antecedent and the other with the negation of the consequent, and add two nodes with
        *w* to *b''*, one with the negation of the antecedent and the other with the consequent,
        then tick *n*.
        """
        negated  = True
        operator = Oper.Biconditional

    class Existential(FDE.QuantifierSkinnyRule):
        """
        From an unticked existential node *n* with world *w* on a branch *b*, quantifying over
        variable *v* into sentence *s*, add a node with world *w* to *b* with the substitution
        into *s* of *v* with a constant new to *b*, then tick *n*.
        """
        quantifier = Quantifier.Existential
        branch_level = 1

        def _get_node_targets(self, node: Node, branch: Branch):
            s: Quantified = self.sentence(node)
            r = s.unquantify(branch.new_constant())
            w = node.get('world')
            return {
                'adds': (({'sentence': r, 'world': w},),),
            }

    class ExistentialNegated(DefaultNodeRule):
        """
        From an unticked negated existential node *n* with world *w* on a branch *b*,
        quantifying over variable *v* into sentence *s*, add a universally quantified
        node to *b* with world *w* over *v* into the negation of *s*, then tick *n*.
        """
        negated    = True
        quantifier = Quantifier.Existential
        convert_to = Quantifier.Universal
        branch_level = 1

        def _get_node_targets(self, node: Node, branch: Branch):
            s: Quantified = self.sentence(node)
            # Keep conversion neutral for inheritance below.
            sq = self.convert_to(s.variable, s.sentence.negate())
            w = node.get('world')
            return {
                'adds': (
                    ({'sentence': sq, 'world': w},),
                ),
            }

    class Universal(FDE.QuantifierFatRule):
        """
        From a universal node with world *w* on a branch *b*, quantifying over variable *v* into
        sentence *s*, result *r* of substituting a constant *c* on *b* (or a new constant if none
        exists) for *v* into *s* does not appear at *w* on *b*, add a node with *w* and *r* to
        *b*. The node *n* is never ticked.
        """
        quantifier   = Quantifier.Universal
        branch_level = 1

        def _get_constant_nodes(self, node: Node, c: Constant, branch: Branch):
            s: Quantified = self.sentence(node)
            r = s.unquantify(c)
            w = node.get('world')
            return ({'sentence': r, 'world': w},)

    class UniversalNegated(ExistentialNegated):
        """
        From an unticked negated universal node *n* with world *w* on a branch *b*,
        quantifying over variable *v* into sentence *s*, add an existentially
        quantified node to *b* with world *w* over *v* into the negation of *s*,
        then tick *n*.
        """
        negated    = True
        quantifier = Quantifier.Universal
        convert_to = Quantifier.Existential

    class Possibility(DefaultNodeRule):
        """
        From an unticked possibility node with world *w* on a branch *b*, add a node with a
        world *w'* new to *b* with the operand of *n*, and add an access-type node with
        world1 *w* and world2 *w'* to *b*, then tick *n*.
        """
        operator = Oper.Possibility
        branch_level = 1

        Helpers = (
            AppliedQuitFlag,
            AppliedSentenceCounter,
            MaxWorldsTracker,
        )
        # Helper Type Annotations
        apqf: AppliedQuitFlag        = Annotate.HelperAttr
        apsc: AppliedSentenceCounter = Annotate.HelperAttr
        maxw: MaxWorldsTracker       = Annotate.HelperAttr

        def _get_node_targets(self, node: Node, branch: Branch):

            # Check for max worlds reached
            if self.maxw.max_worlds_exceeded(branch):
                self.nf.release(node, branch)
                if self.apqf.get(branch):
                    return
                return {
                    'flag': True,
                    'adds': ((self.maxw.quit_flag(branch),),),
                }

            s: Operated = self.sentence(node)
            si = s.operand
            w1 = node['world']
            w2 = branch.next_world

            return {
                'sentence' : si,
                'adds'     : (
                    (
                        {'sentence': si, 'world': w2},
                        {'world1': w1, 'world2': w2},
                    ),
                ),
            }

        def score_candidate(self, target):
            """
            :overrides: AdzHelper.ClosureScore
            """

            if target.get('flag'):
                return 1

            # override
            branch = target.branch
            s = self.sentence(target.node)
            si = s.operand

            # Don't bother checking for closure since we will always have a new world

            track_count = self.apsc[branch].get(si, 0)
            if track_count == 0:
                return 1

            return -1 * self.maxw.modal_complexity(s) * track_count

        def group_score(self, target: Target):

            if target['candidate_score'] > 0:
                return 1

            branch = target.branch
            s = self.sentence(target.node)
            si = s.operand

            return -1 * self.apsc[branch].get(si, 0)

    class PossibilityNegated(DefaultNodeRule):
        """
        From an unticked negated possibility node *n* with world *w* on a branch *b*, add a
        necessity node to *b* with *w*, whose operand is the negation of the negated 
        possibilium of *n*, then tick *n*.
        """
        negated    = True
        operator   = Oper.Possibility
        convert_to = Oper.Necessity
        branch_level = 1

        def _get_node_targets(self, node: Node, branch: Branch):
            s: Operated = self.sentence(node)
            sm = self.convert_to((s.operand.negate(),))
            w = node['world']
            return {
                'adds': (
                    ({'sentence': sm, 'world': w},),
                ),
            }

    class Necessity(DefaultNodeRule):
        """
        From a necessity node *n* with world *w1* and operand *s* on a branch *b*, for any
        world *w2* such that an access node with w1,w2 is on *b*, if *b* does not have a node
        with *s* at *w2*, add it to *b*. The node *n* is never ticked.
        """
        ticking = False
        operator = Oper.Necessity
        branch_level = 1

        Helpers = (
            AppliedNodeCount,
            AppliedNodesWorlds,
            AppliedQuitFlag,
            MaxWorldsTracker,
            VisibleWorldsIndex,
        )

        # Helper Type Annotations
        apnc: AppliedNodeCount   = Annotate.HelperAttr
        apnw: AppliedNodesWorlds = Annotate.HelperAttr
        apqf: AppliedQuitFlag    = Annotate.HelperAttr
        maxw: MaxWorldsTracker   = Annotate.HelperAttr
        visw: VisibleWorldsIndex = Annotate.HelperAttr

        Timers = (
            'get_targets',
        )

        def _get_node_targets(self, node: Node, branch: Branch) -> list[Target]:

            # Check for max worlds reached
            if self.maxw.max_worlds_exceeded(branch):
                self.nf.release(node, branch)
                if self.apqf.get(branch):
                    return
                return {
                    'flag': True,
                    'adds': ((self.maxw.quit_flag(branch),),),
                }

            # Only count least-applied-to nodes
            if not self.apnc.isleast(node, branch):
                return

            with self.timers['get_targets']:

                targets = []

                s: Operated = self.sentence(node)
                si = s.operand
                w1 = node['world']

                for anode in branch.find_all({'world1': w1}):

                    w2 = anode['world2']

                    if (node, w2) in self.apnw[branch]:
                        continue

                    access = Access(w1, w2)
                    if not self.visw.has(branch, w1, w2):
                        continue

                    add = {'sentence': si, 'world': w2}

                    if not branch.has(add):
                        anode = self.visw.nodes[branch][access]
                        targets.append({
                            'sentence' : si,
                            'world'    : w2,
                            'nodes'    : {node, anode},
                            'adds'     : ((add,),),
                        })
            return targets

        def score_candidate(self, target: Target):

            if target.get('flag'):
                return 1

            # We are already restricted to least-applied-to nodes by
            # ``_get_node_targets()``

            # Check for closure
            if self.adz.closure_score(target) == 1:
                return 1

            # Not applied to yet
            apcount = self.apnc[target.branch].get(target.node, 0)
            if apcount == 0:
                return 1

            # Pick the least branching complexity
            return -1 * self.tableau.branching_complexity(target.node)

        def group_score(self, target: Target):

            if self.score_candidate(target) > 0:
                return 1

            return -1 * self.apnc[target.branch].get(target.node, 0)

        def example_nodes(self):
            s = Operated.first(self.operator)
            access = Access(0, 1)
            return (
                {'sentence': s, 'world': access.world1},
                access.tonode(),
            )

    class NecessityNegated(PossibilityNegated):
        """
        From an unticked negated necessity node *n* with world *w* on a branch *b*, add a
        possibility node whose operand is the negation of the negated necessitatum of *n*,
        then tick *n*.
        """
        negated    = True
        operator   = Oper.Necessity
        convert_to = Oper.Possibility

    class IdentityIndiscernability(DefaultNodeRule):
        """
        From an unticked node *n* having an Identity sentence *s* at world *w* on an open branch *b*,
        and a predicated node *n'* whose sentence *s'* has a constant that is a parameter of *s*,
        if the replacement of that constant for the other constant of *s* is a sentence that does
        not appear on *b* at *w*, then add it.
        """
        Helpers = (PredicatedNodesTracker,)

        predicate    = Identity
        branch_level = 1
        ticking      = False

        def _get_node_targets(self, node: Node, branch: Branch) -> list[Target]:
            pnodes = self.pn[branch]
            pa, pb = node['sentence']
            if pa == pb:
                # Substituting a param for itself would be silly.
                return
            targets = []
            # Find other nodes with one of the identicals.
            for n in pnodes:
                if n is node:
                    continue
                s: Predicated = n['sentence']
                if pa in s.params:
                    p_old, p_new = pa, pb
                elif pb in s.params:
                    p_old, p_new = pb, pa
                else:
                    # This continue statement does not register as covered,
                    # but it is by ``test_identity_indiscernability_not_applies()```
                    continue # pragma: no cover
                # Replace p with p1.
                params = substitute_params(s.params, p_old, p_new)
                # Since we have SelfIdentityClosure, we don't need a = a.
                if s.predicate == self.predicate and params[0] == params[1]:
                    continue
                # Create a node with the substituted param.
                s_new = s.predicate(params)
                n_new = {'sentence': s_new, 'world': node.get('world')}
                # Check if it already appears on the branch.
                if branch.has(n_new):
                    continue
                # The rule applies.
                targets.append({
                    'nodes' : {node, n},
                    'adds'  : ((n_new,),),
                })
            return targets

        def example_nodes(self):
            w = 0 if self.modal else None
            s1 = Predicated.first()
            s2 = self.predicate((s1[0], s1[0].next()))
            return (
                {'sentence': s1, 'world': w},
                {'sentence': s2, 'world': w},
            )

    closure_rules = (
        ContradictionClosure,
        SelfIdentityClosure,
        NonExistenceClosure,
    )

    rule_groups = (
        (
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
        ),
        (
            # branching rules
            ConjunctionNegated,
            Disjunction,
            MaterialConditional,
            MaterialBiconditional,
            MaterialBiconditionalNegated,
            Conditional,
            Biconditional,
            BiconditionalNegated,
        ),
        (
            # modal operator rules
            Necessity,
            Possibility,
        ),
        (
            Existential,
            Universal,
        ),
    )
TableauxRules = TabRules