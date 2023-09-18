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
"""

"""
from __future__ import annotations

import logging
import os
import re
import threading
import traceback
from collections import deque
from itertools import product
from os.path import abspath
from typing import TYPE_CHECKING, Callable, Iterator

if TYPE_CHECKING:
    from PIL import Image

def readlist(s: str, /, *, sep=','):
    return filter(None, map(str.strip, s.split(sep)))

def make_queue_workers(queue: deque, threadcount: int, func: Callable, *args, **kw):
    return tuple(
        threading.Thread(
            name=f'Worker-{i + 1}',
            target=queue_worker,
            args=(queue, func, *args),
            kwargs=kw)
        for i in range(min(threadcount, len(queue))))

def queue_worker(queue: deque, func: Callable, *args, **kw):
    logger = logging.getLogger(threading.current_thread().name)
    while True:
        try:
            item = queue.popleft()
        except IndexError:
            break
        logger.info(f'Processing {item}')
        try:
            func(item, *args, **kw)
        except:
            traceback.print_exc()
            logger.warning(f'Failed to process: {item}')

def resolve_srcfiles(srcdir: str, srcext: str, outdir: str, outext: str, incremental: bool):
    srcpat, srcout = (
        re.compile(r'(.+)\.'f'{re.escape(ext)}$')
        for ext in (srcext, outext))
    if incremental:
        ignore = frozenset(filter(srcout.match, os.listdir(outdir)))
    else:
        ignore = frozenset()
    outrepl = r'\1.'f'{outext}'
    return {
        abspath(f'{srcdir}/{srcname}'): abspath(f'{outdir}/{outname}')
        for srcname, outname in (
            (name, srcpat.sub(outrepl, name))
            for name in sorted(
                filter(srcpat.match, os.listdir(srcdir)),
                key=str.lower)) 
        if outname not in ignore}

def autocrop(image: Image.Image, /, **kw) -> Image.Image:
    return image.crop(tuple(findbox(image, **kw)))

def findbox(image: Image.Image, /, *, margin: int = 1) -> Iterator[int]:
    margin += 1
    H = range(image.height)
    W = range(image.width)
    BLANK = 255
    get = image.getpixel
    # left
    for x, y in product(W, H):
        if get((x, y)) != BLANK:
            yield max(0, x - margin)
            break
    # upper
    for y, x in product(H, W):
        if get((x, y)) != BLANK:
            yield max(0, y - margin)
            break
    # right
    for x, y in product(reversed(W), H):
        if get((x, y)) != BLANK:
            yield min(x + margin, image.width - 1)
            break
    # lower
    for y, x in product(reversed(H), W):
        if get((x, y)) != BLANK:
            yield min(y + margin, image.height - 1)
            break
