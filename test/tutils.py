import examples, lexicals, tools.misc as misc
from lexicals import Argument, Predicates, Sentence, LexWriter
from models import BaseModel
from parsers import notations as parser_notns, create_parser, parse_argument, parse, Parser
from proof.tableaux import Tableau, Branch, Node, Rule
from proof.rules import ClosureRule
from tools.misc import get_logic

from collections.abc import Callable, Iterable, Iterator
from inspect import isclass, getmembers
from itertools import chain

from enum import Enum
def _setattrs(obj, **attrs):
    if isclass(obj):
        cls = obj
    else:
        cls = obj.__class__
    dyn = getattr(cls, '_dynattrs', set())
    for attr, val in attrs.items():
        if attr in dyn:
            cls.dynamic(attr, val)
        else:
            setattr(obj, attr, val)

def using(**attrs) -> Callable:
    def wrapper(func):
        if isclass(func):
            _setattrs(func, **attrs)
            return func
        def wrapped(obj, *args, **kw):
            saved = {
                attr: getattr(obj, attr)
                for attr in attrs
                if hasattr(obj, attr)
            }
            err = None
            try:
                _setattrs(obj, **attrs)
                return func(obj, *args, **kw)
            except Exception as e:
                err = e
            for attr, val in saved.items():
                setattr(obj, attr, val)
            if err:
                raise err
        return wrapped
    return wrapper

def dynattrs(*names) -> Callable:
    def wrapper(cls):
        assert isclass(cls)
        cls._dynattrs = getattr(cls, '_dynattrs', tuple()) + names
        for attr in names:
            if hasattr(cls, attr):
                cls.dynamic(attr, getattr(cls, attr))
        return cls
    return wrapper

def larg(*largs) -> Callable:
    def decor(what):
        if isclass(what): raise TypeError()
        def operwrap(self, *args, **kw):
            what(self, *largs, *args, **kw)
        return operwrap
    return decor

def loopgen(n, col):
    i = 0
    for x in range(n):
        if i == len(col): i = 0
        yield col[i]
        i += 1

def skip(what) -> Callable:
    if isclass(what):
        class Skipped(object):
            pass
        return Skipped
    def skipped(*args, **kw):
        pass
    return skipped

def clsmbrsrecurse(cls) -> Iterator[type]:
    mine = list(
        m for n,m in getmembers(cls)
        if isclass(m) and n[0] != '_'
    )
    return chain(mine, chain.from_iterable(
        clsmbrsrecurse(c) for c in mine
    ))


class AbstractSuite(object):
    pass

@dynattrs('logic')
class BaseSuite(AbstractSuite):

    vocab = examples.preds
    notn = 'polish'
    logic = get_logic('CFOL')
    fix_ss = ('Kab', 'a', 'b', 'Na', 'NNb', 'NKNab')
    lw = LexWriter(notn='standard')

    @classmethod
    def dynamic(cls, attr, val):
        if attr == 'logic':
            val = get_logic(val)
            cls.logic = val
            for member in clsmbrsrecurse(cls):
                member.logic = val

    def set_logic(self, logic):
        self.logic = get_logic(logic)

    def crparser(self, *args, **kw) -> Parser:
        for val in args:
            if isinstance(val, Predicates):
                key = 'vocab'
            elif val in parser_notns:
                key = 'notn'
            else:
                raise ValueError('Unrecognized positional argument {}'.format(val))
            if key in kw:
                raise KeyError('Positional argument {} duplicates keyword {}'.format(val, key))
            kw[key] = val
        if 'vocab' not in kw:
            kw['vocab'] = self.vocab
        if 'notn' not in kw:
            kw['notn'] = self.notn
        return create_parser(**kw)

    def p(self, s, *args, **kw) -> Sentence:
        return self.crparser(*args, **kw).parse(s)

    def pp(self, *sargs, **kw) -> list[Sentence]:
        args = []
        sens = []
        for val in sargs:
            if isinstance(val, Predicates) or val in parser_notns:
                args.append(val)
            else:
                sens.append(val)
        p = self.crparser(*args, **kw)
        return list(p.parse(s) for s in sens)

    def sgen(self, n, ss = None, **kw):
        if ss == None: ss = self.fix_ss
        p = self.crparser(**kw)
        for s in loopgen(n, ss):
            yield p.parse(s)

    def _gennode(self, i, s, **kw):
        return {'sentence': s}

    def ngen(self, n, **kw):
        for i, s in enumerate(self.sgen(n, **kw)):
            yield Node(self._gennode(i, s, **kw))

    def parg(self, conc, *prems, **kw) -> Argument:
        if isinstance(conc, Argument):
            return conc
        try:
            return examples.argument(conc)
        except (KeyError, TypeError):
            pass
        if 'notn' not in kw:
            kw['notn'] = self.notn
        premises = []
        for prem in prems:
            if isinstance(prem, (list, tuple)):
                premises.extend(prem)
            elif isinstance(prem, Predicates):
                if 'vocab' in kw:
                    raise KeyError('duplicate: vocab')
                kw['vocab'] = prem
            else:
                premises.append(prem)
        if 'vocab' not in kw:
            kw['vocab'] = self.vocab
        return parse_argument(conc, premises, **kw)

    def tab(self, *args, **kw) -> Tableau:
        is_build = kw.pop('is_build', None)# if 'is_build' in kw else None
        if 'is_build_models' not in kw:
            kw['is_build_models'] = True
        nn = kw.pop('nn', None)# if 'nn' in kw else None
        val = args[0] if len(args) == 1 else None
        if val in examples.args:
            arg = examples.argument(val)
        elif isinstance(val, Argument):
            arg = val
        elif args:
            arg = self.parg(*args, **kw)
        else:
            arg = None
        if arg and is_build == None:
            is_build = True
        tab = Tableau(self.logic, arg, **kw)
        if nn:
            if isinstance(nn, int):
                nn = self.ngen(nn, **kw)
                kw.pop('ss', None)
            b = tab[0] if len(tab) else tab.branch()
            b.extend(nn)
        if is_build:
            tab.build()
        self.t = tab
        return tab

    def valid_tab(self, *args, **kw) -> Tableau:
        tab = self.tab(*args, **kw)
        assert tab.valid
        return tab

    def invalid_tab(self, *args, **kw) -> Tableau:
        tab = self.tab(*args, **kw)
        assert tab.invalid
        return tab

    def b(self, *nn) -> Branch:
        b = Branch()
        b.extend(nn)
        return b

    def tabb(self, *args, **kw) -> tuple[Tableau, Branch]:
        if args and isinstance(args[0], (dict, Node, list, tuple)):
            nn, *args = args
            if isinstance(nn, (dict, Node)):
                nn = (nn,)
        else:
            nn = tuple()
        b = self.b(*nn)
            # if isinstance(arg, dict):
            #     arg = (arg,)
            # try:
            #     b.extend(arg)
            # except TypeError:
            #     print (arg)
            #     print (args)
            #     raise
        tab = self.tab(*args, **kw)
        tab.add(b)
        return (tab, b)

    def acmm(self, *args, **kw) -> tuple[Argument, list[BaseModel]]:
        kw['is_build_models'] = True
        tab = self.invalid_tab(*args, **kw)
        arg, models = tab.argument, list(tab.models)
        assert bool(models)
        for m in models:
            assert m.is_countermodel_to(arg)
        return (arg, models)

    def cmm(self, *args, **kw) -> list[BaseModel]:
        return self.acmm(*args, **kw)[1]

    # return one model
    def cm(self, *args, **kw) -> BaseModel:
        return self.acmm(*args, **kw)[1][0]

    def rule_tab(self, rule, bare = False, **kw) -> tuple[Rule, Tableau]:
        manual = False
        t = self.tab()
        try:
            rule = t.rules.get(rule)
        except ValueError:
            if isinstance(rule, str):
                rule = getattr(t.logic.TabRules, rule)
            t.rules.add(rule)
            rule = t.rules.get(rule)
            manual = True
        cls = rule.__class__
        tab = self.tab(**kw)
        if bare or manual:
            if bare:
                tab.rules.clear()
            tab.rules.add(cls)
        rule = tab.rules.get(cls)
        return (rule, tab)

    def rule_eg(self, rule, step = True, **kw) -> tuple[Rule, Tableau]:
        rule, tab = self.rule_tab(rule, **kw)
        tab.branch().extend(rule.example_nodes())
        assert len(tab) == 1
        assert len(tab.open) == 1
        if step:
            entry = tab.step()
            tab.finish()
            assert entry.rule == rule
            assert tab.current_step == 1
            if isinstance(rule, ClosureRule):
                assert len(tab.open) == 0

        return (rule, tab)

    def m(self, b: Branch = None) -> BaseModel:
        m: BaseModel = self.Model()
        if b:
            m.read_branch(b)
        return m

    @property
    def Model(self) -> type[BaseModel]:
        return self.logic.Model

misc.drepr.lw = LexWriter._sys = BaseSuite.lw
# if utils._testlw is None:
#     lexicals._syslw = utils._testlw = BaseSuite.lw
    
def tp(tab):
    print(
        '\n\n'.join([
            '\n'.join(['b%d' % i] + ['  %s' % n for n in b])
            for i, b in enumerate(tab)
        ])
    )
def tabtup(tab):
    return tuple(tuple(dict(n) for n in b) for b in tab)

def tabeq(t1, t2):
    return tabtup(t1) == tabtup(t2)

def titer(tab):
    return  chain.from_iterable(iter(b) for b in tab)
    nn = titer(tab)

    # print the sentences
    ss = filter(bool, (n.get('sentence') for n in nn))
    pr = (lw.write(s) for s in ss)
    print('\n'.join(list(pr)))
