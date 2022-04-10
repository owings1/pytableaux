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


__all__ = (
    'metadress',
    'lexdress',
    'refplus',
)

import lexicals
from lexicals import LexType
import parsers
from tools import T, F
from tools.doc import docinspect, extension

from docutils import nodes
from docutils.parsers.rst import roles as _docroles
import functools
import re
import sphinx.roles
from sphinx.util import logging
from sphinx.util.docutils import SphinxRole
from typing import Any, Callable, Generic, NamedTuple, overload

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

class BaseRole(SphinxRole):
    @property
    def helper(self):
        return extension.gethelper(self.env.app)

class refplus(sphinx.roles.XRefRole, BaseRole):

    refdomain = 'std'
    reftype = 'ref'
    _classes = 'xref', refdomain, f'{refdomain}-{reftype}'

    innernodeclass = nodes.inline
    fix_parens = False
    lowercase = True #False
    warn_dangling = True # False

    def __init__(self, **_) -> None:
        pass

    _logic_union = '|'.join(
        sorted(docinspect.get_logic_names(), key = len, reverse = True)
    )
    patterns = dict(
        logicref = (
            r'({@(?P<name>%s)' % _logic_union +
            r'(?:\s+(?P<sect>[\sa-zA-Z-]+)?(?P<anchor><.*?>)?)?})'
        )
    )

    @rolerun
    def run(self):
        def _log():
            logger.info(
                f'rawtext={repr(self.rawtext)}, '
                f'text={repr(self.text)}, '
                f'title={repr(self.title)}, '
                f'target={repr(self.target)}'
            )
        # _log()
        
        self.classes = list(self._classes)

        lrmatch = re.match(self.patterns['logicref'], self.text)
        if lrmatch:
            self.logicname = lrmatch.group('name')
            # logger.info('Match!')
            self._logic_ref(**lrmatch.groupdict())
        else:
            self.logicname = None
            # _log()

        if self.disabled:
            ret = self.create_non_xref_node()
        else:
            ret = self.create_xref_node()

        if lrmatch:
            ...
            # logger.info(ret[0][0].astext())
        return ret

    def _logic_ref(self, *, name: str, sect: str|None, anchor: str|None):
        # Link to a logic:
        #   {@K3}        -> K3 <K3>`
        #   {@FDE Model} -> `FDE Model <fde-model>`
        if sect is None:
            self.title = name
        else:
            self.title = f'{name} {sect}'.strip()
        if anchor is None:
            if sect is None:
                self.target = name
            else:
                self.target = '-'.join(re.split(r'\s+', self.title.lower()))
        else:
            self.target = anchor[1:-1]
        self.text = f'{self.title} <{self.target}>'
        self.rawtext = f":{self.name}:`{self.text}`"
        self.classes.append('logicref')

class lexdress(BaseRole):

    _parser: parsers.Parser = None
    _lw: lexicals.LexWriter = None

    def __init__(self, *, wnotn: str = None, pnotn: str = None, preds:lexicals.Predicates = None):
        'Override app options with constructor.'
        from docutil import Helper
        defaults = Helper._defaults
        if wnotn is not None:
            self._lw = lexicals.LexWriter(wnotn, 'unicode')

        if pnotn is not None or preds is not None:
            if pnotn is None:
                pnotn = defaults['pnotn']
            if preds is None:
                preds = defaults['preds']
            self._parser = parsers.Parser(pnotn, preds)

    @property
    def parser(self):
        if self._parser is None:
            self._parser = self.helper.parser
        return self._parser

    @property
    def lw(self):
        if self._lw is None:
            wnotn = self.helper.opts['wnotn']
            self._lw = lexicals.LexWriter(wnotn, 'unicode')
        return self._lw

    _ctypes_valued = {
        LexType.Operator, LexType.Quantifier, lexicals.Predicate.System
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

class metadress(BaseRole):

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
            return self._unhinted()

        matchd = match.groupdict()
        mode: str = self.prefixes[matchd['prefix']]
        value: str = matchd['value']

        if mode == 'logic_name':
            return self.logicname_node(value)

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


    def _unhinted(self):
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

    @classmethod
    def logicname_node(cls, name: str):
        moded = cls.modes['logic_name']
        classes = ['metawrite', 'logic_name']
        nodecls = moded['nodecls']
        for pat, addcls in moded['match'].items():
            m = re.match(pat, name)
            if not m:
                continue
            md = m.groupdict()
            classes.extend(addcls)
            node = nodecls(classes = classes)
            nodecls_map: dict = moded['nodecls_map']
            node += [
                nodecls(text = md[key], classes = [key])
                for key, nodecls in nodecls_map.items()
                if key in md
            ]
            return node
        return nodecls(text = name, classes = classes)


@overload
def getentry(rolecls: type[T]) -> _RoleItem[T]|None: ...
@overload
def getentry(rolefn: F) -> _RoleItem[F]|None: ...
@overload
def getentry(roleish: str) -> _RoleItem[__RoleT]|None:...

def getentry(roleish):
    'Get loaded role name and instance, by name, instance or type.'
    idx: dict = _docroles._roles
    if isinstance(roleish, str):
        inst = idx.get(roleish)
        if inst is None:
            return None
        name = roleish
    else:
        checktype = isinstance(roleish, type)
        for name, inst in idx.items():
            if checktype:
                if type(inst) is roleish:
                    break
            elif inst is roleish:
                break
        else:
            return None
    return _RoleItem(name, inst)


class __RoleItem(NamedTuple):
    name: str
    inst: Any

class _RoleItem(__RoleItem, Generic[T]):
    name: str
    inst: T

__RoleT = Callable[..., tuple[list[nodes.Node], list[nodes.system_message]]]
