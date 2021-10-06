from lexicals import create_lexwriter, default_notation, default_notn_encs
from utils import cat

from os import path
from copy import deepcopy

from jinja2 import Environment, FileSystemLoader

formats = ('text', 'html')
default_format = 'text'
default_format_notn_encs = {
    'text' : default_notn_encs,
    'html' : {'polish': 'html', 'standard': 'html'},
}

def write_tableau(tableau, *args, **kw):
    return create_tabwriter(*args, **kw).write(tableau)

def create_tabwriter(notn=None, format=None, **opts):
    if not notn:
        notn = default_notation
    if not format:
        format = default_format
    if 'lw' not in opts:
        lwopts = {}
        if 'enc' not in opts:
            defencs = default_format_notn_encs.get(format)
            if defencs and notn in defencs:
                lwopts['enc'] = defencs[notn]
            else:
                lwopts['enc'] = default_notn_encs[notn]
        opts['lw'] = create_lexwriter(notn=notn, **lwopts, **opts)
    if format == 'html':
        return HtmlTableauWriter(**opts)
    elif format == 'text':
        return TextTableauWriter(**opts)
    raise ValueError('Unknown output format: {0}'.format(str(format)))

class TableauWriter(object):

    defaults = {}

    def __init__(self, lw, **opts):
        if not callable(getattr(lw, 'write', None)):
            raise TypeError('lw has no write method')
        self.opts = deepcopy(self.defaults)
        self.opts.update(opts)
        self.lw = lw

    def document_header(self):
        return ''

    def document_footer(self):
        return ''

    def attachments(self, tableau):
        return {}

    def write(self, tableau):
        return self._write_tableau(tableau)

    def _write_tableau(self, tableau):
        raise NotImplementedError()

templates_basedir = path.join(path.dirname(path.abspath(__file__)), 'templates')

class TemplateWriter(TableauWriter):

    base_dir = path.join(path.dirname(path.abspath(__file__)), 'templates')
    path_prefix = ''
    proof_template = 'proof.jinja2'
    jinja_opts = {}

    def __init__(self, *args, **kw):
        super().__init__(*args, **kw)
        dir = path.join(self.base_dir, self.path_prefix)
        if not getattr(self, 'template_dir', None):
            self.template_dir = dir
        jopts = dict(self.jinja_opts)
        if 'loader' not in jopts:
            jopts['loader'] = FileSystemLoader(dir)
        self.jenv = Environment(**jopts)

    def get_template(self, template):
        return self.jenv.get_template(template)

    def render(self, template, context={}):
        return self.get_template(template).render(context)

    def get_argstrs(self, argument):
        if not argument:
            return (None, None)
        lw = self.lw
        return (
            [lw.write(premise) for premise in argument.premises],
            lw.write(argument.conclusion)
        )

    def get_context(self, tableau):
        premises, conclusion = self.get_argstrs(tableau.argument)
        return {
            'tableau'    : tableau,
            'stats'      : tableau.stats,
            'logic'      : tableau.logic,
            'argument'   : tableau.argument,
            'premises'   : premises,
            'conclusion' : conclusion,
            'lw'         : self.lw,
            'opts'       : self.opts,
        }

    def _write_tableau(self, tableau):
        return self.render(self.proof_template, self.get_context(tableau))

class HtmlTableauWriter(TemplateWriter):

    name = 'HTML'
    format = 'html'
    defaults = {
        'classes'      : [],
        'wrap_classes' : [],
        'inline_css'   : False,
    }

    path_prefix = 'html'
    jinja_opts = {
        'trim_blocks'   : True,
        'lstrip_blocks' : True,
    }

    def attachments(self, *_a, **_k):
        with open(path.join(self.template_dir, 'static/tableau.css'), 'r') as f:
            return {'css': f.read()}
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
class TextTableauWriter(TemplateWriter):

    name = 'Text'
    format = 'text'
    defaults = {
        'summary'  : True,
        'argument' : True,
        'heading'  : True,
    }

    path_prefix = 'text'
    jinja_opts = {
        'trim_blocks'   : True,
        'lstrip_blocks' : True,
    }

    def _write_tableau(self, tableau):
        strs = []
        opts = self.opts
        context = self.get_context(tableau)
        if opts['summary']:
            strs.append(self.render('summary.jinja2', context))
        if opts['heading']:
            strs.append(self.render('heading.jinja2', context))
        strs.append(self._write_structure(tableau.tree))
        return '\n'.join(strs)

    def _write_structure(self, structure, prefix = ''):
        nodestr = self.render('nodes.jinja2', {
            'structure' : structure,
            'lw'        : self.lw
        })
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
