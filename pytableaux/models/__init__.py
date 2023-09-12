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
from collections.abc import Mapping
from dataclasses import dataclass
from functools import partial
from itertools import product, starmap
from types import MappingProxyType as MapProxy
from typing import Any, Generic, Iterable, Iterator, Self, TypeVar, TYPE_CHECKING

from ..errors import DenotationError, IllegalStateError, ModelValueError, check
from ..lang import (Argument, Atomic, Constant, Operated, Operator, Predicate,
                    Predicated, Quantified, Sentence)
from ..logics import LogicType
from ..proof import (AccessNode, Branch, DesignationNode, Node, SentenceNode,
                     WorldNode, sdwnode)
from ..tools import EMPTY_SET, abcs, maxceil, minfloor

if TYPE_CHECKING:
    from ..logics import LogicType as Logic

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

    Meta: type[Logic.Meta]

    values: type[MvalT_co]
    "The values of the model"

    truth_function: Logic.Model.TruthFunction[MvalT_co]
    "The truth function instance"

    frames: Mapping[int, Logic.Model.Frame[MvalT_co]]
    "A map from worlds to their frame"

    constants: set[Constant]

    sentences: set[Sentence]

    R: Logic.Model.Access
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
        self.R = self.Access()
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
            (oper := s.operator) is oper.Negation and (
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

    def value_of_opaque(self, s: Sentence, /, *, world: int = 0) -> MvalT_co:
        self._check_finished()
        return self.frames[world].opaques.get(s, self.Meta.unassigned_value)

    def value_of_atomic(self, s: Atomic, /, *, world: int = 0) -> MvalT_co:
        self._check_finished()
        return self.frames[world].atomics.get(s, self.Meta.unassigned_value)

    def value_of_predicated(self, s: Predicated, /, *, world: int = 0) -> MvalT_co:
        self._check_finished()
        params = s.params
        for param in params:
            if param not in self.constants:
                raise DenotationError(f'Parameter {param} is not in the constants')
        return self.frames[world].predicates[s.predicate].get(params, self.Meta.unassigned_value)

    def value_of_quantified(self, s: Quantified, /, **kw) -> MvalT_co:
        self._check_finished()
        if not self.Meta.quantified:
            raise NotImplementedError(f'Model does not support quantification')
        it = self._unquantify_values(s, **kw)
        q = s.quantifier
        if q is q.Existential:
            return maxceil(self.maxval, it, self.minval)
        if q is q.Universal:
            return minfloor(self.minval, it, self.maxval)
        raise NotImplementedError from ValueError(s.quantifier)

    def _unquantify_values(self, s: Quantified, /, **kw) -> Iterator[MvalT_co]:
        value_of = self.value_of
        for c in self.constants:
            yield value_of(c >> s, **kw)

    def _unmodal_values(self, s: Operated, /, *, world: int = 0) -> Iterator[MvalT_co]:
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
            if oper is oper.Possibility:
                return maxceil(self.maxval, it, self.minval)
            if oper is oper.Necessity:
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
        if type(s) is Operated and (oper := s.operator) is oper.Negation:
            value = self.truth_function(oper, value)
            return self.set_literal_value(s.lhs, value, **kw)
        if type(s) is Atomic:
            return self.set_atomic_value(s, value, **kw)
        if type(s) is Predicated:
            return self.set_predicated_value(s, value, **kw)
        raise NotImplementedError from TypeError(type(s))

    def set_opaque_value(self, s: Sentence, value: MvalT_co, /, *, world: int = 0):
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

    def set_atomic_value(self, s: Atomic, value: MvalT_co, /, *, world: int = 0):
        self._check_not_finished()
        value = self.values[value]
        atomics = self.frames[world].atomics
        if atomics.get(s, value) is not value:
            raise ModelValueError(f'Inconsistent value for sentence {s}: {value}')
        atomics[s] = value
        self.sentences.add(s)

    def set_predicated_value(self, s: Predicated, value: MvalT_co, /, *, world: int = 0):
        self._check_not_finished()
        value = self.values[value]
        frame = self.frames[world]
        if len(s.variables):
            raise ValueError(f'Free variables not allowed')
        frame.predicates[s.predicate][s.params] = value
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

    def _read_node(self, node: Node, branch: Branch, /) -> None:
        self._check_not_finished()
        if isinstance(node, AccessNode):
            self.R.add(node.pair())
            return
        if isinstance(node, WorldNode):
            w = node['world']
            self.R[w]
        else:
            w = 0
        if not isinstance(node, SentenceNode):
            return
        s = node['sentence']
        self.sentences.add(s)
        self.constants.update(s.constants)
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
                base = 'TNFB'
            else:
                base = 'FNTB'
            value = base[2 * d + has_negative]
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
        self.R.enforce()
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
        for w in self.frames:
            self.R[w]
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
            raise IllegalStateError('Model not yet finished')

    def _check_not_finished(self):
        if self.finished:
            raise IllegalStateError('Model already finished')

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

        __slots__ = (
            'maxval',
            'minval',
            'values')

        def __init__(self, values: type[MvalT]) -> None:
            self.values = values
            self.maxval = max(values)
            self.minval = min(values)

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

        def Assertion(self, a: MvalT) -> MvalT:
            return self.values[a]

        def Negation(self, a: MvalT) -> MvalT:
            if a == 'F':
                return self.values['T']
            if a == 'T':
                return self.values['F']
            return self.values[a]

        def MaterialConditional(self, a: MvalT, b: MvalT) -> MvalT:
            return self.Disjunction(self.Negation(a), b)

        def Conjunction(self, a: MvalT, b: MvalT) -> MvalT:
            return min(a, b)

        def Disjunction(self, a: MvalT, b: MvalT) -> MvalT:
            return max(a, b)

        def Conditional(self, a: MvalT, b: MvalT) -> MvalT:
            return self.MaterialConditional(a, b)

        def MaterialBiconditional(self, a: MvalT, b: MvalT) -> MvalT:
            return self.Conjunction(*starmap(self.MaterialConditional, ((a, b), (b, a))))

        def Biconditional(self, a: MvalT, b: MvalT) -> MvalT:
            return self.Conjunction(*starmap(self.Conditional, ((a, b), (b, a))))


    class Frame(Generic[MvalT], metaclass=ModelsMeta):
        """
        A Frame comprises the interpretation of sentences and predicates at a world.
        """

        atomics: dict[Atomic, MvalT]
        "An assignment of each atomic sentence to a truth value"

        opaques: dict[Sentence, MvalT]
        "An assignment of each opaque (un-interpreted) sentence to a value"

        predicates: Mapping[Predicate, PredicateInterpretation[MvalT]]
        "A mapping of predicates to their interpretation"

        model: Logic.Model[MvalT]
        'Reference to the parent model'

        __slots__ = ('atomics', 'opaques', 'predicates', 'model')

        def __init__(self, model: Logic.Model[MvalT], /):
            self.model = model
            self.atomics = {}
            self.opaques = {}
            self.predicates = defaultdict(partial(PredicateInterpretation, model))

        def get_data(self) -> dict:
            return dict(
                Atomics = self._get_sentencemap_data(self.atomics),
                Opaques = self._get_sentencemap_data(self.opaques),
                Predicates = self._get_predicates_data())

        def _get_sentencemap_data(self, base: Mapping[Sentence, MvalT]):
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
            interp = self.predicates[predicate]
            data = self._get_predicate_data_part(predicate, interp.having(*'TB'))
            many_valued = self.model.Meta.many_valued
            if many_valued:
                data['symbol'] += '+'
            yield data
            if not many_valued:
                return
            data = self._get_predicate_data_part(predicate, interp.having(*'BF'))
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
            otherpreds = other.predicates
            if len(self.predicates) != len(otherpreds):
                return False
            for pred, interp in self.predicates.items():
                if pred not in otherpreds:
                    return False
                if otherpreds[pred] != interp:
                    return False
            return True

    class Access(defaultdict[int, set[int]]):

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

        def enforce(self):
            pass

@dataclass(kw_only = True)
class TruthTable(Generic[MvalT]):
    'Truth table data class.'

    inputs: tuple[tuple[MvalT, ...], ...]
    outputs: tuple[MvalT, ...]
    operator: Operator
    values: type[MvalT]
    mapping: Mapping[tuple[MvalT, ...], MvalT]

class PredicateInterpretation(Mapping[tuple[Constant, ...], MvalT]):

    __slots__ = ('model', 'mapping')

    def __init__(self, model: Logic.Model[MvalT]):
        self.model = model
        self.mapping = {}

    def having(self, *values) -> Iterator[tuple[Constant, ...]]:
        get = self.model.values.get
        values = set(filter(None, (get(str(value), None) for value in values)))
        if not values:
            return
        for params, value in self.items():
            if value in values:
                yield params

    def __setitem__(self, key, value):
        value = self.model.values[value]
        if self.get(key, value) is not value:
            raise ModelValueError(f'{value=} {key=}')
        self.mapping[key] = value

    def __getitem__(self, key):
        return self.mapping[key]

    def __iter__(self):
        yield from self.mapping

    def __len__(self):
        return len(self.mapping)

    def __eq__(self, other):
        if self is other:
            return True
        if not isinstance(other, type(self)):
            return NotImplemented
        return self.mapping == other.mapping

class SerialAccess(BaseModel.Access):

    def enforce(self):
        needs_world = {w for w in self if not self[w]}
        if needs_world:
            # only add one extra world
            w2 = max(self) + 1
            add = self.add
            for w1 in needs_world:
                # make all who need it access the new world
                add((w1, w2))
            # make the new world access itself
            add((w2, w2))

class ReflexiveAccess(BaseModel.Access):

    def enforce(self):
        for w in self:
            self.add((w, w))

class ReflexiveTransitiveAccesss(ReflexiveAccess):

    def enforce(self):
        while True:
            super().enforce()
            to_add = set()
            add = to_add.add
            for w1 in self:
                for w2 in self[w1]:
                    for w3 in self[w2]:
                        if w3 not in self[w1]:
                            add((w1, w3))
            if not to_add:
                break
            for _ in map(self.add, to_add): pass

class GlobalAccess(ReflexiveTransitiveAccesss):

    def enforce(self):

        while True:
            super().enforce()
            to_add = set()
            add = to_add.add
            for w1 in self:
                for w2 in self[w1]:
                    if w1 not in self[w2]:
                        add((w2, w1))
            if not to_add:
                break
            for _ in map(self.add, to_add): pass
