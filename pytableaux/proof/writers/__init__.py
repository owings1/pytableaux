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
from typing import TYPE_CHECKING, Callable, MutableMapping, Self, TypeVar

from ...errors import Emsg, check
from ...lang import LexWriter, Notation, StringTable
from ...tools import EMPTY_MAP, MapCover, abcs
from ..tableaux import Tableau

if TYPE_CHECKING:
    from typing import overload

NOARG = object()
_T = TypeVar('_T')
_TWT = TypeVar('_TWT', bound='TabWriter')

__all__ = (
    'registries',
    'registry',
    'TabWriter',
    'TabWriterRegistry')

class TabWriterMeta(abcs.AbcMeta):

    def __call__(cls: type[_T]|Self, *args, **kw) -> _T:
        if cls is not TabWriter:
            return super().__call__(*args, **kw)
        try:
            reg = registries['default']
        except KeyError:
            reg = registry
        if args:
            fmt, *args = args
        elif 'format' in kw:
            fmt = kw.pop('format')
        else:
            return reg.default(*args, **kw)
        try:
            reg[fmt]
        except KeyError:
            for reg in registries.values():
                if fmt in reg:
                    break
            else:
                raise
        return reg[fmt](*args, **kw)

class TabWriter(metaclass=TabWriterMeta):
    """Tableau writer base class.

    Constructing a ``TabWriter``.

    Examples::

    >>> # make an instance of the default writer class, with the default notation.
    >>> writer = TabWriter()

    >>> # make an HtmlTabWriter, with the default notation.
    >>> writer = TabWriter('html')

    >>> # make an HtmlTabWriter, with standard notation.
    >>> writer = TabWriter('html', 'standard')
    """

    engine: str = 'unknown'
    "The writer engine (jinja, doctree, etc.)"

    format: str
    "The format registry identifier."

    file_extension: str
    "The file extension for output files."

    defaults = EMPTY_MAP
    "Default options."

    lw: LexWriter
    "The writer's `LexWriter` instance."

    opts: dict
    "The writer's options."

    __slots__ = ('lw', 'opts')

    def __init__(self, notation: Notation = None, strings: StringTable|None = None, *, lw: LexWriter = None, **opts):
        """__init__(self, format: str|None = None, notation: Notation = None, strings: StringTable|None = None, *, lw: LexWriter = None, **opts)
        Create a TabWriter

        Args:
            format (str): The format, e.g. 'html', 'latex'
            notation (str|Notation): The notation
            strings (StringTable): A specific string table to use
        
        Keyword Args:
            lw (LexWriter): A specific LexWriter to use
            **opts: Options to pass to the TabWriter
        """
        if lw is None:
            if notation is None:
                notation = LexWriter.DEFAULT_NOTATION
            else:
                notation = Notation(notation)
            lw = LexWriter(notation=notation, format=self.format, strings=strings, **opts)
        elif lw.format != self.format or strings is not None and strings.format != self.format:
            raise Emsg.ValueConflict(lw.format, self.format)
        self.lw = lw
        self.opts = dict(self.defaults) | opts

    def attachments(self, /):
        return EMPTY_MAP

    @abstractmethod
    def __call__(self, tab: Tableau, **kw) -> str:
        raise NotImplementedError

    def __init_subclass__(cls) -> None:
        super().__init_subclass__()
        try:
            cls.file_extension
        except AttributeError:
            try:
                cls.file_extension = cls.format
            except AttributeError:
                pass

class TabWriterRegistry(MapCover[str, type[TabWriter]], MutableMapping[str, type[TabWriter]]):
    "A tableau writer class registry."

    __slots__ = ('default', 'name', 'register', '__delitem__')

    name: str|None
    default: type[TabWriter]|None

    def __init__(self, *, name: str|None = None):
        super().__init__(mapping := {})
        self.name = name
        self.default = None
        def register(cls=NOARG, /, *, key=None, force=False, default=None):
            if cls is NOARG:
                return lambda cls: register(cls, key=key, force=force, default=default)
            if abcs.isabstract(cls := check.subcls(cls, TabWriter)):
                raise TypeError(f'Cannot register abstract class: {cls}')
            if key is None:
                key = cls.format
            if not force and key in self:
                raise KeyError(f"Format/key {key} already registered")
            mapping[check.inst(key, str)] = cls
            if default or default is None and not self.default:
                self.default = cls
            return cls
        self.register = register
        self.__delitem__ = mapping.__delitem__

    def __setitem__(self, key, value):
        self.register(value, key=key, force=True)

    if TYPE_CHECKING:
        @overload
        def register(self, cls:type[_TWT], /, *, key:str=..., force:bool=..., default:bool|None=...) -> type[_TWT]:
            """Register a ``TabWriter`` class. Returns the argument, so it can be
            used as a decorator.

            Args:
                cls: The writer class.

            Keyword Args:
                key: An alternate key to store, default is the writer's format.
                force: Replace format/key if exists, default False.
                default: Set as default writer.

            Returns:
                The writer class.
            """
        @overload
        def register(self, /, *, key:str=..., force:bool=..., default:bool|None=...) -> Callable[[type[_TWT]], type[_TWT]]:
            """Decorator factory for registering with options.

            Keyword Args:
                key: An alternate key to store, default is the writer's format.
                force: Replace format/key if exists.
                default: Set as default writer.
            
            Returns:
                Class decorator.
            """

registry = TabWriterRegistry(name='default')
"The default tableau writer class registry."

registries = {registry.name: registry}

try:
    from . import jinja as jinja
except ImportError:
    import traceback
    import warnings
    traceback.print_exc()
    warnings.warn('Failed to import jinja')
else:
    registries[jinja.registry.name] = jinja.registry
    registry.update(jinja.registry)

from . import doctree

registries[doctree.registry.name] = doctree.registry
registry.update(doctree.registry)
registry.default = doctree.registry.default
