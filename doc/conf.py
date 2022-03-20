# -*- coding: utf-8 -*-
#
# pytableaux documentation build configuration file, created by
# sphinx-quickstart on Sat Mar  1 22:48:49 2014.

# If extensions (or modules to document with autodoc) are in another directory,
# add these directories to sys.path here. If the directory is relative to the
# documentation root, use os.path.abspath to make it absolute, like shown here.
import sys
sys.path.insert(1, '../src')

import docutil, fixed

copyright = '2014-2022, Doug Owings. Released under the GNU Affero General Public License v3 or later'

# Add any Sphinx extension module names here, as strings. They can be
# extensions coming with Sphinx (named 'sphinx.ext.*') or your custom
# ones.
extensions = [
    'sphinx.ext.autodoc',
    'sphinx.ext.doctest',
    'sphinx.ext.viewcode',
]

autodoc_member_order = 'bysource'

# General information about the project.
project = u'pytableaux'

# The version info for the project you're documenting, acts as replacement for
# |version| and |release|, also used in various other places throughout the
# built documents.
#
# The short X.Y version.
version = fixed.__version__
# The full version, including alpha/beta/rc tags.
release = version

pygments_style = 'colorful'
#pygments_style = 'xcode'
#pygments_style = 'material'

# html_theme = 'default'
html_theme = 'sphinx_rtd_theme'

# Theme options are theme-specific and customize the look and feel of a theme
# further.  For a list of options available for each theme, see the
# documentation.
html_theme_options = {}

# https://github.com/readthedocs/sphinx_rtd_theme
if html_theme == 'sphinx_rtd_theme':
    html_theme_options.update({
        'style_external_links': True,
    })

# If true, SmartyPants will be used to convert quotes and dashes to
# typographically correct entities.
html_use_smartypants = False

# If true, "Created using Sphinx" is shown in the HTML footer. Default is True.
html_show_sphinx = False

# Add any paths that contain custom static files (such as style sheets) here,
# relative to this directory. They are copied after the builtin static files,
# so a file named "default.css" will overwrite the builtin "default.css".
#html_static_path = ['_static']
html_static_path = ['../src/www/static', 'res', '../src/proof/templates/html/static']

# Output file base name for HTML help builder.
htmlhelp_basename = 'pytableauxdoc'

# List of patterns, relative to source directory, that match files and
# directories to ignore when looking for source files.
exclude_patterns = [
    '_build', '*.jinja2', '**/include/*', 'css/fonts/**', '**/*.js', 'css/proof.*.css',
    'jquery-ui', 'css/app.*.css',
]

# Add any paths that contain templates here, relative to this directory.
#templates_path = ['_templates']

# The suffix of source filenames.
source_suffix = '.rst'

# The master toctree document.
master_doc = 'index'

# If true, the current module name will be prepended to all description
# unit titles (such as .. function::).
add_module_names = False

def sphinxcontrib_autodoc_filterparams(fun, param):
    raise NotImplementedError

def setup(app):
    docutil.init_sphinx(app, {
        'html_theme': html_theme,
    })

def ____():
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

    # If false, no module index is generated.
    #html_domain_indices = True

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