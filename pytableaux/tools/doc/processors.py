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

import os
import re
import shutil
from typing import TYPE_CHECKING, Optional

from pytableaux.errors import check
from pytableaux.logics import registry
from pytableaux.tools import closure
from pytableaux.tools.doc import (AutodocProcessor, ConfKey, Processor,
                                  ReplaceProcessor, SphinxEvent, docinspect,
                                  is_enum_member)
from sphinx.ext import autodoc
from sphinx.util import logging

if TYPE_CHECKING:
    from typing import Any

    import sphinx_toolbox.more_autodoc.overloads
    from proof.tableaux import Rule
    from sphinx.application import Sphinx
    from sphinx.config import Config
    

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
            logger.debug(f'Skipping enum member value for {self.objpath}')
            return True
        return super().should_suppress_value_header()

# class EnumMemberValue(AutodocProcessor):

#     on: None|AutodocProcessor.Record = None
#     member: None|enum.Enum = None

#     namemap: dict[str, type[Enum]]

#     def __init__(self):
#         self.namemap = {}

#     def applies(self):
#         return is_enum_member(self.record.name)

#     def run(self):
#         return

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
    'Prepend docstring with html rule example.'

    def applies(self):
        return docinspect.is_concrete_rule(self.record.obj)

    def run(self):
        obj: type[Rule] = self.record.obj
        logic = registry.locate(obj)
        lines = self.lines.copy()
        self.lines.clear()
        self += f"""
        .. tableau::
            :logic: {logic.name}
            :rule: {obj.name}
        """
        self += lines
        

class BuildtrunkExample(AutodocProcessor):
    'Append docstring with html build_trunk example.'

    def applies(self):
        return (docinspect.is_concrete_build_trunk(self.record.obj) and
                not self.hastext(':build-trunk:'))

    def run(self):
        logic = registry.locate(self.record.obj)
        self += f"""
        .. tableau::
            :logic: {logic.name}
            :build-trunk:
            :prolog:
        """

# ------------------------------------------------

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
                    if not isinstance(pat, str):
                        pat = pat.pattern
                    pat = re.compile(r'(?<!`)' + pat)
                    defns.append((pat, rep))

        self._defns = defns
        return defns

# ------------------------------------------------

class CopyFileTree(Processor):

    def __init__(self, app: Sphinx, config: Config):
        self.app = app
        self.validate()
        app.connect('build-finished', self)

    def __call__(self, app: Sphinx, e: Exception|None):
        if e is None:
            self.app = app
            self.run()
    
    def validate(self):

        for entry in self.config[ConfKey.copy_file_tree]:
            check.inst(entry, (list, tuple))
            src, dest = entry[0:2]
            check.inst(src, str)
            check.inst(dest, str)
            if len(entry) > 2:
                check.inst(entry[2], dict)

    def run(self):

        app = self.app

        for entry in app.config[ConfKey.copy_file_tree]:
            src = os.path.join(app.srcdir, entry[0])
            dest = os.path.join(app.outdir, entry[1])
            eopts = dict(entry[2]) if len(entry) > 2 else {}
            eopts.setdefault('dirs_exist_ok', True)
            ignore = eopts.get('ignore')
            if ignore is not None:
                if not callable(ignore):
                    if isinstance(ignore, str):
                        ignore = ignore,
                    eopts['ignore'] = shutil.ignore_patterns(*ignore)
            shutil.copytree(src, dest, **eopts)

# ------------------------------------------------


def setup(app: Sphinx):

    app.setup_extension('sphinx.ext.autodoc')
    app.add_config_value(ConfKey.auto_skip_enum_value, True, 'env', [bool])
    app.add_autodocumenter(AttributeDocumenter, True)

    ev = 'autodoc-process-docstring'
    # app.connect(ev, EnumMemberValue(), -1)
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
    
    app.add_config_value(ConfKey.copy_file_tree, [], 'env',
        [list[tuple[str, str, Optional[dict]]]]
    )
    app.connect('config-inited', CopyFileTree)



# from sphinx.transforms import post_transforms
# class ReferencesResolver(post_transforms.ReferencesResolver):
#     def run(self, **kw):
#         # self.document.findall(addnodes.pending_xref)
#         pass
# app.add_post_transform(ReferencesResolver)
