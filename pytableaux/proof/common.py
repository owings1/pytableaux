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
"""
pytableaux.proof.common
^^^^^^^^^^^^^^^^^^^^^^^

"""
from __future__ import annotations

import builtins
import operator as opr
from collections import defaultdict
from collections.abc import Set
from typing import (TYPE_CHECKING, Any, Collection, Iterable, Iterator,
                    Mapping, SupportsIndex)

from pytableaux import tools
from pytableaux.errors import Emsg, check
from pytableaux.lang.lex import Constant, Sentence
from pytableaux.proof.util import BranchEvent, PropMap
from pytableaux.tools import EMPTY_MAP, isattrstr, isint, abcs, MapProxy
from pytableaux.tools.decorators import lazy, operd, raisr
from pytableaux.tools.events import EventEmitter
from pytableaux.tools.hybrids import qset
from pytableaux.tools.mappings import ItemsIterator, MapCover, dmap, dmapattr
from pytableaux.tools.sequences import SequenceApi
from pytableaux.tools.sets import EMPTY_SET, SetView, setf

if TYPE_CHECKING:
    from typing import Literal, overload

    from pytableaux.models import BaseModel
    from pytableaux.proof.tableaux import Rule
    from pytableaux.proof.util import StepEntry

__all__ = (
    'Branch',
    'Node',
    'Target',
)

_first_const = Constant.first()

NOARG = object()

class Node(MapCover):
    'A tableau node.'

    __slots__ = (
        '_is_access',
        '_is_modal',
        '_worlds',
        'step',
        'ticked',
    )

    def __new__(cls, arg = None, /):
        if type(arg) is cls:
            return arg
        return object.__new__(cls)

    @tools.closure
    def __init__():
        sa = object.__setattr__
        def init(self: Node, mapping: Mapping = EMPTY_MAP, /):
            if mapping is self:
                return
            try:
                if len(mapping):
                    mapping = MapProxy(dict(mapping))
                else:
                    mapping = EMPTY_MAP
            except TypeError:
                check.inst(mapping, Mapping)
                raise
            sa(self, '_cov_mapping', mapping)
        return init

    def copy(self: Node) -> Node:
        inst = object.__new__(type(self))
        object.__setattr__(inst, '_cov_mapping', self._cov_mapping)
        return inst

    @property
    def id(self) -> int:
        return id(self)

    @property
    def is_closure(self) -> bool:
        return self.get('flag') == PropMap.ClosureNode['flag']

    @lazy.prop
    def is_modal(self) -> bool:
        return self.any('world', 'world1', 'world2')

    @lazy.prop
    def is_access(self) -> bool:
        return self.has('world1', 'world2')

    @lazy.prop
    def worlds(self, /, *, names = ('world', 'world1', 'world2')) -> setf[int]:
        """
        The set of worlds referenced in the node properties. This combines
        the properties `world`, `world1`, and `world2`.
        """
        return setf(filter(isint, map(self.get, names)))

    def has(self, *names: str) -> bool:
        'Whether the node has a non-``None`` property of all the given names.'
        for value in map(self.get, names):
            if value is None:
                return False
        return True

    def any(self, *names: str) -> bool:
        """
        Whether the node has a non-``None`` property of any of the given names.
        """
        for value in map(self.get, names):
            if value is not None:
                return True
        return False

    def meets(self, props: Mapping, /) -> bool:
        'Whether the node properties match all those give in ``props``.'
        for prop in props:
            if prop not in self or props[prop] != self[prop]:
                return False
        return True

    __bool__    = operd(tools.true)
    __eq__      = operd(opr.is_)
    __hash__    = operd(builtins.id)
    __delattr__ = raisr(AttributeError)

    if TYPE_CHECKING:
        @overload
        def get(self, key: Literal['sentence']) -> Sentence|None:...
        @overload
        def __getitem__(self, key: Literal['sentence']) -> Sentence:...

    def __getitem__(self, key):
        try:
            return self._cov_mapping[key]
        except KeyError:
            return PropMap.NodeDefaults[key]

    def __setattr__(self, name: str, value: Any, /, *, _sa = object.__setattr__):
        if (v := getattr(self, name, NOARG)) is not NOARG and (
            name != 'ticked' or value is not v
        ):
            raise Emsg.ReadOnly(self, name)
        _sa(self, name, value)

    @classmethod
    def _oper_res_type(cls, other_type: type[Iterable]) -> type[Mapping]:
        'Always produce a ``dmap`` on math operations.'
        return dmap

    def __repr__(self):
        return f'<{type(self).__name__} id:{self.id} props:{dict(self)}>'

class Branch(SequenceApi[Node], EventEmitter):
    'A tableau branch.'

    __closed: bool
    __constants: set[Constant]
    __index: Branch.Index
    __model: BaseModel
    __nextconst: Constant
    __nextworld: int
    __nodes: qset[Node]
    __origin: Branch
    __parent: Branch|None
    __ticked: set[Node]
    __worlds: set[int]
    _constants: SetView[Constant]
    _worlds: SetView[int]

    __slots__ = (
        '__closed',
        '__constants',
        '__index',
        '__model',
        '__nextconst',
        '__nextworld',
        '__nodes',
        '__origin',
        '__parent',
        '__ticked',
        '__worlds',
        '_constants',
        '_worlds',
    )

    def __init__(self, parent: Branch = None, /):
        """Create a branch.
        
        Args:
            parent: The parent branch, if any.
        """

        self.__init_parent(parent)

        EventEmitter.__init__(self, *BranchEvent)

        # Make sure properties are copied if needed in copy()

        self.__closed = False

        self.__nodes = qset()
        self.__ticked = set()

        self.__index = self.Index()
        self.__worlds = set()
        self.__constants = set()

        self.__nextworld = 0
        self.__nextconst = _first_const

    def copy(self, *, parent: Branch = None, listeners: bool = False) -> Branch:
        """Copy of the branch.
        
        Args:
            parent: The branch to set as the new branch's parent.
            listeners: Whether to copy event listeners, default ``False``.
        
        Returns:
            The new branch.
        """
        cls = type(self)
        b = cls.__new__(cls)

        b.__init_parent(parent)

        b.events = self.events.copy(listeners = listeners)

        b.__closed = self.__closed

        b.__nodes = self.__nodes.copy()
        b.__ticked = self.__ticked.copy()

        b.__index = self.__index.copy()
        b.__worlds = self.__worlds.copy()
        b.__constants = self.__constants.copy()

        b.__nextworld = self.__nextworld
        b.__nextconst = self.__nextconst

        try:
            b.__model = self.__model
        except AttributeError:
            pass

        return b

    @property
    def id(self) -> int:
        "The branch object id."
        return id(self)

    @property
    def parent(self) -> Branch|None:
        "The parent branch, if any."
        return self.__parent

    @property
    def origin(self) -> Branch:
        "The root branch."
        return self.__origin

    @property
    def closed(self) -> bool:
        "Whether the branch is closed."
        return self.__closed

    @property
    def leaf(self) -> Node|None:
        "The leaf node, if any."
        return self[-1] if len(self) else None

    @property
    def model(self) -> BaseModel|None:
        "The associated model, if any."
        try:
            return self.__model
        except AttributeError:
            pass

    @model.setter
    def model(self, model: BaseModel):
        try:
            self.__model
        except AttributeError:
            pass
        else:
            raise AttributeError
        self.__model = model

    @lazy.prop
    def worlds(self) -> SetView[int]:
        "The set of worlds on the branch."
        return SetView(self.__worlds)

    @lazy.prop
    def constants(self) -> SetView[Constant]:
        "The set of constants on the branch."
        return SetView(self.__constants)

    def has(self, props: Mapping, /) -> bool:
        """Whether there is a node on the branch that matches the given properties.
        
        Args:
            props: A mapping of properties.
        
        Returns:
            bool: Whether there is a match.
        """
        for _ in self.search(props, limit = 1):
            return True
        return False

    def any(self, mappings: Iterable[Mapping], /) -> bool:
        """Check a list of property mappings against the ``has()`` method.
        
        Args:
            mappings: An iterable of property mappings.
        
        Returns:
            ``True`` when the first match is found, else ``False``.
        """
        for props in mappings:
            for _ in self.search(props, limit = 1):
                return True
        return False

    def all(self, mappings: Iterable[Mapping], /) -> bool:
        """Check a list of property mappings against the ``has()`` method.
        
        Args:
            mappings: An iterable of property mappings.
        
        Returns:
            ``False`` when the first non-match is found, else ``True``.
        """
        for props in mappings:
            for _ in self.search(props, limit = 1):
                break
            else:
                return False
        return True

    def find(self, props: Mapping, /) -> Node|None:
        """Find the first node on the branch that matches the given properties.

        Args:
            props: A mapping of properties.
        
        Returns:
            The node, or ``None`` if not found.
        """
        for node in self.search(props, limit = 1):
            return node

    def search(self, props: Mapping, /, limit: int = None) -> Iterator[Node]:
        """
        Search the nodes on the branch that match the given properties, up to the
        limit, if given.

        Args:
            props: A mapping of properties.
            limit (int): An optional result limit.

        Returns:
            A generator.
        """
        n = 0
        for node in self.__index.select(props, self):
            if limit is not None and n >= limit:
                return
            if node.meets(props):
                n += 1
                yield node

    def append(self, node: Mapping, /) -> Branch:
        """Append a node.

        Args:
            node: Node object or mapping.
        
        Returns:
            self
        
        Raises:
            DuplicateValueError: if the node is already on the branch.
        """
        node = Node(node)
        self.__nodes.append(node)

        if (s := node.get('sentence')) is not None:
            if len(cons := s.constants):
                if self.__nextconst in cons:
                    self.__nextconst = max(cons).next()
                self.__constants.update(cons)

        if len(worlds := node.worlds):
            maxworld = max(worlds)
            if maxworld >= self.__nextworld:
                self.__nextworld = maxworld + 1
            self.__worlds.update(worlds)

        # Add to index *before* after_node_add event
        self.__index.add(node)
        self.emit(BranchEvent.AFTER_ADD, node, self)
        return self

    def extend(self, nodes: Iterable[Mapping], /) -> Branch:
        """Add multiple nodes.

        Args:
            nodes: An iterable of node objects/mappings.

        Returns:
            self

        Raises:
            DuplicateValueError: if a node is already on the branch.
        """
        for _ in map(self.append, nodes): pass
        return self

    def tick(self, node: Node) -> None:
        """Tick a node for the branch.
        
        Args:
            node: The node to tick.
        """
        if node not in self.__ticked:
            self.__ticked.add(node)
            node.ticked = True
            self.emit(BranchEvent.AFTER_TICK, node, self)

    def close(self) -> Branch:
        """Close the branch. Adds a flag node and emits the `AFTER_BRANCH_CLOSE
        event.
        
        Returns:
            self.
        """
        if not self.__closed:
            self.__closed = True
            self.append(PropMap.ClosureNode)
            self.emit(BranchEvent.AFTER_CLOSE, self)
        return self

    def is_ticked(self, node: Node, /) -> bool:
        """Whether the node is ticked relative to the branch.

        Args:
            node: The node instance.
        
        Returns
            bool: Whether the node is ticked.
        """
        return node in self.__ticked

    def new_constant(self) -> Constant:
        'Return a new constant that does not appear on the branch.'
        return self.__nextconst

    def new_world(self) -> int:
        """Return a new world that does not appear on the branch.
        """
        return self.__nextworld

    def __init_parent(self, parent: Branch|None, /):
        try:
            self.__parent
        except AttributeError:
            pass
        else:
            raise AttributeError
        if parent is not None:
            if parent is self:
                raise ValueError('A branch cannot be its own parent')
            check.inst(parent, Branch)
            self.__origin = parent.origin
        else:
            self.__origin = self
        self.__parent = parent

    if TYPE_CHECKING:
        @overload
        def add(self, node: Mapping, /) -> Branch:...
        @overload
        def __getitem__(self, index: SupportsIndex) -> Node:...
        @overload
        def __getitem__(self, slice_: slice) -> qset[Node]:...

    add = append

    def __getitem__(self, i):
        return self.__nodes[i]

    def __len__(self):
        return len(self.__nodes)

    def __iter__(self) -> Iterator[Node]:
        return iter(self.__nodes)

    __bool__ = operd(tools.true)
    __eq__   = operd(opr.is_)
    __hash__ = operd(builtins.id)

    def __contains__(self, node, /):
        return node in self.__nodes

    def __repr__(self):
        leafid = leaf.id if (leaf := self.leaf) else None
        return (
            f'<{type(self).__name__} id:{self.id} nodes:{len(self)} '
            f'leaf:{leafid} closed:{self.closed}>'
        )

    @classmethod
    def _from_iterable(cls, it: Iterable, /):
        b = cls()
        b.extend(it)
        return b

    class Index(dict[str, dict[Any, set[Node]]], abcs.Copyable):
        "Branch node index."

        __slots__ = EMPTY_SET

        def __init__(self):
            self.update(
                sentence   = defaultdict(set),
                designated = defaultdict(set),
                world      = defaultdict(set),
                world1     = defaultdict(set),
                world2     = defaultdict(set),
                w1Rw2      = defaultdict(set),
            )

        def add(self, node: Node, /):
            for prop in self:
                value = None
                found = False
                if prop == 'w1Rw2':
                    if node.get('world1') is not None and node.get('world2') is not None:
                        value = (node['world1'], node['world2'])
                        found = True
                elif prop in node:
                    value = node[prop]
                    found = True
                if found:
                    self[prop][value].add(node)

        def copy(self) -> Branch.Index:
            inst = type(self)()
            for prop, index in self.items():
                for value, nodes in index.items():
                    inst[prop][value].update(nodes)
            return inst

        def select(self, props: Mapping, default: Collection[Node], /) -> Collection[Node]:
            best = None
            for prop in self:
                value = None
                found = False
                if prop == 'w1Rw2':
                    if 'world1' in props and 'world2' in props:
                        value = (props['world1'], props['world2'])
                        found = True
                elif prop in props:
                    value = props[prop]
                    found = True
                if found:
                    if value not in self[prop]:
                        return EMPTY_SET
                    nodes = self[prop][value]
                    if best is None or len(nodes) < len(best):
                        best = nodes
                    # we could do no better
                    if len(best) == 1:
                        break
            if best is None:
                best = default
            return best

class Target(dmapattr[str, Any]):
    """Rule application target.
    """

    branch : Branch
    constant : Constant
    designated : bool
    flag   : str
    node   : Node
    nodes  : Set[Node]
    rule   : Rule
    sentence : Sentence
    world  : int
    world1 : int
    world2 : int
    _entry : StepEntry

    __slots__ = (
        'rule', 'branch', 'constant', 'designated', 'flag', 'node', 'nodes',
        'sentence', 'world', 'world1', 'world2',
    )

    # For dmapattr
    _keyattr_ok = staticmethod(setf(__slots__).__contains__)

    __slots__ += '_entry',

    def __init__(self, it: Iterable = None, /, **kw):
        if it is not None:
            self.update(it)
        if len(kw):
            self.update(kw)
        if 'branch' not in self:
            raise Emsg.MissingValue('branch')

    @property
    def type(self) -> str:
        if 'nodes'  in self: return 'Nodes'
        if 'node'   in self: return 'Node'
        if 'branch' in self: return 'Branch'
        raise ValueError

    def __setitem__(self, key: str, value: Any):
        if self._keyattr_ok(key):
            if self.get(key, value) != value:
                raise Emsg.ValueConflictFor(key, value, self[key])
        elif not isattrstr(key):
            check.inst(key, str)
            raise Emsg.BadAttrName(key)
        super().__setitem__(key, value)

    __bool__    = operd(tools.true)
    __delitem__ = raisr(TypeError)
    __delattr__ = raisr(AttributeError)

    def __dir__(self):
        return list(self._names())

    def __repr__(self):
        props = dict(ItemsIterator(self._names(), vget = self.get))
        return f'<{type(self).__name__} {props}>'

    def _names(self) -> Iterator[str]:
        return (name for name in self.__slots__
            if self._keyattr_ok(name))


del(
    builtins,
    lazy,
    operd,
    opr,
    raisr,
)
