# -*- coding: utf-8 -*-
# pytableaux, a multi-logic proof generator.
# Copyright (C) 2014-2022 Doug Owings.
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

from typing import Any, Callable, Optional, cast

from pytableaux.errors import DenotationError, ModelValueError, check
from pytableaux.lang.collect import Argument
from pytableaux.lang.lex import (Atomic, Constant, Operated, Operator,
                                 Predicate, Predicated, Quantified, Quantifier,
                                 Sentence)
from pytableaux.logics import fde as FDE
from pytableaux.models import BaseModel, ValueCPL
from pytableaux.proof import TableauxSystem as BaseSystem
from pytableaux.proof import filters, rules
from pytableaux.proof.common import Branch, Node, Target
from pytableaux.proof.helpers import (AdzHelper, AplSentCount, FilterHelper,
                                      MaxWorlds, NodeCount, NodesWorlds,
                                      PredNodes, QuitFlag, WorldIndex)
from pytableaux.proof.tableaux import Tableau
from pytableaux.proof.util import Access, adds, group, swnode
from pytableaux.tools import closure
from pytableaux.tools.hybrids import qsetf
from pytableaux.tools.sets import EMPTY_SET
from pytableaux.tools.typing import LogicType

name = 'K'

class Meta:
    title       = 'Kripke Normal Modal Logic'
    category    = 'Bivalent Modal'
    description = 'Base normal modal logic with no access relation restrictions'
    category_order = 1
    tags = (
        'bivalent',
        'modal',
        'first-order',
    )
    native_operators = FDE.Meta.native_operators + (Operator.Possibility, Operator.Necessity)

def substitute_params(params, old_value, new_value):
    return tuple(new_value if p == old_value else p for p in params)

class Model(BaseModel[ValueCPL]):
    """
    A K model comprises a non-empty collection of K-frames, a world access
    relation, and a set of constants (the domain).
    """

    Value = ValueCPL

    unassigned_value = Value.F

    frames: dict[int, Frame]
    "A map from worlds to their frame"

    access: set[tuple[int, int]]
    "A set of pairs of worlds, i.e. the `access` relation"

    constants: set[Constant]
    "The fixed domain of constants, common to all worlds in the model"


    def __init__(self):

        super().__init__()

        self.frames = {}
        self.access = set()
        self.constants = set()

        self.predicates: set[Predicate] = set(Predicate.System)

        # ensure there is a w0
        self.world_frame(0)

    @staticmethod
    @closure
    def truth_function(Value = Value):
        model = FDE.Model()
        model.Value = Value
        return cast(
            Callable[[Operator, Any, Optional[Any]], ValueCPL],
            model.truth_function,
        )

    def value_of_predicated(self, s: Predicated, **kw):
        """
        A sentence for predicate `P` is true at :m:`w` iff the tuple of the parameters
        is in the extension of `P` at :m:`w`.
        """
        params = s.params
        for param in params:
            if param not in self.constants:
                raise DenotationError(f'Parameter {param} is not in the constants')
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

    def value_of_possibility(self, s: Operated, world: int = 0, **kw):
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

    def value_of_necessity(self, s: Operated, /, world: int = 0, **kw):
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

    def is_countermodel_to(self, argument: Argument, /) -> bool:
        """
        A model is a countermodel for an argument iff the value of each premise
        is V{T} at `w0` and the value of the conclusion is V{F} at :m:`w0`.
        """
        Value = self.Value
        Tru = Value.T
        for premise in argument.premises:
            if self.value_of(premise, world = 0) is not Tru:
                return False
        return self.value_of(argument.conclusion, world = 0) is Value.F

    def get_data(self) -> dict:
        return dict(
            Worlds = dict(
                description     = 'set of worlds',
                in_summary      = True,
                datatype        = 'set',
                member_datatype = 'int',
                member_typehint = 'world',
                symbol          = 'W',
                values          = sorted(self.frames),
            ),
            Access = dict(
                description     = 'access relation',
                in_summary      = True,
                datatype        = 'set',
                typehint        = 'access_relation',
                member_datatype = 'tuple',
                member_typehint = 'access',
                symbol          = 'R',
                values          = sorted(self.access),
            ),
            Frames = dict(
                description     = 'world frames',
                datatype        = 'list',
                typehint        = 'frames',
                member_datatype = 'map',
                member_typehint = 'frame',
                symbol          = 'F',
                values          = [
                    frame.get_data()
                    for frame in sorted(self.frames.values())
                ]
            )
        )

    def read_branch(self, branch: Branch, /):
        for _ in map(self._read_node, branch):
            pass
        self.finish()

    def _read_node(self, node: Node, /):
        s = node.get('sentence')
        if s is not None:
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
        ext = self.get_extension(Predicate.System.Identity, world = w)
        for c in self.constants:
            # make sure each constant is self-identical
            ext.add((c, c))

    def _ensure_self_existence(self, w):
        ext = self.get_extension(Predicate.System.Existence, world = w)
        for c in self.constants:
            # make sure each constant exists
            ext.add((c,))

    def _agument_extension_with_identicals(self, pred: Predicate, w):
        extension = self.get_extension(pred, world = w)
        for c in self.constants:
            identicals = self._get_identicals(c, world = w)
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
                denoters = {c}.union(self._get_identicals(c, world = w))
                frame.denotation.update({c: denotum for c in denoters})
                todo -= denoters
        assert not todo

    def _generate_property_classes(self, w):
        frame = self.world_frame(w)
        w = frame.world
        for pred in self.predicates:
            # Skip identity and existence
            if pred in Predicate.System:
                continue
            frame.property_classes[pred] = {
                tuple(self.get_denotum(p, world = w) for p in params)
                for params in self.get_extension(pred, world = w)
            }

    def _get_identicals(self, c: Constant, **kw) -> set[Constant]:
        ext = self.get_extension(Predicate.System.Identity, **kw)
        identicals = set()
        for params in ext:
            if c in params:
                identicals.update(params)
        identicals.discard(c)
        return identicals

    def set_literal_value(self, s: Sentence, value: ValueCPL, /, **kw):
        if self.is_sentence_opaque(s):
            self.set_opaque_value(s, value, **kw)
        elif (stype := type(s)) is Operated and s.operator is Operator.Negation:
            negval = self.truth_function(s.operator, value)
            self.set_literal_value(s.lhs, negval, **kw)
        elif stype is Atomic:
            self.set_atomic_value(s, value, **kw)
        elif stype is Predicated:
            self.set_predicated_value(s, value, **kw)
        else:
            raise NotImplementedError

    def set_opaque_value(self, s: Sentence, value: ValueCPL, /, world: int = 0):
        value = self.Value[value]
        frame = self.world_frame(world)
        if frame.opaques.get(s, value) is not value:
            raise ModelValueError(f'Inconsistent value for sentence {s}')
        # We might have a quantified opaque sentence, in which case we will need
        # to still check every subsitution, so we want the constants.
        # NB: in FDE we added the atomics to all_atomics, but we don't have that
        #     here since we do frames -- will that be a problem?
        self.constants.update(s.constants)
        self.predicates.update(s.predicates)
        frame.opaques[s] = value

    def set_atomic_value(self, s: Atomic, value: ValueCPL, /, world: int = 0):
        value = self.Value[value]
        frame = self.world_frame(world)
        if s in frame.atomics and frame.atomics[s] is not value:
            raise ModelValueError(f'Inconsistent value for sentence {s}')
        frame.atomics[s] = value

    def set_predicated_value(self, s: Predicated, value: ValueCPL, /, **kw):
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
                    f'Cannot set value {value} for tuple {params} already in extension'
                )
            anti_extension.add(params)
        if value is Value.T:
            if params in anti_extension:
                raise ModelValueError(
                    f'Cannot set value {value} for tuple {params} already in anti-extension'
                )
            extension.add(params)

    def get_extension(self, pred: Predicate, /, world: int = 0) -> set[tuple[Constant, ...]]:
        frame = self.world_frame(world)
        if pred not in self.predicates:
            self.predicates.add(pred)
        if pred not in frame.extensions:
            frame.extensions[pred] = set()
        if pred not in frame.anti_extensions:
            frame.anti_extensions[pred] = set()
        return frame.extensions[pred]

    def get_anti_extension(self, pred: Predicate, /, world: int = 0) -> set[tuple[Constant, ...]]:
        frame = self.world_frame(world)
        if pred not in self.predicates:
            self.predicates.add(pred)
        if pred not in frame.extensions:
            frame.extensions[pred] = set()
        if pred not in frame.anti_extensions:
            frame.anti_extensions[pred] = set()
        return frame.anti_extensions[pred]

    def get_domain(self, world: int = 0):
        # TODO: wip
        return self.world_frame(world).domain

    def get_denotation(self, world: int = 0):
        # TODO: wip
        return self.world_frame(world).denotation

    def get_denotum(self, c: Constant, /, world = 0):
        # TODO: wip
        frame = self.world_frame(world)
        world = frame.world
        den = self.get_denotation(world = world)
        try:
            return den[c]
        except KeyError:
            raise DenotationError(f'{c} does not have a reference at w{world}')

    def add_access(self, w1: int, w2: int, /):
        self.access.add((w1, w2))
        self.world_frame(w1)
        self.world_frame(w2)

    def has_access(self, w1: int, w2: int, /) -> bool:
        return (w1, w2) in self.access

    def visibles(self, world: int, /) -> set[int]:
        return {w for w in self.frames if (world, w) in self.access}

    def world_frame(self, world: int) -> Frame:
        if world is None:
            world = 0
        if not isinstance(world, int):
            raise TypeError(world)
        if world not in self.frames:
            self.frames[world] = Frame(world)
        return self.frames[world]

    def value_of_opaque(self, s: Sentence, /, world: int = 0, **kw):
        return self.world_frame(world).opaques.get(s, self.unassigned_value)

    def value_of_atomic(self, s: Atomic, /, world: int = 0, **kw):
        return self.world_frame(world).atomics.get(s, self.unassigned_value)

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

    world: int
    "The world of the frame"

    atomics: dict[Atomic, ValueCPL]
    "An assignment of each atomic sentence to a truth value"

    opaques: dict[Sentence, ValueCPL]
    "An assignment of each opaque (un-interpreted) sentence to a value"

    extensions: dict[Predicate, set[tuple[Constant, ...]]]
    "A map of predicates to their extension."

    def __init__(self, world):

        self.world = world
        self.atomics = {}
        self.opaques = {}
        self.extensions = {pred: set() for pred in Predicate.System}

        # Track the anti-extensions to ensure integrity
        self.anti_extensions = {}

        # TODO: WIP
        self.denotation = {}
        self.domain = set()
        self.property_classes = {pred: set() for pred in Predicate.System}

    def get_data(self) -> dict:
        return dict(
            description = f'frame at world {self.world}',
            datatype    = 'map',
            typehint    = 'frame',
            value       = dict(
                world   = dict(
                    description = 'world',
                    datatype    = 'int',
                    typehint    = 'world', 
                    value       = self.world,
                    symbol      = 'w',
                ),
                Atomics = dict(
                    description     = 'atomic values',
                    datatype        = 'function',
                    typehint        = 'truth_function',
                    input_datatype  = 'sentence',
                    output_datatype = 'string',
                    output_typehint = 'truth_value',
                    symbol          = 'v',
                    values          = [
                        dict(
                            input  = sentence,
                            output = self.atomics[sentence]
                        )
                        for sentence in sorted(self.atomics)
                    ]
                ),
                Opaques = dict(
                    description     = 'opaque values',
                    datatype        = 'function',
                    typehint        = 'truth_function',
                    input_datatype  = 'sentence',
                    output_datatype = 'string',
                    output_typehint = 'truth_value',
                    symbol          = 'v',
                    values          = [
                        dict(
                            input  = sentence,
                            output = self.opaques[sentence],
                        )
                        for sentence in sorted(self.opaques)
                    ]
                ),
                # TODO: include (instead?) domain and property class data
                Predicates = dict(
                    description = 'predicate extensions',
                    datatype    = 'list',
                    values      = [
                        dict(
                            description     = f'predicate extension for {pred.name}',
                            datatype        = 'function',
                            typehint        = 'extension',
                            input_datatype  = 'predicate',
                            output_datatype = 'set',
                            output_typehint = 'extension',
                            symbol          = 'P',
                            values          = [
                                dict(
                                    input  = pred,
                                    output = self.extensions[pred],
                                )
                            ]
                        )
                        for pred in sorted(self.extensions)
                    ]
                )
            )
        )

    def is_equivalent_to(self, other: Frame) -> bool:
        other = check.inst(other, Frame)
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

class TableauxSystem(BaseSystem):
    """
    Modal tableaux are similar to classical tableaux, with the addition of a
    *world* index for each sentence node, as well as *access* nodes representing
    "visibility" of worlds. The worlds and access nodes come into play with
    the rules for Possibility and Necessity. All other rules function equivalently
    to their classical counterparts.
    """

    neg_branchable = {
        Operator.Conjunction,
        Operator.MaterialBiconditional,
        Operator.Biconditional,
    }
    pos_branchable = {
        Operator.Disjunction,
        Operator.MaterialConditional,
        Operator.Conditional,
    }

    modal = True

    @classmethod
    def build_trunk(cls, tab: Tableau, arg: Argument, /):
        """
        To build the trunk for an argument, add a node with each premise, with
        world :m:`w0`, followed by a node with the negation of the conclusion
        with world :m:`w0`.
        """
        w = 0 if cls.modal else None
        add = tab.branch().append
        for premise in arg.premises:
            add(swnode(premise, w))
        add(swnode(~arg.conclusion, w))

    @classmethod
    def branching_complexity(cls, node: Node) -> int:
        s = node.get('sentence')
        if s is None:
            return 0
        last_is_negated = False
        complexity = 0
        for oper in s.operators:
            if oper is Operator.Assertion:
                continue
            if oper is Operator.Negation:
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

class DefaultNodeRule(rules.GetNodeTargetsRule):
    """Default K node rule with:
    
    - filters.ModalNode with defaults: modal = `True`, access = `None`.
    - NodeFilter implements `_get_targets()` with abstract `_get_node_targets()`.
    - FilterHelper implements `example_nodes()` with its `example_node()` method.
    - AdzHelper implements `_apply()` with its `_apply()` method.
    - AdzHelper implements `score_candidate()` with its `closure_score()` method.
    """
    NodeFilters = filters.ModalNode,
    modal  : bool = True
    access : bool|None = None

class OperatorNodeRule(rules.OperatedSentenceRule, DefaultNodeRule):
    'Convenience mixin class for most common rules.'
    pass

@TableauxSystem.initialize
class TabRules(LogicType.TabRules):
    """
    Rules for modal operators employ *world* indexes as well access-type
    nodes. The world indexes are transparent for the rules for classical
    connectives.
    """

    class ContradictionClosure(rules.BaseClosureRule):
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

    class SelfIdentityClosure(rules.BaseClosureRule, rules.PredicatedSentenceRule):
        """
        A branch closes when a sentence of the form :s:`~a = a` appears on the
        branch *at any world*.
        """
        modal = True
        negated = True
        predicate = Predicate.System.Identity

        def _branch_target_hook(self, node: Node, branch: Branch, /):
            res = self.node_will_close_branch(node, branch)
            if res:
                return Target(node = node, branch = branch)
            if res is False:
                self[FilterHelper].release(node, branch)

        def node_will_close_branch(self, node: Node, branch: Branch, /) -> bool:
            if self[FilterHelper](node, branch):
                if len(self.sentence(node).paramset) == 1:
                    return True
                return False

        @classmethod
        def example_nodes(cls) -> tuple[dict]:
            w = 0 if cls.modal else None
            c = Constant.first()
            return swnode(~cls.predicate((c, c)), w),

    class NonExistenceClosure(rules.BaseClosureRule):
        """
        A branch closes when a sentence of the form :s:`~!a` appears on the branch
        *at any world*.
        """
        modal = True

        def _branch_target_hook(self, node: Node, branch: Branch, /):
            if self.node_will_close_branch(node, branch):
                return Target(node = node, branch = branch)

        def node_will_close_branch(self, node: Node, _, /):
            s = node.get('sentence')
            return (
                isinstance(s, Operated) and
                s.operator is Operator.Negation and
                isinstance(s.lhs, Predicated) and
                s.lhs.predicate is Predicate.System.Existence
            )

        @classmethod
        def example_nodes(cls) -> tuple[dict]:
            s = ~Predicated.first(Predicate.System.Existence)
            w = 0 if cls.modal else None
            return swnode(s, w),

    class DoubleNegation(OperatorNodeRule):
        """
        From an unticked double negation node *n* with world *w* on a branch *b*, add a
        node to *b* with *w* and the double-negatum of *n*, then tick *n*.
        """
        negated  = True
        operator = Operator.Negation
        branch_level = 1

        def _get_node_targets(self, node: Node, _, /):
            return adds(
                group(swnode(self.sentence(node).lhs, node.get('world')))
            )

    class Assertion(OperatorNodeRule):
        """
        From an unticked assertion node *n* with world *w* on a branch *b*,
        add a node to *b* with the operand of *n* and world *w*, then tick *n*.
        """
        operator = Operator.Assertion
        branch_level = 1

        def _get_node_targets(self, node: Node, _, /):
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
        operator = Operator.Assertion
        branch_level = 1

        def _get_node_targets(self, node: Node, _, /):
            return adds(
                group(swnode(~self.sentence(node).lhs, node.get('world')))
            )

    class Conjunction(OperatorNodeRule):
        """
        From an unticked conjunction node *n* with world *w* on a branch *b*,
        for each conjunct, add a node with world *w* to *b* with the conjunct,
        then tick *n*.
        """
        operator = Operator.Conjunction
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
        operator = Operator.Conjunction
        branch_level = 2

        def _get_node_targets(self, node: Node, _, /):
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
        operator = Operator.Disjunction
        branch_level = 2

        def _get_node_targets(self, node: Node, _, /):
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
        operator = Operator.Disjunction
        branch_level = 1

        def _get_node_targets(self, node: Node, _, /):
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
        operator = Operator.MaterialConditional
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
        operator = Operator.MaterialConditional
        branch_level = 1

        def _get_node_targets(self, node: Node, _, /):
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
        operator = Operator.MaterialBiconditional
        branch_level = 2

        def _get_node_targets(self, node: Node, _, /):
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
        operator = Operator.MaterialBiconditional
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
        operator = Operator.Conditional

    class ConditionalNegated(MaterialConditionalNegated):
        """
        The rule functions the same as the corresponding material conditional rule.

        From an unticked negated conditional node *n* with world *w* on a branch *b*,
        add two nodes with *w* to *b*, one with the antecedent and the other with the negation
        of the consequent, then tick *n*.
        """
        negated  = True
        operator = Operator.Conditional

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
        operator = Operator.Biconditional

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
        operator = Operator.Biconditional

    class Existential(rules.NarrowQuantifierRule, DefaultNodeRule):
        """
        From an unticked existential node *n* with world *w* on a branch *b*, quantifying over
        variable *v* into sentence *s*, add a node with world *w* to *b* with the substitution
        into *s* of *v* with a constant new to *b*, then tick *n*.
        """
        quantifier = Quantifier.Existential
        branch_level = 1

        def _get_node_targets(self, node: Node, branch: Branch, /):
            s = self.sentence(node)
            return adds(
                group(swnode(branch.new_constant() >> s, node.get('world')))
            )

    class ExistentialNegated(rules.QuantifiedSentenceRule, DefaultNodeRule):
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

    class Universal(rules.ExtendedQuantifierRule, DefaultNodeRule):
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
        convert    = Quantifier.Existential

    class Possibility(rules.OperatedSentenceRule, DefaultNodeRule):
        """
        From an unticked possibility node with world *w* on a branch *b*, add a node with a
        world *w'* new to *b* with the operand of *n*, and add an access-type node with
        world1 *w* and world2 *w'* to *b*, then tick *n*.
        """
        operator = Operator.Possibility
        branch_level = 1

        Helpers = QuitFlag, MaxWorlds, AplSentCount,
        modal_operators = Model.modal_operators

        def _get_node_targets(self, node: Node, branch: Branch, /):

            # Check for max worlds reached
            if self[MaxWorlds].is_exceeded(branch):
                self[FilterHelper].release(node, branch)
                if self[QuitFlag].get(branch):
                    return
                fnode = self[MaxWorlds].quit_flag(branch)
                return adds(group(fnode), flag = fnode['flag'])

            si = self.sentence(node).lhs
            w1 = node['world']
            w2 = branch.new_world()
            return adds(
                group(swnode(si, w2), Access(w1, w2)._asdict()),
                sentence = si
            )

        def score_candidate(self, target: Target, /) -> float:
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
            return -1.0 * self[MaxWorlds].modals(s) * track_count

        def group_score(self, target: Target, /) -> float:
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
        operator   = Operator.Possibility
        convert    = Operator.Necessity
        branch_level = 1

        def _get_node_targets(self, node: Node, _, /):
            s = self.sentence(node)
            return adds(
                group(swnode(self.convert(~s.lhs), node['world']))
            )

    class Necessity(rules.OperatedSentenceRule, DefaultNodeRule):
        """
        From a necessity node *n* with world *w1* and operand *s* on a branch *b*, for any
        world *w2* such that an access node with w1,w2 is on *b*, if *b* does not have a node
        with *s* at *w2*, add it to *b*. The node *n* is never ticked.
        """
        ticking = False
        operator = Operator.Necessity
        branch_level = 1

        Helpers = QuitFlag, MaxWorlds, NodeCount, NodesWorlds, WorldIndex,
        modal_operators = Model.modal_operators

        def _get_node_targets(self, node: Node, branch: Branch, /):

            # Check for max worlds reached
            if self[MaxWorlds].is_exceeded(branch):
                self[FilterHelper].release(node, branch)
                if self[QuitFlag].get(branch):
                    return
                fnode = self[MaxWorlds].quit_flag(branch)
                yield adds(group(fnode), flag = fnode['flag'])
                return

            # Only count least-applied-to nodes
            if not self[NodeCount].isleast(node, branch):
                return

            s = self.sentence(node)
            si = s.lhs
            w1 = node['world']

            for w2 in self[WorldIndex][branch].get(w1, EMPTY_SET):
                if (node, w2) in self[NodesWorlds][branch]:
                    continue
                add = swnode(si, w2)
                if not branch.has(add):
                    anode = self[WorldIndex].nodes[branch][w1, w2]
                    yield adds(group(add),
                        sentence = si,
                        world    = w2,
                        nodes    = qsetf({node, anode}),
                    )

        def score_candidate(self, target: Target, /) -> float:

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

        def group_score(self, target: Target, /) -> float:

            if self.score_candidate(target) > 0:
                return 1.0

            return -1.0 * self[NodeCount][target.branch].get(target.node, 0)

        @classmethod
        def example_nodes(cls) -> tuple[dict, dict]:
            s = Operated.first(cls.operator)
            a = Access(0, 1)
            return swnode(s, a.w1), a._asdict()

    class NecessityNegated(PossibilityNegated):
        """
        From an unticked negated necessity node *n* with world *w* on a branch *b*, add a
        possibility node whose operand is the negation of the negated necessitatum of *n*,
        then tick *n*.
        """
        operator = Operator.Necessity
        convert  = Operator.Possibility

    class IdentityIndiscernability(rules.PredicatedSentenceRule, DefaultNodeRule):
        """
        From an unticked node *n* having an Identity sentence *s* at world *w* on an open branch *b*,
        and a predicated node *n'* whose sentence *s'* has a constant that is a parameter of *s*,
        if the replacement of that constant for the other constant of *s* is a sentence that does
        not appear on *b* at *w*, then add it.
        """
        ticking   = False
        predicate = Predicate.System.Identity

        branch_level = 1

        def _get_node_targets(self, node: Node, branch: Branch, /) -> list[Target]:
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

        @classmethod
        def example_nodes(cls) -> tuple[dict, dict]:
            w = 0 if cls.modal else None
            s1 = Predicated.first()
            s2 = cls.predicate((s1[0], s1[0].next()))
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
