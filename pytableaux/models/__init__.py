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
from functools import partial, reduce
from itertools import product, starmap
from types import MappingProxyType as MapProxy
from typing import (TYPE_CHECKING, Generic, Iterable, Iterator, Self, Sequence,
                    TypeVar)

from ..errors import DenotationError, IllegalStateError, ModelValueError, check
from ..lang import (Argument, Atomic, Constant, Operated, Operator, Predicate,
                    Predicated, Quantified, Quantifier, Sentence)
from ..logics import LogicType
from ..proof import (AccessNode, Branch, DesignationNode, Node, SentenceNode,
                     WorldNode, sdwnode)
from ..tools import EMPTY_SET, abcs, maxceil, minfloor

if TYPE_CHECKING:
    from ..logics import LogicType as Logic

__all__ = (
    'BaseModel',
    'Mval',
    'TruthTable',
    'ValueFDE',
    'ValueK3',
    'ValueLP',
    'ValueCPL')

MvalT = TypeVar('MvalT', bound='Mval')
MvalT_co = TypeVar('MvalT_co', bound='Mval', covariant=True)
_T = TypeVar('_T')
NOARG = object()

class Mval(abcs.Ebc):

    __slots__ = ('name', 'value')

    F: float
    T: float

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

    valseq: Sequence[MvalT_co]

    minval: MvalT_co
    maxval: MvalT_co

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
        if self.Meta.modal:
            self.frames = defaultdict(partial(self.Frame, self))
        else:
            self.frames = MapProxy({0: self.Frame(self)})
        self.constants = set()
        self.sentences = set()
        self.R = self.Access(hook=self.frames.__getitem__)
        self.frames[0]
        self.R[0]

    def isopaque(self, s: Sentence, /) -> bool:
        Meta = self.Meta
        if not Meta.quantified and type(s) is Quantified:
            return True
        if not Meta.modal and type(s) is Operated and s.operator in Meta.modal_operators:
            return True
        return False

    def isliteral(self, s: Sentence, /) -> bool:
        return self.isopaque(s) or type(s) in (Atomic, Predicated) or (
            type(s) is Operated and
            (oper := s.operator) is oper.Negation and (
                type(s.lhs) in (Atomic, Predicated) or
                self.isopaque(s.lhs)))

    def value_of_opaque(self, s: Sentence, w: int, /) -> MvalT_co:
        self._check_finished()
        return self.frames[w].opaques.get(s, self.Meta.unassigned_value)

    def value_of_atomic(self, s: Atomic, w: int, /) -> MvalT_co:
        self._check_finished()
        return self.frames[w].atomics.get(s, self.Meta.unassigned_value)

    def value_of_predicated(self, s: Predicated, w: int, /) -> MvalT_co:
        self._check_finished()
        params = s.params
        for param in params:
            if param not in self.constants:
                raise DenotationError(f'Parameter {param} is not in the constants')
        return self.frames[w].predicates[s.predicate].get(params, self.Meta.unassigned_value)

    def value_of_quantified(self, s: Quantified, w: int, /) -> MvalT_co:
        self._check_finished()
        if not self.Meta.quantified:
            raise NotImplementedError(f'Model does not support quantification')
        it = self.unquantify_values(s, w)
        q = s.quantifier
        if q is q.Existential:
            return maxceil(self.maxval, it, self.minval)
        if q is q.Universal:
            return minfloor(self.minval, it, self.maxval)
        raise NotImplementedError from ValueError(s.quantifier)

    def value_of_operated(self, s: Operated, w: int, /) -> MvalT_co:
        self._check_finished()
        oper = s.operator
        Meta = self.Meta
        if oper in Meta.truth_functional_operators:
            return self.truth_function(oper, *(self[s, w] for s in s))
        if oper in Meta.modal_operators:
            if not Meta.modal:
                raise NotImplementedError(f'Model does not support modal operators')
            it = self.unmodal_values(s, w)
            if oper is oper.Possibility:
                return maxceil(self.maxval, it, self.minval)
            if oper is oper.Necessity:
                return minfloor(self.minval, it, self.maxval)
        raise NotImplementedError from ValueError(oper)

    def unquantify_values(self, s: Quantified, w: int, /) -> Iterator[MvalT_co]:
        for c in self.constants:
            yield self[c >> s, w]

    def unmodal_values(self, s: Operated, w: int, /) -> Iterator[MvalT_co]:
        s, = s
        for w2 in self.R[w]:
            yield self[s, w2]

    def is_countermodel_to(self, a: Argument, /) -> bool:
        isdes = self.Meta.designated_values.__contains__
        it = map(self.__getitem__, a)
        return not isdes(next(it)) and all(map(isdes, it))

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
        if not self.isliteral(s):
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
        self[s, w] = value

    def finish(self) -> Self:
        self._check_not_finished()
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

    def __getitem__(self, key: tuple[Sentence, int]|Sentence) -> MvalT_co:
        if isinstance(key, tuple):
            s, w = key
        else:
            s, w = key, 0
        self._check_finished()
        if self.isopaque(s):
            name = 'value_of_opaque'
        else:
            name = f'value_of_{type(s).__name__.lower()}'
        try:
            func = getattr(self, name)
        except AttributeError:
            check.inst(s, Sentence)
            raise NotImplementedError from ValueError(s)
        return func(s, w)

    def __setitem__(self, key: tuple[Sentence, int]|Sentence, value: MvalT_co):
        if isinstance(key, tuple):
            s, w = key
        else:
            s, w = key, 0
        self._check_not_finished()
        value = self.values[value]
        frame = self.frames[w]
        if self.isopaque(s):
            frame.opaques[s] = value
        elif type(s) is Operated and (oper := s.operator) is oper.Negation:
            value = self.truth_function(oper, value)
            self[s.lhs, w] = value
            return
        elif type(s) is Atomic:
            frame.atomics[s] = value
        elif type(s) is Predicated:
            if len(s.variables):
                raise ValueError(f'Free variables not allowed')
            frame.predicates[s.predicate][s.params] = value
        else:
            raise NotImplementedError from TypeError(type(s))
        self.sentences.add(s)
        for pred in s.predicates:
            frame.predicates[pred]
        self.constants.update(s.constants)

    __iter__ = None

    def __enter__(self) -> Self:
        self._check_not_finished()
        return self

    def __exit__(self, type, value, traceback):
        if not self.finished:
            self.finish()

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
        values = Meta.values
        cls.values = values
        cls.valseq = tuple(values)
        cls.minval = min(values)
        cls.maxval = max(values)
        cls.truth_function = cls.TruthFunction(values)

    class TruthFunction(Generic[MvalT], metaclass=ModelsMeta):

        values: type[MvalT]
        maxval: MvalT
        minval: MvalT
        generalizers = MapProxy({
            Quantifier.Existential: Operator.Disjunction,
            Quantifier.Universal: Operator.Conjunction,
            Operator.Possibility: Operator.Disjunction,
            Operator.Necessity: Operator.Conjunction})

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
            a = self.values[a]
            if a is a.F:
                return a.T
            if a is a.T:
                return a.F
            return a

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

        def generalize(self, oper: Operator|Quantifier, it: Iterable[MvalT], *args, **kw) -> MvalT:
            oper = Operator(self.generalizers.get(oper, oper))
            return reduce(getattr(self, oper.name), it, *args, **kw)

    class Frame(Generic[MvalT], metaclass=ModelsMeta):
        """
        A Frame comprises the interpretation of sentences and predicates at a world.
        """

        atomics: Interpretation[Atomic, MvalT]
        "An assignment of each atomic sentence to a truth value"

        opaques: Interpretation[Sentence, MvalT]
        "An assignment of each opaque (un-interpreted) sentence to a value"

        predicates: Mapping[Predicate, Interpretation[tuple[Constant, ...], MvalT]]
        "A mapping of predicates to their interpretation"

        model: Logic.Model[MvalT]
        'Reference to the parent model'

        __slots__ = ('atomics', 'opaques', 'predicates', 'model')

        def __init__(self, model: Logic.Model[MvalT], /):
            self.model = model
            self.atomics = Interpretation(model)
            self.opaques = Interpretation(model)
            self.predicates = defaultdict(partial(Interpretation, model))

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

    class Access(defaultdict[int, set[int]], metaclass=ModelsMeta):

        __slots__ = ('hook')

        def __init__(self, *args, hook=None, **kw):
            self.hook = hook or int
            super().__init__(set, *args, **kw)

        def has(self, pair: tuple[int, int], /) -> bool:
            w1, w2 = pair
            return w1 in self and w2 in self[w1]

        def add(self, pair: tuple[int, int], /):
            w1, w2 = pair
            self.hook(w1)
            self.hook(w2)
            self[w1].add(w2)
            self[w2]

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

class Interpretation(Mapping[_T, MvalT]):

    __slots__ = ('model', 'mapping')

    def __init__(self, model: Logic.Model[MvalT]):
        self.model = model
        self.mapping = {}

    def having(self, *values) -> Iterator[_T]:
        get = self.model.values.get
        values = set(filter(None, (get(str(value), None) for value in values)))
        if not values:
            return
        for key, value in self.items():
            if value in values:
                yield key

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
        add = self.add
        for w in self:
            add((w, w))

class ReflexiveTransitiveAccesss(ReflexiveAccess):

    def enforce(self):
        myadd = self.add
        enforce = super().enforce
        while True:
            enforce()
            to_add = set()
            add = to_add.add
            for w1 in self:
                for w2 in self[w1]:
                    for w3 in self[w2]:
                        if w3 not in self[w1]:
                            add((w1, w3))
            if not to_add:
                break
            for _ in map(myadd, to_add): pass

class GlobalAccess(ReflexiveTransitiveAccesss):

    def enforce(self):
        myadd = self.add
        enforce = super().enforce
        while True:
            enforce()
            to_add = set()
            add = to_add.add
            for w1 in self:
                for w2 in self[w1]:
                    if w1 not in self[w2]:
                        add((w2, w1))
            if not to_add:
                break
            for _ in map(myadd, to_add): pass
