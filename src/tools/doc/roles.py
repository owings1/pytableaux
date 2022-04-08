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
# pytableaux - tools.doc.roles module
from __future__ import annotations
from typing import Any

__all__ = (
    'metadress',
    'lexdress',
    'refplus',
)

from lexicals import LexType, LexWriter, Parser, Predicate, Predicates
from tools import F

from docutils import nodes
from docutils.parsers.rst import roles as _docroles
import functools
import re
import sphinx.roles
from sphinx.util import logging
from sphinx.util.docutils import SphinxRole

logger = logging.getLogger(__name__)

def rolerun(func: F) -> F:
    'Decorator for role run method.'
    @functools.wraps(func)
    def run(self):
        ret = func(self)
        if isinstance(ret, nodes.Node):
            # Allow a single node.
            return [ret], []
        if not isinstance(ret, tuple):
            # Allow just the list of nodes.
            return ret, []
        return ret
    return run

class refplus(sphinx.roles.XRefRole):

    refdomain = 'std'
    reftype = 'ref'
    _classes = 'xref', refdomain, f'{refdomain}-{reftype}'

    innernodeclass = nodes.inline
    fix_parens = False
    lowercase = True #False
    warn_dangling = True # False

    def __init__(self, **_) -> None:
        pass

    @rolerun
    def run(self):
        self.classes = list(self._classes)
        if self.disabled:
            return self.create_non_xref_node()
        else:
            return self.create_xref_node()

class lexdress(SphinxRole):

    #: The input notation.
    pnotn = 'standard'
    #: The output notation.
    wnotn = 'standard'
    #: The parser predicates store.
    preds = Predicates(Predicate.gen(3))

    parser: Parser
    lw: LexWriter

    def __init__(self, *, wnotn = None, pnotn = None, preds = None):
        if wnotn is not None:
            self.wnotn = wnotn
        if pnotn is not None:
            self.pnotn = pnotn
        if preds is not None:
            self.preds = preds

        self.parser = Parser(self.pnotn, self.preds)
        self.lw = LexWriter(self.wnotn, 'unicode')

    _ctypes_valued = {
        LexType.Operator, LexType.Quantifier, Predicate.System
    }
    _ctypes_nosent = _ctypes_valued | {
        LexType.Constant, LexType.Variable, LexType.Predicate,
    }
    _re_nosent = re.compile(r'^(.)([0-9]*)$')

    @rolerun
    def run(self):

        text = self.text

        classes = ['lexitem']

        item = None
        match = self._re_nosent.match(text)

        if match:
            char, sub = match.groups()
            table = self.parser.table
            ctype = table.type(char)
            if ctype in self._ctypes_nosent:
                # Non-sentence items.
                sub = int(sub) if len(sub) else 0
                if ctype in self._ctypes_valued:
                    item = table.value(char)
                elif ctype is LexType.Predicate:
                    preds = self.parser.preds
                    item = preds.get((table.value(char), sub))
                else:
                    item = ctype.cls(table.value(char), sub)

        if item is None:
            # Parse as sentence.
            item = self.parser(text)

        classes.append(item.TYPE.name.lower())

        rend = self.lw(item)

        return nodes.inline(text = rend, classes = classes)


class metadress(SphinxRole):

    prefixes = {
        'L': 'logic_name',
        'V': 'truth_value',
        '!': 'rewrite',
    }
    modes = dict(
        logic_name = dict(
            match = {
                r'^(?:(?P<main>B|G|K|L|Ł|P|RM)(?P<down>3))$' : ('subber',),
                r'^(?:(?P<main>B)(?P<up>3)(?P<down>E))$'  : ('subsup',),
                r'^(?:(?P<main>K)(?P<up>3)(?P<down>WQ?))$': ('subsup',),
            },
            nodecls = nodes.inline,
            nodecls_map = dict(
                main= nodes.inline,
                up  = nodes.superscript,
                down= nodes.subscript
            ),
        ),
        truth_value = dict(
            nodecls = nodes.strong,
        ),
        # Regex rewrite.
        rewrite = {
            r'^(?:([a-zA-Z])-)?ntuple$': dict(
                rep = lambda m, a = 'a': (
                    f'\\langle {m[1] or a}_0'
                    ', ... ,'
                    f'{m[1] or a}_n\\rangle'
                ),
                classes = ('tuple', 'ntuple'),
                nodecls = nodes.math,
            ),
            r'^(w)([0-9]+)$': dict(
                rep = r'\1_\2',
                classes = ('modal', 'world'),
                nodecls = nodes.math,
            ),
        },
    )
    generic = dict(
        # Math symbol replace.
        math_symbols = {
            r'<': re.escape('\\langle '),
            r'>': re.escape('\\rangle'),
        }
    )
    patterns = dict(
        prefixed = r'(?P<raw>(?P<prefix>[%s]){(?P<value>.*?)})' % (
            re.escape(''.join(prefixes.keys()))
        ),
    )
    patterns.update(
        prefixed_role = '^%s$' % patterns['prefixed']
    )

    def __init__(self, **_):
        pass

    @rolerun
    def run(self):
        text = self.text
        classes = self.classes = ['metawrite']

        match = re.match(self.patterns['prefixed_role'], text)

        if not match:
            return self.unhinted()

        matchd = match.groupdict()
        mode: str = self.prefixes[matchd['prefix']]
        value: str = matchd['value']
        moded: dict = self.modes[mode]

        classes.append(mode)

        if mode == 'rewrite':
            for pat, info in moded.items():
                rend, num = re.subn(pat, info['rep'], value)
                if num:
                    break
            else:
                logger.error(f'No {mode} match for {repr(value)}')
            classes.extend(info['classes'])
            nodecls = info['nodecls']
            return nodecls(text = rend, classes = classes)

        if mode == 'truth_value':
            rend = value
            nodecls = moded['nodecls']
            return nodecls(text = rend, classes = classes)

        if mode == 'logic_name':

            for pat, addcls in moded['match'].items():
                m = re.match(pat, value)
                if not m:
                    continue
                md = m.groupdict()
                classes.extend(addcls)
                nodecls_map: dict = moded['nodecls_map']
                return [
                    nodecls(text = md[key], classes = classes + [key])
                    for key, nodecls in nodecls_map.items()
                    if key in md
                ]

            rend = value
            nodecls = moded['nodecls']
            return nodecls(text = rend, classes = classes)

    def unhinted(self):
        text = self.text
        classes = self.classes
        # Try rewrite.
        mode = 'rewrite'
        for pat, info in self.modes[mode].items():
            rend, num = re.subn(pat, info['rep'], text)
            if num:
                classes.extend(info['classes'])
                nodecls = info['nodecls']
                break
        else:
            # Generic math symbols.
            mode = 'math_symbols'
            nodecls = nodes.math
            if 'w' in text:
                classes.append('modal')
            if '<' in text and '>' in text:
                classes.append('tuple')
            rend = text
            for pat, rep in self.generic[mode].items():
                rend = re.sub(pat, rep, rend)

        classes.append(mode)
        return nodecls(text = rend, classes = classes)

def getentry(roleish: SphinxRole|type[SphinxRole]|str) -> tuple[str, Any]|None:
    'Get loaded role name and instance, by name, instance or type.'
    if isinstance(roleish, str):
        inst = _docroles._roles.get(roleish)
        if inst:
            return roleish, inst
        return None
    if isinstance(roleish, type):
        roletype = roleish
    else:
        roletype = type(roleish)
    for name, inst in _docroles._roles.items():
        if type(inst) is roletype:
            return name, inst
