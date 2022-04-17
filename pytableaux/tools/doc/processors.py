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
# pytableaux - sphinx processors
from __future__ import annotations

__all__ = (
    'BuildtrunkExample',
    'RuledocExample',
    'RuledocInherit',
    'GlobalReplace',
)

import re
from sphinx.util import logging
from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from sphinx.application import Sphinx
    from proof.tableaux import Rule

from pytableaux.logics import getlogic
from pytableaux.lexicals import Argument, Atomic
from pytableaux.tools.doc import (docinspect, docparts, rstutils, AutodocProcessor,
                       ReplaceProcessor, SphinxEvent)

logger = logging.getLogger(__name__)

class RuledocInherit(AutodocProcessor):
    'Create docstring lines for an "inheriting only" ``Rule`` class.'

    def applies(self):
        return docinspect.is_transparent_rule(self.obj)

    def run(self):
        base: type[Rule] = self.obj.mro()[1]
        logic = getlogic(base)
        self += (
            f'*This rule is the same as* :class:`{logic.name} {base.name} '
            f'<{base.__module__}.{base.__qualname__}>`'
        )
        self += base.__doc__

class RuledocExample(AutodocProcessor):
    'Append docstring with html rule example.'

    def applies(self):
        return docinspect.is_concrete_rule(self.obj)

    def run(self):
        logic = getlogic(self.obj)
        self += f"""
        Example:
        
        .. tableau:: {logic.name}.{self.obj.name}
        """
        # self.lines.extend(rstutils.rawblock(self.pw(tab, classes = classes)))

class BuildtrunkExample(AutodocProcessor):
    'Append docstring with html build trunk example.'

    def applies(self):
        return docinspect.is_concrete_build_trunk(self.obj)

    argument = Argument(Atomic(1, 0), map(Atomic, ((0, 1), (0, 2))))

    @property
    def pw(self):
        return self.helper.pwtrunk

    @property
    def lw(self):
        return self.pw.lw

    def run(self):
        logic = getlogic(self.obj)
        arg = self.argument
        tab = docparts.trunk_example_tableau(logic, arg)
        self += 'Example:'
        rawlines = self.arghtml().splitlines()
        rawlines.extend(self.pw(tab).splitlines())
        self.lines.extend(rstutils.rawblock(rawlines))

    def arghtml(self):
        arg = self.argument
        pstr = '</i> ... <i>'.join(map(self.lw, arg.premises))
        argstr = f'Argument: <i>{pstr}</i> &there4; <i>{self.lw(arg.conclusion)}</i>'
        return argstr

class RolewrapReplace(ReplaceProcessor):

    def run(self):
        text = '\n'.join(self.lines)
        count = 0
        for pat, rep in self.defns:
            text, num = pat.subn(rep, text)
            count += num
        if count:
            if self.mode == 'source':
                self.lines[0]= text
            else:
                self.lines.clear()
                self.lines.extend(text.split('\n'))

    _defns: list[tuple[re.Pattern, str]] = None

    @property
    def defns(self):
        defns = self._defns
        if defns is not None:
            return defns

        from pytableaux.tools.doc import roles, role_name
        rolewrap = {
            roles.metadress: ['prefixed'],
            roles.refplus  : ['logicref'],
        }
        defns = []
        for rolecls, patnames in rolewrap.items():
            name = role_name(rolecls)
            if name is not None:
                rep = f':{name}:'r'`\1`'
                for patname in patnames:
                    pat = rolecls.patterns[patname]
                    pat = re.compile(r'(?<!`)' + rolecls.patterns[patname])
                    defns.append((pat, rep))

        self._defns = defns
        return defns

def setup(app: Sphinx):

    app.setup_extension('sphinx.ext.autodoc')

    app.connect('autodoc-process-docstring', RuledocInherit())
    app.connect('autodoc-process-docstring', RuledocExample())
    app.connect('autodoc-process-docstring', BuildtrunkExample())

    replacers = (
        RolewrapReplace(),
    )

    for inst in replacers:
        app.connect(SphinxEvent.IncludeRead, inst)
        app.connect('source-read', inst)
        app.connect('autodoc-process-docstring', inst)
