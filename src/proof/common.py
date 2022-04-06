from __future__ import annotations as _

__all__ = 'Node', 'Branch', 'Target'

from errors import instcheck as instcheck, Emsg
# from tools.abcs import Abc, T
from tools.callables import preds, cchain
from tools.decorators import (
    # abstract,
    closure,
    static,
    # overload,
    # final,
    lazy, operd, raisr
)
from tools.events import EventEmitter
from tools.hybrids import qset
from tools.mappings import (
    dmap,
    dmapattr,
    ItemsIterator,
    MappingApi,
    MapCover
) 
from tools.sequences import (
    SequenceApi,
    # SequenceCover,
)
from tools.sets import EMPTY_SET, setf#, SetCover
from lexicals import Constant, Sentence

from proof.types import BranchEvent

from collections.abc import Set
from functools import partial
from itertools import (
    chain,
    filterfalse,
    # starmap,
)
import operator as opr
from typing import (
    Any,
    # Callable,
    # Generic,
    Iterable,
    Iterator,
    Mapping,
    NamedTuple,
    # Sequence,
    SupportsIndex,
    # TypeVar,
)

class Node(MappingApi):
    'A tableau node.'

    __slots__ = (
        'step', 'ticked', '_is_access', '_is_modal', '_worlds',
        '__len__', '_getitem_orig_', '__iter__', '__reversed__',
    )

    def __new__(cls, arg = None, /):
        if type(arg) is cls: return arg
        return object.__new__(cls)

    def __init__(self, mapping: Mapping = None, /):
        if self is mapping:
            return
        self.__mapinit(dmap(mapping or EMPTY_SET), self)

    def copy(self):
        return self.__mapinit(self, object.__new__(type(self)))

    @property
    def is_closure(self) -> bool:
        return self.get('flag') == 'closure'

    @lazy.prop
    def is_modal(self) -> bool:
        return self.has_any('world', 'world1', 'world2', 'worlds')

    @lazy.prop
    def is_access(self) -> bool:
        return self.has('world1', 'world2')

    @lazy.prop
    def worlds(self, /, filtpred = preds.instanceof[int]) -> setf[int]:
        """
        Return the set of worlds referenced in the node properties. This combines
        the properties `world`, `world1`, `world2`, and `worlds`.
        """
        return setf(filter(filtpred,
            chain(self.get('worlds', EMPTY_SET),
            map(self.get, ('world', 'world1', 'world2'))),
        ))

    def has(self, *names: str):
        'Whether the node has a non-``None`` property of all the given names.'
        for name in names:
            if self.get(name) is None:
                return False
        return True

    def has_any(self, *names: str):
        """
        Whether the node has a non-``None`` property of any of the given names.
        """
        for name in names:
            if self.get(name) is not None:
                return True
        return False

    def has_props(self, props: Mapping):
        'Whether the node properties match all those give in ``props``.'
        for prop in props:
            if prop not in self or props[prop] != self[prop]:
                return False
        return True

    __bool__    = preds.true
    __eq__      = operd(opr.is_)
    __hash__    = operd(id)
    __delattr__ = raisr(AttributeError)

    id = property(operd(id)())

    @static
    @closure

    def __mapinit():
        items = tuple(dict(
            __len__  = '__len__',
            __iter__ = '__iter__',
            _getitem_orig_ = '__getitem__',
            __reversed__   = '__reversed__',
        ).items())
        sa = object.__setattr__
        ga = object.__getattribute__
        def mapinit(src: Mapping, dest: Node, /,):
            'Copy the Mapping methods from the source.'
            for name, lookup in items:
                sa(dest, name, ga(src, lookup))
            return dest
        return mapinit

    def __getitem__(self, key, /, *,
        getdefault = MapCover(world = None, designated = None).__getitem__
    ):
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
        'Always produce a plain dict on math operations.'
        return dmap

    def __repr__(self):
        from tools.misc import orepr
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

    def todict(self) -> dict[str, int]:
        return self._asdict()

    def tonode(self) -> Node:
        return Node(self.todict())

    def reverse(self) -> Access:
        return self._make(reversed(self))

class Branch(SequenceApi[Node], EventEmitter):
    'A tableau branch.'

    def __init__(self, parent: Branch = None, /):

        self.__init_parent(parent)

        super().__init__(*BranchEvent)

        # Make sure properties are copied if needed in copy()

        self.__closed = False

        # self.__nodes   : list[Node] = []
        self.__nodes   : qset[Node] = qset()
        # self.__nodeset : set[Node] = set()
        self.__ticked  : set[Node] = set()

        self.__worlds    : set[int] = set()
        self.__nextworld : int = 0
        self.__constants : set[Constant] = set()
        self.__nextconst : Constant = Constant.first()
        self.__pidx      : dict[str, dict[Any, set[Node]]]= dict(
            sentence   = {},
            designated = {},
            world      = {},
            world1     = {},
            world2     = {},
            w1Rw2      = {},
        )

    @property
    def parent(self) -> Branch:
        return self.__parent

    @property
    def origin(self) -> Branch:
        return self.__origin

    @property
    def closed(self) -> bool:
        return self.__closed

    @property
    def leaf(self) -> Node:
        return self[-1] if len(self) else None

    @property
    def model(self):
        try: return self.__model
        except AttributeError: pass

    @model.setter
    def model(self, model):
        try:
            self.__model
        except AttributeError: pass
        else:
            raise AttributeError
        self.__model = model

    @property
    def world_count(self):
        return len(self.__worlds)

    @property
    def constants_count(self):
        return len(self.__constants)

    @property
    def next_constant(self):
        # TODO: WIP
        return self.__nextconst

    @property
    def next_world(self) -> int:
        """
        Return a new world that does not appear on the branch.
        """
        return self.__nextworld

    def has(self, props: Mapping, ticked: bool = None) -> bool:
        """
        Check whether there is a node on the branch that matches the given properties,
        optionally filtered by ticked status.
        """
        return self.find(props, ticked = ticked) != None

    def has_any(self, props_list: Iterable[Mapping], ticked: bool = None) -> bool:
        """
        Check a list of property dictionaries against the ``has()`` method. Return ``True``
        when the first match is found.
        """
        for props in props_list:
            if self.has(props, ticked=ticked):
                return True
        return False

    def has_all(self, props_list: Iterable[Mapping], ticked: bool = None) -> bool:
        """
        Check a list of property dictionaries against the ``has()`` method. Return ``False``
        when the first non-match is found.
        """
        for props in props_list:
            if not self.has(props, ticked=ticked):
                return False
        return True

    def find(self, props: Mapping, ticked: bool = None) -> Node:
        """
        Find the first node on the branch that matches the given properties, optionally
        filtered by ticked status. Returns ``None`` if not found.
        """
        results = self.search_nodes(props, ticked = ticked, limit = 1)
        if results:
            return results[0]
        return None

    def find_all(self, props: Mapping, ticked: bool = None) -> list[Node]:
        """
        Find all the nodes on the branch that match the given properties, optionally
        filtered by ticked status. Returns a list.
        """
        return self.search_nodes(props, ticked = ticked)

    def search_nodes(self, props: Mapping, ticked: bool = None, limit: int = None) -> list[Node]:
        """
        Find all the nodes on the branch that match the given properties, optionally
        filtered by ticked status, up to the limit, if given. Returns a list.
        """
        results = []
        best_haystack = self.__select_index(props, ticked)
        if not best_haystack:
            return results
        for node in best_haystack:
            if limit != None and len(results) >= limit:
                break
            if ticked != None and self.is_ticked(node) != ticked:
                continue
            if node.has_props(props):
                results.append(node)
        return results

    def append(self, node: Mapping):
        """
        Append a node (Node object or dict of props). Returns self.
        """
        node = Node(node)
        self.__nodes.append(node)
        # self.__nodeset.add(node)
        s: Sentence = node.get('sentence')
        if s:
            cons = s.constants
            if cons:
                if self.__nextconst in cons:
                    # TODO: new_constant() is still a prettier result, since it
                    #       finds the mimimum available by searching for gaps.
                    self.__nextconst = max(cons).next()
                self.__constants.update(cons)
        if node.worlds:
            maxworld = max(node.worlds)
            if maxworld >= self.__nextworld:
                self.__nextworld = maxworld + 1
            self.__worlds.update(node.worlds)

        # Add to index *before* after_node_add event
        self.__add_to_index(node)
        self.emit(BranchEvent.AFTER_NODE_ADD, node, self)
        return self

    add = append

    def extend(self, nodes: Iterable[Mapping]):
        'Add multiple nodes. Returns self.'
        for node in nodes:
            self.append(node)
        return self

    def tick(self, *nodes: Node):
        'Tick a node for the branch.'
        for node in filterfalse(self.is_ticked, nodes):
            self.__ticked.add(node)
            node.ticked = True
            self.emit(BranchEvent.AFTER_NODE_TICK, node, self)

    def close(self):
        'Close the branch. Returns self.'
        if not self.closed:
            self.__closed = True
            self.append({'is_flag': True, 'flag': 'closure'})
            self.emit(BranchEvent.AFTER_BRANCH_CLOSE, self)
        return self

    def is_ticked(self, node: Node) -> bool:
        'Whether the node is ticked relative to the branch.'
        return node in self.__ticked

    def copy(self, parent: Branch = None, events: bool = False) -> Branch:
        """
        Return a copy of the branch. Event listeners are *not* copied.
        Parent is not copied, but can be explicitly set.
        """
        cls = type(self)
        b = cls.__new__(cls)
        b.__init_parent(parent)

        b.events = self.events.copy() if events else self.events.barecopy()
        
        b.__closed = self.__closed

        b.__nodes   = self.__nodes.copy()
        # b.__nodeset = self.__nodeset.copy()
        b.__ticked  = self.__ticked.copy()

        b.__worlds    = self.__worlds.copy()
        b.__nextworld = self.__nextworld
        b.__constants = self.__constants.copy()
        b.__nextconst = self.__nextconst
        b.__pidx = {
            prop : {
                key : self.__pidx[prop][key].copy()
                for key in self.__pidx[prop]
            }
            for prop in self.__pidx
        }
        try: b.__model = self.__model
        except AttributeError: pass

        return b

    # def constants(self):
    #     'Return the set of constants that appear on the branch.'
    #     # return self._views.constants(self.__constants)
    #     return self.__constants

    def new_constant(self):
        'Return a new constant that does not appear on the branch.'
        if not self.__constants:
            return Constant.first()
        maxidx = Constant.TYPE.maxi
        coordset = setf(c.coords for c in self.__constants)
        index = sub = 0
        while (index, sub) in coordset:
            index += 1
            if index > maxidx:
                index, sub = 0, sub + 1
        return Constant((index, sub))

    def __init_parent(self, parent: Branch | None):
        if hasattr(self, '_Branch__parent'):
            raise AttributeError
        if parent is not None:
            if parent is self:
                raise ValueError('A branch cannot be its own parent')
            if not isinstance(parent, Branch):
                raise TypeError(parent)
            self.__origin = parent.origin
        else:
            self.__origin = self
        self.__parent = parent

    def __add_to_index(self, node: Node):
        for prop in self.__pidx:
            val = None
            found = False
            if prop == 'w1Rw2':
                if node.has('world1', 'world2'):
                    val = (node['world1'], node['world2'])
                    found = True
            elif prop in node:
                val = node[prop]
                found = True
            if found:
                if val not in self.__pidx[prop]:
                    self.__pidx[prop][val] = set()
                self.__pidx[prop][val].add(node)

    def __select_index(self, props, ticked):
        best_index = None
        for prop in self.__pidx:
            val = None
            found = False
            if prop == 'w1Rw2':
                if 'world1' in props and 'world2' in props:
                    val = (props['world1'], props['world2'])
                    found = True
            elif prop in props:
                val = props[prop]
                found = True
            if found:
                if val not in self.__pidx[prop]:
                    return False
                index = self.__pidx[prop][val]
                if best_index == None or len(index) < len(best_index):
                    best_index = index
                # we could do no better
                if len(best_index) == 1:
                    break
        if not best_index:
            if ticked:
                best_index = self.__ticked
            else:
                best_index = self
        return best_index

    def __getitem__(self, key: SupportsIndex) -> Node:
        return self.__nodes[key]

    def __len__(self):
        return len(self.__nodes)

    def __iter__(self) -> Iterator[Node]:
        return iter(self.__nodes)

    __hash__ = operd(id)
    __eq__   = operd(opr.is_)
    __bool__ = preds.true

    id = property(operd(id)())

    def __contains__(self, node):
        return node in self.__nodes
        # return node in self.__nodeset

    def __repr__(self):
        from tools.misc import orepr
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

class Target(dmapattr[str, Any]):

    branch : Branch
    rule   : object
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

    def __setitem__(self, key: str, value, /, *, ok = _keyattr_ok):
        if ok(key):
            if key in self and self[key] != value:
                raise Emsg.ValueConflictFor(key, value, self[key])
        elif not preds.isattrstr(key):
            instcheck(key, str)
            raise Emsg.BadAttrName(key)
        super().__setitem__(key, value)

    __delitem__ = raisr(TypeError)
    __delattr__ = raisr(AttributeError)
    __bool__    = preds.true

    def __dir__(self):
        return list(self._names())

    def __repr__(self):
        from tools.misc import orepr
        return orepr(self, dict(ItemsIterator(self._names(), vget = self.get)))

    def _names(self, /, *, redcr = partial(cchain.reduce_filter, __slots__),
        pred = preds.notnone
    ):
        return redcr(self.get, pred)


del(EventEmitter, lazy, operd)