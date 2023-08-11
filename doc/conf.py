# -*- coding: utf-8 -*-
#
# pytableaux documentation build configuration file, created by
# sphinx-quickstart on Sat Mar  1 22:48:49 2014.

# If extensions (or modules to document with autodoc) are in another directory,
# add these directories to sys.path here. If the directory is relative to the
# documentation root, use os.path.abspath to make it absolute, like shown here.
from __future__ import annotations

import os
import sys

from sphinx.application import Sphinx

os.environ['DOC_MODE'] = 'True'

# =================================================================================
# =================================================================================

_dir = os.path.abspath(os.path.dirname(__file__))
if _dir not in sys.path:
    sys.path.insert(1, _dir)

addpath = os.path.abspath(os.path.join(_dir, '..'))
if addpath not in sys.path:
    sys.path.insert(1, addpath)
# General information about the project.

from pytableaux import package

project = package.name
# The version info for the project you're documenting, acts as replacement for
# |version| and |release|, also used in various other places throughout the
# built documents.
#
# The short X.Y version.
version = package.version.short
# The full version, including alpha/beta/rc tags.
release = package.version.full
copyright = package.copyright

# =================================================================================
# =================================================================================

# Add any Sphinx extension module names here, as strings. They can be
# extensions coming with Sphinx (named 'sphinx.ext.*') or your custom
# ones.
extensions = [
    'sphinx.ext.napoleon',
    'sphinx.ext.doctest',
    'sphinx.ext.viewcode',
    'sphinx.ext.autodoc',
    'sphinx.ext.intersphinx',
    # 'sphinx_sitemap',
    # 'sphinx_toolbox.more_autodoc.overloads',
    'pytabdoc']

# =================================================================================
# =================================================================================


# sphinx.ext.napoleon
# -------------------
# https://www.sphinx-doc.org/en/master/usage/extensions/napoleon.html#configuration

napoleon_numpy_docstring = False
"We don't use the numpy format"

napoleon_preprocess_types = True
napoleon_attr_annotations = True
napoleon_type_aliases = {

}

# sphinx.ext.autodoc
# ------------------
# https://www.sphinx-doc.org/en/master/usage/extensions/autodoc.html


# autodoc_class_signature = 'separated'

# Note: Turning this off keeps overriden members from showing up if
#       they do not have a docstring.
autodoc_inherit_docstrings = False
"""
This value controls the docstrings inheritance. If set to True the
docstring for classes or methods, if not explicitly set, is inherited
from parents.

The default is True.
"""

autodoc_typehints = 'description'
"""
This value controls how to represent typehints. The setting takes the
following values:

* 'signature' - Show typehints in the signature (default)

* 'description' - Show typehints as content of the function or method.
    The typehints of overloaded functions or methods will still be
    represented in the signature.

* 'none' - Do not show typehints

* 'both' - Show typehints in the signature and as content of the
    function or method.

Overloaded functions or methods will not have typehints included in
the description because it is impossible to accurately represent all
possible overloads as a list of parameters.
"""

autodoc_typehints_format = 'short'
"""
This value controls the format of typehints. The setting takes the
following values:

  * 'fully-qualified' - Show the module name and its name of typehints

  * 'short' - Suppress the leading module names of the typehints
     (ex. io.StringIO -> StringIO) (default)

New in version 4.4.

Changed in version 5.0: The default setting was changed to 'short'
"""


autodoc_docstring_signature = True
"""
Functions imported from C modules cannot be introspected, and therefore the
signature for such functions cannot be automatically determined. However, it is
an often-used convention to put the signature into the first line of the
function's docstring.

If this boolean value is set to True (which is the default), autodoc will look
at the first line of the docstring for functions and methods, and if it looks
like a signature, use the line as the signature and remove it from the
docstring content.

autodoc will continue to look for multiple signature lines, stopping at the
first line that does not look like a signature. This is useful for declaring
overloaded function signatures.

New in version 1.1.

Changed in version 3.1: Support overloaded signatures

Changed in version 4.0: Overloaded signatures do not need to be separated by a backslash
"""


autodoc_member_order = 'bysource' # 'groupwise'

auto_skip_enum_value = True

autodoc_default_options = {
    'exclude-members': 'for_json',
    # 'no-value': True,
    # 'special-members': '__init__',

    # For modules, __all__ will be respected when looking for members
    # unless you give the ignore-module-all flag option.
    # Without ignore-module-all, the order of the members will also
    # be the order in __all__.
    'ignore-module-all': True}


# sphinx_toolbox.more_autodoc.overloads
# -------------------------------------
# https://sphinx-toolbox.readthedocs.io/en/latest/extensions/more_autodoc/overloads.html

overloads_location = [
    'signature',
    'top',
    'bottom'][ 2 ]


# pytableaux.tools.doc
# --------------------

copy_file_tree = [
    (
        f'{package.root}/web/static/css/fonts/charmonman',
        '_static/fonts/charmonman')]

delete_file_tree = [
    '_modules']

# sphinx.ext.intersphinx
# ----------------------
# https://www.sphinx-doc.org/en/master/usage/extensions/intersphinx.html

intersphinx_mapping = dict(
    python = (
        'https://docs.python.org/3',
        # local cache of https://docs.python.org/3/objects.inv
        os.environ.get('ISPX_PY3_OBJINV')))



# -------------------
# -  Prolog/Epilog
# -------------------
#
# https://www.sphinx-doc.org/en/master/usage/configuration.html#confval-rst_prolog
#
#
rst_epilog = """
.. |[+]| unicode:: 0x2295
.. |[-]| unicode:: 0x2296
.. |(x)| unicode:: 0x2297
"""


rst_prolog = """
.. testsetup:: *

    from pytableaux.lang import *
    from pytableaux.proof import *
    from pytableaux.logics import registry
"""

# -------------------
# -  Smartquote
# -------------------
# 
# https://docutils.sourceforge.io/docs/user/smartquotes.html
# https://www.sphinx-doc.org/en/master/usage/configuration.html#confval-smartquotes
#
#

smartquotes = False

# -------------------
# -  HTML
# -------------------
# 
# https://github.com/readthedocs/sphinx_rtd_theme
# 

html_theme = 'sphinx_rtd_theme' # 'default'

# Theme options are theme-specific and customize the look and feel of a theme
# further.  For a list of options available for each theme, see the
# documentation.
html_theme_options = {}

if html_theme == 'sphinx_rtd_theme':
    # https://sphinx-rtd-theme.readthedocs.io/en/stable/configuring.html
    html_theme_options.update(
        # style_external_links = True,
    )

# Others tried: material, xcode
pygments_style = 'colorful'

# If true, "Created using Sphinx" is shown in the HTML footer. Default is True.
html_show_sphinx = False

# Add any paths that contain custom static files (such as style sheets) here,
# relative to this directory. They are copied after the builtin static files,
# so a file named "default.css" will overwrite the builtin "default.css".
html_static_path = [
    '_static',
    f'{package.root}/proof/writers/templates/html/static',
]

# Output file base name for HTML help builder.
htmlhelp_basename = 'pytableauxdoc'

# If false, no module index is generated.
html_domain_indices = False

# -------------------
# -  Sitemap
# -------------------
# 
# https://sphinx-sitemap.readthedocs.io/en/latest/getting-started.html
# 
html_baseurl = os.getenv('DOC_BASEURL', 'https://logic.dougowings.net/doc/')
sitemap_url_scheme = "{link}"

# =================================================================================
# =================================================================================


# List of patterns, relative to source directory, that match files and
# directories to ignore when looking for source files.
exclude_patterns = [
    '_build',
    'node_modules',
    '**/include/*',
]

# Add any paths that contain templates here, relative to this directory.
templates_path = ['_templates']

# The suffix of source filenames.
source_suffix = '.rst'

# The master toctree document.
master_doc = 'index'


# If true, the current module name will be prepended to all description
# unit titles (such as .. function::).
add_module_names = False


cssflag = {
    'doc.css'         : True,
    'doc.default.css' : html_theme == 'default',
    'doc.rtd.css'     : html_theme == 'sphinx_rtd_theme',
    'tableau.css'     : True,
}

exclude_patterns.extend(file
    for file, flag in cssflag.items()
        if not flag)

def setup(app: Sphinx):
    for file, flag in cssflag.items():
        if flag:
            app.add_css_file(file)

if False:
    pass
    # -------------------------------------------------------------------
    # The encoding of source files.
    #source_encoding = 'utf-8-sig'

    # The language for content autogenerated by Sphinx. Refer to documentation
    # for a list of supported languages.
    #language = None

    # There are two options for replacing |today|: either, you set today to some
    # non-false value, then it is used:
    #today = ''
    # Else, today_fmt is used as the format for a strftime call.
    #today_fmt = '%B %d, %Y'

    # The reST default role (used for this markup: `text`) to use for all
    # documents.
    #default_role = None

    # If true, '()' will be appended to :func: etc. cross-reference text.
    #add_function_parentheses = True
    # A list of ignored prefixes for module index sorting.
    #modindex_common_prefix = []

    # If true, keep warnings as "system message" paragraphs in the built documents.
    #keep_warnings = False

    # If your documentation needs a minimal Sphinx version, state it here.
    #needs_sphinx = '1.0'

    # -- Options for HTML output ----------------------------------------------

    # Add any extra paths that contain custom files (such as robots.txt or
    # .htaccess) here, relative to this directory. These files are copied
    # directly to the root of the documentation.
    #html_extra_path = []

    # If true, an OpenSearch description file will be output, and all pages will
    # contain a <link> tag referring to it.  The value of this option must be the
    # base URL from which the finished HTML is served.
    #html_use_opensearch = ''

    # A shorter title for the navigation bar.  Default is the same as html_title.
    #html_short_title = None

    # The name of an image file (relative to this directory) to place at the top
    # of the sidebar.
    #html_logo = None

    # The name of an image file (within the static path) to use as favicon of the
    # docs.  This file should be a Windows icon file (.ico) being 16x16 or 32x32
    # pixels large.
    #html_favicon = None

    # If true, "(C) Copyright ..." is shown in the HTML footer. Default is True.
    #html_show_copyright = True

    # This is the file name suffix for HTML files (e.g. ".xhtml").
    #html_file_suffix = None

    # If not '', a 'Last updated on:' timestamp is inserted at every page bottom,
    # using the given strftime format.
    #html_last_updated_fmt = '%b %d, %Y'

    # Custom sidebar templates, maps document names to template names.
    #html_sidebars = {}

    # Additional templates that should be rendered to pages, maps page names to
    # template names.
    #html_additional_pages = {}

    # Add any paths that contain custom themes here, relative to this directory.
    #html_theme_path = []

    # The name for this set of Sphinx documents.  If None, it defaults to
    # "<project> v<release> documentation".
    #html_title = None

    # If false, no index is generated.
    #html_use_index = True

    # If true, the index is split into individual pages for each letter.
    #html_split_index = False

    # If true, links to the reST sources are added to the pages.
    #html_show_sourcelink = True

    # If true, sectionauthor and moduleauthor directives will be shown in the
    # output. They are ignored by default.
    #show_authors = False

    # -- Options for LaTeX output ---------------------------------------------

    #latex_elements = {
    # The paper size ('letterpaper' or 'a4paper').
    #'papersize': 'letterpaper',

    # The font size ('10pt', '11pt' or '12pt').
    #'pointsize': '10pt',

    # Additional stuff for the LaTeX preamble.
    #'preamble': '',
    #}

    # Grouping the document tree into LaTeX files. List of tuples
    # (source start file, target name, title,
    #  author, documentclass [howto, manual, or own class]).
    # latex_documents = [
    #   ('index', 'pytableaux.tex', u'pytableaux Documentation',
    #    u'Doug Owings', 'manual'),
    # ]

    # The name of an image file (relative to this directory) to place at the top of
    # the title page.
    #latex_logo = None

    # For "manual" documents, if this is true, then toplevel headings are parts,
    # not chapters.
    #latex_use_parts = False

    # If true, show page references after internal links.
    #latex_show_pagerefs = False

    # If true, show URL addresses after external links.
    #latex_show_urls = False

    # Documents to append as an appendix to all manuals.
    #latex_appendices = []

    # If false, no module index is generated.
    #latex_domain_indices = True


    # -- Options for manual page output ---------------------------------------

    # One entry per manual page. List of tuples
    # (source start file, name, description, authors, manual section).
    # man_pages = [
    #     ('index', 'pytableaux', u'pytableaux Documentation',
    #      [u'Doug Owings'], 1)
    # ]

    # If true, show URL addresses after external links.
    #man_show_urls = False


    # -- Options for Texinfo output -------------------------------------------

    # Grouping the document tree into Texinfo files. List of tuples
    # (source start file, target name, title, author,
    #  dir menu entry, description, category)
    # texinfo_documents = [
    #   ('index', 'pytableaux', u'pytableaux Documentation',
    #    u'Doug Owings', 'pytableaux', 'A multi-logic proof and semantic model generator.',
    #    'Logic'),
    # ]

    # Documents to append as an appendix to all manuals.
    #texinfo_appendices = []

    # If false, no module index is generated.
    #texinfo_domain_indices = True

    # How to display URL addresses: 'footnote', 'no', or 'inline'.
    #texinfo_show_urls = 'footnote'

    # If true, do not generate a @detailmenu in the "Top" node's menu.
    #texinfo_no_detailmenu = False
    pass