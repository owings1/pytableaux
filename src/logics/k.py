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
from __future__ import annotations
name = 'K'

class Meta(object):
    title    = 'Kripke Normal Modal Logic'
    category = 'Bivalent Modal'
    description = 'Base normal modal logic with no access relation restrictions'
    tags = ['bivalent', 'modal', 'first-order']
    category_display_order = 1

from tools.abcs import static, T
from tools.hybrids import qsetf
from tools.sets import EMPTY_SET

from lexicals import Predicate, Atomic, Constant, Operated, Predicated, Quantified, \
    Operator as Oper, Quantifier, Argument, Sentence, Predicates
from models import BaseModel, Mval

from proof.common import Access
from proof.tableaux import (
    TableauxSystem as BaseSystem,
    Tableau,
)
from proof.baserules import (
    BaseClosureRule,
    BaseNodeRule,
    GetNodeTargetsRule,
    ExtendedQuantifierRule,
    NarrowQuantifierRule,
    OperatedSentenceRule,
    PredicatedSentenceRule,
    QuantifiedSentenceRule,
    group, adds,
)
from proof.common import Access, Branch, Node, Target
from proof.filters import NodeFilters
from proof.helpers import (
    NodesWorlds, AplSentCount,
    MaxWorlds, PredNodes, QuitFlag, AdzHelper,
    FilterHelper, NodeCount, WorldIndex,
)
from errors import DenotationError, ModelValueError, instcheck

import operator as opr

from logics.fde import Model as FDEModel

Identity  = Predicates.System.Identity
Existence = Predicates.System.Existence

def substitute_params(params, old_value, new_value):
    return tuple(new_value if p == old_value else p for p in params)

class Model(BaseModel):
    """
    A K model comprises a non-empty collection of K-frames, a world access
    relation, and a set of constants (the domain).
    """

    class Value(Mval):
        'The admissible values for sentences.'
        F = 'False', 0.0
        T = 'True', 1.0

    unassigned_value = Value.F

    def __init__(self):

        super().__init__()

        #: A map from worlds to their frame. Worlds are reprented as integers.
        #:
        #: :type: dict
        self.frames: dict[int, Frame] = {}

        #: A set of pairs of worlds, which functions as an `access` relation.
        #:
        #: :type: set
        self.access: set[tuple[int, int]] = set()

        #: The fixed domain of constants, common to all worlds in the model.
        #:
        #: :type: set
        self.constants: set[Constant] = set()

        self.predicates: set[Predicate] = {Identity, Existence}
        self.fde = FDEModel()
        self.fde.Value = self.Value

        # ensure there is a w0
        self.world_frame(0)

    def value_of_operated(self, s: Operated, **kw):
        if self.is_sentence_opaque(s):
            return self.value_of_opaque(s, **kw)
        if s.operator in self.modal_operators:
            return self.value_of_modal(s, **kw)
        return super().value_of_operated(s, **kw)

    def value_of_predicated(self, s: Predicated, **kw):
        """
        A sentence for predicate `P` is true at :m:`w` iff the tuple of the parameters
        is in the extension of `P` at :m:`w`.
        """
        params = s.params
        for param in params:
            if param not in self.constants:
                raise DenotationError(
                    'Parameter {0} is not in the constants'.format(param)
                )
        if params in self.get_extension(s.predicate, **kw):
            return self.Value.T
        return self.Value.F

    def value_of_existential(self, s: Quantified, **kw):
        """
        An existential sentence is true at :m:`w`, just when the sentence resulting in the
        subsitution of some constant in the domain for the variable is true at :m:`w`.
        """
        Value = self.Value
        Tru = Value.T
        for c in self.constants:
            if self.value_of(c >> s, **kw) is Tru:
                return Tru
        return Value.F

    def value_of_universal(self, s: Quantified, **kw):
        """
        A universal sentence is true at :m:`w`, just when the sentence resulting in the
        subsitution of each constant in the domain for the variable is true at :m:`w`.
        """
        Value = self.Value
        Fals = Value.F
        for c in self.constants:
            if self.value_of(c >> s, **kw) is Fals:
                return Fals
        return Value.T

    def value_of_possibility(self, s: Operated, world=0, **kw):
        """
        A possibility sentence is true at :m:`w` iff its operand is true at :m:`w'` for
        some :m:`w'` such that :m:`<w, w'>` in the access relation.
        """
        Value = self.Value
        Tru = Value.T
        for w2 in self.visibles(world):
            if self.value_of(s.lhs, world=w2, **kw) is Tru:
                return Tru
        return Value.F

    def value_of_necessity(self, s: Operated, world=0, **kw):
        """
        A necessity sentence is true at :m:`w` iff its operand is true at :m:`w'` for
        each :m:`w'` such that :m:`<w, w'>` is in the access relation.
        """
        Value = self.Value
        Fals = Value.F
        for w2 in self.visibles(world):
            if self.value_of(s.lhs, world=w2, **kw) is Fals:
                return Fals
        return Value.T

    def is_countermodel_to(self, argument: Argument):
        """
        A model is a countermodel for an argument iff the value of each premise
        is :m:`T` at `w0` and the value of the conclusion is :m:`F` at :m:`w0`.
        """
        Value = self.Value
        Tru = Value.T
        for premise in argument.premises:
            if self.value_of(premise, world=0) is not Tru:
                return False
        return self.value_of(argument.conclusion, world=0) is Value.F

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

    def read_node(self, node: Node):
        s: Sentence = node.get('sentence')
        if s:
            w = node.get('world')
            if w == None:
                w = 0
            if self.is_sentence_opaque(s):
                self.set_opaque_value(s, self.Value.T, world = w)
            elif self.is_sentence_literal(s):
                self.set_literal_value(s, self.Value.T, world = w)
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
            self._generate_denotation(w)
            self._generate_property_classes(w)

            for pred in self.predicates:
                self._agument_extension_with_identicals(pred, w)
            self._ensure_self_identity(w)
            self._ensure_self_existence(w)

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

    def _ensure_self_identity(self, w):
        ext = self.get_extension(Identity, world = w)
        for c in self.constants:
            # make sure each constant is self-identical
            ext.add((c, c))

    def _ensure_self_existence(self, w):
        ext = self.get_extension(Existence, world = w)
        for c in self.constants:
            # make sure each constant exists
            ext.add((c,))

    def _agument_extension_with_identicals(self, pred: Predicate, w):
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

    def _generate_denotation(self, w: int):
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

    def _generate_property_classes(self, w):
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

    def get_identicals(self, c: Constant, **kw) -> set[Constant]:
        ext = self.get_extension(Identity, **kw)
        identicals = set()
        for params in ext:
            if c in params:
                identicals.update(params)
        identicals.discard(c)
        return identicals

    def set_literal_value(self, s: Sentence, value, **kw):
        cls = s.TYPE.cls
        if self.is_sentence_opaque(s):
            self.set_opaque_value(s, value, **kw)
        elif cls is Operated and s.operator is Oper.Negation:
            negval = self.truth_function(s.operator, value)
            self.set_literal_value(s.lhs, negval, **kw)
        elif cls is Atomic:
            self.set_atomic_value(s, value, **kw)
        elif cls is Predicated:
            self.set_predicated_value(s, value, **kw)
        else:
            raise NotImplementedError

    def set_opaque_value(self, s: Sentence, value, world = 0, **kw):
        value = self.Value[value]
        frame = self.world_frame(world)
        if frame.opaques.get(s, value) is not value:
            raise ModelValueError('Inconsistent value for sentence {0}'.format(s))
        # We might have a quantified opaque sentence, in which case we will need
        # to still check every subsitution, so we want the constants.
        # NB: in FDE we added the atomics to all_atomics, but we don't have that
        #     here since we do frames -- will that be a problem?
        self.constants.update(s.constants)
        self.predicates.update(s.predicates)
        frame.opaques[s] = value

    def set_atomic_value(self, s: Atomic, value, world = 0, **kw):
        value = self.Value[value]
        frame = self.world_frame(world)
        if s in frame.atomics and frame.atomics[s] is not value:
            raise ModelValueError('Inconsistent value for sentence {0}'.format(s))
        frame.atomics[s] = value

    def set_predicated_value(self, s: Predicated, value, **kw):
        Value = self.Value
        value = Value[value]
        pred = s.predicate
        params = s.params
        if pred not in self.predicates:
            self.predicates.add(pred)
        for param in params:
            if param.is_constant:
                self.constants.add(param)
        extension = self.get_extension(pred, **kw)
        anti_extension = self.get_anti_extension(pred, **kw)
        if value is Value.F:
            if params in extension:
                raise ModelValueError(
                    'Cannot set value {0} for tuple {1} already in extension'.format(
                        value, params
                    )
                )
            anti_extension.add(params)
        if value is Value.T:
            if params in anti_extension:
                raise ModelValueError(
                    'Cannot set value {0} for tuple {1} already in anti-extension'.format(
                        value, params
                    )
                )
            extension.add(params)

    def get_extension(self, pred, world = 0, **kw) -> set[tuple[Constant, ...]]:
        frame = self.world_frame(world)
        if pred not in self.predicates:
            self.predicates.add(pred)
        if pred not in frame.extensions:
            frame.extensions[pred] = set()
        if pred not in frame.anti_extensions:
            frame.anti_extensions[pred] = set()
        return frame.extensions[pred]

    def get_anti_extension(self, pred, world = 0, **kw) -> set[tuple[Constant, ...]]:
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

    def value_of_opaque(self, s: Sentence, world = 0, **kw):
        return self.world_frame(world).opaques.get(s, self.unassigned_value)

    def value_of_atomic(self, s: Atomic, world = 0, **kw):
        return self.world_frame(world).atomics.get(s, self.unassigned_value)

    def value_of_modal(self, s: Operated, **kw):
        oper = s.operator
        if oper == Oper.Possibility:
            return self.value_of_possibility(s, **kw)
        if oper == Oper.Necessity:
            return self.value_of_necessity(s, **kw)
        raise NotImplementedError

    def value_of_quantified(self, s: Quantified, **kw):
        q = s.quantifier
        if q == Quantifier.Existential:
            return self.value_of_existential(s, **kw)
        elif q == Quantifier.Universal:
            return self.value_of_universal(s, **kw)
        raise NotImplementedError

    def truth_function(self, operator: Oper, a, b=None):
        return self.fde.truth_function(operator, a, b)

class Denotum:
    __slots__ = EMPTY_SET
    # WIP - Generating "objects" like k-constants for a domain, dentation, and
    #       predicate "property" extensions.
    #
    #       With the current implemtation of how values are set and checked
    #       dynamically for integrity, we can't easily generate a useful
    #       domain until we know the model is finished.
    #
    #       For now, the purpose of this WIP feature is merely informational.
    pass

class Frame:
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

    def get_data(self) -> dict:
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
                        for sentence in sorted(self.atomics)
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
                        for sentence in sorted(self.opaques)
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
                        for pred in sorted(self.extensions)
                    ]
                }
            }
        }

    def is_equivalent_to(self, other) -> bool:
        other = instcheck(other, Frame)
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
        if not isinstance(other, Frame):
            return NotImplemented
        return self.__dict__ == other.__dict__

    def __ne__(self, other):
        if not isinstance(other, Frame):
            return NotImplemented
        return other == None or self.__dict__ != other.__dict__

    def __lt__(self, other):
        if not isinstance(other, Frame):
            return NotImplemented
        return self.world < other.world

    def __le__(self, other):
        if not isinstance(other, Frame):
            return NotImplemented
        return self.world <= other.world

    def __gt__(self, other):
        if not isinstance(other, Frame):
            return NotImplemented
        return self.world > other.world

    def __ge__(self, other):
        if not isinstance(other, Frame):
            return NotImplemented
        return self.world >= other.world

@static
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

    modal = True

    @classmethod
    def build_trunk(cls, tab: Tableau, arg: Argument, /):
        """
        To build the trunk for an argument, add a node with each premise, with
        world :m:`*w0*`, followed by a node with the negation of the conclusion
        with world :m:`*w0*`.
        """
        w = 0 if cls.modal else None
        add = tab.branch().append
        for premise in arg.premises:
            add(swnode(premise, w))
        add(swnode(~arg.conclusion, w))

    @classmethod
    def branching_complexity(cls, node: Node) -> int:
        s: Sentence = node.get('sentence')
        if s is None:
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

class DefaultNodeRule(GetNodeTargetsRule):
    """Default K node rule with:
    
    - NodeFilters.Modal with defaults: modal = `True`, access = `None`.
    - NodeFilter implements `_get_targets()` with abstract `_get_node_targets()`.
    - FilterHelper implements `example_nodes()` with its `example_node()` method.
    - AdzHelper implements `_apply()` with its `_apply()` method.
    - AdzHelper implements `score_candidate()` with its `closure_score()` method.
    """
    NodeFilters =  NodeFilters.Modal,
    modal  : bool = True
    access : bool|None = None

class OperatorNodeRule(OperatedSentenceRule, DefaultNodeRule):
    'Convenience mixin class for most common rules.'
    pass


def swnode(s: Sentence, w: int|None):
    'Make a sentence/world node dict. Excludes world if None.'
    if w is None:
        return dict(sentence = s)
    return dict(sentence = s, world = w)

def anode(w1: int, w2: int):
    'Make an Access node dict.'
    return Access(w1, w2).todict()

@static
class TabRules:
    """
    Rules for modal operators employ *world* indexes as well access-type
    nodes. The world indexes are transparent for the rules for classical
    connectives.
    """

    class ContradictionClosure(BaseClosureRule):
        """
        A branch closes when a sentence and its negation both appear on a node **with the
        same world** on the branch.
        """
        modal = True

        def _branch_target_hook(self, node: Node, branch: Branch, /):
            nnode = self._find_closing_node(node, branch)
            if nnode is not None:
                return Target(
                    nodes = qsetf((node, nnode)),
                    branch = branch,
                )

        def node_will_close_branch(self, node: Node, branch: Branch, /) -> bool:
            return bool(self._find_closing_node(node, branch))

        def example_nodes(self):
            s = Atomic.first()
            w = 0 if self.modal else None
            return swnode(s, w), swnode(~s, w)

        # private util

        def _find_closing_node(self, node: Node, branch: Branch, /):
            s = self.sentence(node)
            if s is not None:
                return branch.find(swnode(s.negative(), node.get('world')))

    class SelfIdentityClosure(BaseClosureRule, PredicatedSentenceRule):
        """
        A branch closes when a sentence of the form :s:`~a = a` appears on the
        branch *at any world*.
        """
        modal = True
        negated = True
        predicate = Predicate.System.Identity

        def _branch_target_hook(self, node: Node, branch: Branch):
            res = self.node_will_close_branch(node, branch)
            if res:
                return Target(node = node, branch = branch)
            if res is False:
                self[FilterHelper].release(node, branch)

        def node_will_close_branch(self, node: Node, branch: Branch,/) -> bool:
            if self[FilterHelper](node, branch):
                if len(self.sentence(node).paramset) == 1:
                    return True
                return False

        def example_nodes(self):
            w = 0 if self.modal else None
            c = Constant.first()
            return swnode(~self.predicate((c, c)), w),

    class NonExistenceClosure(BaseClosureRule):
        """
        A branch closes when a sentence of the form :s:`~!a` appears on the branch
        *at any world*.
        """
        modal = True

        def _branch_target_hook(self, node: Node, branch: Branch,/):
            if self.node_will_close_branch(node, branch):
                return Target(node = node, branch = branch)

        def node_will_close_branch(self, node: Node, _,/):
            s = node.get('sentence')
            return (
                isinstance(s, Operated) and
                s.operator is Oper.Negation and
                isinstance(s.lhs, Predicated) and
                s.lhs.predicate == Existence
            )

        def example_nodes(self):
            s = ~Predicated.first(Existence)
            w = 0 if self.modal else None
            return swnode(s, w),

    class DoubleNegation(OperatorNodeRule):
        """
        From an unticked double negation node *n* with world *w* on a branch *b*, add a
        node to *b* with *w* and the double-negatum of *n*, then tick *n*.
        """
        negated  = True
        operator = Oper.Negation
        branch_level = 1

        def _get_node_targets(self, node: Node, _):
            return adds(
                group(swnode(self.sentence(node).lhs, node.get('world')))
            )

    class Assertion(OperatorNodeRule):
        """
        From an unticked assertion node *n* with world *w* on a branch *b*,
        add a node to *b* with the operand of *n* and world *w*, then tick *n*.
        """
        operator = Oper.Assertion
        branch_level = 1

        def _get_node_targets(self, node: Node, _):
            return adds(
                group(swnode(self.sentence(node).lhs, node.get('world')))
            )

    class AssertionNegated(OperatorNodeRule):
        """
        From an unticked, negated assertion node *n* with world *w* on a branch *b*,
        add a node to *b* with the negation of the assertion of *n* and world *w*,
        then tick *n*.
        """
        negated  = True
        operator = Oper.Assertion
        branch_level = 1

        def _get_node_targets(self, node: Node, _):
            return adds(
                group(swnode(~self.sentence(node).lhs, node.get('world')))
            )

    class Conjunction(OperatorNodeRule):
        """
        From an unticked conjunction node *n* with world *w* on a branch *b*,
        for each conjunct, add a node with world *w* to *b* with the conjunct,
        then tick *n*.
        """
        operator = Oper.Conjunction
        branch_level = 1

        def _get_node_targets(self, node: Node, _):
            s = self.sentence(node)
            w = node.get('world')
            return adds(
                group(swnode(s.lhs, w), swnode(s.rhs, w))
            )

    class ConjunctionNegated(OperatorNodeRule):
        """
        From an unticked negated conjunction node *n* with world *w* on a branch *b*, for each
        conjunct, make a new branch *b'* from *b* and add a node with *w* and the negation of
        the conjunct to *b*, then tick *n*.
        """
        negated  = True
        operator = Oper.Conjunction
        branch_level = 2

        def _get_node_targets(self, node: Node, _):
            s = self.sentence(node)
            w = node.get('world')
            return adds(
                group(swnode(~s.lhs, w)),
                group(swnode(~s.rhs, w)),
            )

    class Disjunction(OperatorNodeRule):
        """
        From an unticked disjunction node *n* with world *w* on a branch *b*, for each disjunct,
        make a new branch *b'* from *b* and add a node with the disjunct and world *w* to *b'*,
        then tick *n*.
        """
        operator = Oper.Disjunction
        branch_level = 2

        def _get_node_targets(self, node: Node, _):
            s = self.sentence(node)
            w = node.get('world')
            return adds(
                group(swnode(s.lhs, w)),
                group(swnode(s.rhs, w)),
            )

    class DisjunctionNegated(OperatorNodeRule):
        """
        From an unticked negated disjunction node *n* with world *w* on a branch *b*, for each
        disjunct, add a node with *w* and the negation of the disjunct to *b*, then tick *n*.
        """
        negated  = True
        operator = Oper.Disjunction
        branch_level = 1

        def _get_node_targets(self, node: Node, _):
            s = self.sentence(node)
            w = node.get('world')
            return adds(
                group(swnode(~s.lhs, w), swnode(~s.rhs, w))
            )

    class MaterialConditional(OperatorNodeRule):
        """
        From an unticked material conditional node *n* with world *w* on a branch *b*, make two
        new branches *b'* and *b''* from *b*, add a node with world *w* and the negation of the
        antecedent to *b'*, and add a node with world *w* and the conequent to *b''*, then tick
        *n*.
        """
        operator = Oper.MaterialConditional
        branch_level = 2

        def _get_node_targets(self, node: Node, _):
            s = self.sentence(node)
            w = node.get('world')
            return adds(
                group(swnode(~s.lhs, w)),
                group(swnode( s.rhs, w)),
            )

    class MaterialConditionalNegated(OperatorNodeRule):
        """
        From an unticked negated material conditional node *n* with world *w* on a branch *b*,
        add two nodes with *w* to *b*, one with the antecedent and the other with the negation
        of the consequent, then tick *n*.
        """
        negated  = True
        operator = Oper.MaterialConditional
        branch_level = 1

        def _get_node_targets(self, node: Node, _):
            s = self.sentence(node)
            w = node.get('world')
            return adds(
                group(swnode(s.lhs, w), swnode(~s.rhs, w))
            )

    class MaterialBiconditional(OperatorNodeRule):
        """
        From an unticked material biconditional node *n* with world *w* on a branch *b*, make
        two new branches *b'* and *b''* from *b*, add two nodes with world *w* to *b'*, one with
        the negation of the antecedent and one with the negation of the consequent, and add two
        nodes with world *w* to *b''*, one with the antecedent and one with the consequent, then
        tick *n*.
        """
        operator = Oper.MaterialBiconditional
        branch_level = 2

        def _get_node_targets(self, node: Node, _):
            s = self.sentence(node)
            w = node.get('world')
            lhs, rhs = s
            return adds(
                group(swnode(~lhs, w), swnode(~rhs, w)),
                group(swnode( rhs, w), swnode( lhs, w)),
            )

    class MaterialBiconditionalNegated(OperatorNodeRule):
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

        def _get_node_targets(self, node: Node, _):
            s = self.sentence(node)
            w = node.get('world')
            lhs, rhs = s
            return adds(
                group(swnode( lhs, w), swnode(~rhs, w)),
                group(swnode(~rhs, w), swnode( lhs, w)),
            )

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

    class Existential(NarrowQuantifierRule, DefaultNodeRule):
        """
        From an unticked existential node *n* with world *w* on a branch *b*, quantifying over
        variable *v* into sentence *s*, add a node with world *w* to *b* with the substitution
        into *s* of *v* with a constant new to *b*, then tick *n*.
        """
        quantifier = Quantifier.Existential
        branch_level = 1

        def _get_node_targets(self, node: Node, branch: Branch):
            s = self.sentence(node)
            return adds(
                group(swnode(branch.new_constant() >> s, node.get('world')))
            )

    class ExistentialNegated(QuantifiedSentenceRule, DefaultNodeRule):
        """
        From an unticked negated existential node *n* with world *w* on a branch *b*,
        quantifying over variable *v* into sentence *s*, add a universally quantified
        node to *b* with world *w* over *v* into the negation of *s*, then tick *n*.
        """
        negated    = True
        quantifier = Quantifier.Existential
        convert    = Quantifier.Universal
        branch_level = 1

        def _get_node_targets(self, node: Node, _):
            v, si = self.sentence(node)[1:]
            # Keep conversion neutral for inheritance below.
            return adds(
                group(swnode(self.convert(v, ~si), node.get('world')))
            )

    class Universal(ExtendedQuantifierRule, DefaultNodeRule):
        """
        From a universal node with world *w* on a branch *b*, quantifying over variable *v* into
        sentence *s*, result *r* of substituting a constant *c* on *b* (or a new constant if none
        exists) for *v* into *s* does not appear at *w* on *b*, add a node with *w* and *r* to
        *b*. The node *n* is never ticked.
        """
        quantifier   = Quantifier.Universal
        branch_level = 1

        def _get_constant_nodes(self, node: Node, c: Constant, _, /):
            return group(swnode(c >> self.sentence(node), node.get('world')))

    class UniversalNegated(ExistentialNegated):
        """
        From an unticked negated universal node *n* with world *w* on a branch *b*,
        quantifying over variable *v* into sentence *s*, add an existentially
        quantified node to *b* with world *w* over *v* into the negation of *s*,
        then tick *n*.
        """
        negated    = True
        quantifier = Quantifier.Universal
        convert = Quantifier.Existential

    class Possibility(OperatedSentenceRule, DefaultNodeRule):
        """
        From an unticked possibility node with world *w* on a branch *b*, add a node with a
        world *w'* new to *b* with the operand of *n*, and add an access-type node with
        world1 *w* and world2 *w'* to *b*, then tick *n*.
        """
        operator = Oper.Possibility
        branch_level = 1

        Helpers = QuitFlag, MaxWorlds, AplSentCount,

        def _get_node_targets(self, node: Node, branch: Branch):

            # Check for max worlds reached
            if self[MaxWorlds].max_worlds_exceeded(branch):
                self[FilterHelper].release(node, branch)
                if self[QuitFlag].get(branch):
                    return
                fnode = self[MaxWorlds].quit_flag(branch)
                return adds(group(fnode)) | dict(flag = True)

            si = self.sentence(node).lhs
            w1 = node['world']
            w2 = branch.next_world
            return dict(sentence = si) | adds(
                group(swnode(si, w2), Access(w1, w2).todict())
            )

        def score_candidate(self, target: Target):
            """
            :overrides: AdzHelper closure score
            """
            if target.get('flag'):
                return 1.0
            # override
            branch = target.branch
            s = self.sentence(target.node)
            si = s.lhs
            # Don't bother checking for closure since we will always have a new world
            track_count = self[AplSentCount][branch].get(si, 0)
            if track_count == 0:
                return 1.0
            return -1.0 * self[MaxWorlds].modal_complexity(s) * track_count

        def group_score(self, target: Target):
            if target['candidate_score'] > 0:
                return 1.0
            s = self.sentence(target.node)
            si = s.lhs
            return -1.0 * self[AplSentCount][target.branch].get(si, 0)

    class PossibilityNegated(OperatorNodeRule):
        """
        From an unticked negated possibility node *n* with world *w* on a branch *b*, add a
        necessity node to *b* with *w*, whose operand is the negation of the negated 
        possibilium of *n*, then tick *n*.
        """
        negated    = True
        operator   = Oper.Possibility
        convert    = Oper.Necessity
        branch_level = 1

        def _get_node_targets(self, node: Node, _):
            s = self.sentence(node)
            return adds(
                group(swnode(self.convert(~s.lhs), node['world']))
            )

    class Necessity(OperatedSentenceRule, DefaultNodeRule):
        """
        From a necessity node *n* with world *w1* and operand *s* on a branch *b*, for any
        world *w2* such that an access node with w1,w2 is on *b*, if *b* does not have a node
        with *s* at *w2*, add it to *b*. The node *n* is never ticked.
        """
        ticking = False
        operator = Oper.Necessity
        branch_level = 1

        Helpers = QuitFlag, MaxWorlds, NodeCount, NodesWorlds, WorldIndex,

        Timers = 'get_targets',

        def _get_node_targets(self, node: Node, branch: Branch):

            # Check for max worlds reached
            if self[MaxWorlds].max_worlds_exceeded(branch):
                self[FilterHelper].release(node, branch)
                if self[QuitFlag].get(branch):
                    return
                fnode = self[MaxWorlds].quit_flag(branch)
                return adds(group(fnode)) | dict(flag = True)

            # Only count least-applied-to nodes
            if not self[NodeCount].isleast(node, branch):
                return

            with self.timers['get_targets']:

                targets = []

                s = self.sentence(node)
                si = s.lhs
                w1 = node['world']

                for w2 in self[WorldIndex][branch].get(w1, EMPTY_SET):
                    if (node, w2) in self[NodesWorlds][branch]:
                        continue
                    add = swnode(si, w2)
                    if not branch.has(add):
                        anode = self[WorldIndex].nodes[branch][w1, w2]
                        targets.append(dict(
                            sentence = si,
                            world    = w2,
                            nodes    = qsetf({node, anode}),
                            ** adds(group(add))
                        ))
            return targets

        def score_candidate(self, target: Target):

            if target.get('flag'):
                return 1.0

            # We are already restricted to least-applied-to nodes by
            # ``_get_node_targets()``

            # Check for closure
            if self[AdzHelper].closure_score(target) == 1:
                return 1.0

            # Not applied to yet
            apcount = self[NodeCount][target.branch].get(target.node, 0)
            if apcount == 0:
                return 1.0

            # Pick the least branching complexity
            return -1.0 * self.tableau.branching_complexity(target.node)

        def group_score(self, target: Target):

            if self.score_candidate(target) > 0:
                return 1.0

            return -1.0 * self[NodeCount][target.branch].get(target.node, 0)

        def example_nodes(self):
            s = Operated.first(self.operator)
            a = Access(0, 1)
            return swnode(s, a.w1), a.todict()

    class NecessityNegated(PossibilityNegated):
        """
        From an unticked negated necessity node *n* with world *w* on a branch *b*, add a
        possibility node whose operand is the negation of the negated necessitatum of *n*,
        then tick *n*.
        """
        operator = Oper.Necessity
        convert  = Oper.Possibility

    class IdentityIndiscernability(PredicatedSentenceRule, DefaultNodeRule):
        """
        From an unticked node *n* having an Identity sentence *s* at world *w* on an open branch *b*,
        and a predicated node *n'* whose sentence *s'* has a constant that is a parameter of *s*,
        if the replacement of that constant for the other constant of *s* is a sentence that does
        not appear on *b* at *w*, then add it.
        """
        ticking   = False
        predicate = Predicate.System.Identity

        branch_level = 1

        def _get_node_targets(self, node: Node, branch: Branch) -> list[Target]:
            pnodes = self[PredNodes][branch]
            pa, pb = self.sentence(node)
            if pa == pb:
                # Substituting a param for itself would be silly.
                return
            targets = []
            w = node.get('world')
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
                n_new = swnode(s.predicate(params), w)
                # Check if it already appears on the branch.
                if branch.has(n_new):
                    continue
                # The rule applies.
                targets.append(dict(
                    nodes = qsetf({node, n}),
                    ** adds(group(n_new)),
                ))
            return targets

        def example_nodes(self):
            w = 0 if self.modal else None
            s1 = Predicated.first()
            s2 = self.predicate((s1[0], s1[0].next()))
            return swnode(s1, w), swnode(s2, w)

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

del(static)