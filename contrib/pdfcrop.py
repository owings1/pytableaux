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
import tempfile
from itertools import product
from typing import Iterator

from pdf2image import convert_from_path
from PIL import Image


def readpdf(file: str) -> Image.Image:
    with tempfile.TemporaryDirectory() as path:
        image, = convert_from_path(file, output_folder=path, grayscale=True)
    return image

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

if __name__ == '__main__':
    src, dest = sys.argv[1:]
    autocrop(readpdf(src)).save(dest)
