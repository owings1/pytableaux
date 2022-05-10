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
pytableaux.tools.doc.roles
^^^^^^^^^^^^^^^^^^^^^^^^^^

"""
from __future__ import annotations

import functools
import re
from collections import ChainMap
from typing import TYPE_CHECKING

import sphinx.roles
from docutils import nodes
from pytableaux import logics
from pytableaux.lang import Notation
from pytableaux.lang.collect import Predicates
from pytableaux.lang.lex import LexType, Predicate
from pytableaux.lang.parsing import Parser
from pytableaux.lang.writing import LexWriter
from pytableaux.tools import MapProxy, abcs
from pytableaux.tools.doc import BaseRole, classopt, nodeopt, predsopt
from pytableaux.tools.doc.extension import Helper
from pytableaux.tools.hybrids import qsetf
from pytableaux.tools.typing import F
from sphinx.util import logging

if TYPE_CHECKING:
    from sphinx.application import Sphinx

__all__ = ('lexdress', 'metadress', 'refplus',)

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
        sorted(logics.registry.all(), key = len, reverse = True)
        # sorted(docinspect.get_logic_names(), key = len, reverse = True)
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
        
        self.classes = list(self._classes)

        lrmatch = re.match(self.patterns['logicref'], self.text)
        if lrmatch:
            self.logicname = lrmatch.group('name')
            self._logic_ref(**lrmatch.groupdict())
        else:
            self.logicname = None

        if self.disabled:
            ret = self.create_non_xref_node()
        else:
            ret = self.create_xref_node()

        if lrmatch:
            ...
        return ret

    def _logic_ref(self, *, name: str, sect: str|None, anchor: str|None):
        # Link to a logic:
        #   {@K3}        -> K3 <K3>`
        #   {@FDE Model} -> `FDE Model <fde-model>`
        if sect is None:
            self.title = name
        else:
            self.title = f'{name} {sect}'.strip()
        self.has_explicit_title = True
        if anchor is None:
            if sect is None:
                self.target = name
            else:
                self.target = '-'.join(re.split(r'\s+', self.title.lower()))
        else:
            self.target = anchor[1:-1]
        self.text = f'{self.title} <{self.target}>'
        self.rawtext = f":{self.name}:`{self.text}`"
        if False:
            logger.info(
                f'name={repr(name)}, '
                f'sect={repr(sect)}, '
                f'anchor={repr(anchor)}, '
                f'self.title={repr(self.title)}, '
                f'self.target={repr(self.target)}, '
                f'self.text={repr(self.text)}, '
                f'self.rawtext={repr(self.rawtext)}, '
            )
        
        self.classes.append('logicref')


class _Ctype(frozenset, abcs.Ebc):
    valued = {
        LexType.Operator, LexType.Quantifier, Predicate.System
    }
    nosent = valued | {
        LexType.Constant, LexType.Variable, LexType.Predicate,
    }

_re_nosent = re.compile(r'^(.)([0-9]*)$')


class lexdress(BaseRole):

    option_spec = MapProxy(dict({'class': None},
        node = nodeopt,
        wnotn = Notation,
        pnotn = Notation,
        preds = predsopt,
        classes = classopt,
    ))

    opt_defaults = MapProxy(dict({'class': None},
        node = nodes.inline,
        wnotn = Helper.defaults['wnotn'],
        pnotn = Helper.defaults['pnotn'],
        preds = Predicates(Helper.defaults['preds']),
        classes = qsetf(['lexitem']),
    ))


    @rolerun
    def run(self):

        classes = self.set_classes()
        classes.update(self.opt_defaults['classes'])

        preds: Predicates
        opts = ChainMap(self.options, self.opt_defaults)

        nodecls = opts['node']
        parser = Parser(opts['pnotn'], preds := opts['preds'])
        lw = LexWriter(opts['wnotn'], 'unicode')

        text = self.text

        item = None
        match = _re_nosent.match(text)

        if match is not None:
            char, sub = match.groups()
            table = parser.table
            ctype = table.type(char)
            if ctype in _Ctype.nosent:
                # Non-sentence items.
                if len(sub):
                    sub = int(sub)
                else:
                    sub = 0
                if ctype in _Ctype.valued:
                    item = table.value(char)
                elif ctype is LexType.Predicate:
                    item = preds.get((table.value(char), sub))
                else:
                    item = ctype.cls(table.value(char), sub)

        if item is None:
            # Parse as sentence.
            item = parser(text)

        classes.add(item.TYPE.name.lower())

        rend = lw(item)

        return nodecls(text = rend, classes = classes)

class metadress(BaseRole):

    prefixes = {
        'L': 'logic_name',
        'V': 'truth_value',
        '!': 'rewrite',
    }

    modes = dict(
        logic_name = dict(
            match_map = {
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
            r"^(L'*?)$": dict(
                rep = r'\1',
                classes = ('big-l',),
                nodecls = nodes.inline,
            ),
            r'^(\|-|conseq|impl(ies)?)$': dict(
                rep = '⊢',
                classes = ('conseq',),
                nodecls = nodes.inline,
            ),
            r'^(\|(/|!)-|no(n|t)?-?(conseq|impl(ies)?))$': dict(
                rep = '⊬',
                classes = ('non-conseq',),
                nodecls = nodes.inline,
            ),
            r'^(\|\?-|(conseq|impl(ies)?)\?)$' : dict(
                static = True,
                nodes = [
                    nodes.inline(
                        '', '',
                        nodes.inline(text = '⊢', classes = ['conseq']),
                        nodes.superscript(text = '?'),
                        classes = ['metawrite', 'conseqq',],
                    )
                ]
            )
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
                if info.get('static'):
                    if re.match(pat, value):
                        return info['nodes']
                else:
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
            if info.get('static'):
                if re.match(pat, text):
                    return info['nodes']
            else:
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
        for pat, addcls in moded['match_map'].items():
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
        

def setup(app: Sphinx):
    # The role directive in reStructuredText::
    #
    #     .. role:: sc(s)
    #        :node: literal
    #        :class: code
    #

    app.add_role('s', role_s := lexdress())
    app.add_role(name_sc := 'sc', role_s.wrapped(name_sc, dict(
        node = 'literal',
        classes = ['code'],
    )))


    app.add_role('m', metadress())
    app.add_role('refp', refplus())
