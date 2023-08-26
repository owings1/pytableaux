from __future__ import annotations

from types import MappingProxyType as MapProxy
from typing import Collection, Iterable, Mapping, NamedTuple, Sequence, TypeVar, Generic
from unittest import TestCase
import operator as opr

from pytableaux import examples
from pytableaux.lang import *
from pytableaux.logics import registry, LogicType
from pytableaux.models import BaseModel
from pytableaux.proof import *
from pytableaux.tools import inflect, qset

from .logics import knownargs

_T = TypeVar('_T')
_RT = TypeVar('_RT', bound=Rule)


def loopgen(c: Collection[_T], n: int = None):
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


class RuleTab(NamedTuple):
    rule: Rule
    tab: Tableau

class TabBranch(NamedTuple):
    tab: Tableau
    branch: Branch

class ArgModels(NamedTuple):
    arg: Argument
    models: list[BaseModel]


class BaseCase(TestCase):

    logic: LogicType
    preds = Predicates(Predicate.gen(3))
    notn = Notation.polish
    fix_ss = ('Kab', 'a', 'b', 'Na', 'NNb', 'NKNab')

    def __init_subclass__(cls, autorules=False, autoargs=False, autotables=False, **kw):
        if autorules:
            bare = bool(kw.pop('bare', None))
        super().__init_subclass__(**kw)
        if getattr(cls, 'logic', None):
            cls.logic = registry(cls.logic)
        ns = MapProxy(cls.__dict__)
        gennames = *filter(lambda key: key.startswith('gentest'), ns),
        for name in gennames:
            for name, func in getattr(cls, name)():
                name = inflect.slug('test_' + str(name).removeprefix('test_') + '_gen')
                assert name not in ns
                setattr(cls, name, func)
        if autorules:
            for rulecls in cls.logic.Rules.all():
                name = f'test_rule_{rulecls.name}_auto'
                assert not hasattr(cls, name)
                setattr(cls, name, cls.maketest('rule_eg', rulecls, bare=bare))
            def test_groups(self: BaseCase):
                cls.logic.Rules._check_groups()
            setattr(cls, 'test_rules_check_groups', test_groups)
        if autoargs:
            for category in ('valid', 'invalid'):
                known = qset()
                if getattr(cls, 'logic', None):
                    known.update(getattr(knownargs, f'{category}ities')[cls.logic.Meta.name])
                for arg in known:
                    if isinstance(arg, Argument):
                        title = arg.title or hash(arg)
                    else:
                        title = arg
                    name = f'test_{category}_{inflect.slug(title)}_auto'
                    assert not hasattr(cls, name)
                    setattr(cls, name, cls.maketest(f'{category}_tab', arg))
        if autotables:
            for oper, exp in getattr(cls, 'tables', {}).items():
                name = f'test_truth_table_{oper}_auto'
                assert not hasattr(cls, name)
                setattr(cls, name, cls.maketest('tttest', oper, exp))

    @staticmethod
    def maketest(method, *args, **kw):
        caller = opr.methodcaller(method, *args, **kw)
        def test(self):
            caller(self)
        return test

    def valid_tab(self, *args, **kw):
        tab = self.tab(*args, **kw)
        self.assertTrue(tab.valid)
        return tab

    def invalid_tab(self, *args, **kw):
        tab = self.tab(*args, **kw)
        self.assertTrue(tab.invalid)
        if tab.argument:
            for model in tab.models:
                self.assertTrue(model.is_countermodel_to(tab.argument))
        return tab

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
        return self.crparser(*args, **kw)(s)

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
        return parser.argument(conc, premises, title=kw.get('title'))

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
            elif isinstance(nn, Mapping):
                nn = [nn]
            b = tab[0] if len(tab) else tab.branch()
            b.extend(nn)
        if is_build:
            tab.build()
        self.t = tab
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

    def rule_tab(self, rule:str|type[_RT], bare = False, **kw) -> tuple[_T, Tableau]|RuleTab:
        'Return (rule, tab) pair.'
        manual = False
        t = self.tab()
        try:
            rule = t.rules.get(rule)
        except KeyError:
            if isinstance(rule, str):
                rule = getattr(t.logic.Rules, rule)
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

    def rule_eg(self, rule, step = True, **kw) -> RuleTab:
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
            self.assertEqual(rule.branching, len(tab) - 1)
        return rt

    def m(self, b: Branch = None):
        m = self.Model()
        if b:
            m.read_branch(b)
        return m

    def tttest(self, oper, exp: Mapping|Sequence):
        tbl = self.Model().truth_table(oper)
        if isinstance(exp, Mapping):
            exp = {tuple(key): value for key, value in exp.items()}
        else:
            exp = {tuple(map(str, key)): value for key, value in zip(tbl.mapping, exp)}
        res = {
            tuple(map(str, key)): str(value)
            for key, value in tbl.mapping.items()}
        self.assertEqual(res, exp)

    def snode(self, s):
        return snode(self.p(s))
    def sdnode(self, s, d):
        return sdnode(self.p(s), d)
    def swnode(self, s, w=0):
        return swnode(self.p(s), w)

    @property
    def Model(self) -> type[BaseModel]:
        return self.logic.Model
