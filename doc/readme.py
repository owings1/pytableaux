# -*- coding: utf-8 -*-
# pytableaux, a multi-logic proof generator.
# Copyright (C) 2014-2023 Doug Owings.
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
from __future__ import annotations

import sys
import argparse
from os.path import abspath
from dataclasses import dataclass
import re
from collections import deque
import logging
from pytableaux import package
from pytableaux.logics import registry
from pytableaux.tools import lazy

logger = logging.getLogger('readme')

parser = argparse.ArgumentParser(
    description='Update README.md with auto-replacements')

arg = parser.add_argument
arg(
    '--file', '-f',
    type=abspath,
    default=abspath(f'{package.root}/../README.md'),
    help='Location of readme file')

@dataclass(kw_only=True, slots=True)
class Options:
    file: str

def main(*args):
    opts = Options(**vars(parser.parse_args(args)))
    logging.basicConfig(level=logging.INFO)
    Helper(opts).run()


class Helper:

    tags = ['copyright', 'refs', 'logics']

    logic_pretty = dict(
        K3WQ='K<sup>3</sup><sub>WQ</sub>',
        B3E='B<sup>3</sup><sub>E</sub>',
        K3W='K<sup>3</sup><sub>W</sub>',
        RM3='RM<sub>3</sub>',
        G3='G<sub>3</sub>',
        K3='K<sub>3</sub>',
        L3='L<sub>3</sub>',
        Ł3='Ł<sub>3</sub>',
        P3='P<sub>3</sub>')

    opts: Options

    @lazy.prop
    def logics_grouped(self):
        return registry.grouped()

    def __init__(self, opts: Options):
        self.opts = opts
        self.tags = sorted(set(self.tags))
        self.pat_begin = re.compile(
            r'<!-- \[(?P<tag>' +
            '|'.join(map(re.escape, self.tags)) +
            r')-begin\] -->')
        self.endstrs = {tag: f'<!-- [{tag}-end] -->' for tag in self.tags}
        self.linefuncs = {tag: getattr(self, f'lines_{tag}') for tag in self.tags}

    def run(self):
        lines = deque(self.getlines())
        with open(self.opts.file, 'w') as file:
            file.write('\n'.join(lines))

    def getlines(self):
        mbegin = self.pat_begin.match
        with open(self.opts.file, 'r') as file:
            self.file = file
            while True:
                line = file.readline()
                if not line:
                    break
                line = line.rstrip('\r\n')
                yield line
                match = mbegin(line)
                if not match:
                    continue
                tag = match.group('tag')
                content = list(self.read_tag_content(tag))
                lines = list(self.linefuncs[tag](list(content)))
                self.log_diff(tag, lines, content)
                yield from lines
                yield self.endstrs[tag]
        self.file = None

    def read_tag_content(self, tag: str):
        readline = self.file.readline
        mbegin = self.pat_begin.match
        endstr = self.endstrs[tag]
        mend = re.compile(re.escape(endstr)).match
        while True:
            line = readline()
            if not line:
                raise ValueError(f'Missing end tag: {endstr}')
            line = line.rstrip('\r\n')
            if mend(line):
                break
            if mbegin(line):
                raise ValueError(f'Nested start tag: {line}')
            yield line

    def log_diff(self, tag: str, lines: list[str], content: list[str]):
        if lines == content:
            logger.info(f'{tag}: no change')
            return
        if not lines and content:
            logger.warning(f'{tag}: empty content')
            return
        lineset = set(lines)
        removed = [line for line in content if line not in lineset]
        if removed:
            logger.info(f'{tag} -:\n' + '\n'.join(removed))
        lineset = set(content)
        added = [line for line in lines if line not in lineset]
        if added:
            logger.info(f'{tag} +:\n' + '\n'.join(added))
        if not added and not removed:
            logger.info(f'{tag}: replaced')

    def lines_copyright(self, content):
        yield f'Copyright (C) {package.copyright_markdown.rstrip(".")}.'

    def lines_refs(self, content):
        yield f'[site]: {package.homepage.url}'
        yield f'[doc]: {package.documentation.url}'
        yield f'[license]: {package.license.url}'
        yield f'[issues]: {package.issues.url}'
        yield f'[mailto]: mailto:{package.author.email}'
        geturl = (package.documentation.url.rstrip('/') + '/logics/%s.html').__mod__
        for group in self.logics_grouped.values():
            for logic in group:
                name = logic.Meta.name
                yield f'[{name}]: {geturl(name.lower())}'

    def lines_logics(self, content):
        yield ''
        for category, group in self.logics_grouped.items():
            yield f'### {category.title}'
            yield ''
            for logic in group:
                meta = logic.Meta
                name = meta.name
                name_pretty = name
                title_pretty = meta.title
                for key, value in self.logic_pretty.items():
                    name_pretty = name_pretty.replace(key, value)
                    title_pretty = title_pretty.replace(key, value)
                yield f'- [**{name_pretty}** - {title_pretty}][{name}]'
            yield ''

if __name__ == '__main__':
    main(*sys.argv[1:])
