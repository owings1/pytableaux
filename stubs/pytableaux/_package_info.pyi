import typing

class SemVer(typing.NamedTuple):
    major: int
    minor: int
    patch: int
    release: str
    @property
    def short(self): ...
    @property
    def display(self): ...
    @property
    def full(self): ...

class package:
    name: str
    version: SemVer
    author: object
    license: object
    repository: object
    issues: object
    class author:
        name: str
        email: str
    class license:
        id: str
        title: str
        url: str
    class repository:
        type: str
        url: str
    class issues:
        url: str
    year: int
    copyright: str
    root: str
    docformat: str
