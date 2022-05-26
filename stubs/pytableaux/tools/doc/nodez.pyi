from __future__ import annotations
from typing import Any, NamedTuple, overload

from pytableaux.lang import Notation
import docutils
from docutils import nodes
from docutils.nodes import Element

import sphinx.addnodes
import sphinx.application
import sphinx.writers.html5
import docutils.writers._html_base

class BaseTranslator(sphinx.writers.html5.HTML5Translator, docutils.writers._html_base.HTMLTranslator, nodes.NodeVisitor):
    # body: list[str]
    document: sphinx.addnodes.document
class HTML5Translator(BaseTranslator):
    class OptStacks(NamedTuple):
        notn: list[tuple[Element, Notation|str]]
        charset: list[tuple[Element, str]]

    def visit_block(self, node: Element) -> None: ...
    def depart_block(self, node: Element) -> None: ...
    def visit_sentence(self, node: Element) -> None: ...
    def depart_sentence(self, node: Element) -> None: ...
    def get_lwargs(self, node: Element) -> tuple[Notation|str, str]: ...
def setup(app: sphinx.application.Sphinx) -> None:...


class sentence(nodes.Inline, nodes.TextElement): ...
class block(Element):...

