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
pytableaux.proof.writers
========================

"""
from __future__ import annotations

from abc import abstractmethod
from types import MappingProxyType as MapProxy
from typing import TYPE_CHECKING, Callable, MutableMapping, Self, TypeVar

from ... import __docformat__
from ...errors import Emsg, check
from ...lang import LexWriter, Notation
from ...tools import EMPTY_MAP,  MapCover, abcs
from ..tableaux import Tableau
from .nodes import Node

NOARG = object()
_T = TypeVar('_T')
_TWT = TypeVar('_TWT', bound='TabWriter')
_NT = TypeVar('_NT', bound='Node')

if TYPE_CHECKING:
    from typing import overload

__all__ = (
    'registry',
    'TabWriter',
    'TabWriterRegistry')

class TabWriterMeta(abcs.AbcMeta):

    DefaultFormat = 'text'

    def __call__(cls: type[_T]|Self, *args, **kw) -> _T:
        if cls is TabWriter:
            if args:
                fmt, *args = args
            else:
                fmt = cls.DefaultFormat
            return registry[fmt](*args, **kw)
        return super().__call__(*args, **kw)

class TabWriter(metaclass = TabWriterMeta):
    """Tableau writer base class.

    Constructing a ``TabWriter``.

    Examples::

        # make an instance of the default writer class, with the default notation.
        writer = TabWriter()

        # make an HtmlTabWriter, with the default notation and charset.
        writer = TabWriter('html')

        # make an HtmlTabWriter, with standard notation and ASCII charset.
        writer = TabWriter('html', 'standard', 'ascii')
    """

    format: str
    "The format registry identifier."

    default_charsets = MapProxy({
        notn: notn.default_charset for notn in Notation})
    "Default ``LexWriter`` charset for each notation."

    defaults = EMPTY_MAP
    "Default options."

    lw: LexWriter
    "The writer's `LexWriter` instance."

    opts: dict
    "The writer's options."

    __slots__ = ('lw', 'opts')

    def __init__(self, notn = None, charset = None, *, lw: LexWriter = None, **opts):
        if lw is None:
            if notn is None:
                notn = Notation.default
            else:
                notn = Notation(notn)
            if charset is None:
                charset = self.default_charsets[notn]
            lw = LexWriter(notn, charset, **opts)
        else:
            if notn is not None:
                if Notation(notn) is not lw.notation:
                    raise Emsg.ValueConflict(notn, lw.notation)
            if charset is not None:
                if charset != lw.charset:
                    raise Emsg.ValueConflict(charset, lw.charset)
        self.lw = lw
        self.opts = dict(self.defaults) | opts

    def attachments(self, /):
        return EMPTY_MAP

    @abstractmethod
    def __call__(self, tab: Tableau, **kw) -> str:
        raise NotImplementedError


class TabWriterRegistry(MapCover[str, type[TabWriter]], MutableMapping[str, type[TabWriter]]):
    "A tableau writer class registry."

    __slots__ = ('register', '__delitem__')

    def __init__(self):
        super().__init__(mapping := {})
        def register(cls=NOARG, /, *, key=None, force=False):
            if cls is NOARG:
                return lambda cls: register(cls, key=key, force=force)
            if abcs.isabstract(cls := check.subcls(cls, TabWriter)):
                raise TypeError(f'Cannot register abstract class: {cls}')
            if key is None:
                key = cls.format
            if not force and key in self:
                raise KeyError(f"Format/key {key} already registered")
            mapping[check.inst(key, str)] = cls
            return cls
        self.register = register
        self.__delitem__ = mapping.__delitem__

    def __setitem__(self, key, value):
        self.register(value, key=key, force=True)

    if TYPE_CHECKING:
        @overload
        def register(self, cls: type[_TWT], /, *, key: str = ..., force: bool = ...) -> type[_TWT]:
            """Register a ``TabWriter`` class. Returns the argument, so it can be
            used as a decorator.

            Args:
                cls: The writer class.

            Kwargs:
                force: Replace format/key if exists, default False.
                key: An alternate key to store, default is the writer's format.
            
            Returns:
                The writer class.
            """
        @overload
        def register(self, /, *, key: str = ..., force: bool = ...) -> Callable[[type[_TWT]], type[_TWT]]:
            """Decorator factory for registering with options.

            Kwargs:
                force: Replace format/key if exists.
                key: An alternate key to store, default is the writer's format.
            
            Returns:
                Class decorator factory.
            """

registry = TabWriterRegistry()
"The default tableau writer class registry."

from . import doctree, jinja

registry.update(jinja.registry)

