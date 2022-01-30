from __future__ import annotations

__all__ = (
    'BaseSuite',
    'larg',
    'using',
    'skip',
)
from tools.abcs import abcm, F, TT, T, VT
from tools.decorators import overload
from tools.hybrids import qset
from tools.misc import drepr, get_logic
from lexicals import (
    Argument, Predicates, Sentence, LexWriter, Notation
)
from models import BaseModel
from parsers import create_parser, parse_argument, Parser
import examples
from proof.common import Branch, Node
from proof.rules import ClosureRule
from proof.tableaux import Tableau, Rule

from inspect import isclass, getmembers
from itertools import chain, filterfalse
import sys
from typing import (
    Callable,
    Collection,
    Iterable,
    Iterator,
    Mapping,
    NamedTuple,
    Sequence,
)

def _setattrs(obj, **attrs):
    if isclass(obj):
        cls = obj
    else:
        cls = type(obj)
    dyn = getattr(cls, '_dynattrs', set())
    for attr, val in attrs.items():
        if attr in dyn:
            cls.dynamic(attr, val)
        else:
            setattr(obj, attr, val)

def using(**attrs) -> Callable[[F], F]:
    def wrapper(func: F) -> F:
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


def dynattrs(*names) -> Callable[[TT], TT]:
    def wrapper(cls):
        assert isclass(cls)
        cls._dynattrs = getattr(cls, '_dynattrs', tuple()) + names
        for attr in names:
            if hasattr(cls, attr):
                cls.dynamic(attr, getattr(cls, attr))
        return cls
    return wrapper

def larg(*largs) -> Callable[[F], F]:
    def decor(what: F) -> F:
        if isclass(what): raise TypeError
        def operwrap(self, *args, **kw):
            what(self, *largs, *args, **kw)
        return operwrap
    return decor

def loopgen(c: Collection[T], n: int = None):
    if not len(c) and (n is None or n > 0):
        raise TypeError('empty collection')
    it = iter(c)
    i = 0
    while n is None or n > i:
        try:
            yield next(it)
        except StopIteration:
            it = iter(c)
            continue
        if n is not None:
            i += 1

SKIPPED = []

@overload
def skip(cls: TT) -> TT: ...

@overload
def skip(func: F) -> F: ...

def skip(what):
    def skipped(*_, **__):
        SKIPPED.append(what)
    if isclass(what):
        class Skipped:
            test_skipped = skipped
        return Skipped
    return skipped

def clsmbrsrecurse(cls) -> Iterator[type]:
    mine = list(
        m for n,m in getmembers(cls)
        if isclass(m) and n[0] != '_'
    )
    return chain(mine, chain.from_iterable(
        clsmbrsrecurse(c) for c in mine
    ))

def get_subclasses(supcls: type[T]) -> qset[type[T]]:
    'Get all (non-abstract) subclasses recusively.'
    classes = qset()
    todo = [supcls]
    while len(todo):
        for child in filterfalse(classes.__contains__, todo.pop().__subclasses__()):
            todo.append(child)
            if not abcm.isabstract(child):
                classes.append(child)
    return classes

class RuleTab(NamedTuple):
    rule: Rule
    tab: Tableau

class TabBranch(NamedTuple):
    tab: Tableau
    branch: Branch

class ArgModels(NamedTuple):
    arg: Argument
    models: list[BaseModel]

@dynattrs('logic')
class BaseSuite:

    vocab = examples.preds
    notn = Notation.polish
    logic = get_logic('CFOL')
    fix_ss = ('Kab', 'a', 'b', 'Na', 'NNb', 'NKNab')
    lw = LexWriter(Notation.standard)

    @classmethod
    def dynamic(cls, attr, val):
        if attr == 'logic':
            val = get_logic(val)
            cls.logic = val
            for member in clsmbrsrecurse(cls):
                member.logic = val

    def set_logic(self, logic):
        self.logic = get_logic(logic)

    def crparser(self, *args, **kw):
        for val in args:
            if isinstance(val, Predicates):
                key = 'vocab'
            elif val in Notation:
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

    def p(self, s, *args, **kw):
        return self.crparser(*args, **kw).parse(s)

    def pp(self, *sargs, **kw):
        args = []
        sens = []
        for val in sargs:
            if isinstance(val, Predicates) or val in Notation:
                args.append(val)
            else:
                sens.append(val)
        return list(map(self.crparser(*args, **kw), sens))

    def sgen(self, n, ss = None, **kw):
        yield from map(self.crparser(**kw), loopgen(ss or self.fix_ss, n))

    def ngen(self, n, **kw):
        yield from map(Node, ({'sentence': s} for s in self.sgen(n, **kw)))

    def parg(self, conc, *prems, **kw) -> Argument:
        if isinstance(conc, Argument):
            return conc
        try:
            return examples.argument(conc)
        except (KeyError, TypeError):
            pass
        kw.setdefault('notn', self.notn)
        premises = []
        for prem in prems:
            if isinstance(prem, Predicates):
                if 'vocab' in kw:
                    raise KeyError('duplicate: vocab')
                kw['vocab'] = prem
            elif isinstance(prem, Iterable) and not isinstance(prem, (str, Sentence)):
                premises.extend(prem)
            else:
                premises.append(prem)
        kw.setdefault('vocab', self.vocab)
        return parse_argument(conc, premises, **kw)

    def tab(self, *args, is_build = None, nn = None, ss = None, **kw) -> Tableau:
        kw.setdefault('is_build_models', True)
        val = args[0] if len(args) == 1 else None
        if val in examples.args:
            arg = examples.argument(val)
        elif isinstance(val, Argument):
            arg = val
        elif args:
            arg = self.parg(*args, **kw)
        else:
            arg = None
        if arg and is_build is None:
            is_build = True
        tab = Tableau(self.logic, arg, **kw)
        if nn:
            if isinstance(nn, int):
                nn = self.ngen(nn, ss = ss, **kw)
            b = tab[0] if len(tab) else tab.branch()
            b.extend(nn)
        if is_build:
            tab.build()
        self.t = tab
        return tab

    def valid_tab(self, *args, **kw):
        tab = self.tab(*args, **kw)
        assert tab.valid
        return tab

    def invalid_tab(self, *args, **kw):
        tab = self.tab(*args, **kw)
        assert tab.invalid
        return tab

    def tabb(self, nn = None, *args, **kw):
        tab = self.tab(*args, nn=nn, **kw)
        if not len(tab):
            tab.branch()
        return TabBranch(tab, tab[0])

    def acmm(self, *args, **kw) -> tuple[Argument, list[BaseModel]]:
        'Return argument, models.'
        kw['is_build_models'] = True
        tab = self.invalid_tab(*args, **kw)
        arg, models = tab.argument, list(tab.models)
        assert bool(models)
        for m in models:
            assert m.is_countermodel_to(arg)
        return ArgModels(arg, models)

    def cmm(self, *args, **kw):
        'Return list of models.'
        return self.acmm(*args, **kw)[1]

    def cm(self, *args, **kw):
        'Return one model.'
        return self.acmm(*args, **kw)[1][0]

    def rule_tab(self, rule:str|Rule|type[Rule], bare = False, **kw):
        'Return (rule, tab) pair.'
        manual = False
        t = self.tab()
        try:
            rule = t.rules.get(rule)
        except ValueError:
            if isinstance(rule, str):
                rule = getattr(t.logic.TabRules, rule)
            t.rules.append(rule)
            rule = t.rules.get(rule)
            manual = True
        cls = type(rule)
        tab = self.tab(**kw)
        if bare or manual:
            if bare:
                tab.rules.clear()
            tab.rules.append(cls)
        rule = tab.rules.get(cls)
        return RuleTab(rule, tab)

    def rule_eg(self, rule, step = True, **kw):
        rule, tab = rt = self.rule_tab(rule, **kw)
        tab.branch().extend(rule.example_nodes())
        assert len(tab) == 1
        assert len(tab.open) == 1
        if step:
            entry = tab.step()
            tab.finish()
            assert entry.rule == rule
            assert len(tab.history) == 1
            if isinstance(rule, ClosureRule):
                assert len(tab.open) == 0
        return rt

    def m(self, b: Branch = None):
        m = self.Model()
        if b:
            m.read_branch(b)
        return m

    @property
    def Model(self) -> type[BaseModel]:
        return self.logic.Model

drepr.lw = LexWriter._sys = BaseSuite.lw
