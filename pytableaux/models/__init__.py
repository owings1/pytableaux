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
"""
pytableaux.models
^^^^^^^^^^^^^^^^^

"""
from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass
from functools import partial
from itertools import product, starmap
from types import MappingProxyType as MapProxy
from typing import (Any, Generic, Iterable, Iterator, Literal, Mapping,
                    NamedTuple, Self, TypeVar)

from ..errors import DenotationError, Emsg, ModelValueError, check
from ..lang import (Argument, Atomic, Constant, Operated, Operator, Predicate,
                    Predicated, Quantified, Quantifier, Sentence)
from ..logics import LogicType
from ..proof import (AccessNode, Branch, DesignationNode, Node, SentenceNode,
                     WorldNode, sdwnode)
from ..tools import EMPTY_MAP, EMPTY_SET, abcs, maxceil, minfloor

__all__ = (
    'BaseModel',
    'Mval',
    'PredicateInterpretation',
    'TruthTable',
    'ValueFDE',
    'ValueK3',
    'ValueLP',
    'ValueCPL')

MvalT = TypeVar('MvalT', bound='Mval')
MvalT_co = TypeVar('MvalT_co', bound='Mval', covariant=True)

class Mval(abcs.Ebc):

    __slots__ = ('name', 'value')

    def __eq__(self, other):
        if self is other:
            return True
        if isinstance(other, (float, int)):
            return other == self.value
        if isinstance(other, str):
            return other == self.name
        return NotImplemented

    def __hash__(self):
        # Since equal names can have unequal nums, we hash the name, so
        # equal values have equal hashes.
        return hash(self.name)

    def __le__(self, other):
        return self.value <= other
    def __lt__(self, other):
        return self.value < other
    def __ge__(self, other):
        return self.value >= other
    def __gt__(self, other):
        return self.value > other
    def __sub__(self, other):
        return type(self)(self.value - other)
    def __rsub__(self, other):
        return other - self.value
    def __add__(self, other):
        return type(self)(self.value + other)
    def __radd__(self, other):
        return other + self.value
    def __truediv__(self, other):
        return type(self)(self.value / other)
    def __rtruediv__(self, other):
        return other / self.value
    def __floordiv__(self, other):
        return type(self)(self.value // other)
    def __rfloordiv__(self, other):
        return other // self.value
    def __float__(self):
        return self.value
    def __str__(self):
        return self.name

class ValueFDE(Mval):
    "Model values for gappy + glutty 4-valued logics, like FDE."

    F = 0.0
    N = 0.25
    B = 0.75
    T = 1.0

class ValueK3(Mval):
    "Model values for gappy 3-valued logics, like K3 and others."

    F = 0.0
    N = 0.5
    T = 1.0

class ValueLP(Mval):
    "Model values for glutty 3-valued logics, like LP and others."

    F = 0.0
    B = 0.5
    T = 1.0

class ValueCPL(Mval):
    'Model values for 2-valued "classical" logics.'

    F = 0.0
    T = 1.0

class ModelsMeta(abcs.AbcMeta):

    def __prepare__(clsname, bases, **kw):
        return dict(__slots__=EMPTY_SET)

class BaseModel(Generic[MvalT_co], metaclass=ModelsMeta):
    Meta: type[LogicType.Meta]

    values: type[MvalT_co]
    "The values of the model"

    truth_function: LogicType.Model.TruthFunction[MvalT_co]

    frames: Mapping[int, LogicType.Model.Frame]
    "A map from worlds to their frame"

    constants: set[Constant]

    sentences: set[Sentence]

    R: AccessGraph
    "The `access` relation"

    __slots__ = (
        '_finished',
        '_is_frame_complete',
        'constants',
        'frames',
        'R',
        'sentences')

    @property
    def id(self) -> int:
        return id(self)

    @property
    def finished(self) -> bool:
        return self._finished

    def __init__(self):
        self._finished = False
        self._is_frame_complete = False
        if self.Meta.modal:
            self.frames = defaultdict(partial(self.Frame, self))
        else:
            self.frames = MapProxy({0: self.Frame(self)})
        self.constants = set()
        self.sentences = set()
        self.R = AccessGraph()
        self.frames[0]
        self.R[0]

    def is_sentence_opaque(self, s: Sentence, /) -> bool:
        if not self.Meta.quantified and type(s) is Quantified:
            return True
        if not self.Meta.modal and type(s) is Operated and s.operator in self.Meta.modal_operators:
            return True
        return False

    def is_sentence_literal(self, s: Sentence, /) -> bool:
        return type(s) in (Atomic, Predicated) or (
            type(s) is Operated and
            s.operator is Operator.Negation and (
                type(s.lhs) in (Atomic, Predicated) or
                self.is_sentence_opaque(s.lhs)))

    def value_of(self, s: Sentence, /, **kw) -> MvalT_co:
        self._check_finished()
        if self.is_sentence_opaque(s):
            return self.value_of_opaque(s, **kw)
        try:
            name = f'value_of_{type(s).__name__.lower()}'
            func = getattr(self, name)
        except AttributeError:
            check.inst(s, Sentence)
            raise NotImplementedError from ValueError(s)
        return func(s, **kw)

    def value_of_opaque(self, s: Sentence, /, *, world: int = 0):
        self._check_finished()
        return self.frames[world].opaques.get(s, self.Meta.unassigned_value)

    def value_of_atomic(self, s: Atomic, /, *, world: int = 0):
        self._check_finished()
        return self.frames[world].atomics.get(s, self.Meta.unassigned_value)

    def value_of_predicated(self, s: Predicated, /, *, world: int = 0) -> MvalT_co:
        self._check_finished()
        params = s.params
        for param in params:
            if param not in self.constants:
                raise DenotationError(f'Parameter {param} is not in the constants')
        return self.frames[world].predicates[s.predicate].get_value(params, self.values)

    def value_of_quantified(self, s: Quantified, /, **kw) -> MvalT_co:
        if not self.Meta.quantified:
            raise NotImplementedError(f'Model does not support quantification')
        self._check_finished()
        it = self._unquantify_values(s, **kw)
        if s.quantifier is Quantifier.Existential:
            return maxceil(self.maxval, it, self.minval)
        if s.quantifier is Quantifier.Universal:
            return minfloor(self.minval, it, self.maxval)
        raise NotImplementedError from ValueError(s.quantifier)

    def _unquantify_values(self, s: Quantified, /, **kw) -> Iterator[MvalT_co]:
        value_of = self.value_of
        for c in self.constants:
            yield value_of(c >> s, **kw)

    def _unmodal_values(self, s: Operated, /, world: int = 0) -> Iterator[MvalT_co]:
        value_of = self.value_of
        for w2 in self.R[world]:
            yield value_of(s.lhs, world=w2)

    def value_of_operated(self, s: Operated, /, **kw) -> MvalT_co:
        self._check_finished()
        oper = s.operator
        if oper in self.Meta.truth_functional_operators:
            it = (self.value_of(s, **kw) for s in s)
            return self.truth_function(oper, *it)
        if oper in self.Meta.modal_operators:
            if not self.Meta.modal:
                raise NotImplementedError(f'Model does not support modal operators')
            it = self._unmodal_values(s, **kw)
            if oper is Operator.Possibility:
                return maxceil(self.maxval, it, self.minval)
            if oper is Operator.Necessity:
                return minfloor(self.minval, it, self.maxval)
        raise NotImplementedError from ValueError(oper)

    def set_value(self, s: Sentence, value: MvalT_co, /, **kw):
        self._check_not_finished()
        value = self.values[value]
        if self.is_sentence_opaque(s):
            return self.set_opaque_value(s, value, **kw)
        if self.is_sentence_literal(s):
            return self.set_literal_value(s, value, **kw)
        raise NotImplementedError from TypeError(type(s))

    def set_literal_value(self, s: Sentence, value: MvalT_co, /, **kw):
        self._check_not_finished()
        value = self.values[value]
        if self.is_sentence_opaque(s):
            return self.set_opaque_value(s, value, **kw)
        if type(s) is Operated and s.operator is Operator.Negation:
            value = self.truth_function(s.operator, value)
            return self.set_literal_value(s.lhs, value, **kw)
        if type(s) is Atomic:
            return self.set_atomic_value(s, value, **kw)
        if type(s) is Predicated:
            return self.set_predicated_value(s, value, **kw)
        raise NotImplementedError from TypeError(type(s))

    def set_opaque_value(self, s: Sentence, value: MvalT_co, /, world: int = 0):
        self._check_not_finished()
        value = self.values[value]
        frame = self.frames[world]
        opaques = frame.opaques
        if opaques.get(s, value) is not value:
            raise ModelValueError(f'Inconsistent value for sentence {s}: {value}')
        opaques[s] = value
        self.sentences.add(s)
        # We might have a quantified opaque sentence, in which case we will need
        # to still check every subsitution, so we want the constants.
        for pred in s.predicates:
            frame.predicates[pred]
        self.constants.update(s.constants)

    def set_atomic_value(self, s: Atomic, value: MvalT_co, /, world: int = 0):
        self._check_not_finished()
        value = self.values[value]
        atomics = self.frames[world].atomics
        if atomics.get(s, value) is not value:
            raise ModelValueError(f'Inconsistent value for sentence {s}: {value}')
        atomics[s] = value
        self.sentences.add(s)

    def set_predicated_value(self, s: Predicated, value, /, *, world: int = 0):
        self._check_not_finished()
        value = self.values[value]
        frame = self.frames[world]
        if len(s.variables):
            raise ValueError(f'Free variables not allowed')
        frame.predicates[s.predicate].set_value(s.params, value)
        self.constants.update(s.constants)
        self.sentences.add(s)

    def is_countermodel_to(self, a: Argument, /) -> bool:
        return (
            all(map(self.Meta.designated_values.__contains__, map(self.value_of, a.premises))) and
            self.value_of(a.conclusion) not in self.Meta.designated_values)

    def read_branch(self, branch: Branch, /) -> Self:
        self._check_not_finished()
        read = self._read_node
        for node in branch:
            read(node, branch)
        self.finish()
        return self

    def _read_node(self, node: Node, branch: Branch, /) -> Self:
        self._check_not_finished()
        if isinstance(node, AccessNode):
            self.R.add(node.pair())
            return
        if isinstance(node, SentenceNode):
            s = node['sentence']
            self.sentences.add(s)
            self.constants.update(s.constants)
        if isinstance(node, WorldNode):
            w = node['world']
        else:
            w = 0
        self.R[w]
        if not isinstance(node, SentenceNode):
            return
        s = node['sentence']
        is_literal = self.is_sentence_literal(s)
        is_opaque = self.is_sentence_opaque(s)
        if not is_literal and not is_opaque:
            return
        if isinstance(node, DesignationNode):
            d = node['designated']
            s_negative = -s
            has_negative = branch.has(sdwnode(s_negative, d, node.get('world')))
            is_negated = type(s) is Operated and s.operator is Operator.Negation
            if is_negated:
                s = s_negative
                if d:
                    value = 'FB'[has_negative]
                else:
                    value = 'TN'[has_negative]
            else:
                if d:
                    value = 'TB'[has_negative]
                else:
                    value = 'FN'[has_negative]
        else:
            value = 'T'
        value = self.values[value]
        if is_opaque:
            self.set_opaque_value(s, value, world=w)
        else:
            self.set_literal_value(s, value, world=w)

    def finish(self) -> Self:
        self._check_not_finished()
        self._complete_frames()
        self._finished = True
        return self

    def get_data(self) -> dict:
        frames = self.frames
        if not self.Meta.modal:
            return frames[0].get_data()
        worlds = sorted(frames)
        return dict(
            Worlds = dict(
                in_summary      = True,
                datatype        = 'set',
                member_datatype = 'int',
                member_typehint = 'world',
                symbol          = 'W',
                values          = worlds),
            Access = dict(
                in_summary      = True,
                datatype        = 'set',
                typehint        = 'access_relation',
                member_datatype = 'tuple',
                member_typehint = 'access',
                symbol          = 'R',
                values          = list(self.R.flat(w1s=worlds, sort=True))),
            Frames = dict(
                datatype        = 'list',
                typehint        = 'frames',
                member_datatype = 'map',
                member_typehint = 'frame',
                symbol          = 'F',
                values          = [
                    dict(
                        description = f'frame at world {w}',
                        datatype    = 'map',
                        typehint    = 'frame',
                        value       = frames[w].get_data())
                    for w in worlds]))

    def __enter__(self) -> Self:
        self._check_not_finished()
        return self

    def __exit__(self, type, value, traceback):
        if not self.finished:
            self.finish()

    def _complete_frames(self):
        self._check_not_finished()
        if self._is_frame_complete:
            return
        # track all atomics and opaques
        atomics = set()
        opaques = set()
        preds = set()
        for s in self.sentences:
            atomics.update(s.atomics)
            preds.update(s.predicates)
        # ensure frames for each world
        for w in self.R:
            self.frames[w]
        # ensure R has each world
        # for w in self.frames:
        #     self.R[w]
        for w, frame in self.frames.items():
            atomics.update(frame.atomics)
            opaques.update(frame.opaques)
            preds.update(frame.predicates)
        unass = self.Meta.unassigned_value
        for w, frame in self.frames.items():
            for pred in preds:
                frame.predicates[pred]
            for s in atomics:
                if s not in frame.atomics:
                    frame.atomics[s] = unass
            for s in opaques:
                if s not in frame.opaques:
                    frame.opaques[s] = unass
        self._is_frame_complete = True

    def _check_finished(self):
        if not self.finished:
            raise Emsg.IllegalState('Model not yet finished')

    def _check_not_finished(self):
        if self.finished:
            raise Emsg.IllegalState('Model already finished')

    @classmethod
    def truth_table(cls, oper: Operator, / , *, reverse=False) -> TruthTable[MvalT_co]:
        oper = Operator(oper)
        values = cls.values
        if reverse:
            values = tuple(reversed(values))
        inputs = tuple(product(values, repeat=oper.arity))
        outputs = tuple(starmap(getattr(cls.truth_function, oper.name), inputs))
        return TruthTable(
            inputs = inputs,
            outputs = outputs,
            operator = oper,
            values = cls.values,
            mapping = MapProxy(dict(zip(inputs, outputs))))

    @classmethod
    def __init_subclass__(cls):
        super().__init_subclass__()
        Meta = cls.__dict__.get('Meta', LogicType.Meta.for_module(cls.__module__))
        if not Meta:
            return
        cls.Meta = Meta
        cls.values = Meta.values
        cls.minval = min(Meta.values)
        cls.maxval = max(Meta.values)
        cls.truth_function = cls.TruthFunction(Meta.values)

    class TruthFunction(Generic[MvalT], metaclass=ModelsMeta):

        values: type[MvalT]
        maxval: MvalT
        minval: MvalT
        values_sequence: tuple[MvalT, ...]
        values_indexes: Mapping[MvalT, int]

        generalizing_operators: Mapping[Operator, Literal['min', 'max']] = EMPTY_MAP
        generalized_orderings: Mapping[Literal['min', 'max'], tuple[MvalT, ...]] = EMPTY_MAP
        generalized_indexes: Mapping[Literal['min', 'max'], Mapping[MvalT, int]]

        __slots__ = (
            'generalized_indexes',
            'maxval',
            'minval',
            'values_indexes',
            'values_sequence',
            'values')

        def __init__(self, values: type[MvalT]) -> None:
            self.values = values
            self.maxval = max(values)
            self.minval = min(values)
            self.values_sequence = tuple(self.values)
            self.values_indexes = MapProxy({
                value: i
                for i, value in enumerate(self.values_sequence)})
            self.generalized_indexes = MapProxy({
                key: MapProxy(dict(map(reversed, enumerate(value))))
                for key, value in self.generalized_orderings.items()})

        def __call__(self, oper: Operator, *args: MvalT) -> MvalT:
            try:
                name = oper.name
            except AttributeError:
                name = Operator(oper).name
            try:
                func = getattr(self, name)
            except AttributeError:
                raise NotImplementedError from ValueError(oper)
            return func(*args)

        def Assertion(self, a, /):
            return self.values[a]

        def Negation(self, a, /):
            if a == 'F':
                return self.values['T']
            if a == 'T':
                return self.values['F']
            return self.values[a]

        Conjunction = staticmethod(min)

        Disjunction = staticmethod(max)

        def MaterialConditional(self, a, b, /):
            return self.Disjunction(self.Negation(a), b)

        def MaterialBiconditional(self, a, b, /):
            return self.Conjunction(*starmap(self.MaterialConditional, ((a, b), (b, a))))

        Conditional = MaterialConditional

        def Biconditional(self, a, b, /):
            return self.Conjunction(*starmap(self.Conditional, ((a, b), (b, a))))

        def generalize(self, oper: Operator, it: Iterable[MvalT], /) -> MvalT:
            mode = self.generalizing_operators[oper]
            try:
                ordering = self.generalized_orderings[mode]
            except KeyError:
                if mode == 'max':
                    return maxceil(self.maxval, it, self.minval)
                if mode == 'min':
                    return minfloor(self.minval, it, self.maxval)
                raise NotImplementedError from ValueError(mode)
            indexes = self.generalized_indexes[mode]
            it = map(indexes.__getitem__, it)
            if mode == 'max':
                return ordering[maxceil(len(ordering) - 1, it, 0)]
            if mode == 'min':
                return ordering[minfloor(0, it, len(ordering) - 1)]
            raise NotImplementedError from ValueError(mode)

    class Frame(metaclass=ModelsMeta):
        """
        A Frame comprises the interpretation of sentences and predicates at a world.
        """

        atomics: dict[Atomic, Mval]
        "An assignment of each atomic sentence to a truth value"

        opaques: dict[Sentence, Mval]
        "An assignment of each opaque (un-interpreted) sentence to a value"

        predicates: dict[Predicate, PredicateInterpretation]
        "A mapping of predicates to their interpretation (extention/anti-extension)"

        model: LogicType.Model
        'Reference to the parent model'

        __slots__ = ('atomics', 'opaques', 'predicates', 'model')

        def __init__(self, model: LogicType.Model, /):
            self.model = model
            self.atomics = {}
            self.opaques = {}
            self.predicates = defaultdict(PredicateInterpretation.blank)

        def get_data(self) -> dict:
            return dict(
                Atomics = self._get_sentencemap_data(self.atomics),
                Opaques = self._get_sentencemap_data(self.opaques),
                Predicates = self._get_predicates_data())

        def _get_sentencemap_data(self, base: Mapping[Sentence, Any]):
            return dict(
                datatype        = 'function',
                typehint        = 'truth_function',
                input_datatype  = 'sentence',
                output_datatype = 'string',
                output_typehint = 'truth_value',
                symbol          = 'v',
                values          = [
                    dict(input=sentence, output=base[sentence])
                    for sentence in sorted(base)])

        def _get_predicates_data(self):
            return dict(
                in_summary  = True,
                datatype    = 'list',
                values      = [
                    v for predicate in sorted(self.predicates)
                        for v in self._get_predicate_data_values(predicate)])

        def _get_predicate_data_values(self, predicate: Predicate):
            data = self._get_predicate_data_part(predicate, self.predicates[predicate].pos)
            many_valued = self.model.Meta.many_valued
            if many_valued:
                data['symbol'] += '+'       
            yield data
            if not many_valued:
                return
            data = self._get_predicate_data_part(predicate, self.predicates[predicate].neg)
            data['symbol'] += '-'
            yield data

        def _get_predicate_data_part(self, predicate: Predicate, tuples: Iterable[tuple[Constant, ...]]):
            return dict(
                datatype        = 'function',
                typehint        = 'extension',
                input_datatype  = 'predicate',
                output_datatype = 'set',
                output_typehint = 'extension',
                symbol = 'P',
                values = [dict(input=predicate, output=sorted(tuples))])

        def __eq__(self, other):
            if other is self:
                return True
            if not isinstance(other, __class__):
                return NotImplemented
            if self.atomics != other.atomics or self.opaques != other.opaques:
                return False
            if len(self.predicates) != len(other.predicates):
                return False
            for pred, interp in self.predicates.items():
                if pred not in other.predicates:
                    return False
                if other.predicates[pred].pos != interp.pos:
                    return False
                if self.model.Meta.many_valued and other.predicates[pred].neg != interp.neg:
                    return False
            return True

@dataclass(kw_only = True)
class TruthTable:
    'Truth table data class.'

    inputs: tuple[tuple[MvalT, ...], ...]
    outputs: tuple[MvalT, ...]
    operator: Operator
    values: type[MvalT]
    mapping: Mapping[tuple[MvalT, ...], MvalT]

class PredicateInterpretation(NamedTuple):

    neg: set[tuple[Constant, ...]]
    pos: set[tuple[Constant, ...]]

    def set_value(self, params: tuple[Constant, ...], value: Mval|str, /):
        if value == 'T':
            if params in self.neg:
                raise Emsg.ConflictForAntiExtension(value, params)
            self.pos.add(params)
        elif value == 'F':
            if params in self.pos:
                raise Emsg.ConflictForExtension(value, params)
            self.neg.add(params)
        elif value == 'N':
            if params in self.pos:
                raise Emsg.ConflictForExtension(value, params)
            if params in self.neg:
                raise Emsg.ConflictForAntiExtension(value, params)
        elif value == 'B':
            self.pos.add(params)
            self.neg.add(params)
        else:
            raise NotImplementedError from ValueError(value)

    def get_value(self, params: tuple[Constant, ...], values, /):
        if params in self.neg:
            if params in self.pos:
                value = 'B'
            else:
                value = 'F'
        elif params in self.pos:
            value = 'T'
        else:
            if 'N' in values:
                value = 'N'
            else:
                value = 'F'
        return values[value]

    @classmethod
    def blank(cls):
        return cls(set(), set())

class AccessGraph(defaultdict[int, set[int]]):

    __slots__ = EMPTY_SET

    def __init__(self, *args, **kw):
        super().__init__(set, *args, **kw)

    def has(self, pair: tuple[int, int], /) -> bool:
        w1, w2 = pair
        return w1 in self and w2 in self[w1]

    def add(self, pair: tuple[int, int], /):
        w1, w2 = pair
        self[w1].add(w2)
        self[w2]

    def addall(self, it):
        for _ in map(self.add, it): pass

    def flat(self, *, w1s=None, sort=False):
        if w1s is None:
            w1s = sorted(self) if sort else self
        for w1 in w1s:
            w2s = sorted(self[w1]) if sort else self[w1]
            for w2 in w2s:
                yield w1, w2