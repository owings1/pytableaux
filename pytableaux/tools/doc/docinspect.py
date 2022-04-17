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
#
# ------------------
#
# pytableaux - documentation inspection utilities
from __future__ import annotations

__all__ = (
    'get_logic_names',
    'is_concrete_build_trunk',
    'is_concrete_rule',
    'is_transparent_rule',
)

from pytableaux.proof.tableaux import ClosingRule, Rule, TableauxSystem as TabSys
from pytableaux.logics import getlogic

from inspect import getsource
import re
import os
from typing import Any

def get_logic_names(logic_docdir: str = None, suffix: str = '.rst', /) -> set[str]:
    'Get all logic names with a .rst document in the doc dir.'
    if logic_docdir is None:
        logic_docdir = os.path.abspath(
            os.path.join(os.path.dirname(__file__), '../../../doc/logics')
        )
    return set(
        os.path.basename(file).removesuffix(suffix).upper()
        for file in os.listdir(logic_docdir)
        if file.endswith(suffix)
    )

def is_concrete_rule(obj: Any, /) -> bool:
    return _is_rulecls(obj) and obj not in (Rule, ClosingRule)

def is_concrete_build_trunk(obj: Any, /,):
    return TabSys.build_trunk in _methmro(obj) and obj not in {TabSys.build_trunk}
    # return obj is not TabSys.build_trunk and TabSys.build_trunk in _methmro(obj)

def is_transparent_rule(obj: Any) -> bool:
    """Whether a rule class:
        - is included in TabRules groups for the module it belongs to
        - inherits from a rule class that belongs to another logic module
        - the parent class is in the other logic's rule goups
        - there is no implementation besides pass
        - there is no docblock
    """
    return (
        _is_rulecls(obj) and
        _is_nodoc(obj) and
        _is_nocode(obj) and
        _rule_is_self_grouped(obj) and
        _rule_is_parent_grouped(obj)
    )

def _is_rulecls(obj: Any) -> bool:
    'Wether obj is a rule class.'
    return isinstance(obj, type) and issubclass(obj, Rule)

def _is_nodoc(obj: Any) -> bool:
    return not bool(getattr(obj, '__doc__', None))

def _is_nocode(obj: Any) -> bool:
    'Try to determine if obj has no "effective" code.'
    isblock = False
    isfirst = True
    pat = rf'^(class|def) {obj.__name__}(\([a-zA-Z0-9_.]+\))?:$'
    try:
        it = filter(len, map(str.strip, getsource(obj).split('\n')))
    except:
        return False
    for line in it:
        if isfirst:
            isfirst = False
            m = re.findall(pat, line)
            if not m:
                return False
            continue
        if line.startswith('#'):
            continue
        if line == 'pass':
            continue
        if line.startswith('"""'):
            # not perfect, but more likely to produce false negatives
            # than false positives
            isblock = not isblock
            continue
        if isblock:
            continue
        return False
    return True

def _rule_is_grouped(rule: type[Rule], logic: Any) -> bool:
    'Whether the rule class is grouped in the TabRules of the given logic.'
    if not _is_rulecls(rule):
        return False
    try:
        logic = getlogic(logic)
    except:
        return False
    tabrules = logic.TabRules
    if rule in tabrules.closure_rules:
        return True
    for grp in tabrules.rule_groups:
        if rule in grp:
            return True
    return False

def _rule_is_self_grouped(rule: type[Rule]) -> bool:
    'Whether the Rule class is grouped in the TabRules of its own logic.'
    return _rule_is_grouped(rule, rule)

def _rule_is_parent_grouped(rule: type[Rule]) -> bool:
    "Whether the Rule class's parent is grouped in its own logic."
    if not isinstance(rule, type):
        return False
    return _rule_is_self_grouped(rule.mro()[1])

def _methmro(meth: Any) -> list[str]:
    """Get the methods of the same name of the mro (safe) of the class the
    method is bound to."""
    try:
        it = (getattr(c, meth.__name__, None) for c in meth.__self__.__mro__)
    except:
        return []
    return list(filter(None, it))