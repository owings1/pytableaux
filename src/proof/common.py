from utils import rcurry, lcurry, dictrepr, Decorators, isstr, EmptySet, ReadOnlyDict
from lexicals import Operated, Quantified
from itertools import islice
from typing import Generator
lazyget = Decorators.lazyget

class NodeMeta(type):
    pass
    def __call__(cls, props = {}, parent = None):
        if isinstance(props, cls):
            if parent == props.parent:
                return props
            if props == parent:
                raise TypeError('A node cannot be its own parent %s=%s', (props.id, parent.id))
            if parent != None:
                props = {} | props
        return super().__call__(props=props, parent=parent)

class Node(object, metaclass = NodeMeta):
    """
    A tableau node.
    """

    def __init__(self, props = {}, parent = None):
        #: A dictionary of properties for the node.
        self.props = ReadOnlyDict({
            'world'      : None,
            'designated' : None,
        } | props)
        # TODO: branch props, protect
        self.__parent = parent
        self.ticked = False
        self.step = None
        self.ticked_step = None

    @property
    def id(self):
        return id(self)

    @property
    def parent(self):
        return self.__parent

    @property
    def is_closure(self):
        return self.get('flag') == 'closure'

    @property
    @lazyget
    def is_modal(self):
        return self.has_any('world', 'world1', 'world2', 'worlds')

    @property
    @lazyget
    def worlds(self):
        """
        Return the set of worlds referenced in the node properties. This combines
        the properties `world`, `world1`, `world2`, and `worlds`.
        """
        return frozenset(
            self.get('worlds', EmptySet) |
            {self[k] for k in ('world', 'world1', 'world2') if self.has(k)}
        )

    def get(self, name, default = None):
        return self.props.get(name, default)

    def has(self, *names):
        """
        Whether the node has a non-``None`` property of all the given names.
        """
        for name in names:
            if self.get(name) == None:
                return False
        return True

    def has_any(self, *names):
        """
        Whether the node has a non-``None`` property of any of the given names.
        """
        for name in names:
            if self.get(name) != None:
                return True
        return False

    def has_props(self, props):
        """
        Whether the node properties match all those give in ``props`` (dict).
        """
        for prop in props:
            if prop not in self or not props[prop] == self[prop]:
                return False
        return True

    def keys(self):
        return self.props.keys()

    def items(self):
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
        if isinstance(other, self.__class__):
            other = other.props
        if isinstance(other, dict):
            return dict.__or__(self.props, other)
        raise TypeError(
            'Unsupported %s operator between %s and %s'
            % ('|', self.__class__, other.__class__)
        )

    def __ror__(self, other):
        if isinstance(other, self.__class__):
            other = other.props
        if isinstance(other, dict):
            return dict.__ror__(self.props, other)
        raise TypeError(
            'Unsupported %s operator between %s and %s' %
            ('|', other.__class__, self.__class__)
        )

    def __repr__(self):
        clsname = self.__class__.__name__
        return dictrepr({
            clsname  : self.id,
        } | {k: v for k, v in {
            'parent' : self.parent.id if self.parent else None,
            'ticked' : self.ticked,
            'step'   : self.step,
        }.items() if v != None
        } | {
            'props': dictrepr({
            k: str(self[k])[0:10] for k in
            islice((k for k in self), 5)
            })
        })


class Target(object):

    __reqd = {'branch'}
    __attrs = {'branch', 'rule', 'node', 'nodes', 'world', 'world1', 'world2', 'sentence', 'designated'}

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
        # if not obj:
        #     raise TypeError('Cannot create a target from a falsy object: %s' % type(obj))
        # if isinstance(obj, cls):
        #     obj.update(context)
        #     return obj
        # if obj == True:
        #     target = cls(context)
        # else:
        #     if isinstance(obj, cls):
        #         target = obj
        #         target.update(context)
        #     else:
        #         target = cls(obj, **context)
        # return target

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
            raise TypeError('Cannot create targets from %s object' % type(objs))
        return [cls.create(obj, **context) for obj in objs]

    def __init__(self, obj, **context):
        self.__data = {}
        if isinstance(obj, self.__class__):
            raise TypeError(self.__class__)
        if not obj:
            raise TypeError('Cannot create a target from a falsy object: %s' % type(obj))
        if not isinstance(obj, (bool, dict)):
            raise TypeError(('Cannot create a target from a %s' % type(obj)))
        if obj != True:
            self.update(obj)
        self.update(context)
        miss = self.__reqd.difference(self.__data)
        if miss:
            raise TypeError("missing %s" % miss)

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

    def __repr__(self):
        return (self.__class__.__name__, ('type', self.type)).__repr__()

    def __bool__(self):
        return True

    def update(self, obj):
        for k in obj:
            self[k] = obj[k]

    def get(self, key, default = None):
        try:
            return self[key]
        except KeyError:
            return default

    @property
    def type(self):
        if 'nodes' in self.__data:
            return 'Nodes'
        if 'node' in self.__data:
            return 'Node'
        return 'Branch'

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
                (attr, self[attr]) for attr in
                ('rule', 'sentence', 'designated', 'world', 'worlds')
                if attr in self
            ), 3)
        )
        istr = ','.join(['%s:%s' % (k, str(v)[0:20]) for k,v in items])
        return '%s[%s]' % (self.__class__.__name__, istr)
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
        attrs = (('modal', 'is_modal'),)
        def example_node(self):
            n = {}
            attrs = self.example()
            if attrs.get('is_modal'):
                n['world'] = 0
            return n

Filters.Node = NodeFilters