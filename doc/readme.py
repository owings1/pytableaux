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
from pytableaux.logics import LogicType, registry

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

    opts: Options
    tags = ['copyright', 'refs']

    def __init__(self, opts: Options):
        self.opts = opts
    
    def setup(self):
        self.tags = sorted(set(self.tags))
        self.pat_begin = re.compile(
            r'<!-- \[(?P<tag>' + '|'.join(map(re.escape, self.tags)) + r')-begin\] -->'
        )
        self.endstrs = {tag: f'<!-- [{tag}-end] -->' for tag in self.tags}

    def run(self):
        self.setup()
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
                yield from self.get_tag_lines(tag)
                yield self.endstrs[tag]
        self.file = None

    def get_tag_lines(self, tag: str):
        content = list(self.read_tag_content(tag))
        func = getattr(self, f'lines_{tag}')
        lines = list(func(list(content)))
        if lines == content:
            logger.info(f'{tag}: no change')
            yield from lines
            return
        if not lines and content:
            logger.warning(f'Empty content for {tag}')
            return
        lineset = set(lines)
        removed = [line for line in content if line not in lineset]
        if removed:
            logger.info(f'Removed {tag}:\n' + '\n'.join(removed))
        lineset = set(content)
        added = [line for line in lines if line not in lineset]
        if added:
            logger.info(f'Added {tag}:\n' + '\n'.join(added))
        if not added and not removed:
            logger.info(f'Replaced {tag}')
        yield from lines

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

    def lines_copyright(self, content):
        yield f'Copyright (C) {package.copyright_markdown.rstrip(".")}.'

    def lines_refs(self, content):
        yield f'[site]: {package.homepage.url}'
        yield f'[doc]: {package.documentation.url}'
        yield f'[license]: {package.license.url}'
        yield f'[issues]: {package.issues.url}'
        yield f'[mailto]: mailto:{package.author.email}'
        geturl = (package.documentation.url.rstrip('/') + '/logics/%s.html').__mod__
        for category, group in registry.grouped().items():
            for logic in group:
                name = logic.Meta.name
                yield f'[{name}]: {geturl(name.lower())}'

if __name__ == '__main__':
    main(*sys.argv[1:])
