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
pytableaux.tools.doc.processors
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
"""
from __future__ import annotations

import enum
import re
from enum import Enum
from typing import TYPE_CHECKING, Any, cast

from pytableaux.lang.collect import Argument
from pytableaux.lang.lex import Atomic, Operator
from pytableaux.logics import registry
from pytableaux.tools.doc import (AutodocProcessor, ConfKey, ReplaceProcessor,
                                  SphinxEvent, docinspect, docparts,
                                  is_enum_member, rstutils)
from sphinx.ext import autodoc
from sphinx.ext.autodoc import importer
from sphinx.util import logging

if TYPE_CHECKING:
    import sphinx_toolbox.more_autodoc.overloads
    from proof.tableaux import Rule
    from sphinx.application import Sphinx
    

__all__ = (
    'BuildtrunkExample',
    'RuledocExample',
    'RuledocInherit',
    'GlobalReplace',
)

logger = logging.getLogger(__name__)



class AttributeDocumenter(autodoc.AttributeDocumenter):

    def should_suppress_value_header(self) -> bool:
        if self.config[ConfKey.auto_skip_enum_value] and is_enum_member(self.modname, self.objpath):
            logger.info(f'Skipping enum member value for {self.objpath}')
            return True
        return super().should_suppress_value_header()


class EnumMemberValue(AutodocProcessor):

    on: None|AutodocProcessor.Record = None
    member: None|enum.Enum = None

    namemap: dict[str, type[Enum]]

    def __init__(self):
        self.namemap = {}

    def applies(self):
        return is_enum_member(self.record.name)
        # fullpath = self.record.name.split('.')
        # if len(fullpath) > 2:
        #     objpath = [fullpath[-2], fullpath[-1]]
        #     modname = '.'.join(fullpath[0:-2])
        #     isenum = is_enum_member(modname, objpath)
        #     return isenum
        # else:
        #     return False
        # rec = self.record
        # obj = rec.obj
        # if isinstance(obj, type) and issubclass(obj, Enum):
        #     for member in obj:
        #         self.namemap[f'{rec.name}.{member._name_}'] = obj
        # if (enumcls := self.namemap.get(rec.name)) is not None:



        #     member = self.member = enumcls(obj)
        #     print('$MEMBER$  rec.name', rec.name, '__module__', getattr(obj, '__module__', None))#obj: ', obj, '  member: ', member)
        #     return True
        # return False

        # if rec.obj is Operator:
        #     print('!' * 20, rec.obj)

        # if 'pytableaux.lang.lex.Operator' in rec.name:
        #     print(
        #         ' --- ', rec.name, ' what: ', rec.what, '  obj: ', rec.obj,
        #         '  type(obj): ', type(rec.obj),
        #         '  isinsta'
        #     )
        #     print('     on? ', bool(self.on), '  ', self.on)
        # if not self.on:
        #     if isinstance(rec.obj, enum.EnumMeta):
        #         self.on = rec
        #     return

        # ecls = self.on.obj

        # if rec.name.startswith(self.on.name):
        #     membname = rec.name.removeprefix(f'{self.on.name}.')
        #     try:
        #         self.member = ecls[membname]
        #     except:
        #         pass
        #     else:
        #         return True
        # else:
        #     self.on = None
        # print(ecls, rec.obj)
        # return False

    def run(self):
        print('$MEMBER$  rec.name', self.record.name)
        return
        # member = self.member
        # hidestr = ':meta hide-value:'
        # if not self.hastext(hidestr):
        #     self.lines.extend(['',hidestr,''])
        # # print(self.lines)
        # self.member = None

class RuledocInherit(AutodocProcessor):
    'Create docstring lines for an "inheriting only" ``Rule`` class.'

    def applies(self):
        return docinspect.is_transparent_rule(self.record.obj)

    def run(self):
        obj: type[Rule] = self.record.obj
        base: type[Rule] = obj.mro()[1]
        logic = registry.locate(base)
        self += (
            f'*This rule is the same as* :class:`{logic.name} {base.name} '
            f'<{base.__module__}.{base.__qualname__}>`'
        )
        self += base.__doc__

class RuledocExample(AutodocProcessor):
    'Append docstring with html rule example.'

    def applies(self):
        return docinspect.is_concrete_rule(self.record.obj)

    def run(self):
        obj: type[Rule] = self.record.obj
        logic = registry.locate(obj)
        self += f"""
        Example:
        
        .. tableau:: {logic.name}.{obj.name}
        """
        # self.lines.extend(rstutils.rawblock(self.pw(tab, classes = classes)))

class BuildtrunkExample(AutodocProcessor):
    'Append docstring with html build trunk example.'

    def applies(self):
        return docinspect.is_concrete_build_trunk(self.record.obj)

    argument = Argument(Atomic(1, 0), map(Atomic, ((0, 1), (0, 2))))

    @property
    def pw(self):
        return self.helper.pwtrunk

    @property
    def lw(self):
        return self.pw.lw

    def run(self):
        rec = self.record
        logic = registry.locate(rec.obj)
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

        from pytableaux.tools.doc import role_name, roles
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

    app.add_config_value(ConfKey.auto_skip_enum_value, True, 'env')

    app.add_autodocumenter(AttributeDocumenter, True)

    ev = 'autodoc-process-docstring'
    app.connect(ev, EnumMemberValue(), -1)
    app.connect(ev, RuledocInherit())
    app.connect(ev, RuledocExample())
    app.connect(ev, BuildtrunkExample())

    replacers = (
        RolewrapReplace(),
    )

    for inst in replacers:
        app.connect(SphinxEvent.IncludeRead, inst)
        app.connect('source-read', inst)
        app.connect('autodoc-process-docstring', inst)
