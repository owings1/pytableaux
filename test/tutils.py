import examples
from inspect import isclass
from lexicals import Argument, Vocabulary
from parsers import notations as parser_notns, parse_argument, parse
from proof.tableaux import Tableau
from utils import get_logic

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

def using(**attrs):
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

def dynattrs(*names):
    def wrapper(cls):
        assert isclass(cls)
        if not hasattr(cls, '_dynattrs'):
            cls._dynattrs = set()
        cls._dynattrs.update(names)
        for attr in names:
            if hasattr(cls, attr):
                cls.dynamic(attr, getattr(cls, attr))
        return cls
    return wrapper

@dynattrs('logic')
class LogicTester(object):

    vocab = examples.vocabulary
    notn = 'polish'
    logic = 'CFOL'

    @classmethod
    def dynamic(cls, attr, val):
        if attr == 'logic':
            cls.logic = get_logic(val)

    def p(self, s, *args, **kw):
        for val in args:
            if isinstance(val, Vocabulary):
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
        return parse(s, **kw)

    def pp(self, *sargs, **kw):
        args = []
        sens = []
        for val in sargs:
            if isinstance(val, Vocabulary) or val in parser_notns:
                args.append(val)
            else:
                sens.append(val)
        return list(self.p(s, *args, **kw) for s in sens)

    def parg(self, conc, *prems, **kw):
        if 'notn' not in kw:
            kw['notn'] = self.notn
        premises = []
        for prem in prems:
            if isinstance(prem, (list, tuple)):
                premises.extend(prem)
            elif isinstance(prem, Vocabulary):
                if 'vocab' in kw:
                    raise KeyError('duplicate: vocab')
                kw['vocab'] = prem
            else:
                premises.append(prem)
        if 'vocab' not in kw:
            kw['vocab'] = self.vocab
        return parse_argument(conc, premises, **kw)

    def tab(self, *args, **kw):
        is_build = kw.pop('is_build') if 'is_build' in kw else None
        if 'is_build_models' not in kw:
            kw['is_build_models'] = True
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

    def acmm(self, *args, **kw):
        kw['is_build_models'] = True
        tab = self.invalid_tab(*args, **kw)
        arg, models = tab.argument, list(tab.models)
        assert bool(models)
        for m in models:
            assert m.is_countermodel_to(arg)
        return (arg, models)

    def cmm(self, *args, **kw):
        return self.acmm(*args, **kw)[1]

    def cm(self, *args, **kw):
        return self.acmm(*args, **kw)[1][0]

    def rule_tab(self, rule, bare = False, **kw):
        manual = False
        try:
            rule = self.tab().get_rule(rule)
        except ValueError:
            rule = self.tab().add_rule_group([rule]).get_rule(rule)
            manual = True
        cls = rule.__class__
        tab = self.tab(**kw)
        if bare:
            tab.clear_rules()
        if bare or manual:
            if rule.is_closure:
                tab.add_closure_rule(cls)
            else:
                tab.add_rule_group((cls,))
        rule = tab.get_rule(cls)
        return (rule, tab)

    def rule_eg(self, rule, step = True, **kw):
        rule, tab = self.rule_tab(rule, **kw)
        tab.branch().update(rule.example_nodes())
        assert tab.branch_count == 1
        assert tab.open_branch_count == 1
        if step:
            entry = tab.step()
            tab.finish()
            assert entry.rule == rule
            assert tab.current_step == 1
            if rule.is_closure:
                assert tab.open_branch_count == 0
        return (rule, tab)

    @property
    def Model(self):
        return self.logic.Model



