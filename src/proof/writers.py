from __future__ import annotations

__all__ = (
    'TabWriter',
)

from errors import Emsg, instcheck
from tools.abcs import abstract, overload, abcf, abcm, AbcMeta, MapProxy, TT
from tools.misc import cat
from lexicals import Argument, LexWriter, Notation
from proof.tableaux import TabStatKey, TabFlag, Tableau

from jinja2 import Environment, FileSystemLoader, Template
from os import path
from typing import Any, ClassVar, Mapping

class TabWriterMeta(AbcMeta):
    def __call__(cls, *args, **kw):
        if cls is TabWriter:
            if args:
                fmt, *args = args
            else:
                fmt = TabWriter.DefaultFormat
            return TabWriter.Registry[fmt](*args, **kw)
        return super().__call__(*args, **kw)

class TabWriter(metaclass = TabWriterMeta):

    Registry: ClassVar[Mapping[str, type[TabWriter]]]
    DefaultFormat = 'text'

    format: ClassVar[str]
    name: ClassVar[str]
    default_charsets: ClassVar[Mapping[Notation, str]]
    defaults: Mapping[str, Any] = MapProxy()

    lw: LexWriter
    opts: dict[str, Any]

    def __init__(self, notn: Notation|str = None, charset: str = None, *, lw: LexWriter = None, **opts):
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
                if Notation(notn) != lw.notation:
                    raise Emsg.ValueConflict(notn, lw.notation)
            if charset is not None:
                if charset != lw.charset:
                    raise Emsg.ValueConflict(charset, lw.charset)
            instcheck(lw, LexWriter)
        self.lw = lw
        self.opts = dict(self.defaults) | opts

    def document_header(self):
        return ''

    def document_footer(self):
        return ''

    def attachments(self, tableau: Tableau, /) -> Mapping[str, Any]:
        return {}

    def write(self, tableau: Tableau, /):
        return self._write_tableau(tableau)

    __call__ = write

    @abstract
    def _write_tableau(self, tableau: Tableau, /):
        raise NotImplementedError

    @classmethod
    @overload
    def register(cls, subcls: TT) -> TT: ...

    @abcf.before
    def prepare(ns: dict, bases):

        _registry: dict[str, type[TabWriter]] = {}

        def register(cls: type[TabWriter], subcls: type[TabWriter]):
            'Update available writers.'
            if not issubclass(subcls, __class__):
                raise TypeError(subcls, __class__)
            if abcm.isabstract(subcls):
                raise TypeError('Cannot register abstract class: %s' % subcls)
            fmt = subcls.format
            if fmt in _registry:
                raise TypeError(
                    "%s format '%s' already registered" % (__class__.__name__, fmt)
                )
            _registry[fmt] = subcls
            type(cls).register(cls, subcls)
            return subcls

        ns.update(
            Registry = MapProxy(_registry),
            register = classmethod(register),
        )

class TemplateWriter(TabWriter):

    base_dir = path.join(path.dirname(path.abspath(__file__)), 'templates')
    path_prefix = ''
    proof_template = 'proof.jinja2'
    jinja_opts = {}
    template_dir: str

    def __init__(self, *args, **kw):
        super().__init__(*args, **kw)
        dir = path.join(self.base_dir, self.path_prefix)
        if getattr(self, 'template_dir', None) is None:
            self.template_dir = dir
        jopts = dict(self.jinja_opts)
        if 'loader' not in jopts:
            jopts['loader'] = FileSystemLoader(dir)
        self.jenv = Environment(**jopts)

    def get_template(self, template: str) -> Template:
        return self.jenv.get_template(template)

    def render(self, template: str, context: dict = {}) -> str:
        return self.get_template(template).render(context)

    def get_argstrs(self, arg: Argument, /) -> tuple[tuple[str, ...], str]:
        if not arg:
            return (None, None)
        lw = self.lw
        return tuple(map(lw, arg.premises)), lw(arg.conclusion)

    def get_context(self, tableau: Tableau, /):
        premises, conclusion = self.get_argstrs(tableau.argument)
        return dict(
            tableau    = tableau,
            stats      = tableau.stats,
            logic      = tableau.logic,
            argument   = tableau.argument,
            premises   = premises,
            conclusion = conclusion,
            lw         = self.lw,
            opts       = self.opts,
            TabStatKey = TabStatKey,
            TabFlag    = TabFlag,
        )

    def _write_tableau(self, tableau: Tableau, /):
        return self.render(self.proof_template, self.get_context(tableau))

@TabWriter.register
class HtmlTabWriter(TemplateWriter):

    format = 'html'
    name = 'HTML'
    default_charsets = {notn: 'html' for notn in Notation}
    defaults = dict(
        classes      = (),
        wrap_classes = (),
        inline_css   = False,
    )

    path_prefix = 'html'
    jinja_opts = dict(
        trim_blocks   = True,
        lstrip_blocks = True,
    )

    def attachments(self, tableau: Tableau, /):
        with open(path.join(self.template_dir, 'static/tableau.css'), 'r') as f:
            return dict(css = f.read())

    # classes:
    #   wrapper : tableau-wrapper
    #      tableau : tableau
    #        structure : structure [, root, has-open, has-closed, leaf, only-branch, closed, open]
    #          node-segment : node-sement
    #             vertical-line : vertical-line
    #             horizontal-line : horizontal-line
    #                node : node [, ticked]
    #                   node-props : node-props [, ticked]
    #                        inline : [sentence, world, designation, designated, undesignated, world1,
    #                                   world2, access, ellipsis, flag, <flag>]
    #                   
    #               
    #   misc : clear
    #
    #

@TabWriter.register
class TextTabWriter(TemplateWriter):

    format = 'text'
    name = 'Text'
    default_charsets = {notn: notn.default_charset for notn in Notation}
    defaults = dict(
        summary  = True,
        argument = True,
        heading  = True,
    )

    path_prefix = 'text'
    jinja_opts = dict(
        trim_blocks   = True,
        lstrip_blocks = True,
    )

    def _write_tableau(self, tableau: Tableau, /):
        strs = []
        opts = self.opts
        context = self.get_context(tableau)
        if opts['summary']:
            strs.append(self.render('summary.jinja2', context))
        if opts['heading']:
            strs.append(self.render('heading.jinja2', context))
        strs.append(self._write_structure(tableau.tree))
        return '\n'.join(strs)

    def _write_structure(self, structure, prefix: str = ''):
        nodestr = self.render('nodes.jinja2', dict(
            structure = structure,
            lw        = self.lw
        ))
        lines = [cat(prefix, nodestr)]
        children = structure['children']
        prefix += (' ' * (len(nodestr) - 1))
        for c, child in enumerate(children):
            is_last = c == len(children) - 1
            next_pfx = cat(prefix, ' ' if is_last else '|')
            lines.append(self._write_structure(child, prefix = next_pfx))
            if not is_last:
                lines.append(next_pfx)
        return '\n'.join(lines)
