from typing import Any, ClassVar, Mapping, overload

from pytableaux.lang import (LangCommonMeta, Lexical, LexType, Notation,
                             RenderSet)


class LexWriterMeta(LangCommonMeta):...
class LexWriter(metaclass=LexWriterMeta):
    notation: ClassVar[Notation]
    defaults: ClassVar[dict[str, Any]]
    renderset: RenderSet
    opts: dict[str, Any]
    _methodmap: ClassVar[Mapping[LexType, str]]
    @property
    def charset(self) -> str: ...
    def write(self, item: Lexical) -> str: ...
    def __call__(self, item: Lexical) -> str: ...
    @classmethod
    def canwrite(cls, obj: Any) -> bool: ...
    def __init__(self, notn: Notation|str = ..., /, charset: str = ..., renderset: RenderSet = ..., **opts) -> None: ...
    @classmethod
    def register(cls, subcls: type[LexWriter]): ...
    def __init_subclass__(subcls: type[LexWriter], **kw): ...
    def _test(self) -> list[str]:...
class BaseLexWriter(LexWriter):
    def __init__(self, charset: str = ..., renderset: RenderSet = ..., **opts) -> None: ...

class PolishLexWriter(BaseLexWriter):...

class StandardLexWriter(BaseLexWriter):...
