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
#
# ------------------
#
# pytableaux test utils
from __future__ import annotations

import operator as opr
from types import MappingProxyType as MapProxy
from typing import Sequence, TypeVar
from unittest import TestCase

from pytableaux.examples import arguments as examples
from pytableaux.lang import *
from pytableaux.logics import LogicType, registry
from pytableaux.proof import *
from pytableaux.tools import EMPTY_MAP, inflect

from .logics import knownargs

_RT = TypeVar('_RT', bound=Rule)

__all__ = (
    'BaseCase',
    'maketest',
    'tabiter')

class BaseCase(TestCase):

    logic: LogicType

    @property
    def Model(self) -> type[LogicType.Model]:
        return self.logic.Model

    @property
    def System(self) -> type[LogicType.System]:
        return self.logic.System

    def tab(self, arg:Argument|str|None=None, /, *, is_build=None, **kw) -> Tableau:
        kw.setdefault('is_build_models', True)
        if arg is not None:
            arg = knownargs.arguments.get(arg) or Argument(arg)
            if is_build is None:
                is_build = True
        tab = Tableau(self.logic, arg, **kw)
        if is_build:
            tab.build()
        return tab

    def valid_tab(self, arg:Argument|str, /, **kw):
        tab = self.tab(arg, **kw)
        self.assertTrue(tab.valid)
        return tab

    def invalid_tab(self, arg:Argument|str, /, *, skip_countermodel=False, **kw):
        tab = self.tab(arg, **kw)
        self.assertTrue(tab.invalid)
        if not skip_countermodel:
            for model in tab.models:
                self.assertTrue(model.is_countermodel_to(tab.argument))
        return tab

    def rule_test(self, rule: str|type[_RT]|_RT):
        rulecls = self.logic.Rules.get(rule)
        test = rulecls.test(logic=self.logic, noassert=True)
        self.assertFalse(test.failures, rulecls)
        return test

    def table_test(self, oper, exp: Sequence):
        table = self.Model().truth_table(oper)
        exp = {
            tuple(map(str, key)): value
            for key, value in zip(table.mapping, exp)}
        res = {
            tuple(map(str, key)): str(value)
            for key, value in table.mapping.items()}
        self.assertEqual(res, exp)
        return table

    def m(self, b: Branch = None):
        m = self.Model()
        if b:
            m.read_branch(b)
        return m

    @classmethod
    def p(cls, s):
        return next(cls.pp(s))

    @staticmethod
    def pp(*s):
        return map(Parser(), s)

    @classmethod
    def snode(self, s):
        return snode(self.p(s))

    @classmethod
    def sdnode(self, s, d):
        return sdnode(self.p(s), d)

    @classmethod
    def swnode(self, s, w=0):
        return swnode(self.p(s), w)

    def __init_subclass__(cls, autorules=False, autoargs=False, autotables=False, **kw):
        super().__init_subclass__(**kw)
        if getattr(cls, 'logic', None):
            cls.logic = registry(cls.logic)
        ns = MapProxy(cls.__dict__)
        gennames = *filter(lambda key: key.startswith('gentest'), ns),
        for name in gennames:
            for name, func in getattr(cls, name)():
                name = f'test_{inflect.slug(name)}_gen'
                assert name not in ns
                setattr(cls, name, func)
        if autorules:
            for rulecls in cls.logic.Rules.all():
                name = f'test_rule_{rulecls.name}_auto'
                setattr(cls, name, maketest('rule_test', rulecls))
            name = 'test_rules_check_groups_auto'
            def test(self: BaseCase):
                self.logic.Rules._check_groups()
            setattr(cls, name, test)
        if autoargs:
            kws = getattr(cls, 'autoargs_kws', EMPTY_MAP)
            it = zip(knownargs.get_known(cls.logic), ('invalid', 'valid'), strict=True)
            for known, category in it:
                for arg in known:
                    title = arg.title or arg.argstr()
                    kw = kws.get(title, EMPTY_MAP)
                    name = f'test_{category}_{inflect.slug(title)}_auto'
                    setattr(cls, name, maketest(f'{category}_tab', arg, **kw))
        if autotables:
            for oper, exp in getattr(cls, 'tables', {}).items():
                name = f'test_truth_table_{inflect.slug(oper)}_auto'
                setattr(cls, name, maketest('table_test', oper, exp))

def maketest(method, *args, **kw):
    caller = opr.methodcaller(method, *args, **kw)
    def test(self):
        caller(self)
    return test

def tabiter(*logics, build=True, grouparg=False, registry=registry, shuffle=False, **opts):
    if not len(logics):
        logics = tuple(registry.all())
    if grouparg:
        it = ((logic, arg) for arg in examples.values() for logic in logics)
    else:
        it = ((logic, arg) for logic in logics for arg in examples.values())
    if shuffle:
        import random
        it = list(it)
        random.shuffle(it)
    for logic, arg in it:
        tab = Tableau(logic, arg, **opts)
        if build:
            tab.build()
        yield tab
