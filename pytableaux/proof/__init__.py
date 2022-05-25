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
from collections import deque

from typing import TYPE_CHECKING, Any, Callable, Iterable, Mapping, Sequence

from pytableaux import _ENV, __docformat__
from pytableaux.proof.util import HelperAttr, RuleAttr
from pytableaux.tools import EMPTY_MAP, MapProxy, abstract, closure, abcs
from pytableaux.tools.hybrids import EMPTY_QSET, qsetf
from pytableaux.tools.mappings import dmap
from pytableaux.tools.sets import EMPTY_SET, setf
from pytableaux.tools.typing import LogicModule, NotImplType, LogicType, SysRulesT

if TYPE_CHECKING:
    from typing import overload

    from pytableaux.lang.collect import Argument
    from pytableaux.proof.common import Node
    from pytableaux.proof.tableaux import Rule, Tableau, TabRuleGroups

__all__ = (
    'Branch',
    'ClosingRule',
    'Node',
    'RuleHelper',
    'RuleMeta',
    'Tableau',
    'TableauxSystem',
    'TabWriter',
    'Target',
    'Rule'
)

NOARG = object()

class TableauxSystem(metaclass = abcs.AbcMeta):
    'Tableaux system base class.'

    @classmethod
    @abstract
    def build_trunk(cls, tableau: Tableau, argument: Argument, /) -> None:
        """Build the trunk for an argument on the tableau.
        
        Args:
            tableau: The tableau instance.
            argument: The argument.
        """
        raise NotImplementedError

    @classmethod
    def branching_complexity(cls, node: Node, /) -> int:
        """Compute how many new branches would be added if a rule were to be
        applied to the node.

        Args:
            node: The node instance.
        
        Returns:
            The number of new branches.
        """
        return 0

    @classmethod
    def add_rules(cls, logic: LogicModule, rules: TabRuleGroups, /) -> None:
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
    def initialize(cls, RulesClass: type[SysRulesT], /) -> type[SysRulesT]:
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
    def configure_rule(cls, rulecls: type[Rule], config: Any, /):
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

        def get_params(value: Callable, /) -> list[Param]:
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

        def insp_configure_rule(subcls: type):
            yield abcs.check_mrodict(subcls.__mro__, name := HelperAttr.InitRuleCls)
            yield callable(value := getattr(subcls, name))
            yield len(params := get_params(value)) > 1
            yield is_positional(params[1])
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

        cache: dict[type, tuple[bool|NotImplType, Any]] = {}

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
    def __prepare__(cls, clsname: str, bases: tuple[type, ...], **kw) -> dict[str, Any]:
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

        return Class


from pytableaux.proof.writers import TabWriter
from pytableaux.proof.common import Branch, Node, Target
from pytableaux.proof.tableaux import Tableau, Rule
from pytableaux.proof.rules import ClosingRule
from pytableaux.proof import filters, helpers