# -*- coding: utf-8 -*-
# pytableaux, a multi-logic proof generator.
# Copyright (C) 2014-2022 Doug Owings.
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
#
# ------------------
# pytableaux - sphinx extension
from __future__ import annotations

from tools.doc import Helper, SphinxEvent
from sphinx.application import Sphinx
import sphinx.config


def setup(app: Sphinx):
    app.add_config_value('pt_options', {}, 'env', [dict])
    app.connect('config-inited', _init_app)
    app.connect('build-finished', _remove_app)

    from tools.doc import directives, roles
    directives.setup(app)
    roles.setup(app)

def _init_app(app: Sphinx, config: sphinx.config.Config):

    from tools.doc import processors, _helpers

    _helpers[app] = helper = Helper(**config['pt_options'])

    def conn(event, *handlers):
        for handler in handlers:
            app.connect(event, handler)

    from tools.doc import processors
    processors.setup(app)
    conn('autodoc-process-docstring',
        helper.sphinx_simple_replace_autodoc,
    )

    conn('source-read', helper.sphinx_simple_replace_source)
    conn(SphinxEvent.IncludeRead, helper.sphinx_simple_replace_include)

def _remove_app(app: Sphinx, exception):
    from tools.doc import _helpers
    del _helpers[app]


# Python domain:
#    https://www.sphinx-doc.org/en/master/usage/restructuredtext/domains.html?#the-python-domain
# Autodoc directives:
#    https://www.sphinx-doc.org/en/master/usage/extensions/autodoc.html#directives
# Built-in roles:
#    https://www.sphinx-doc.org/en/master/usage/restructuredtext/roles.html
# Sphinx events:
#    https://www.sphinx-doc.org/en/master/extdev/appapi.html#sphinx-core-events
# Docutils doctree:
#    https://docutils.sourceforge.io/docs/ref/doctree.html
# Font (GPL):
#    http://www.gust.org.pl/projects/e-foundry/tg-math/download/index_html#Bonum_Math
# Creating  Directives:
#    https://docutils.sourceforge.io/docs/howto/rst-directives.html
