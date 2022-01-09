from __future__ import annotations
from callables import Caller, gets, preds #calls, 
from decorators import abstract, lazyget
from events import EventEmitter
import lexicals
from lexicals import Constant, Sentence, Operated, Quantified
from tools.abcs import Abc, AbcMeta
from tools.sets import EMPTY_SET, setf
from utils import drepr, orepr

from collections.abc import Callable, Iterable, ItemsView, \
    Iterator, KeysView, Mapping, Sequence, ValuesView
from itertools import islice
from keyword import iskeyword
from types import MappingProxyType
from typing import Any, ClassVar, NamedTuple, TypeVar
import enum
# from collections import defaultdict, deque
# from inspect import getmembers, isclass
# from typing import Annotated, Final, Union, final
# from enum import Enum, auto
# import typing
# from copy import copy
# from utils import RetType, T

import operator as opr

class BranchEvent(enum.Enum):
    AFTER_BRANCH_CLOSE = enum.auto()
    AFTER_NODE_ADD     = enum.auto()
    AFTER_NODE_TICK    = enum.auto()

class RuleEvent(enum.Enum):
    BEFORE_APPLY = enum.auto()
    AFTER_APPLY  = enum.auto()

class TabEvent(enum.Enum):
    AFTER_BRANCH_ADD    = enum.auto()
    AFTER_BRANCH_CLOSE  = enum.auto()
    AFTER_NODE_ADD      = enum.auto()
    AFTER_NODE_TICK     = enum.auto()
    AFTER_TRUNK_BUILD   = enum.auto()
    BEFORE_TRUNK_BUILD  = enum.auto()

class KEY(enum.Enum):
    FLAGS       = enum.auto()
    STEP_ADDED  = enum.auto()
    STEP_TICKED = enum.auto()
    STEP_CLOSED = enum.auto()
    INDEX       = enum.auto()
    PARENT      = enum.auto()
    NODES       = enum.auto()

class FLAG(enum.Flag):
    NONE   = 0
    TICKED = 1
    CLOSED = 2
    PREMATURE   = 4
    FINISHED    = 8
    TIMED_OUT   = 16
    TRUNK_BUILT = 32


class NodeMeta(AbcMeta):
    def __call__(cls, props = {}):
        if isinstance(props, cls):
            return props
        return super().__call__(props)

__all__ = 'Node', 'Branch', 'Target'

class Node(Mapping, metaclass = NodeMeta):
    'A tableau node.'

    __slots__ = 'props', 'step', 'ticked', '_is_access', '_is_modal', '_worlds'
    defaults = MappingProxyType({'world': None, 'designated': None})

    def __init__(self, props = {}):
        #: A dictionary of properties for the node.
        # p = dict(self.defaults)
        p = {}
        p.update(props)
        self.props = MappingProxyType(p)

    @property
    def id(self) -> int:
        return id(self)

    @property
    def is_closure(self) -> bool:
        return self.get('flag') == 'closure'

    @lazyget.prop
    def is_modal(self) -> bool:
        return self.has_any('world', 'world1', 'world2', 'worlds')

    @lazyget.prop
    def is_access(self) -> bool:
        return self.has('world1', 'world2')

    @lazyget.prop
    def worlds(self) -> setf[int]:
        """
        Return the set of worlds referenced in the node properties. This combines
        the properties `world`, `world1`, `world2`, and `worlds`.
        """
        return setf(filter(preds.instanceof[int],
            self.get('worlds', EMPTY_SET) |
            {self[k] for k in ('world', 'world1', 'world2') if self.has(k)}
        ))

    def has(self, *names: str) -> bool:
        """
        Whether the node has a non-``None`` property of all the given names.
        """
        for name in names:
            if self.get(name) is None:
                return False
        return True

    def has_any(self, *names: str) -> bool:
        """
        Whether the node has a non-``None`` property of any of the given names.
        """
        for name in names:
            if self.get(name) is not None:
                return True
        return False

    def has_props(self, props: Mapping) -> bool:
        """
        Whether the node properties match all those give in ``props``.
        """
        for prop in props:
            if prop not in self or props[prop] != self[prop]:
                return False
        return True

    def get(self, name, default = None):
        try:
            return self[name]
        except KeyError:
            return default

    def keys(self) -> KeysView:
        return self.props.keys()

    def items(self) -> ItemsView:
        return self.props.items()

    def values(self) -> ValuesView:
        return self.props.values()

    def __eq__(self, other):
        return self is other

    def __hash__(self):
        return hash(self.id)

    def __len__(self):
        return len(self.props)

    def __bool__(self):
        return True

    def __getitem__(self, key):
        try:
            return self.props[key]
        except KeyError:
            return self.defaults[key]

    def __contains__(self, key):
        return key in self.props

    def __iter__(self):
        return iter(self.props)

    def __copy__(self):
        return self.__class__(self.props)

    def __or__(self, other) -> Mapping:
        # self | other
        if isinstance(other, self.__class__):
            return self.props | other.props
        if isinstance(other, self.props.__class__):
            return self.props | other
        if isinstance(other, dict):
            return dict(self.props) | other
        return NotImplemented

    def __ror__(self, other) -> Mapping:
        # other | self
        if isinstance(other, self.__class__):
            return other.props | self.props
        if isinstance(other, self.props.__class__):
            return other | self.props
        if isinstance(other, dict):
            return other | dict(self.props)
        return NotImplemented

    def __repr__(self):
        return orepr(self,
            id = self.id,
            props = drepr({
                k: v for k,v in self.props.items() if v != None
            }, limit = 4, paren = False, j = ',')
        )

    def __setattr__(self, attr, val):
        if hasattr(self, attr) and getattr(self, attr) != val:
            raise AttributeError('Node.%s is readonly' % attr)
        super().__setattr__(attr, val)

    def __delattr__(self, attr):
        raise AttributeError('Node is readonly')

NodeType = Node|Mapping

class Access(NamedTuple):

    w1: int
    w2: int

    @property
    def world1(self) -> int:
        return self.w1

    @property
    def world2(self) -> int:
        return self.w2

    @classmethod
    def fornode(cls, node: NodeType) -> tuple[int, int]:
        return cls(node['world1'], node['world2'])

    def todict(self) -> dict[str, int]:
        return {'world1': self[0], 'world2': self[1]}

    def tonode(self) -> Node:
        return Node(Access.todict(self))

    def reverse(self) -> tuple[int, int]:
        return Access(self[1], self[0])

LHS = TypeVar('LHS')
RHS = TypeVar('RHS')

class Comparer(Callable[..., bool]):

    __slots__ = '__lhs', '__dict__'

    @property
    def lhs(self): return self.__lhs

    def __init__(self, lhs):
        self.__lhs = lhs

    def __repr__(self):
        me = self.__class__.__qualname__
        them = self._lhsrepr(self.lhs)
        return orepr(me, lhs = them)

    def _lhsrepr(self, lhs) -> str:
        try: return lhs.__class__.__qualname__
        except AttributeError: return lhs.__class__.__name__

class Filters:

    class Attr(Comparer):

        #: LHS attr -> RHS attr mapping.
        attrmap: dict[str, str] = {}

        #: Attribute getters
        lget: ClassVar[Callable[[LHS, str], Any]] = gets.attr(flag = Caller.SAFE)
        rget: ClassVar[Callable[[RHS, str], Any]] = gets.attr()
        #: Comparison
        fcmp: ClassVar[Callable[[Any, Any], bool]] = opr.eq

        def __init__(self, lhs: LHS, **attrmap):
            super().__init__(lhs)
            self.attrmap = self.attrmap | attrmap

        def __call__(self, rhs: RHS) -> bool:
            for lattr, rattr in self.attrmap.items():
                val = self.lget(self.lhs, lattr)
                if val is not None and val != self.rget(rhs, rattr):
                    return False
            return True

        def example(self) -> dict:
            {k:v for k,v in dict(
                (rattr, self.lget(self.lhs, lattr))
                for lattr, rattr in self.attrmap.items()
            ).items() if v is not None}
            props = {}
            for attr, rattr in self.attrmap.items():
                val = self.lget(self.lhs, attr)
                if val is not None:
                    props[rattr] = val
            return props

    class Sentence(Comparer):

        rget: Callable[[RHS], lexicals.Sentence] = gets.thru()

        @property
        def negated(self) -> bool:
            if self.__negated is not None:
                return self.__negated
            return getattr(self.lhs, 'negated', None)

        @negated.setter
        def negated(self, val):
            self.__negated = val

        @property
        def applies(self) -> bool:
            return self.__applies

        def get(self, rhs: RHS) -> lexicals.Sentence:
            s = self.rget(rhs)
            if s:
                if not self.negated: return s
                if s.is_negated: return s.operand

        def example(self) -> lexicals.Sentence:
            if not self.applies:
                return
            lhs = self.lhs
            if lhs.operator != None:
                s = Operated.first(lhs.operator)
            elif lhs.quantifier != None:
                s = Quantified.first(lhs.quantifier)
            if lhs.negated:
                s = s.negate()
            return s

        def __init__(self, lhs: LHS, negated = None):
            super().__init__(lhs)
            self.__negated = None
            self.__applies = any((lhs.operator, lhs.quantifier, lhs.predicate))
            if negated is not None:
                self.negated = negated

        def __call__(self, rhs: RHS) -> bool:
            if not self.applies: return True
            s = self.get(rhs)
            if not s: return False
            lhs = self.lhs
            if lhs.operator and lhs.operator != s.operator:
                return False
            if lhs.quantifier and lhs.quantifier != s.quantifier:
                return False
            if lhs.predicate:
                if not s.predicate or lhs.predicate != s.predicate:
                    return False
            return True

    class ItemValue(Comparer):

        lhs: Callable[[Any], bool]
        rget: opr.itemgetter(1)
        def __call__(self, rhs):
            return bool(self.lhs(self.rget(rhs)))

class NodeFilters(Filters):

    class Sentence(Filters.Sentence):

        rget: Callable[[Node], lexicals.Sentence] = gets.key('sentence', flag = Caller.SAFE)

        def example_node(self) -> dict:
            n = {}
            s = self.example()
            if s: n['sentence'] = s
            return n

    class Designation(Filters.Attr):

        attrmap = {'designation': 'designated'}
        rget: Callable[[Node], bool] = gets.key()

        def example_node(self) -> dict:
            return self.example()

    class Modal(Filters.Attr):

        attrmap = {'modal': 'is_modal', 'access': 'is_access'}

        def example_node(self) -> dict:
            n = {}
            attrs = self.example()
            if attrs.get('is_access'):
                n.update(Access(0, 1).todict())
            elif attrs.get('is_modal'):
                n['world'] = 0
            return n


class Branch(Sequence[Node], EventEmitter, Abc):
    'Represents a tableau branch.'

    def __init__(self, parent: Branch = None, /):

        self.__init_parent(parent)

        super().__init__(*BranchEvent)

        # Make sure properties are copied if needed in copy()

        self.__closed = False

        self.__nodes   : list[Node] = []
        self.__nodeset : set[Node] = set()
        self.__ticked  : set[Node] = set()

        self.__worlds    : set[int] = set()
        self.__nextworld : int = 0
        self.__constants : set[Constant] = set()
        self.__nextconst : Constant = Constant.first()
        self.__pidx      : dict[str, dict[Any, set[Node]]]= {
            'sentence'   : {},
            'designated' : {},
            'world'      : {},
            'world1'     : {},
            'world2'     : {},
            'w1Rw2'      : {},
        }

    @property
    def id(self) -> int:
        return id(self)

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

    def has(self, props: NodeType, ticked: bool = None) -> bool:
        """
        Check whether there is a node on the branch that matches the given properties,
        optionally filtered by ticked status.
        """
        return self.find(props, ticked = ticked) != None

    # def has_access(self, w1: int, w2: int) -> bool:
    #     """
    #     Check whether a tuple of the given worlds is on the branch.

    #     This is a performant way to check typical "access" nodes on the
    #     branch with `world1` and `world2` properties. For more advanced
    #     searches, use the ``has()`` method.
    #     """
    #     return (w1, w2) in self.__pidx['w1Rw2']

    def has_any(self, props_list: Iterable[NodeType], ticked: bool = None) -> bool:
        """
        Check a list of property dictionaries against the ``has()`` method. Return ``True``
        when the first match is found.
        """
        for props in props_list:
            if self.has(props, ticked=ticked):
                return True
        return False

    def has_all(self, props_list: Iterable[NodeType], ticked: bool = None) -> bool:
        """
        Check a list of property dictionaries against the ``has()`` method. Return ``False``
        when the first non-match is found.
        """
        for props in props_list:
            if not self.has(props, ticked=ticked):
                return False
        return True

    def find(self, props: NodeType, ticked: bool = None) -> Node:
        """
        Find the first node on the branch that matches the given properties, optionally
        filtered by ticked status. Returns ``None`` if not found.
        """
        results = self.search_nodes(props, ticked = ticked, limit = 1)
        if results:
            return results[0]
        return None

    def find_all(self, props: NodeType, ticked: bool = None) -> list[Node]:
        """
        Find all the nodes on the branch that match the given properties, optionally
        filtered by ticked status. Returns a list.
        """
        return self.search_nodes(props, ticked = ticked)

    def search_nodes(self, props: NodeType, ticked: bool = None, limit: int = None) -> list[Node]:
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

    def append(self, node: NodeType) -> Branch:
        """
        Append a node (Node object or dict of props). Returns self.
        """
        node = Node(node)
        self.__nodes.append(node)
        self.__nodeset.add(node)
        s: Sentence = node.get('sentence')
        if s:
            if s.constants:
                if self.__nextconst in s.constants:
                    # TODO: new_constant() is still a prettier result, since it
                    #       finds the mimimum available by searching for gaps.
                    self.__nextconst = max(s.constants).next()
                self.__constants.update(s.constants)
        if node.worlds:
            maxworld = max(node.worlds)
            if maxworld >= self.__nextworld:
                self.__nextworld = maxworld + 1
            self.__worlds.update(node.worlds)

        # Add to index *before* after_node_add callback
        self.__add_to_index(node)
        self.emit(BranchEvent.AFTER_NODE_ADD, node, self)
        return self

    add = append

    def extend(self, nodes: Iterable[NodeType]) -> Branch:
        'Add multiple nodes. Returns self.'
        for node in nodes:
            self.append(node)
        return self

    def tick(self, *nodes: Node):
        'Tick a node for the branch.'
        for node in nodes:
            if not self.is_ticked(node):
                self.__ticked.add(node)
                node.ticked = True
                self.emit(BranchEvent.AFTER_NODE_TICK, node, self)
        # return self

    def close(self) -> Branch:
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
        # branch = self.__class__(parent = parent)
        cls = self.__class__
        b = cls.__new__(cls)
        b.__init_parent(parent)

        b.events = self.events.copy() if events else self.events.barecopy()
        
        b.__closed = self.__closed

        b.__nodes   = self.__nodes.copy()
        b.__nodeset = self.__nodeset.copy()
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
        if hasattr(self, '_Branch__model'):
            b.__model = self.__model
        return b

    def constants(self) -> set[Constant]:
        'Return the set of constants that appear on the branch.'
        return self.__constants

    def new_constant(self) -> Constant:
        'Return a new constant that does not appear on the branch.'
        if not self.__constants:
            return Constant.first()
        maxidx = Constant.TYPE.maxi
        coordset = set(c.coords for c in self.__constants)
        index, sub = 0, 0
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

    def __eq__(self, other):
        return self is other

    def __hash__(self):
        return hash(self.id)

    def __getitem__(self, key) -> Node:
        return self.__nodes[key]

    def __len__(self):
        return len(self.__nodes)

    def __iter__(self) -> Iterator[Node]:
        return iter(self.__nodes)

    def __bool__(self):
        return True

    __copy__ = copy

    def __contains__(self, node: Node):
        return node in self.__nodeset

    def __repr__(self):
        return orepr(self, 
            id     = self.id,
            nodes  = len(self),
            leaf   = self.leaf.id if self.leaf else None,
            closed = self.closed,
        )

class Target(Mapping[str, Any], Abc):

    __reqd = {'branch'}
    __attrs = __reqd | {
        'rule', 'node', 'nodes', 'world', 'world1', 'world2',
        'sentence', 'designated', 'flag'
    }

    branch: Branch
    node: Node

    @classmethod
    def create(cls, obj, **context):
        """
        Always returns a Target object.
        :param obj: True, Target, dict.
        """
        if isinstance(obj, cls):
            obj.update(context)
            return obj
        return cls(obj, **context)

    @classmethod
    def list(cls, objs, **context) -> list:
        """
        Normalize to a list, possibly empty, of Target objects.
        
        If the parameter qualifies as a single target type, it is cast to a
        list before ``create()`` is called.
        
        Acceptable types for ``objs`` param:
            - a single falsy object, in which case an empty list is returned
            - a single target (dict, Target object, or True)
            - tuple, list, or iterator.
        """
        # Falsy
        if not objs:
            return []
        if isinstance(objs, (cls, dict, bool)):
            # Cast to list
            objs = [objs,]
        elif not (
            isinstance(objs, (tuple, list)) or
            callable(getattr(objs, '__next__', None))
        ):
            raise TypeError('Cannot create Target from %s object' % type(objs))
        return [cls.create(obj, **context) for obj in objs]

    @property
    def type(self) -> str:
        if 'nodes' in self.__data:
            return 'Nodes'
        if 'node' in self.__data:
            return 'Node'
        return 'Branch'

    def get(self, key, default = None):
        try:
            return self[key]
        except KeyError:
            return default

    def update(self, _obj = None, **kw):
        if _obj != None:
            for k in _obj:
                self[k] = _obj[k]
        for k in kw:
            self[k] = kw[k]

    def items(self) -> ItemsView[str, Any]:
        return self.__data.items()

    def keys(self) -> KeysView[str]:
        return self.__data.keys()

    def values(self) -> ValuesView:
        return self.__data.values()

    def copy(self):
        return self.__class__(self.__data)

    def __init__(self, obj, **context):
        self.__data = {}
        if isinstance(obj, self.__class__):
            raise TypeError(self.__class__)
        if not obj:
            raise TypeError('Cannot create a Target from a falsy object: %s' % type(obj))
        if not isinstance(obj, (bool, dict)):
            raise TypeError(('Cannot create a Target from a %s' % type(obj)))
        if obj != True:
            self.update(obj)
        self.update(context)
        for attr in self.__reqd:
            if attr not in self.__data:
                raise TypeError("Missing required keys: %s" % self.__reqd.difference(self.__data))

    def __copy__(self):
        return self.copy()

    def __len__(self):
        return len(self.__data)

    def __iter__(self) -> Iterator[str]:
        return iter(self.__data)

    def __getitem__(self, key: str):
        return self.__data[key]

    def __setitem__(self, key: str, val):
        if not isinstance(key, str):
            raise TypeError(key)
        if not key.isidentifier() or iskeyword(key):
            raise ValueError('Invalid target key: %s' % key)
        if self.__data.get(key, val) != val:
            raise ValueError("Value conflict %s: %s (was: %s)" % (key, val, self.__data[key]))
        self.__data[key] = val

    def __contains__(self, key: str):
        return key in self.__data

    def __getattr__(self, name):
        if name in self.__attrs:
            try:
                return self.__data[name]
            except:
                pass
        raise AttributeError(name)

    def __setattr__(self, name, val):
        if name in self.__attrs:
            self[name] = val
        elif not hasattr(self, name) or name in self.__dict__:
            self.__dict__[name] = val
        else:
            raise AttributeError(name)

    def __bool__(self):
        return True

    def __dir__(self):
        return [
            attr for attr in self.__attrs
            if self.__data.get(attr, None) != None
        ]

    def __repr__(self):
        bid = self.__data['branch'].id if 'branch' in self.__data else '?'
        items = (
            ('branch', bid),
            ('type', self.type), *islice((
                (attr, self[attr].__class__ if attr == 'rule' else self[attr])
                for attr in
                ('rule', 'sentence', 'designated', 'world', 'worlds')
                if attr in self
            ), 3)
        )
        return orepr(self, dict(items))

del(EventEmitter)