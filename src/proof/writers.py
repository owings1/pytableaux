from lexicals import create_lexwriter
from errors import BadArgumentError
from fixed import default_notation
from os import path

templates_dir = path.join(path.dirname(path.abspath(__file__)), 'templates')

def create_tabwriter(notn=None, format=None, **opts):
    if not notn:
        notn = default_notation
    if not format:
        format = 'ascii'
    lw = create_lexwriter(notn=notn, format=format, **opts)
    if format == 'html':
        return HtmlTableauWriter(lw, **opts)
    raise ValueError('Unknown output format: {0}'.format(str(format)))

class TableauWriter(object):

    def __init__(self, lw, **opts):
        # Extra check during refactor
        if not callable(getattr(lw, 'write', None)):
            raise TypeError('lw has no write method')
        self.opts = opts
        self.lw = lw

    def document_header(self):
        return ''

    def document_footer(self):
        return ''

    def write(self, tableau):
        return self._write_tableau(tableau)

    def _write_tableau(self, tableau, sw, opts):
        raise NotImplementedError()

def create_tabwriter(notn=None, format=None, **opts):
    if not notn:
        notn = default_notation
    if not format:
        format = 'ascii'
    if 'lw' not in opts:
        lwopts = {}
        if 'enc' not in opts and format == 'html':
            lwopts['enc'] = 'html'
        opts['lw'] = create_lexwriter(notn=notn, **lwopts, **opts)
    if format == 'html':
        return HtmlTableauWriter(**opts)
    raise BadArgumentError('Unknown output format: {0}'.format(str(format)))

class HtmlTableauWriter(TableauWriter):

    name = 'HTML'

    @staticmethod
    def _get_template(file):
        if not getattr(HtmlTableauWriter, 'jenv', False):
            from jinja2 import Environment, FileSystemLoader
            HtmlTableauWriter.jenv = Environment(
                loader = FileSystemLoader(path.join(templates_dir, 'html')),
                trim_blocks = True,
                lstrip_blocks = True,
            )
        return HtmlTableauWriter.jenv.get_template(file)

    __defaults = {}

    def __init__(self, *args, **kw):
        super().__init__(*args, **self.__defaults, **kw)

    def get_template(self, file):
        return HtmlTableauWriter._get_template(file)

    def _write_tableau(self, tableau):
        lw = self.lw
        if tableau.argument:
            premises = [lw.write(premise) for premise in tableau.argument.premises]
            conclusion = lw.write(tableau.argument.conclusion)
        else:
            premises = None
            conclusion = None
        return self.get_template('proof.html').render({
            'tableau'    : tableau,
            'lw'         : lw,
            'opts'       : self.opts,
            'premises'   : premises,
            'conclusion' : conclusion,
        })