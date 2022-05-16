# -*- coding: utf-8 -*-
# pytableaux, a multi-logic proof generator.
# Copyright (C) 2014-2022 Doug Owings.
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
"""
pytableaux.proof
^^^^^^^^^^^^^^^^

"""
from __future__ import annotations

from typing import Any, NamedTuple, Sequence

from pytableaux import _ENV, __docformat__
from pytableaux.lang import Operator, Predicate, Quantifier
from pytableaux.tools import EMPTY_MAP, MapProxy, abstract, closure, abcs
from pytableaux.tools.hybrids import EMPTY_QSET, qsetf
from pytableaux.tools.mappings import ItemMapEnum, dmap
from pytableaux.tools.sets import EMPTY_SET, setf
from pytableaux.tools.timing import Counter, StopWatch
from pytableaux.tools.typing import LogicType



__all__ = (
    'adds',
    'anode',
    'Branch',
    'BranchEvent',
    'ClosingRule',
    'group',
    'HelperAttr',
    'Node',
    'Rule',
    'RuleAttr',
    'RuleEvent',
    'RuleHelper',
    'RuleMeta',
    'sdnode',
    'snode',
    'swnode',
    'TabEvent',
    'Tableau',
    'TableauxSystem',
    'TabWriter',
    'Target',
)

NOARG = object()

class HelperAttr(str, abcs.Ebc):
    'Special ``RuleHelper`` class attribute names.'

    InitRuleCls = 'configure_rule'

#******  Rule Enum

class RuleAttr(str, abcs.Ebc):
    'Special ``Rule`` class attribute names.'

    Helpers     = 'Helpers'
    "Rule helper classes."

    Timers      = 'Timers'
    "Rule timer names."

    DefaultOpts = '_defaults'
    "Rule default options."

    OptKeys     = '_optkeys'
    "Rule option keys."

    Name        = 'name'
    "Rule class name attribute."

    NodeFilters = 'NodeFilters'
    "For `FilterHelper`."

    IgnoreTicked = 'ignore_ticked'
    "For `FilterHelper`."

    ModalOperators = 'modal_operators'
    "For `MaxWorlds` helper."

    Modal = 'modal'
    "Modal flag."

    Legend = 'legend'
    "Rule legend"


class ProofAttr(str, abcs.Ebc):

    def __str__(self):
        return self.value

class NodeAttr(ProofAttr):

    designation = 'designated'
    closure = 'closure'
    flag    = 'flag'
    is_flag = 'is_flag'
    world   = 'world'


class PropMap(ItemMapEnum):

    NodeDefaults = {
        NodeAttr.designation: None,
        NodeAttr.world: None,
    }

    ClosureNode = {
        NodeAttr.closure: True,
        NodeAttr.flag: NodeAttr.closure,
        NodeAttr.is_flag: True
    },


#******  Branch Enum

class BranchEvent(abcs.Ebc):
    'Branch events.'
    AFTER_CLOSE = abcs.eauto()
    AFTER_ADD   = abcs.eauto()
    AFTER_TICK  = abcs.eauto()

#******  Helper Enum



class RuleEvent(abcs.Ebc):
    'Rule events.'

    BEFORE_APPLY = abcs.eauto()
    AFTER_APPLY  = abcs.eauto()

class RuleState(abcs.FlagEnum):
    'Rule state bit flags.'

    __slots__ = 'value', '_value_'

    NONE   = 0
    INIT   = 1
    LOCKED = 2

class RuleClassFlag(abcs.FlagEnum):
    "WIP: Rule class feature flags."

    __slots__ = 'value', '_value_'

    Modal = 4
    RankOptimSupported = 8


#******  Tableau Enum

class TabEvent(abcs.Ebc):
    'Tableau events.'

    AFTER_BRANCH_ADD    = abcs.eauto()
    AFTER_BRANCH_CLOSE  = abcs.eauto()
    AFTER_NODE_ADD      = abcs.eauto()
    AFTER_NODE_TICK     = abcs.eauto()
    AFTER_TRUNK_BUILD   = abcs.eauto()
    BEFORE_TRUNK_BUILD  = abcs.eauto()
    AFTER_FINISH        = abcs.eauto()

class TabStatKey(abcs.Ebc):
    'Tableau ``stat()`` keys.'

    FLAGS       = abcs.eauto()
    STEP_ADDED  = abcs.eauto()
    STEP_TICKED = abcs.eauto()
    STEP_CLOSED = abcs.eauto()
    INDEX       = abcs.eauto()
    PARENT      = abcs.eauto()
    NODES       = abcs.eauto()

class TabFlag(abcs.FlagEnum):
    'Tableau state bit flags.'

    __slots__ = 'value', '_value_'

    NONE   = 0
    TICKED = 1
    CLOSED = 2
    PREMATURE   = 4
    FINISHED    = 8
    TIMED_OUT   = 16
    TRUNK_BUILT = 32
    TIMING_INACCURATE = 64

#******  Auxilliary Classes
class StepEntry(NamedTuple):
    #: The rule instance.
    rule   : 'Rule'
    #: The target produced by the rule.
    target : 'Target'
    #: The duration counter.
    duration: Counter

    def __repr__(self):
        return f'<StepEntry:{id(self)}:{self.rule.name}:{self.target.type}>'

class Access(NamedTuple):

    world1: int
    world2: int

    @property
    def w1(self) -> int:
        return self.world1

    @property
    def w2(self) -> int:
        return self.world2

    @classmethod
    def fornode(cls, node):
        return cls._make(map(node.__getitem__, cls._fields))

    def reversed(self):
        return self._make(reversed(self))


class NodeStat(dict):

    __slots__ = EMPTY_SET

    _defaults = MapProxy({
        TabStatKey.FLAGS       : TabFlag.NONE,
        TabStatKey.STEP_ADDED  : TabFlag.NONE,
        TabStatKey.STEP_TICKED : None,
    })

    def __init__(self):
        super().__init__(self._defaults)

class BranchStat(dict):

    __slots__ = EMPTY_SET

    _defaults = MapProxy({
        TabStatKey.FLAGS       : TabFlag.NONE,
        TabStatKey.STEP_ADDED  : TabFlag.NONE,
        TabStatKey.STEP_CLOSED : TabFlag.NONE,
        TabStatKey.INDEX       : None,
        TabStatKey.PARENT      : None,
    })

    def __init__(self, mapping = None, /, **kw):
        super().__init__(self._defaults)
        self[TabStatKey.NODES] = {}
        if mapping is not None:
            self.update(mapping)
        if len(kw):
            self.update(kw)

    def node(self, node, /):
        'Get the stat info for the node, and create if missing.'
        # Avoid using defaultdict, since it may hide problems.
        try:
            return self[TabStatKey.NODES][node]
        except KeyError:
            return self[TabStatKey.NODES].setdefault(node, NodeStat())

    def view(self):
        return {k: self[k] for k in self._defaults}

class TabTimers(NamedTuple):
    'Tableau timers data class.'

    build  : StopWatch
    trunk  : StopWatch
    tree   : StopWatch
    models : StopWatch

    @staticmethod
    def create(it = (False,) * 4):
        return TabTimers._make(map(StopWatch, it))


class TableauxSystem(metaclass = abcs.AbcMeta):
    'Tableaux system base class.'

    @classmethod
    @abstract
    def build_trunk(cls, tableau, argument, /) -> None:
        """Build the trunk for an argument on the tableau.
        
        Args:
            tableau: The tableau instance.
            argument: The argument.
        """
        raise NotImplementedError

    @classmethod
    def branching_complexity(cls, node, /) -> int:
        """Compute how many new branches would be added if a rule were to be
        applied to the node.

        Args:
            node: The node instance.
        
        Returns:
            The number of new branches.
        """
        return 0

    @classmethod
    def add_rules(cls, logic: LogicType, rules: TabRuleGroups, /) -> None:
        """Populate rules/groups for a tableau.

        Args:
            logic: The logic.
            rules: The tableau's rules.
        """
        Rules = logic.TabRules
        rules.groups.create('closure').extend(Rules.closure_rules)
        for classes in Rules.rule_groups:
            rules.groups.create().extend(classes)


    @classmethod
    def initialize(cls, RulesClass:LogicType.TabRules, /):
        RulesClass.all_rules = RulesClass.closure_rules + tuple(
            r for g in RulesClass.rule_groups for r in g)
        return RulesClass

class RuleHelper(metaclass = abcs.AbcMeta):
    'Rule helper interface.'

    __slots__ = EMPTY_SET

    rule: Rule
    config: Any

    def __init__(self, rule: Rule, /):
        self.rule = rule
        self.config = rule.Helpers.get(type(self))

    @classmethod
    def configure_rule(cls, rulecls, config: Any, /):
        """``RuleHelper`` hook for initializing & verifiying a ``Rule`` class.
        
        Args:
            rulecls: The rule class using the helper class.
            config: Config from the rule class, if any.
        """
        pass

    @classmethod
    @closure
    def __subclasshook__():

        from inspect import Parameter as Param
        from inspect import Signature

        POSMASK = Param.POSITIONAL_ONLY | Param.POSITIONAL_OR_KEYWORD | Param.VAR_POSITIONAL

        def is_descriptor(obj, /, *, names = ('__get__', '__set__', '__delete__')) -> bool:
            return any(hasattr(obj, name) for name in names)

        def is_positional(param: Param) -> bool:
            return param.kind & POSMASK == param.kind

        def get_params(value, /) -> list[Param]:
            return list(Signature.from_callable(value).parameters.values())

        # ---------------------
        def insp_rule(subcls: type):
            yield abcs.check_mrodict(subcls.__mro__, name := 'rule')
            yield is_descriptor(getattr(subcls, name))

        def insp_init(subcls: type):
            yield callable(value := subcls.__init__)
            if len(params := get_params(value)) < 2:
                yield callable(value := subcls.__new__)
                yield len(params := get_params(value)) > 1
            yield is_positional(params[1])

        # def insp_configure_rule(subcls: type):
        #     yield abcs.check_mrodict(subcls.__mro__, name := HelperAttr.InitRuleCls)
        #     yield callable(value := getattr(subcls, name))
        #     yield len(params := get_params(value)) > 1
        #     yield is_positional(params[1])
        # ---------------------

        inspections = (
            insp_rule,
            insp_init,
            # insp_configure_rule,
        )

        def compute(subcls: type):
            for fn in inspections:
                for i, v in enumerate(fn(subcls)):
                    if v is not True:
                        return NotImplemented, (fn.__name__, i)
            return True, None

        cache: dict = {}

        def hook_cached(cls, subcls: type, /):
            if cls is not __class__:
                return NotImplemented
            try:
                return cache[subcls][0]
            except KeyError:
                return cache.setdefault(subcls, compute(subcls))[0]

        if _ENV.DEBUG:
            hook_cached.cache = cache

        return hook_cached


class RuleMeta(abcs.AbcMeta):
    """Rule meta class."""

    @classmethod
    def __prepare__(cls, clsname, bases, **kw):
        return dict(__slots__ = EMPTY_SET)

    def __new__(cls, clsname: str, bases: tuple[type, ...], ns: dict, /,
        modal: bool = NOARG, **kw):

        Class = super().__new__(cls, clsname, bases, ns, **kw)

        setattr(Class, RuleAttr.Name, clsname)

        if modal is not NOARG:
            setattr(Class, RuleAttr.Modal, modal)

    #         ancs = list(abcs.mroiter(subcls, supcls = cls))
    #         flagsmap = {anc: anc.FLAGS for anc in ancs}
    #         subcls.FLAGS = functools.reduce(opr.or_, flagsmap.values(), cls.FLAGS)

        defaults = abcs.merge_attr(Class, RuleAttr.DefaultOpts, mcls = cls,
            default = dmap(), transform = MapProxy,
        )

        setattr(Class, RuleAttr.OptKeys, setf(defaults))

        abcs.merge_attr(Class, RuleAttr.Timers, mcls = cls,
            default = EMPTY_QSET, transform = qsetf,
        )

        configs = {}

        for relcls in abcs.mroiter(Class, mcls = cls):
            v = getattr(relcls, RuleAttr.Helpers, EMPTY_MAP)
            if isinstance(v, Sequence):
                for helpercls in v:
                    configs.setdefault(helpercls, None)
            else:
                configs.update(v)

        setattr(Class, RuleAttr.Helpers, MapProxy(configs))
        for helpercls, config in configs.items():
            setup = getattr(helpercls, HelperAttr.InitRuleCls, None)
            if setup:
                configs[helpercls] = setup(Class, config)
                if modal is False and helpercls is helpers.FilterHelper:
                    if filters.ModalNode in (v := getattr(Class, RuleAttr.NodeFilters)):
                        v[filters.ModalNode] = NotImplemented
                        configs[helpercls] = setup(Class, config)

        setattr(Class, RuleAttr.Legend, _rule_legend(Class))
        return Class


def _rule_legend(rulecls):

    legend = {}

    if getattr(rulecls, 'negated', None):
        legend['negated'] = Operator.Negation

    if (oper := getattr(rulecls, 'operator', None)):
        legend['operator'] = Operator[oper]
    elif (quan := getattr(rulecls, 'quantifier', None)):
        legend['quantifier'] = Quantifier[quan]
    elif (pred := getattr(rulecls, 'predicate', None)):
        legend['predicate'] = Predicate(pred)

    if (des := getattr(rulecls, 'designation', None)) is not None:
        legend['designation'] = des

    try:
        if (issubclass(rulecls, ClosingRule)):
            legend['closure'] = True
    except NameError:
        pass

    return tuple(legend.items())

def group(*items):
    """Tuple builder.
    
    Args:
        *items: members.

    Returns:
        The tuple of arguments.
    """
    return items

def adds(*groups, **kw):
    """Target dict builder for `AdzHelper`.
    
    Args:
        *groups: node groups.
        **kw: dict keywords.

    Returns:
        A dict built from ``dict(adds = groups, **kw)``.
    """
    return dict(adds = groups, **kw)

def snode(s):
    'Make a sentence node dict.'
    return dict(sentence = s)

def sdnode(s, d):
    'Make a sentence/designated node dict.'
    return dict(sentence = s, designated = d)

# def swnode(s: Sentence, w: int|None):
def swnode(s, w):
    'Make a sentence/world node dict. Excludes world if None.'
    if w is None:
        return dict(sentence = s)
    return dict(sentence = s, world = w)

def anode(w1, w2):
    'Make an Access node dict.'
    return Access(w1, w2)._asdict()

from pytableaux.proof.common import Branch, Node, Target
from pytableaux.proof.tableaux import Tableau, Rule, TabRuleGroups
from pytableaux.proof.rules import ClosingRule
from pytableaux.proof.writers import TabWriter
from pytableaux.proof import filters, helpers