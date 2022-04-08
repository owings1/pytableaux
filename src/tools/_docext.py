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
# pytableaux - docutils/sphins exentions.
from __future__ import annotations
import traceback

from tools.decorators import wraps

__all__ = (
    'Lexdress',
    'Metadress',
    'RefPlus'
    'include_directive',
)

import examples
from lexicals import LexType, LexWriter, Notation, Parser, Predicate
from tools.abcs import F, MapProxy, AbcMeta

from docutils import nodes
from html import unescape as htmlun
from sphinx.application import Sphinx
from sphinx.roles import XRefRole as BaseRefRole
from sphinx.util import logging
from sphinx.util.docutils import SphinxRole
import re

logger = logging.getLogger(__name__)

def rolemethod(func: F) -> F:
    # Decorator for role method.
    @wraps(func)
    def run(self: BaseRole):
        try:
            ret = func(self)
        except:
            logger.error(
                f"rawtext={repr(self.rawtext)}, "
                f"content={self.content}"
            )
            logger.info('Printing traceback')
            traceback.print_exc()
            raise
        else:
            # Quote from https://docutils.sourceforge.io/docs/howto/rst-roles.html
            #
            # Role functions return a tuple of two values:
            # 
            #  - A list of nodes which will be inserted into the document tree
            #    at the point where the interpreted role was encountered (can be
            #   an empty list).
            # 
            #  - A list of system messages, which will be inserted into the
            #    document tree immediately after the end of the current block
            #   (can also be empty).
            #
            if isinstance(ret, nodes.Node):
                # Allow a single node.
                ret = [ret], []
            elif not isinstance(ret, tuple):
                # Allow just the list of nodes.
                ret = ret, []
            return ret
    return run

class BaseRole(SphinxRole, metaclass = AbcMeta):
    pass


class RefPlus(BaseRefRole, BaseRole):

    refdomain = 'std'
    reftype = 'ref'
    _classes = 'xref', refdomain, f'{refdomain}-{reftype}'

    innernodeclass = nodes.inline
    fix_parens = False
    lowercase = True #False
    warn_dangling = True # False

    def __init__(self, **_) -> None:
        pass

    @rolemethod
    def run(self):
        self.classes = list(self._classes)
        if self.disabled:
            return self.create_non_xref_node()
        else:
            return self.create_xref_node()

class Lexdress(BaseRole):

    _defaults = MapProxy(dict(
        write_notation   = Notation.standard,
        parse_notation   = Notation.standard,
        preds            = examples.preds,
    ))

    _ctypes = dict(
        valued = {
            LexType.Operator,
            LexType.Quantifier,
            Predicate.System
        }
    )
    _ctypes['nosent'] = _ctypes['valued'] | {
        LexType.Constant,
        LexType.Variable,
        LexType.Predicate,
    }

    parser: Parser
    lwhtml: LexWriter

    def __init__(self, **opts):
        opts = dict(self._defaults) | opts
        self.parser = Parser(opts['parse_notation'], opts['preds'])
        self.lwhtml = LexWriter(opts['write_notation'], 'html')

    @rolemethod
    def run(self):

        text = self.text

        classes = ['lexitem']

        item = None
        match = re.match(r'^(.)([0-9]*)$', text)

        if match:
            char, sub = match.groups()
            table = self.parser.table
            ctype = table.type(char)
            _ctypes = self._ctypes
            if ctype in _ctypes['nosent']:
                # Non-sentence items.
                sub = int(sub) if len(sub) else 0
                if ctype in _ctypes['valued']:
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
        rend = htmlun(self.lwhtml(item))

        return nodes.inline(text = rend, classes = classes)

class Metadress(BaseRole):



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

    @rolemethod
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
            # logger.info((text,rend))

        classes.append(mode)
        return nodecls(text = rend, classes = classes)

def include_directive(app: Sphinx):
    "Override include directive that allows the app to modify content via events."

    app.add_event('include-read')

    from sphinx.directives.other import Include as BaseInclude

    class Include(BaseInclude):

        def parse(self, text: str, doc):
            lines = text.split('\n')
            source = doc.attributes['source']
            app.emit('include-read', lines)
            self.state_machine.insert_input(lines, source)

        def run(self):
            self.options['parser'] = lambda: self
            super().run()
            return []

    return Include