from enum import Enum

from _typeshed import Incomplete
from sphinx.application import Sphinx
from sphinx.util.docutils import ReferenceRole

from pytableaux.tools.doc import BaseRole, ParserOptionMixin

class refplus(ReferenceRole, BaseRole):
    section: str
    anchor: str
    logicname: str
    lrmatch: Incomplete
    refdomain: str
    reftype: str
    warn_dangling: bool
    options: Incomplete
    def __init__(self) -> None: ...
    classes: Incomplete
    def run(self): ...
    patterns: Incomplete

class _Ctype(frozenset, Enum):
    valued: Incomplete
    nosent: Incomplete

class lexdress(BaseRole, ParserOptionMixin):
    option_spec: Incomplete
    opt_defaults: Incomplete
    def run(self): ...

class metadress(BaseRole):
    prefixes: Incomplete
    modes: Incomplete
    generic: Incomplete
    patterns: Incomplete
    def __init__(self, **_) -> None: ...
    def run(self): ...
    @classmethod
    def logicname_node(cls, name: str): ...

# Names in __all__ with no definition:
#   refpost
def setup(app: Sphinx)-> None:...
