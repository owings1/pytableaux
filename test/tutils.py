from __future__ import annotations

from inspect import getmembers, isclass
from itertools import chain, filterfalse
from typing import (TYPE_CHECKING, Callable, Collection, Iterable, Iterator,
                    NamedTuple)

from pytableaux import examples
from pytableaux.lang import Notation
from pytableaux.lang.collect import *
from pytableaux.lang.lex import Predicate, Sentence
from pytableaux.lang.parsing import Parser
from pytableaux.lang.writing import LexWriter
from pytableaux.logics import registry
from pytableaux.models import BaseModel
from pytableaux.proof.common import Branch, Node
from pytableaux.proof.rules import ClosingRule, Rule
from pytableaux.proof.tableaux import Tableau
from pytableaux.tools import abcs
from pytableaux.tools.hybrids import qset
from pytableaux.tools.typing import TT, F, RuleT, T

if TYPE_CHECKING:
    from typing import overload
__all__ = (
    'BaseSuite',
    'larg',
    'using',
    'skip',
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

if TYPE_CHECKING:
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
            if not abcs.isabstract(child):
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

    preds = Predicates(Predicate.gen(3))
    notn = Notation.polish
    logic = registry('CFOL')
    fix_ss = ('Kab', 'a', 'b', 'Na', 'NNb', 'NKNab')
    lw = LexWriter(Notation.standard)

    @classmethod
    def dynamic(cls, attr, val):
        if attr == 'logic':
            val = registry(val)
            cls.logic = val
            for member in clsmbrsrecurse(cls):
                member.logic = val

    def set_logic(self, logic):
        self.logic = registry(logic)

    def crparser(self, *args, **kw):
        for val in args:
            if isinstance(val, Predicates):
                key = 'preds'
            elif isinstance(val, (str, Notation)) and val in Notation:
                key = 'notn'
            else:
                raise ValueError(f"Unrecognized positional argument '{val}'")
            if key in kw:
                raise TypeError(f"Positional argument '{val}' duplicates keyword '{key}'")
            kw[key] = val
        kw.setdefault('preds', self.preds)
        kw.setdefault('notn', self.notn)
        return Parser(kw['notn'], kw['preds'])

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
        premises = []
        for val in prems:
            key = None
            if isinstance(val, Predicates):
                key = 'preds'
            elif isinstance(val, (str, Notation)) and val in Notation:
                key = 'notn'
            elif isinstance(val, Iterable) and not isinstance(val, (str, Sentence)):
                premises.extend(val)
            else:
                premises.append(val)
            if key is not None:
                if key in kw:
                    raise TypeError(f"Positional argument '{val}' duplicates keyword '{key}'")
                kw[key] = val
        kw.setdefault('preds', self.preds)
        kw.setdefault('notn', self.notn)
        parser = Parser(kw['notn'], kw['preds'])
        return parser.argument(conc, premises)

    def tab(self, *args, is_build = None, nn = None, ss = None, **kw) -> Tableau:
        kw.setdefault('is_build_models', True)
        val = args[0] if len(args) == 1 else None
        arg = None
        if val is not None:
            try:
                arg = examples.argument(val)
            except KeyError:
                pass

        if arg is None:
            if isinstance(val, Argument):
                arg = val
            elif len(args):
                arg = self.parg(*args, **kw)

        if arg is not None and is_build is None:
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

    def rule_tab(self, rule:str|type[RuleT], bare = False, **kw) -> tuple[RuleT, Tableau]|RuleTab:
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
            if isinstance(rule, ClosingRule):
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

