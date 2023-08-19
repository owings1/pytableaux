# -*- coding: utf-8 -*-
# pytableaux, a multi-logic proof generator.
# Copyright (C) 2014-2023 Doug Owings.
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
from __future__ import annotations

from collections import defaultdict
from typing import cast

from .. import proof
from ..errors import DenotationError, ModelValueError, check
from ..lang import (Argument, Atomic, Constant, Operated, Operator, Predicate,
                    Predicated, Quantified, Quantifier, Sentence)
from ..models import BaseModel, ValueCPL
from ..proof import (AccessNode, Branch, Node, SentenceNode, SentenceWorldNode,
                     Target, WorldPair, adds, anode, filters, rules, swnode)
from ..proof.helpers import (AdzHelper, AplSentCount, FilterHelper, MaxWorlds,
                             NodeCount, NodesWorlds, PredNodes, QuitFlag,
                             WorldIndex)
from ..tools import EMPTY_SET, group, substitute, minfloor, maxceil
from . import LogicType
from . import fde as FDE


class Meta(LogicType.Meta):
    name = 'K'
    title = 'Kripke Normal Modal Logic'
    modal = True
    values: type[ValueCPL] = ValueCPL
    designated_values = frozenset({values.T})
    unassigned_value = values.F
    category = 'Bivalent Modal'
    description = 'Base normal modal logic with no access relation restrictions'
    category_order = 1
    tags = (
        'bivalent',
        'modal',
        'first-order')
    native_operators = FDE.Meta.native_operators + (
        Operator.Possibility,
        Operator.Necessity)

class AccessGraph(defaultdict[int, set[int]]):

    __slots__ = EMPTY_SET

    def __init__(self, *args, **kw):
        super().__init__(set, *args, **kw)

    def has(self, access: tuple[int, int], /) -> bool:
        w1, w2 = access
        return w1 in self and w2 in self[w1]

    def add(self, access: tuple[int, int], /):
        w1, w2 = access
        self[w1].add(w2)

    def worlds(self) -> set[int]:
        worlds = set()
        for w, sees in self.items():
            worlds.add(w)
            worlds.update(sees)
        return worlds

class Model(BaseModel[Meta.values]):
    """
    A K model comprises a non-empty collection of K-frames, a world access
    relation, and a set of constants (the domain).
    """

    TruthFunction = FDE.Model.TruthFunction

    frames: Frames
    "A map from worlds to their frame"

    R: AccessGraph
    "The `access` relation"

    constants: set[Constant]
    "The fixed domain of constants, common to all worlds in the model"

    def __init__(self):

        super().__init__()

        self.frames = Frames()
        self.R = AccessGraph()
        self.constants = set()

        self.predicates: set[Predicate] = set(Predicate.System)

        # ensure there is a w0
        self.frames[0]
        self.maxval = max(self.values)
        self.minval = min(self.values)

    def value_of_opaque(self, s: Sentence, /, world: int = 0):
        return self.frames[world].opaques.get(s, self.unassigned_value)

    def value_of_atomic(self, s: Atomic, /, world: int = 0):
        return self.frames[world].atomics.get(s, self.unassigned_value)

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
            return self.values.T
        return self.values.F

    def value_of_quantified(self, s: Quantified, **kw):
        it = map(lambda s: self.value_of(s, **kw), map(s.unquantify, self.constants))
        if s.quantifier is Quantifier.Existential:
            return maxceil(self.maxval, it, self.minval)
        if s.quantifier is Quantifier.Universal:
            return minfloor(self.minval, it, self.maxval)
        raise TypeError(s.quantifier)

    def value_of_operated(self, s: Operated, **kw):
        if s.operator is Operator.Possibility:
            return self.value_of_possibility(s, **kw)
        if s.operator is Operator.Necessity:
            return self.value_of_necessity(s, **kw)
        return super().value_of_operated(s, **kw)

    def value_of_possibility(self, s: Operated, /, world: int = 0, **kw):
        """
        A possibility sentence is true at :m:`w` iff its operand is true at :m:`w'` for
        some :m:`w'` such that :m:`<w, w'>` in the access relation.
        """
        for w2 in self.R[world]:
            if self.value_of(s.lhs, world=w2, **kw) is self.values.T:
                return self.values.T
        return self.values.F

    def value_of_necessity(self, s: Operated, /, world: int = 0, **kw):
        """
        A necessity sentence is true at :m:`w` iff its operand is true at :m:`w'` for
        each :m:`w'` such that :m:`<w, w'>` is in the access relation.
        """
        for w2 in self.R[world]:
            if self.value_of(s.lhs, world=w2, **kw) is self.values.F:
                return self.values.F
        return self.values.T

    def is_countermodel_to(self, arg: Argument, /) -> bool:
        """
        A model is a countermodel for an argument iff the value of each premise
        is V{T} at `w0` and the value of the conclusion is V{F} at :m:`w0`.
        """
        for premise in arg.premises:
            if self.value_of(premise, world = 0) is not self.values.T:
                return False
        return self.value_of(arg.conclusion, world = 0) is self.values.F

    def get_data(self) -> dict:
        return dict(
            Worlds = dict(
                description     = 'set of worlds',
                in_summary      = True,
                datatype        = 'set',
                member_datatype = 'int',
                member_typehint = 'world',
                symbol          = 'W',
                values          = sorted(self.frames)),
            Access = dict(
                description     = 'access relation',
                in_summary      = True,
                datatype        = 'set',
                typehint        = 'access_relation',
                member_datatype = 'tuple',
                member_typehint = 'access',
                symbol          = 'R',
                values          = sorted((w1, w2) for w1, sees in self.R.items()
                                    for w2 in sees)),
            Frames = dict(
                description     = 'world frames',
                datatype        = 'list',
                typehint        = 'frames',
                member_datatype = 'map',
                member_typehint = 'frame',
                symbol          = 'F',
                values          = [
                    frame.get_data()
                    for frame in sorted(self.frames.values())]))

    def read_branch(self, branch: Branch, /):
        for _ in map(self._read_node, branch):
            pass
        self.finish()

    def _read_node(self, node: Node, /):
        s = node.get('sentence')
        if s is not None:
            w = node.get('world')
            if w is None:
                w = 0
            if self.is_sentence_opaque(s):
                self.set_opaque_value(s, self.values.T, world = w)
            elif self.is_sentence_literal(s):
                self.set_literal_value(s, self.values.T, world = w)
            self.predicates.update(s.predicates)
        elif isinstance(node, AccessNode):
            self.R.add(node.pair())

    def finish(self):
        # track all atomics and opaques
        atomics = set()
        opaques = set()

        # ensure frames for each world
        for w in self.R.worlds():
            self.frames[w]

        for w, frame in self.frames.items():
            atomics.update(frame.atomics)
            opaques.update(frame.opaques)
            for pred in self.predicates:
                self._agument_extension_with_identicals(pred, w)
            self._ensure_self_identity(w)
            self._ensure_self_existence(w)

        # make sure each atomic and opaque is assigned a value in each frame
        for w, frame in self.frames.items():
            for s in atomics:
                if s not in frame.atomics:
                    self.set_literal_value(s, self.unassigned_value, world = w)
            for s in opaques:
                if s not in frame.opaques:
                    self.set_opaque_value(s, self.unassigned_value, world = w)

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
                        new_params = substitute(params, c, new_c)
                        to_add.add(new_params)
            extension.update(to_add)

    def _get_identicals(self, c: Constant, **kw) -> set[Constant]:
        ext = self.get_extension(Predicate.System.Identity, **kw)
        identicals = set()
        for params in ext:
            if c in params:
                identicals.update(params)
        identicals.discard(c)
        return identicals

    def set_literal_value(self, s: Sentence, value, /, **kw):
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

    def set_opaque_value(self, s: Sentence, value, /, world = 0):
        value = self.values[value]
        frame = self.frames[world]
        if frame.opaques.get(s, value) is not value:
            raise ModelValueError(f'Inconsistent value for sentence {s}')
        # We might have a quantified opaque sentence, in which case we will need
        # to still check every subsitution, so we want the constants.
        # NB: in FDE we added the atomics to all_atomics, but we don't have that
        #     here since we do frames -- will that be a problem?
        self.constants.update(s.constants)
        self.predicates.update(s.predicates)
        frame.opaques[s] = value

    def set_atomic_value(self, s: Atomic, value, /, world = 0):
        value = self.values[value]
        frame = self.frames[world]
        if s in frame.atomics and frame.atomics[s] is not value:
            raise ModelValueError(f'Inconsistent value for sentence {s}')
        frame.atomics[s] = value

    def set_predicated_value(self, s: Predicated, value, /, **kw):
        values = self.values
        value = values[value]
        pred = s.predicate
        params = s.params
        self.predicates.add(pred)
        for param in s:
            if type(param) is Constant:
                self.constants.add(param)
        extension = self.get_extension(pred, **kw)
        anti_extension = self.get_anti_extension(pred, **kw)
        if value is values.F:
            if params in extension:
                raise ModelValueError(f'Cannot set value {value} for tuple '
                    f'{params} already in extension')
            anti_extension.add(params)
        if value is values.T:
            if params in anti_extension:
                raise ModelValueError(f'Cannot set value {value} for tuple '
                    f'{params} already in anti-extension')
            extension.add(params)

    def get_extension(self, pred: Predicate, /, world = 0) -> set[tuple[Constant, ...]]:
        frame = self.frames[world]
        self.predicates.add(pred)
        if pred not in frame.extensions:
            frame.extensions[pred] = set()
        if pred not in frame.anti_extensions:
            frame.anti_extensions[pred] = set()
        return frame.extensions[pred]

    def get_anti_extension(self, pred: Predicate, /, world = 0) -> set[tuple[Constant, ...]]:
        frame = self.frames[world]
        self.predicates.add(pred)
        if pred not in frame.extensions:
            frame.extensions[pred] = set()
        if pred not in frame.anti_extensions:
            frame.anti_extensions[pred] = set()
        return frame.anti_extensions[pred]

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
        check.inst(other, Frame)
        return (self.atomics == other.atomics and
            self.opaques == other.opaques and
            self.extensions == other.extensions)

    def __eq__(self, other):
        if not isinstance(other, Frame):
            return NotImplemented
        return self.world == other.world and self.is_equivalent_to(other)

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


class Frames(dict[int, Frame]):

    __slots__ = EMPTY_SET

    def __missing__(self, key):
        if key is None:
            return self[0]
        return self.setdefault(check.inst(key, int), Frame(key))

class System(proof.System):

    neg_branchable = {
        Operator.Conjunction,
        Operator.MaterialBiconditional,
        Operator.Biconditional}

    pos_branchable = {
        Operator.Disjunction,
        Operator.MaterialConditional,
        Operator.Conditional}

    @classmethod
    def build_trunk(cls, b, arg, /):
        """
        To build the trunk for an argument, add a node with each premise, with
        world :m:`w0`, followed by a node with the negation of the conclusion
        with world :m:`w0`.
        """
        w = 0 if cls.modal else None
        b.extend(swnode(s, w) for s in arg.premises)
        b.append(swnode(~arg.conclusion, w))

    @classmethod
    def branching_complexity(cls, node, /) -> int:
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

    @classmethod
    def branching_complexity_hashable(cls, node, /):
        return node.get('sentence')

class DefaultNodeRule(rules.GetNodeTargetsRule, intermediate=True):
    """Default K node rule with:
    
    - (removing...) filters.ModalNode with defaults: modal = `True`, access = `None`.
    - NodeFilter implements `_get_targets()` with abstract `_get_node_targets()`.
    - FilterHelper implements `example_nodes()` with its `example_node()` method.
    - AdzHelper implements `_apply()` with its `_apply()` method.
    - AdzHelper implements `score_candidate()` with its `closure_score()` method.
    """
    NodeFilters = group(filters.NodeType)
    autoattrs = True

    def _get_node_targets(self, node: Node, branch: Branch, /):
        return self._get_sw_targets(self.sentence(node), node.get('world'))

    def _get_sw_targets(self, s: Sentence, w: int|None, /):
        raise NotImplementedError

class OperatorNodeRule(DefaultNodeRule, rules.OperatedSentenceRule, intermediate=True):
    'Convenience mixin class for most common rules.'
    NodeType = SentenceNode

    def _get_sw_targets(self, s: Operated, w: int|None, /):
        raise NotImplementedError

class Rules(LogicType.Rules):

    class ContradictionClosure(rules.FindClosingNodeRule):
        """
        A branch closes when a sentence and its negation both appear on a node **with the
        same world** on the branch.
        """

        def _find_closing_node(self, node, branch, /):
            s = self.sentence(node)
            if s is not None:
                return branch.find(swnode(-s, node.get('world')))

        def example_nodes(self):
            s = Atomic.first()
            w = 0 if self.modal else None
            yield swnode(s, w)
            yield swnode(~s, w)

    class SelfIdentityClosure(rules.BaseClosureRule, rules.PredicatedSentenceRule):
        """
        A branch closes when a sentence of the form :s:`~a = a` appears on the
        branch *at any world*.
        """
        negated = True
        predicate = Predicate.System.Identity

        def _branch_target_hook(self, node, branch, /):
            if self.node_will_close_branch(node, branch):
                return Target(node=node, branch=branch)
            self[FilterHelper].release(node, branch)
            self[PredNodes].release(node, branch)

        def node_will_close_branch(self, node, branch, /) -> bool:
            return (
                self[FilterHelper].pred(node) and
                len(set(self.sentence(node))) == 1)

        def example_nodes(self):
            w = 0 if self.modal else None
            c = Constant.first()
            yield swnode(~self.predicate((c, c)), w)

    class NonExistenceClosure(rules.BaseClosureRule, rules.PredicatedSentenceRule):
        """
        A branch closes when a sentence of the form :s:`~!a` appears on the branch
        *at any world*.
        """
        negated = True
        predicate = Predicate.System.Existence

        def _branch_target_hook(self, node, branch, /):
            if self.node_will_close_branch(node, branch):
                return Target(node=node, branch=branch)
            self[FilterHelper].release(node, branch)
            self[PredNodes].release(node, branch)

        def node_will_close_branch(self, node, branch, /):
            return self[FilterHelper](node, branch)

        def example_nodes(self):
            s = ~Predicated.first(self.predicate)
            w = 0 if self.modal else None
            yield swnode(s, w)

    class DoubleNegation(OperatorNodeRule):
        """
        From an unticked double negation node *n* with world *w* on a branch *b*, add a
        node to *b* with *w* and the double-negatum of *n*, then tick *n*.
        """

        def _get_sw_targets(self, s, w, /):
            yield adds(group(swnode(s.lhs, w)))

    class Assertion(OperatorNodeRule):
        """
        From an unticked assertion node *n* with world *w* on a branch *b*,
        add a node to *b* with the operand of *n* and world *w*, then tick *n*.
        """

        def _get_sw_targets(self, s, w, /):
            yield adds(group(swnode(s.lhs, w)))

    class AssertionNegated(OperatorNodeRule):
        """
        From an unticked, negated assertion node *n* with world *w* on a branch *b*,
        add a node to *b* with the negation of the assertion of *n* and world *w*,
        then tick *n*.
        """

        def _get_sw_targets(self, s, w, /):
            yield adds(group(swnode(~s.lhs, w)))

    class Conjunction(OperatorNodeRule):
        """
        From an unticked conjunction node *n* with world *w* on a branch *b*,
        for each conjunct, add a node with world *w* to *b* with the conjunct,
        then tick *n*.
        """

        def _get_sw_targets(self, s, w, /):
            yield adds(group(swnode(s.lhs, w), swnode(s.rhs, w)))

    class ConjunctionNegated(OperatorNodeRule):
        """
        From an unticked negated conjunction node *n* with world *w* on a branch *b*, for each
        conjunct, make a new branch *b'* from *b* and add a node with *w* and the negation of
        the conjunct to *b*, then tick *n*.
        """

        def _get_sw_targets(self, s, w, /):
            yield adds(
                group(swnode(~s.lhs, w)),
                group(swnode(~s.rhs, w)))

    class Disjunction(OperatorNodeRule):
        """
        From an unticked disjunction node *n* with world *w* on a branch *b*, for each disjunct,
        make a new branch *b'* from *b* and add a node with the disjunct and world *w* to *b'*,
        then tick *n*.
        """

        def _get_sw_targets(self, s, w, /):
            yield adds(
                group(swnode(s.lhs, w)),
                group(swnode(s.rhs, w)))

    class DisjunctionNegated(OperatorNodeRule):
        """
        From an unticked negated disjunction node *n* with world *w* on a branch *b*, for each
        disjunct, add a node with *w* and the negation of the disjunct to *b*, then tick *n*.
        """

        def _get_sw_targets(self, s, w, /):
            yield adds(group(swnode(~s.lhs, w), swnode(~s.rhs, w)))

    class MaterialConditional(OperatorNodeRule):
        """
        From an unticked material conditional node *n* with world *w* on a branch *b*, make two
        new branches *b'* and *b''* from *b*, add a node with world *w* and the negation of the
        antecedent to *b'*, and add a node with world *w* and the conequent to *b''*, then tick
        *n*.
        """

        def _get_sw_targets(self, s, w, /):
            yield adds(
                group(swnode(~s.lhs, w)),
                group(swnode( s.rhs, w)))

    class MaterialConditionalNegated(OperatorNodeRule):
        """
        From an unticked negated material conditional node *n* with world *w* on a branch *b*,
        add two nodes with *w* to *b*, one with the antecedent and the other with the negation
        of the consequent, then tick *n*.
        """

        def _get_sw_targets(self, s, w, /):
            yield adds(group(swnode(s.lhs, w), swnode(~s.rhs, w)))

    class MaterialBiconditional(OperatorNodeRule):
        """
        From an unticked material biconditional node *n* with world *w* on a branch *b*, make
        two new branches *b'* and *b''* from *b*, add two nodes with world *w* to *b'*, one with
        the negation of the antecedent and one with the negation of the consequent, and add two
        nodes with world *w* to *b''*, one with the antecedent and one with the consequent, then
        tick *n*.
        """

        def _get_sw_targets(self, s, w, /):
            yield adds(
                group(swnode(~s.lhs, w), swnode(~s.rhs, w)),
                group(swnode( s.rhs, w), swnode( s.lhs, w)))

    class MaterialBiconditionalNegated(OperatorNodeRule):
        """
        From an unticked negated material biconditional node *n* with world *w* on a branch *b*,
        make two new branches *b'* and *b''* from *b*, add two nodes with *w* to *b'*, one with
        the antecedent and the other with the negation of the consequent, and add two nodes with
        *w* to *b''*, one with the negation of the antecedent and the other with the consequent,
        then tick *n*.
        """

        def _get_sw_targets(self, s, w, /):
            yield adds(
                group(swnode( s.lhs, w), swnode(~s.rhs, w)),
                group(swnode(~s.lhs, w), swnode( s.rhs, w)))

    class Conditional(MaterialConditional):
        """
        The rule functions the same as the corresponding material conditional rule.

        From an unticked conditional node *n* with world *w* on a branch *b*, make two
        new branches *b'* and *b''* from *b*, add a node with world *w* and the negation of the
        antecedent to *b'*, and add a node with world *w* and the conequent to *b''*, then tick
        *n*.
        """

    class ConditionalNegated(MaterialConditionalNegated):
        """
        The rule functions the same as the corresponding material conditional rule.

        From an unticked negated conditional node *n* with world *w* on a branch *b*,
        add two nodes with *w* to *b*, one with the antecedent and the other with the negation
        of the consequent, then tick *n*.
        """

    class Biconditional(MaterialBiconditional):
        """
        The rule functions the same as the corresponding material biconditional rule.

        From an unticked biconditional node *n* with world *w* on a branch *b*, make
        two new branches *b'* and *b''* from *b*, add two nodes with world *w* to *b'*, one with
        the negation of the antecedent and one with the negation of the consequent, and add two
        nodes with world *w* to *b''*, one with the antecedent and one with the consequent, then
        tick *n*.
        """

    class BiconditionalNegated(MaterialBiconditionalNegated):
        """
        The rule functions the same as the corresponding material biconditional rule.

        From an unticked negated biconditional node *n* with world *w* on a branch *b*,
        make two new branches *b'* and *b''* from *b*, add two nodes with *w* to *b'*, one with
        the antecedent and the other with the negation of the consequent, and add two nodes with
        *w* to *b''*, one with the negation of the antecedent and the other with the consequent,
        then tick *n*.
        """

    class Existential(rules.NarrowQuantifierRule, DefaultNodeRule):
        """
        From an unticked existential node *n* with world *w* on a branch *b*, quantifying over
        variable *v* into sentence *s*, add a node with world *w* to *b* with the substitution
        into *s* of *v* with a constant new to *b*, then tick *n*.
        """

        def _get_node_targets(self, node, branch, /):
            s = self.sentence(node)
            yield adds(
                group(swnode(branch.new_constant() >> s, node.get('world'))))

    class ExistentialNegated(rules.QuantifiedSentenceRule, DefaultNodeRule):
        """
        From an unticked negated existential node *n* with world *w* on a branch *b*,
        quantifying over variable *v* into sentence *s*, add a universally quantified
        node to *b* with world *w* over *v* into the negation of *s*, then tick *n*.
        """
        convert = Quantifier.Universal

        def _get_sw_targets(self, s, w, /):
            v, si = s[1:]
            # Keep conversion neutral for inheritance below.
            yield adds(group(swnode(self.convert(v, ~si), w)))

    class Universal(rules.ExtendedQuantifierRule, DefaultNodeRule):
        """
        From a universal node with world *w* on a branch *b*, quantifying over variable *v* into
        sentence *s*, result *r* of substituting a constant *c* on *b* (or a new constant if none
        exists) for *v* into *s* does not appear at *w* on *b*, add a node with *w* and *r* to
        *b*. The node *n* is never ticked.
        """

        def _get_constant_nodes(self, node, c, branch, /):
            yield swnode(c >> self.sentence(node), node.get('world'))

    class UniversalNegated(ExistentialNegated):
        """
        From an unticked negated universal node *n* with world *w* on a branch *b*,
        quantifying over variable *v* into sentence *s*, add an existentially
        quantified node to *b* with world *w* over *v* into the negation of *s*,
        then tick *n*.
        """
        convert = Quantifier.Existential

    class Possibility(OperatorNodeRule):
        """
        From an unticked possibility node with world *w* on a branch *b*, add a node with a
        world *w'* new to *b* with the operand of *n*, and add an access-type node with
        world1 *w* and world2 *w'* to *b*, then tick *n*.
        """
        NodeType = SentenceWorldNode
        Helpers = (QuitFlag, MaxWorlds, AplSentCount)

        def _get_node_targets(self, node, branch, /):

            # Check for max worlds reached
            if self[MaxWorlds].is_exceeded(branch):
                self[FilterHelper].release(node, branch)
                if not self[QuitFlag].get(branch):
                    fnode = self[MaxWorlds].quit_flag(branch)
                    yield adds(group(fnode), flag = fnode['flag'])
                return

            si = self.sentence(node).lhs
            w1 = node['world']
            w2 = branch.new_world()
            yield adds(
                group(swnode(si, w2), anode(w1, w2)),
                sentence = si)

        def score_candidate(self, target, /) -> float:
            """
            Overrides `AdzHelper` closure score
            """
            if target.get('flag'):
                return 1.0
            # override
            s = self.sentence(target.node)
            si = s.lhs
            # Don't bother checking for closure since we will always have a new world
            track_count = self[AplSentCount][target.branch].get(si, 0)
            if track_count == 0:
                return 1.0
            return -1.0 * self[MaxWorlds].modals[s] * track_count

        def group_score(self, target, /) -> float:
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
        convert = Operator.Necessity
        NodeType = SentenceWorldNode

        def _get_sw_targets(self, s, w, /):
            yield adds(group(swnode(self.convert(~s.lhs), w)))

    class Necessity(OperatorNodeRule):
        """
        From a necessity node *n* with world *w1* and operand *s* on a branch *b*, for any
        world *w2* such that an access node with w1,w2 is on *b*, if *b* does not have a node
        with *s* at *w2*, add it to *b*. The node *n* is never ticked.
        """
        ticking = False
        NodeType = SentenceWorldNode
        Helpers = (QuitFlag, MaxWorlds, NodeCount, NodesWorlds, WorldIndex)

        def _get_node_targets(self, node, branch, /):

            # Check for max worlds reached
            if self[MaxWorlds].is_exceeded(branch):
                self[FilterHelper].release(node, branch)
                if not self[QuitFlag].get(branch):
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
                if branch.has(add):
                    continue
                anode = self[WorldIndex].nodes[branch][w1, w2]
                yield adds(group(add),
                    sentence=si,
                    world=w2,
                    nodes=(node, anode))

        def score_candidate(self, target, /) -> float:
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

        def group_score(self, target, /) -> float:
            if self.score_candidate(target) > 0:
                return 1.0
            return -1.0 * self[NodeCount][target.branch].get(target.node, 0)

        def example_nodes(self):
            s = Operated.first(self.operator)
            a = WorldPair(0, 1)
            yield swnode(s, a.w1)
            yield a.tonode()

    class NecessityNegated(PossibilityNegated):
        """
        From an unticked negated necessity node *n* with world *w* on a branch *b*, add a
        possibility node whose operand is the negation of the negated necessitatum of *n*,
        then tick *n*.
        """
        convert = Operator.Possibility

    class IdentityIndiscernability(DefaultNodeRule, rules.PredicatedSentenceRule):
        """
        From an unticked node *n* having an Identity sentence *s* at world *w* on an open branch *b*,
        and a predicated node *n'* whose sentence *s'* has a constant that is a parameter of *s*,
        if the replacement of that constant for the other constant of *s* is a sentence that does
        not appear on *b* at *w*, then add it.
        """
        ticking   = False
        predicate = Predicate.System.Identity

        def _get_node_targets(self, node, branch, /):
            pa, pb = self.sentence(node)
            if pa == pb:
                # Substituting a param for itself would be silly.
                return
            pnodes = self[PredNodes][branch]
            w = node.get('world')
            # Find other nodes with one of the identicals.
            for n in pnodes:
                if n is node:
                    continue
                s = cast(Predicated, n['sentence'])
                if pa in s.params:
                    p_old, p_new = pa, pb
                elif pb in s.params:
                    p_old, p_new = pb, pa
                else:
                    # This continue statement does not register as covered,
                    # but it is by ``test_identity_indiscernability_not_applies()```
                    continue # pragma: no cover
                # Replace p with p1.
                params = substitute(s.params, p_old, p_new)
                # Since we have SelfIdentityClosure, we don't need a = a.
                if s.predicate == self.predicate and params[0] == params[1]:
                    continue
                # Create a node with the substituted param.
                n_new = swnode(s.predicate(params), w)
                # Check if it already appears on the branch.
                if branch.has(n_new):
                    continue
                # The rule applies.
                yield adds(group(n_new), nodes=(node, n))

        def example_nodes(self):
            w = 0 if self.modal else None
            s1 = Predicated.first()
            yield swnode(s1, w)
            s2 = self.predicate((s1[0], s1[0].next()))
            yield swnode(s2, w)

    closure = (
        ContradictionClosure,
        SelfIdentityClosure,
        NonExistenceClosure)

    groups = (
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
            UniversalNegated),
        (
            # branching rules
            ConjunctionNegated,
            Disjunction,
            MaterialConditional,
            MaterialBiconditional,
            MaterialBiconditionalNegated,
            Conditional,
            Biconditional,
            BiconditionalNegated),
        (
            # modal operator rules
            Necessity,
            Possibility),
        (
            Existential,
            Universal))
