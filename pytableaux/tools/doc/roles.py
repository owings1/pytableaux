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
from typing import TYPE_CHECKING

from docutils import nodes
from pytableaux import logics
from pytableaux.lang import (LexType, LexWriter, Notation, Parser, Predicate,
                             Predicates)
from pytableaux.tools import MapProxy, abcs
from pytableaux.tools.doc import (BaseRole, ConfKey, ParserOptionMixin,
                                  classopt, nodeopt, nodez, predsopt)
from pytableaux.tools.hybrids import qset, qsetf
from pytableaux.tools.typing import F
from sphinx.errors import NoUri
from sphinx.util import logging
from sphinx.util.docutils import ReferenceRole

if TYPE_CHECKING:
    from docutils.nodes import Element, Node, system_message
    from sphinx.application import Sphinx
    from sphinx.environment import BuildEnvironment
    from sphinx.transforms import post_transforms
    from stubs.docutils import nodes  # type: ignore

__all__ = ('lexdress', 'metadress', 'refplus', 'refpost',)

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

class refplus(
    # sphinx.roles.XRefRole,
    ReferenceRole,
    BaseRole,
):

    section: str
    anchor: str
    logicname: str 
    lrmatch = None

    # name = 
    refdomain = 'std'
    reftype = 'ref'

    _classes = 'xref', refdomain, f'{refdomain}-{reftype}'

    # lowercase = False
    warn_dangling = True

    def __init__(self):
        # {'class': None}         
        self.options ={}

    @rolerun
    def run(self):
        self.classes = qset(self._classes)
        
        if self._logic_ref():
            self.classes |= 'logicref', 'internal'

            mmnn = metadress.logicname_node(self.logicname)

            node = nodes.reference(self.rawtext, '',
                refuri = self.refuri,
                logicname = self.logicname,
                target = self.target,
                title = self.title,
                refdomain = self.refdomain,
                reftype = self.reftype,
                classes = self.classes,
            )

            a, b = self.title, mmnn.astext()
            if a == b:
                node += mmnn
            else:
                prefix = f'{b} '
                if a.startswith(prefix):
                    node += mmnn
                    node += nodes.inline(text = a.removeprefix(b))
                else:
                    node += nodes.inline(text = a)

            return [node], []

        else:
            if self.has_explicit_title:
                fallback_text = self.title
            else:
                fallback_text = self.text
            logger.warning(NoUri(f"From text: {self.text}"))
            return [nodes.inline(text = fallback_text)], []

    def _logic_ref(self):
        lrmatch = self.patterns['logicref'].match(self.text)
        if not lrmatch:
            return
        m = lrmatch.groupdict()
        self.logicname = m['name']
        self.section = m['sect']
        self.anchor = m['anchor']
        if self.section:
            self.title = f'{self.logicname} {self.section}'.strip()
        else:
            self.title = self.logicname

        self.has_explicit_title = True

        if self.anchor:
            self.target = self.anchor[1:-1]
        else:
            if self.section:
                self.target = self.logicname
            else:
                self.target = '-'.join(re.split(r'\s+', self.title.lower()))
        self.target = self.target.lower()
        self.text = f'{self.title} <{self.target}>'

        self.refuri = f'{self.logicname.lower()}.html#{self.target}'

        return True

    _logic_union = '|'.join(
        sorted((n.split('.')[-1].upper() for n in 
        logics.registry.all()), key = len, reverse = True)
    )
    patterns = dict(
        logicref = re.compile(
            r'({@(?P<name>%s)' % _logic_union +
            r'(?:\s+(?P<sect>[\sa-zA-Z-]+)?(?P<anchor><.*?>)?)?})'
        )
    )

    def _checkregex(self):
        if not re.match(self.patterns['logicref'], '{@FDE}'):
            logger.error(f'PATTERN BROKEN!! for {type(self).__name__}')
            logger.error(self.patterns['logicref'])

    def _debug(self):
        logger.info(
            f'rawtext={self.rawtext}, text={self.text}, '
            f'logicname={self.name}, section={self.section}, anchor={self.anchor}, '
            f'title={self.title}, self.target={self.target}'
        )

class _Ctype(frozenset, abcs.Ebc):
    valued = {
        LexType.Operator, LexType.Quantifier, Predicate.System
    }
    nosent = valued | {
        LexType.Constant, LexType.Variable, LexType.Predicate,
    }

_re_nosent = re.compile(r'^(.)([0-9]*)$')


class lexdress(BaseRole, ParserOptionMixin):

    option_spec = MapProxy(dict({'class': None},
        node = nodeopt,
        wnotn = Notation,
        pnotn = Notation,
        preds = predsopt,
        classes = classopt,
    ))

    opt_defaults = MapProxy(dict({'class': None},
        node = nodes.inline,
        classes = qsetf(['lexitem']),
    ))


    @rolerun
    def run(self):

        classes = self.set_classes()
        classes.update(self.opt_defaults['classes'])

        opts = self.options
        conf = self.config

        parser = self.parser_option()
        preds = parser.preds
        nodecls = opts.get('node', self.opt_defaults['node'])
        wnotn = opts.get('wnotn', conf[ConfKey.wnotn])
        lw = LexWriter(wnotn, 'unicode')

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

        node = nodecls(classes = classes)
        node += nodez.sentence(sentence = item)
        return node

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

    logics.registry.import_all()

    app.add_role('s', role_s := lexdress())
    app.add_role(name_sc := 'sc', role_s.wrapped(name_sc, dict(
        node = 'literal',
        classes = ['code'],
    )))

    app.add_role('m', metadress())
    app.add_role('refp', refplus())
    APPSTATE[app][refplus] = {}

from pytableaux.tools.doc import APPSTATE
