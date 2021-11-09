from utils import rcurry, lcurry, dictrepr, isstr
from lexicals import Operated, Quantified

class Target(object):

    __reqd = {'branch'}
    __attrs = {'branch', 'rule', 'node', 'nodes', 'world', 'world1', 'world2', 'sentence', 'designated'}

    @classmethod
    def create(cls, obj, **data):
        print(data)
        if obj == True:
            target = cls(data)
        else:
            if isinstance(obj, cls):
                target = obj
                target.update(data)
            else:
                target = cls(obj, **data)
        return target

    @classmethod
    def all(cls, objs, **data):
        if isinstance(objs, (cls, dict)):
            objs = (objs,)
        objs = list(objs)
        return [cls.create(obj, **data) for obj in objs]

    def __init__(self, obj, **data):
        if isinstance(obj, self.__class__):
            raise TypeError(self.__class__)
        self.__data = {}
        if obj != True:
            self.update(obj)
        self.update(data)
        miss = self.__reqd.difference(self.__data)
        if miss:
            raise TypeError("missing %s" % miss)

    def __getitem__(self, item):
        return self.__data[item]

    def __setitem__(self, key, val):
        if self.__data.get(key, val) != val:
            raise KeyError("conflict '%s'" % key)
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

    def update(self, obj):
        for k in obj:
            if isstr(k):
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
            if attr in self and self[attr] != None
        ]

    def __repr__(self):
        return '<%s: %s>' % (self.__class__.__name__, dictrepr({
            attr: str(self[attr])[0:20]
            for attr in self.__attrs
            if attr in self and self[attr] != None
        }))

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