from utils import rcurry, lcurry, dictrepr, orepr, Decorators, isstr, EmptySet
from events import Events, EventEmitter
from lexicals import Constant, Operated, Quantified
from copy import copy
from itertools import islice
from types import MappingProxyType
from typing import Generator, Iterable, Union
from enum import Enum, Flag, IntFlag
lazyget = Decorators.lazyget
setonce = Decorators.setonce

dict_keys = type({}.keys())
dict_items = type({}.items())

class Getters(object):

    def __new__(cls, *items):
        return cls.chain(*items)

    @staticmethod
    def chain(*items):
        chain = [cls(*args) for cls, *args in items]
        last = chain.pop()
        class chained(object):
            def __call__(self, obj, *args):
                for func in chain:
                    obj = func(obj)
                return last(obj, *args)
        return chained()

    class Getter(object):
        curry = rcurry
        def __new__(cls, *args):
            inst = object.__new__(cls)
            if args:
                return cls.curry(inst, args)
            return inst

    class Attr(Getter):
        def __call__(self, obj, name):
            return getattr(obj, name)

    class AttrSafe(Getter):
        def __call__(self, obj, name):
            return getattr(obj, name, None)

    class Key(Getter):
        def __call__(self, obj, key):
            return obj[key]

    class KeySafe(Getter):
        def __call__(self, obj, key):
            try:
                return obj[key]
            except KeyError:
                pass

    class It(Getter):
        curry = lcurry
        def __call__(self, obj, _ = None):
            return obj

    attr = Attr()
    attrsafe = AttrSafe()
    key = Key()
    keysafe = KeySafe()
    it = It()

class Filters(object):

    class Filter(object):

        lhs = None

        def __call__(self, *args, **kw):
            raise NotImplemented()

        def __repr__(self):
            me = self.__class__.__qualname__
            them = self.lhs.__class__.__name__
            try:
                them = self.lhs.__class__
                them = self.lhs.__class__.__name__
                them = self.lhs.__class__.__qualname__
            except AttributeError:
                pass
            return '%s for %s' % (me, them)

    class Method(Filter):

        args = tuple()
        kw = {}

        get = Getters.attr
        example = None.__class__

        def __init__(self, meth, *args, **kw):
            self.meth = self.lhs = meth
            if args:
                self.args = args
            self.kw.update(kw)

        def __call__(self, rhs):
            func = self.get(rhs, self.meth)
            return bool(func(*self.args, **self.kw))

        def __repr__(self):
            return '%s for %s' % (self.__class__.__name__, self.meth.__name__)
    
    class Attr(Filter):

        attrs = tuple()

        lget = Getters.attrsafe
        rget = Getters.attr

        def __init__(self, lhs, **attrmap):
            self.lhs = lhs
            self.attrs = tuple(self.attrs + tuple(attrmap.items()))

        def __call__(self, rhs):
            for lattr, rattr in self.attrs:
                val = self.lget(self.lhs, lattr)
                if val != None and val != self.rget(rhs, rattr):
                    return False
            return True

        def example(self):
            props = {}
            for attr, rattr in self.attrs:
                val = self.lget(self.lhs, attr)
                if val != None:
                    props[rattr] = val
            return props

    class Sentence(Filter):

        rget = Getters.it

        @property
        def negated(self):
            if self.__negated != None:
                return self.__negated
            return Getters.attrsafe(self.lhs, 'negated')

        @negated.setter
        def negated(self, val):
            self.__negated = val

        @property
        def lhs(self):
            return self.__lhs

        @property
        def applies(self):
            return self.__applies

        def get(self, rhs):
            s = self.rget(rhs)
            if s:
                if not self.negated:
                    return s
                if s.is_negated:
                    return s.operand

        def example(self):
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

        def __init__(self, lhs, negated = None):
            self.__negated = None
            self.__lhs = lhs
            self.__applies = any((lhs.operator, lhs.quantifier, lhs.predicate))
            if negated != None:
                self.negated = negated

        def __call__(self, rhs):
            if not self.applies:
                return True
            s = self.get(rhs)
            if not s:
                return False
            lhs = self.lhs
            if lhs.operator and lhs.operator != s.operator:
                return False
            if lhs.quantifier and lhs.quantifier != s.quantifier:
                return False
            if lhs.predicate:
                if not s.predicate or lhs.predicate != s.predicate:
                    return False
            return True

    class Type(Filter):

        classinfo = object

        def __init__(self, classinfo):
            self.classinfo = classinfo

        def __call__(self, obj):
            return isinstance(obj, self.classinfo)

        def __repr__(self):
            me = self.__class__.__qualname__
            return '%s for classinfo %s' % (me, self.classinfo)

    Type.INT = Type(int)
    Node = None

class NodeFilters(Filters):

    class Sentence(Filters.Sentence):
        rget = Getters.KeySafe('sentence')
        def example_node(self):
            n = {}
            s = self.example()
            if s:
                n['sentence'] = s
            return n

    class Designation(Filters.Attr):
        attrs = (('designation', 'designated'),)
        rget = Getters.key
        def example_node(self):
            return self.example()

    class Modal(Filters.Attr):
        attrs = (('modal', 'is_modal'), ('access', 'is_access'))
        def example_node(self):
            n = {}
            attrs = self.example()
            if attrs.get('is_access'):
                n['world1'] = 0
                n['world2'] = 1
            elif attrs.get('is_modal'):
                n['world'] = 0
            return n

Filters.Node = NodeFilters

class NodeMeta(type):
    def __call__(cls, props = {}):
        if isinstance(props, cls):
            return props
        return super().__call__(props)

class Node(object, metaclass = NodeMeta):
    """
    A tableau node.
    """

    defaults = MappingProxyType({'world': None, 'designated': None})

    def __init__(self, props = {}):
        #: A dictionary of properties for the node.
        p = dict(self.defaults)
        p.update(props)
        self.props = MappingProxyType(p)

    @property
    def id(self) -> int:
        return id(self)

    @property
    def is_closure(self) -> bool:
        return self.get('flag') == 'closure'

    @property
    @lazyget
    def is_modal(self) -> bool:
        return self.has_any('world', 'world1', 'world2', 'worlds')

    @property
    @lazyget
    def is_access(self) -> bool:
        return self.has('world1', 'world2')

    @property
    @lazyget
    def worlds(self) -> frozenset[int]:
        """
        Return the set of worlds referenced in the node properties. This combines
        the properties `world`, `world1`, `world2`, and `worlds`.
        """
        return frozenset(filter(Filters.Type.INT,
            self.get('worlds', EmptySet) |
            {self[k] for k in ('world', 'world1', 'world2') if self.has(k)}
        ))

    def get(self, name, default = None):
        return self.props.get(name, default)

    def has(self, *names: str) -> bool:
        """
        Whether the node has a non-``None`` property of all the given names.
        """
        for name in names:
            if self.get(name) == None:
                return False
        return True

    def has_any(self, *names: str) -> bool:
        """
        Whether the node has a non-``None`` property of any of the given names.
        """
        for name in names:
            if self.get(name) != None:
                return True
        return False

    def has_props(self, props: dict) -> bool:
        """
        Whether the node properties match all those give in ``props`` (dict).
        """
        for prop in props:
            if prop not in self or not props[prop] == self[prop]:
                return False
        return True

    def keys(self) -> dict_keys:
        return self.props.keys()

    def items(self) -> dict_items:
        return self.props.items()

    def __eq__(self, other):
        return isinstance(other, self.__class__) and self.id == other.id

    def __ne__(self, other):
        return not (isinstance(other, self.__class__) and self.id == other.id)

    def __hash__(self):
        return hash(self.id)

    def __getitem__(self, key):
        return self.props[key]

    def __contains__(self, item):
        return item in self.props

    def __iter__(self):
        return iter(self.props)

    def __copy__(self):
        return self.__class__(self.props, parent = self.parent)

    def __or__(self, other):
        # self | other
        if isinstance(other, self.__class__):
            return self.props | other.props
        if isinstance(other, self.props.__class__):
            return self.props | other
        if isinstance(other, dict):
            return dict(self.props) | other
        raise TypeError(
            'Unsupported %s operator between %s and %s'
            % ('|', self.__class__, other.__class__)
        )

    def __ror__(self, other):
        # other | self
        if isinstance(other, self.__class__):
            return other.props | self.props
        if isinstance(other, self.props.__class__):
            return other | self.props
        if isinstance(other, dict):
            return other | dict(self.props)
        raise TypeError(
            'Unsupported %s operator between %s and %s'
            % ('|', other.__class__, self.__class__)
        )

    def __repr__(self):
        return orepr(self,
            id = self.id,
            # parent = self.parent.id if self.parent else None,
            props = dictrepr({
                k: v for k,v in self.props.items() if v != None
            }, limit = 4, paren = False, j = ',')
        )

NodeType = Union[Node, dict]

class Branch(EventEmitter):
    pass
class Branch(Branch):
    """
    Represents a tableau branch.
    """

    def __init__(self, parent: Branch = None):
        if parent != None:
            if parent == self:
                raise ValueError('A branch cannot be its own parent')
            if not isinstance(parent, Branch):
                raise TypeError('Expecting %s, got %s' % (Branch, type(parent)))
            self.__origin = parent.origin
        else:
            self.__origin = self
        self.__parent = parent

        super().__init__(
            Events.AFTER_BRANCH_CLOSE,
            Events.AFTER_NODE_ADD,
            Events.AFTER_NODE_TICK,
        )
        # Make sure properties are copied if needed in copy()
        
        
        self.__closed = False

        self.__nodes = []
        self.__nodeset = set()
        self.__ticked = set()

        self.__worlds = set()
        self.__nextworld = 0
        self.__constants = set()
        self.__nextconst = Constant.first()
        self.__pidx = {
            'sentence'   : {},
            'designated' : {},
            'world'      : {},
            'world1'     : {},
            'world2'     : {},
            'w1Rw2'      : {},
        }

        self.__model = None

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
        return self.__model

    @model.setter
    @setonce
    def model(self, model):
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

    def has(self, props: dict, ticked: bool = None) -> bool:
        """
        Check whether there is a node on the branch that matches the given properties,
        optionally filtered by ticked status.
        """
        return self.find(props, ticked = ticked) != None

    def has_access(self, w1: int, w2: int) -> bool:
        """
        Check whether a tuple of the given worlds is on the branch.

        This is a performant way to check typical "access" nodes on the
        branch with `world1` and `world2` properties. For more advanced
        searches, use the ``has()`` method.
        """
        return (w1, w2) in self.__pidx['w1Rw2']

    def has_any(self, props_list: Iterable[dict], ticked: bool = None) -> bool:
        """
        Check a list of property dictionaries against the ``has()`` method. Return ``True``
        when the first match is found.
        """
        for props in props_list:
            if self.has(props, ticked=ticked):
                return True
        return False

    def has_all(self, props_list: Iterable[dict], ticked: bool = None) -> bool:
        """
        Check a list of property dictionaries against the ``has()`` method. Return ``False``
        when the first non-match is found.
        """
        for props in props_list:
            if not self.has(props, ticked=ticked):
                return False
        return True

    def find(self, props: dict, ticked: bool = None) -> Node:
        """
        Find the first node on the branch that matches the given properties, optionally
        filtered by ticked status. Returns ``None`` if not found.
        """
        results = self.search_nodes(props, ticked = ticked, limit = 1)
        if results:
            return results[0]
        return None

    def find_all(self, props: dict, ticked: bool = None) -> list[Node]:
        """
        Find all the nodes on the branch that match the given properties, optionally
        filtered by ticked status. Returns a list.
        """
        return self.search_nodes(props, ticked = ticked)

    def search_nodes(self, props: dict, ticked = None, limit = None) -> list[Node]:
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
        s = node.get('sentence')
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
        self.emit(Events.AFTER_NODE_ADD, node, self)
        return self
    add = append

    def extend(self, nodes: Iterable[NodeType]) -> Branch:
        """
        Add multiple nodes. Returns self.
        """
        for node in nodes:
            self.append(node)
        return self

    def tick(self, *nodes: Node) -> Branch:
        """
        Tick a node for the branch. Returns self.
        """
        for node in nodes:
            if not self.is_ticked(node):
                self.__ticked.add(node)
                node.ticked = True
                self.emit(Events.AFTER_NODE_TICK, node, self)
        return self

    def close(self) -> Branch:
        """
        Close the branch. Returns self.
        """
        if not self.closed:
            self.__closed = True
            self.append({'is_flag': True, 'flag': 'closure'})
            self.emit(Events.AFTER_BRANCH_CLOSE, self)
        return self

    def is_ticked(self, node: Node) -> bool:
        """
        Whether the node is ticked relative to the branch.
        """
        return node in self.__ticked

    def copy(self, parent: Branch = None) -> Branch:
        """
        Return a copy of the branch. Event listeners are *not* copied.
        Parent is not copied, but can be explicitly set.
        """
        branch = self.__class__(parent = parent)
        branch.__nodes = list(self.__nodes)
        branch.__nodeset = set(self.__nodeset)
        branch.__ticked = set(self.__ticked)
        branch.__constants = set(self.__constants)
        branch.__nextconst = self.__nextconst
        branch.__worlds = set(self.__worlds)
        branch.__nextworld = self.__nextworld
        branch.__pidx = {
            prop : {
                key : set(self.__pidx[prop][key])
                for key in self.__pidx[prop]
            }
            for prop in self.__pidx
        }
        return branch

    def constants(self) -> set[Constant]:
        """
        Return the set of constants that appear on the branch.
        """
        return self.__constants

    def new_constant(self) -> Constant:
        """
        Return a new constant that does not appear on the branch.
        """
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

    def __add_to_index(self, node):
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
        return isinstance(other, self.__class__) and self.id == other.id

    def __ne__(self, other):
        return not (isinstance(other, self.__class__) and self.id == other.id)

    def __hash__(self):
        return hash(self.id)

    def __getitem__(self, key):
        return self.__nodes[key]

    def __len__(self):
        return len(self.__nodes)

    def __iter__(self):
        return iter(self.__nodes)

    def __copy__(self):
        return self.copy()

    def __contains__(self, node):
        return node in self.__nodeset

    def __repr__(self):
        return orepr(self, 
            id     = self.id,
            nodes  = len(self),
            leaf   = self.leaf.id if self.leaf else None,
            closed = self.closed,
        )

class Target(object):

    __reqd = {'branch'}
    __attrs = {'branch', 'rule', 'node', 'nodes', 'world', 'world1', 'world2', 'sentence', 'designated', 'flag'}

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
    def list(cls, objs, **context):
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

    def __getitem__(self, item):
        return self.__data[item]

    def __setitem__(self, key, val):
        if not isstr(key):
            raise TypeError('Only string subscript allowed, not %s : %s' % (type(key), str(key)))
        if self.__data.get(key, val) != val:
            raise ValueError("Value conflict with key '%s' (%s != %s)" % (key, val, self.__data[key]))
        self.__data[key] = val

    def __contains__(self, item):
        return item in self.__data

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

class StepEntry(object):

    def __init__(self, *entry):
        if len(entry) < 3:
            raise TypeError('Expecting more than {} arguments'.format(len(entry)))
        self.__entry = entry

    @property
    def rule(self):
        return self.__entry[0]

    @property
    def target(self):
        return self.__entry[1]

    @property
    def duration_ms(self):
        return self.__entry[2]

    @property
    def entry(self):
        return self.__entry

    def __len__(self):
        return min(2, len(self.__entry))
    def __iter__(self):
        return islice(self.__entry, 2)