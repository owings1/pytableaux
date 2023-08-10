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
pytableaux.proof.common
^^^^^^^^^^^^^^^^^^^^^^^

"""
from __future__ import annotations

from collections import defaultdict
from collections.abc import Mapping, Sequence, Set
from types import MappingProxyType as MapProxy
from typing import TYPE_CHECKING, Any, Iterable, Optional

from ..errors import Emsg, check
from ..lang import Constant, Sentence
from ..tools import (EMPTY_MAP, EMPTY_SET, MapCover, SetView, abcs, dictattr,
                     isattrstr, isint, itemsiter, lazy, qset)
from ..tools.events import EventEmitter
from . import BranchMeta, NodeMeta

if TYPE_CHECKING:

    from ..models import BaseModel
    from . import Rule, Tableau

__all__ = (
    'Branch',
    'Node',
    'Target')

_FIRST_CONST = Constant.first()

NOARG = object()

class Node(MapCover, abcs.Copyable, metaclass=NodeMeta):
    'A tableau node.'

    __slots__ = ('_worlds', 'step', 'ticked')

    def __init__(self, mapping = EMPTY_MAP, /):
        if mapping is self:
            return
        try:
            if len(mapping):
                mapping = MapProxy(dict(mapping))
            else:
                mapping = EMPTY_MAP
        except TypeError:
            raise Emsg.InstCheck(mapping, Mapping)
        self._cov_mapping = mapping

    def copy(self):
        inst = object.__new__(type(self))
        inst._cov_mapping = self._cov_mapping
        return inst

    @property
    def id(self) -> int:
        "The unique object ID."
        return id(self)

    @property
    def is_modal(self) -> bool:
        "Whether this is a modal node."
        return isinstance(self, Modal)

    @property
    def is_access(self) -> bool:
        "Whether this is a modal access node."
        return isinstance(self, AccessNode)

    @property
    def is_flag(self) -> bool:
        "Whether this is a flag node."
        return isinstance(self, FlagNode)

    @lazy.prop
    def worlds(self, /, *, names = (NodeMeta.Key.world, NodeMeta.Key.w1, NodeMeta.Key.w2)):
        """
        The set of worlds referenced in the node properties. This combines
        the properties `world`, `world1`, and `world2`.
        """
        return frozenset(filter(isint, map(self.get, names)))

    def has(self, *names) -> bool:
        'Whether the node has a non-``None`` property of all the given names.'
        for value in map(self.get, names):
            if value is None:
                return False
        return True

    def any(self, *names) -> bool:
        """
        Whether the node has a non-``None`` property of any of the given names.
        """
        for value in map(self.get, names):
            if value is not None:
                return True
        return False

    def meets(self, mapping: Mapping, /) -> bool:
        'Whether the node properties match all those given in `mapping`.'
        try:
            for key in mapping:
                if self[key] != mapping[key]:
                    break
            else:
                return True
        except KeyError:
            pass
        return False

    def __bool__(self):
        return True

    def __eq__(self, other):
        return self is other

    def __hash__(self):
        return id(self)

    __delattr__ = Emsg.Attribute.razr

    def __getitem__(self, key):
        try:
            return self._cov_mapping[key]
        except KeyError:
            return Node.PropMap.Defaults[key]

    def __repr__(self):
        return f'<{type(self).__name__} id:{self.id} props:{dict(self)}>'

    @staticmethod
    def for_mapping(mapping: Mapping, /):
        if (value := mapping.get(Node.Key.flag)) is not None:
            if value == Node.PropMap.Closure[Node.Key.flag]:
                return ClosureNode(mapping)
            if value == Node.PropMap.QuitFlag[Node.Key.flag]:
                return QuitFlagNode(mapping)
            return FlagNode(mapping)
        if mapping.get(Node.Key.w1) is not None and mapping.get(Node.Key.w2) is not None:
            return AccessNode(mapping)
        if mapping.get(Node.Key.sentence) is not None:
            if mapping.get(Node.Key.world) is not None:
                return SentenceWorldNode(mapping)
            if mapping.get(Node.Key.designation) is not None:
                return SentenceDesignationNode(mapping)
            return SentenceNode(mapping)
        if mapping.get(Node.Key.ellipsis):
            return EllipsisNode(mapping)
        return UnknownNode(mapping)

class Modal: __slots__ = EMPTY_SET
class Designation: __slots__ = EMPTY_SET
class UnknownNode(Node): __slots__ = EMPTY_SET
class EllipsisNode(Node): __slots__ = EMPTY_SET
class FlagNode(Node): __slots__ = EMPTY_SET
class ClosureNode(FlagNode): __slots__ = EMPTY_SET
class QuitFlagNode(FlagNode): __slots__ = EMPTY_SET
class SentenceNode(Node): __slots__ = EMPTY_SET
class SentenceWorldNode(SentenceNode, Modal): __slots__ = EMPTY_SET
class SentenceDesignationNode(SentenceNode, Designation): __slots__ = EMPTY_SET
class AccessNode(Node, Modal): __slots__ = EMPTY_SET

class NodeIndex(dict[tuple[str, ...], dict[tuple[Any, ...], set[Node]]], abcs.Copyable):
    "Branch node index."

    __slots__ = EMPTY_SET

    INDEXES = (
        (Node.Key.sentence,),
        (Node.Key.designation,),
        (Node.Key.world,),
        (Node.Key.world1, Node.Key.world2),
        (Node.Key.world1,),
        (Node.Key.world2,))

    def __init__(self):
        self.update((key, defaultdict(set)) for key in self.INDEXES)

    def add(self, node: Node, /):
        for key, index in self.items():
            try:
                index[*map(node.__getitem__, key)].add(node)
            except KeyError:
                continue

    def copy(self):
        inst = type(self)()
        for key, index in self.items():
            for value, base in index.items():
                inst[key][value].update(base)
        return inst

    def select(self, mapping: Mapping, default, /) -> set[Node]:
        bestsize = max(map(len, (self, mapping)))
        best = default
        for key, index in self.items():
            if len(best) <= bestsize:
                break
            try:
                base = index[*map(mapping.__getitem__, key)]
            except KeyError:
                continue
            if len(base) < len(best):
                best = base
        return best

class Branch(Sequence[Node], EventEmitter, abcs.Copyable, metaclass=BranchMeta):
    'A tableau branch.'

    __constants: set[Constant]
    __index: NodeIndex
    __model: BaseModel
    __nextconst: Constant
    __nextworld: int
    __nodes: qset[Node]
    __origin: Branch
    __parent: Optional[Branch]
    __ticked: set[Node]
    __worlds: set[int]
    _constants: SetView[Constant]
    _worlds: SetView[int]

    __slots__ = (
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
        '_worlds')

    def __init__(self, parent = None, /):
        """Create a branch.
        
        Args:
            parent (Optional[Branch]): The parent branch, if any.
        """
        EventEmitter.__init__(self, *Branch.Events)
        self.parent = parent
        # Make sure properties are copied if needed in copy()
        self.__nodes = qset()
        self.__ticked = set()
        self.__index = NodeIndex()
        self.__worlds = set()
        self.__constants = set()
        self.__nextworld = 0
        self.__nextconst = _FIRST_CONST

    def copy(self, *, parent = None, listeners = False):
        """Copy of the branch.
        
        Args:
            parent (Optional[Branch]): The branch to set as the new branch's parent.
                Defaults to None.
            listeners (bool): Whether to copy event listeners. Defaults to `False`.
        
        Returns:
            Branch: The new branch.
        """
        cls = type(self)
        b = cls.__new__(cls)
        b.parent = parent
        b.events = self.events.copy(listeners = listeners)
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

    @parent.setter
    def parent(self, parent: Branch|None):
        try:
            self.__parent
        except AttributeError:
            pass
        else:
            raise AttributeError
        if parent is not None:
            if parent is self:
                raise ValueError('A branch cannot be its own parent')
            self.__origin = parent.origin
        else:
            self.__origin = self
        self.__parent = parent

    @property
    def origin(self) -> Branch:
        "The root branch."
        return self.__origin

    @property
    def closed(self) -> bool:
        "Whether the branch is closed."
        return bool(len(self) and isinstance(self[-1], ClosureNode))
        # return self.__closed

    @property
    def leaf(self) -> Optional[Node]:
        "The leaf node, if any."
        return self[-1] if len(self) else None

    @property
    def model(self) -> Optional[BaseModel]:
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

    def has(self, mapping: Mapping, /) -> bool:
        """Whether there is a node on the branch that matches the given properties.
        
        Args:
            props (Mapping): A mapping of properties.
        
        Returns:
            bool: Whether there is a match.
        """
        for _ in self.search(mapping, limit = 1):
            return True
        return False

    def any(self, mappings: Iterable[Mapping], /) -> bool:
        """Check a list of property mappings against the :attr:`has` method.
        
        Args:
            mappings (Iterable[Mapping]): An iterable of property mappings.
        
        Returns:
            bool: True when the first match is found, else False.
        """
        for mapping in mappings:
            for _ in self.search(mapping, limit = 1):
                return True
        return False

    def all(self, mappings: Iterable[Mapping], /) -> bool:
        """Check a list of property mappings against the :attr:`has` method.
        
        Args:
            mappings (Iterable[Mapping]): An iterable of property mappings.
        
        Returns:
            bool: False when the first non-match is found, else True.
        """
        for props in mappings:
            for _ in self.search(props, limit = 1):
                break
            else:
                return False
        return True

    def find(self, mapping: Mapping, /) -> Node|None:
        """Find the first node on the branch that matches the given properties.

        Args:
            props (Mapping): A mapping of properties.
        
        Returns:
            Optional[Node]: The node, or ``None`` if not found.
        """
        for node in self.search(mapping, limit = 1):
            return node

    def search(self, mapping: Mapping, /, limit: int|None = None):
        """
        Search the nodes on the branch that match the given properties, up to the
        limit, if given.

        Args:
            props (Mapping): A mapping of properties.
            limit (int): An optional result limit.

        Returns:
            Generator[Node]: Results generator.
        """
        n = 0
        for node in self.__index.select(mapping, self):
            if limit is not None and n >= limit:
                break
            if node.meets(mapping):
                n += 1
                yield node

    def append(self, node: Node|Mapping, /):
        """Append a node.

        Args:
            node (Mapping): Node object or mapping.
        
        Returns:
            Branch: self
        
        Raises:
            DuplicateValueError: if the node is already on the branch.
        """
        if self.closed:
            raise ValueError('Already closed')
        if not isinstance(node, Node):
            node = Node.for_mapping(node)
        
        self.__nodes.append(node)

        if isinstance(node, SentenceNode):
            s: Sentence = node[Node.Key.sentence]
            if len(cons := s.constants):
                if self.__nextconst in cons:
                    self.__nextconst = max(cons).next()
                self.__constants.update(cons)

        if isinstance(node, Modal):
            if len(worlds := node.worlds):
                maxworld = max(worlds)
                if maxworld >= self.__nextworld:
                    self.__nextworld = maxworld + 1
                self.__worlds.update(worlds)

        # Add to index *before* after_node_add event
        self.__index.add(node)
        self.emit(Branch.Events.AFTER_ADD, node, self)
        if isinstance(node, ClosureNode):
            self.emit(Branch.Events.AFTER_CLOSE, self)
        return self

    add = append

    def extend(self, nodes: Iterable[Node|Mapping], /):
        """Add multiple nodes.

        Args:
            nodes (Iterable): An iterable of node objects/mappings.

        Returns:
            Branch: self

        Raises:
            DuplicateValueError: if a node is already on the branch.
        """
        for _ in map(self.append, nodes): pass
        return self

    def tick(self, node: Node) -> None:
        """Tick a node for the branch.
        
        Args:
            node (Node): The node to tick.
        """
        if node not in self.__ticked:
            self.__ticked.add(node)
            node.ticked = True
            self.emit(Branch.Events.AFTER_TICK, node, self)

    def close(self):
        """Close the branch. Adds a flag node and emits the `AFTER_BRANCH_CLOSE
        event.
        
        Returns:
            Branch: self.
        """
        return self.append(ClosureNode(Node.PropMap.Closure))

    def is_ticked(self, node: Node, /) -> bool:
        """Whether the node is ticked relative to the branch.

        Args:
            node (Node): The node instance.
        
        Returns
            bool: Whether the node is ticked.
        """
        return node in self.__ticked

    def new_constant(self) -> Constant:
        """Return a new constant that does not appear on the branch.

        Returns:
            Constant: The new constant.
        """
        return self.__nextconst

    def new_world(self) -> int:
        """Return a new world that does not appear on the branch.

        Returns:
            int: A new word.
        """
        return self.__nextworld

    def __getitem__(self, i):
        return self.__nodes[i]

    def __len__(self):
        return len(self.__nodes)

    def __bool__(self):
        return True

    def __eq__(self, other):
        return self is other

    def __hash__(self):
        return id(self)

    def __contains__(self, node, /):
        return node in self.__nodes

    def __repr__(self):
        leafid = self.leaf.id if self.leaf else None
        return (f'<{type(self).__name__} id:{self.id} nodes:{len(self)} '
            f'leaf:{leafid} closed:{self.closed}>')


class Target(dictattr):
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
    _entry : Tableau.StepEntry

    __slots__ = ('rule', 'branch', 'constant', 'designated', 'flag', 'node',
        'nodes', 'sentence', 'world', 'world1', 'world2')

    # For dictattr
    _keyattr_ok = staticmethod(frozenset(__slots__).__contains__)

    __slots__ += ('_entry',)

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

    def __setitem__(self, key, value):
        if self._keyattr_ok(key):
            if self.get(key, value) != value:
                raise Emsg.ValueConflictFor(key, value, self[key])
        elif not isattrstr(key):
            check.inst(key, str)
            raise Emsg.BadAttrName(key)
        super().__setitem__(key, value)

    def __bool__(self):
        return True

    __delitem__ = pop = popitem = Emsg.Type.razr
    __delattr__ = Emsg.Attribute.razr

    def __dir__(self):
        return list(self._names())

    def __repr__(self):
        props = dict(itemsiter(self._names(), vget = self.get))
        return f'<{type(self).__name__} {props}>'

    def _names(self):
        return filter(self._keyattr_ok, self)
