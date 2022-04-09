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

from sphinx.application import Sphinx
from sphinx.util import docstrings, logging
from typing import Any

from tools.abcs import abstract
from tools.doc import docinspect, docparts, rstutils
from tools.doc.extension import gethelper
from tools.misc import get_logic

from proof.tableaux import ClosingRule, Rule

logger = logging.getLogger(__name__)

class Processor:

    app: Sphinx

    @property
    def helper(self):
        return gethelper(self.app)

    @abstract
    def run(self):
        raise NotImplementedError

class AutodocProcessor(Processor):

    def applies(self):
        return True

    def __call__(self, app: Sphinx, what: str, name: str, obj: Any, options: dict, lines: list[str]):
        self.app = app
        self.what = what
        self.name = name
        self.obj = obj
        self.options = options
        self.lines = lines
        if self.applies():
            self.run()

    def __iadd__(self, other: str|list[str]):
        if not isinstance(other, str):
            other = '\n'.join(other)
        self.lines.extend(docstrings.prepare_docstring(other))
        return self

class RuledocInherit(AutodocProcessor):
    'Create docstring lines for an "inheriting only" ``Rule`` class.'

    def applies(self):
        return docinspect.is_transparent_rule(self.obj)

    def run(self):
        
        base: type[Rule] = self.obj.mro()[1]
        logic = get_logic(base)
        self += (
            f'*This rule is the same as* :class:`{logic.name} {base.name} '
            f'<{base.__module__}.{base.__qualname__}>`'
        )
        self += base.__doc__

class RuledocExample(AutodocProcessor):
    'Append docstring with html rule example.'

    def applies(self):
        return docinspect.is_concrete_rule(self.obj)

    @property
    def pw(self):
        if issubclass(self.obj, ClosingRule):
            return self.helper.pwclosure
        return self.helper.pwrule

    def run(self):
        tab = docparts.rule_example_tableau(self.obj)
        self += 'Example:'
        self.lines.extend(rstutils.rawblock(self.pw(tab)))

class BuildtrunkExample(AutodocProcessor):
    'Append docstring with html build trunk example.'

    def applies(self):
        return docinspect.is_concrete_build_trunk(self.obj)

    @property
    def pw(self):
        return self.helper.pwtrunk

    @property
    def lw(self):
        return self.pw.lw

    def __init__(self):
        from lexicals import Argument, Atomic
        self.argument = Argument(
            Atomic(1, 0), (Atomic(0, 1), Atomic(0, 2))
        )

    def run(self):
        logic = get_logic(self.obj)
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