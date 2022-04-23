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

__all__ = 'Node', 'Branch', 'Target'

import operator as opr
from collections import defaultdict
from collections.abc import Set
from itertools import chain, filterfalse
from typing import (TYPE_CHECKING, Any, Collection, Iterable, Iterator, Mapping, NamedTuple,
                    SupportsIndex)

from pytableaux.lexicals import Constant, Sentence
from pytableaux.errors import Emsg, check
from pytableaux.proof.types import BranchEvent
from pytableaux.tools import closure, isint, isattrstr, true
from pytableaux.tools.decorators import lazy, operd, raisr
from pytableaux.tools.events import EventEmitter
from pytableaux.tools.hybrids import qset
from pytableaux.tools.mappings import ItemsIterator, MapCover, dmap, dmapattr
from pytableaux.tools.misc import orepr
from pytableaux.tools.sequences import SequenceApi
from pytableaux.tools.sets import EMPTY_SET, SetView, setf
if TYPE_CHECKING:
    from pytableaux.models import BaseModel
    from pytableaux.proof.tableaux import Rule

_node_defaults = MapCover(world = None, designated = None)
_first_const = Constant.first()

class Node(MapCover):
    'A tableau node.'

    __slots__ = (
        'step', 'ticked', '_is_access', '_is_modal', '_worlds',
        '__len__', '_getitem_orig_', '__iter__', '__reversed__',
    )

    def __new__(cls, arg = None, /):
        if type(arg) is cls:
            return arg
        return object.__new__(cls)

    def __init__(self, mapping: Mapping = None, /):
        if self is mapping:
            return
        self._init_cover(dict(mapping or EMPTY_SET), self)

    def copy(self):
        inst = object.__new__(type(self))
        self._init_cover(self, inst)
        return inst

    @property
    def is_closure(self) -> bool:
        return self.get('flag') == 'closure'

    @lazy.prop
    def is_modal(self) -> bool:
        return self.any('world', 'world1', 'world2', 'worlds')

    @lazy.prop
    def is_access(self) -> bool:
        return self.has('world1', 'world2')

    @lazy.prop
    def worlds(self) -> setf[int]:
        """
        Return the set of worlds referenced in the node properties. This combines
        the properties `world`, `world1`, `world2`, and `worlds`.
        """
        return setf(filter(isint,
            chain(self.get('worlds', EMPTY_SET),
            map(self.get, ('world', 'world1', 'world2'))),
        ))

    def has(self, *names: str):
        'Whether the node has a non-``None`` property of all the given names.'
        for name in names:
            if self.get(name) is None:
                return False
        return True

    def any(self, *names: str):
        """
        Whether the node has a non-``None`` property of any of the given names.
        """
        for name in names:
            if self.get(name) is not None:
                return True
        return False

    def meets(self, props: Mapping):
        'Whether the node properties match all those give in ``props``.'
        for prop in props:
            if prop not in self or props[prop] != self[prop]:
                return False
        return True

    __bool__    = true
    __eq__      = operd(opr.is_)
    __hash__    = operd(id)
    __delattr__ = raisr(AttributeError)

    @property
    def id(self) -> int:
        return id(self)

    @staticmethod
    @closure
    def _init_cover():
        forig = MapCover._init_cover
        items = tuple((
            dmap(forig.__kwdefaults__['items']) - {'__getitem__'} |
            {'_getitem_orig_': '__getitem__'}
        ).items())
        def init(src: Mapping, dest: Any, /, *, items = items):
            return forig(src, dest, items = items)
        return init

    def __getitem__(self, key, /, *, getdefault = _node_defaults.__getitem__):
        try:
            return self._getitem_orig_(key)
        except KeyError:
            return getdefault(key)

    def __setattr__(self, name, val):
        if getattr(self, name, val) != val:
            raise Emsg.ReadOnlyAttr(name, self)
        super().__setattr__(name, val)

    @classmethod
    def _oper_res_type(cls, other_type):
        'Always produce a ``dmap`` on math operations.'
        return dmap

    def __repr__(self):
        return orepr(self, id = self.id, props = dict(self))

class Access(NamedTuple):

    world1: int
    world2: int

    @property
    def w1(self) -> int:
        return self.world1

    @property
    def w2(self) -> int:
        return self.world2

    @classmethod
    def fornode(cls, node: Mapping) -> Access:
        return cls._make(map(node.__getitem__, cls._fields))

    def tonode(self) -> Node:
        return Node(self._asdict())

    def reverse(self) -> Access:
        return self._make(reversed(self))

class Branch(SequenceApi[Node], EventEmitter):
    'A tableau branch.'

    __closed  : bool
    __nodes   : qset[Node]
    __ticked  : set[Node]
    __worlds    : set[int]
    __nextworld : int
    __constants : set[Constant]
    __nextconst : Constant
    __index: Branch.Index

    def __init__(self, parent: Branch = None, /):
        """Create a branch.
        
        Args:
            parent: The parent branch, if any.
        """

        self.__init_parent(parent)

        EventEmitter.__init__(self, *BranchEvent)

        # Make sure properties are copied if needed in copy()

        self.__closed = False

        self.__nodes   = qset()
        self.__ticked  = set()

        self.__worlds    = set()
        self.__nextworld = 0
        self.__constants = set()
        self.__nextconst = _first_const
        self.__index = self.Index()

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
    def leaf(self) -> Node:
        "The leaf node, if any."
        return self[-1] if len(self) else None

    @property
    def model(self) -> BaseModel|None:
        "The associated model, if any."
        try: return self.__model
        except AttributeError: pass

    @model.setter
    def model(self, model: BaseModel):
        try:
            self.__model
        except AttributeError: pass
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

    def all(self, props_list: Iterable[Mapping], /) -> bool:
        """Check a list of property dictionaries against the ``has()`` method.
        
        Args:
            mappings: An iterable of property mappings.
        
        Returns:
            ``False`` when the first non-match is found, else ``True``.
        """
        for props in props_list:
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
        s: Sentence = node.get('sentence')
        if s:
            cons = s.constants
            if cons:
                if self.__nextconst in cons:
                    self.__nextconst = max(cons).next()
                self.__constants.update(cons)
        if node.worlds:
            maxworld = max(node.worlds)
            if maxworld >= self.__nextworld:
                self.__nextworld = maxworld + 1
            self.__worlds.update(node.worlds)

        # Add to index *before* after_node_add event
        self.__index.add(node)
        self.emit(BranchEvent.AFTER_NODE_ADD, node, self)
        return self

    add = append

    def extend(self, nodes: Iterable[Mapping], /) -> Branch:
        """Add multiple nodes.

        Args:
            nodes: An iterable of node objects/mappings.

        Returns:
            self

        Raises:
            DuplicateValueError: if a node is already on the branch.
        """
        for node in nodes:
            self.append(node)
        return self

    def tick(self, *nodes: Node) -> None:
        """Tick node(s) for the branch.
        
        Args:
            *nodes: The nodes to tick.
        """
        event = BranchEvent.AFTER_NODE_TICK
        for node in filterfalse(self.is_ticked, nodes):
            self.__ticked.add(node)
            node.ticked = True
            self.emit(event, node, self)

    def close(self) -> Branch:
        """Close the branch. Adds a flag node and emits the `AFTER_BRANCH_CLOSE
        event.
        
        Returns:
            self.
        """
        if not self.closed:
            self.__closed = True
            self.append({'is_flag': True, 'flag': 'closure'})
            self.emit(BranchEvent.AFTER_BRANCH_CLOSE, self)
        return self

    def is_ticked(self, node: Node, /) -> bool:
        """Whether the node is ticked relative to the branch.

        Args:
            node: The node instance.
        
        Returns
            bool: Whether the node is ticked.
        """
        return node in self.__ticked

    def copy(self, parent: Branch = None, events: bool = False) -> Branch:
        """
        Return a copy of the branch.
        
        Args:
            parent: The branch to set as the new branch's parent.
            events: Whether to copy event listeners, default ``False``.
        
        Returns:
            The new branch.
        """
        cls = type(self)
        b = cls.__new__(cls)
        b.__init_parent(parent)

        if events:
            b.events = self.events.copy()
        else:
            b.events = self.events.barecopy()
        
        b.__closed = self.__closed

        b.__nodes   = self.__nodes.copy()
        b.__ticked  = self.__ticked.copy()

        b.__worlds    = self.__worlds.copy()
        b.__nextworld = self.__nextworld
        b.__constants = self.__constants.copy()
        b.__nextconst = self.__nextconst
        b.__index = self.__index.copy()

        try:
            b.__model = self.__model
        except AttributeError:
            pass

        return b

    def new_constant(self) -> Constant:
        'Return a new constant that does not appear on the branch.'
        return self.__nextconst

    def new_world(self) -> int:
        """Return a new world that does not appear on the branch.
        """
        return self.__nextworld

    def __init_parent(self, parent: Branch|None, /):
        if hasattr(self, '_Branch__parent'):
            raise AttributeError
        if parent is not None:
            if parent is self:
                raise ValueError('A branch cannot be its own parent')
            check.inst(parent, Branch)
            self.__origin = parent.origin
        else:
            self.__origin = self
        self.__parent = parent

    def __getitem__(self, key: SupportsIndex) -> Node:
        return self.__nodes[key]

    def __len__(self):
        return len(self.__nodes)

    def __iter__(self) -> Iterator[Node]:
        return iter(self.__nodes)

    __hash__ = operd(id)
    __eq__   = operd(opr.is_)
    __bool__ = true

    @property
    def id(self) -> int:
        "The branch object id."
        return id(self)

    def __contains__(self, node):
        return node in self.__nodes

    def __repr__(self):
        return orepr(self, 
            id     = self.id,
            nodes  = len(self),
            leaf   = self.leaf.id if self.leaf else None,
            closed = self.closed,
        )

    @classmethod
    def _from_iterable(cls, nodes):
        b = cls()
        b.extend(nodes)
        return b

    class Index(dict[str, dict[Any, set[Node]]]):
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

        def add(self, node: Node):
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

        __copy__ = copy

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
    rule   : Rule
    node   : Node
    nodes  : Set[Node]
    world  : int
    world1 : int
    world2 : int
    flag   : str
    sentence   : Sentence
    constant   : Constant
    designated : bool

    __slots__ = setf({
        'branch', 'rule', 'node', 'nodes',
        'world', 'world1', 'world2',
        'sentence', 'designated', 'constant',
        'flag',
    })

    def __init__(self, it: Iterable = None, /, **kw):
        if it is not None:
            self.update(it)
        if len(kw):
            self.update(kw)
        if 'branch' not in self:
            raise Emsg.MissingValue('branch')

    @property
    def type(self):
        if 'nodes'  in self: return 'Nodes'
        if 'node'   in self: return 'Node'
        if 'branch' in self: return 'Branch'
        raise ValueError

    # For dmapattr
    _keyattr_ok = __slots__.__contains__

    def __setitem__(self, key: str, value, /, *, isattrkey = _keyattr_ok):
        if isattrkey(key):
            if self.get(key, value) != value:
                raise Emsg.ValueConflictFor(key, value, self[key])
        elif not isattrstr(key):
            check.inst(key, str)
            raise Emsg.BadAttrName(key)
        super().__setitem__(key, value)

    __delitem__ = raisr(TypeError)
    __delattr__ = raisr(AttributeError)
    __bool__    = true

    def __dir__(self):
        return list(self._names())

    def __repr__(self):
        return orepr(self, dict(ItemsIterator(self._names(), vget = self.get)))

    def _names(self) -> Iterator[str]:
        get = self.get
        return (name for name in self.__slots__ if get(name) is not None)


del(lazy, operd, raisr)
