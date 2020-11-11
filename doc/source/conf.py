# -*- coding: utf-8 -*-
#

import sys
import os

sys.path.insert(0, os.path.abspath('../../'))
import limits

on_rtd = os.environ.get('READTHEDOCS', None) == 'True'

if not on_rtd:  # only import and set the theme if we're building docs locally
    import sphinx_rtd_theme
    html_theme = 'sphinx_rtd_theme'
    html_theme_path = [sphinx_rtd_theme.get_html_theme_path()]

autodoc_default_options = {
    "members": True,
    "show-inheritance": True
}

autoclass_content = 'both'

extensions = [
    'sphinx.ext.autodoc',
    'sphinx.ext.intersphinx',
    'sphinx.ext.todo',
    'sphinx.ext.viewcode',
]

source_suffix = '.rst'
master_doc = 'index'
project = u'async_limits'
copyright = u'2020, Anomit Ghosh'

version = release = limits.__version__
exclude_patterns = []
pygments_style = 'sphinx'
htmlhelp_basename = 'limitsdoc'

latex_documents = [
    ('index', 'async_limits.tex', u'async_limits Documentation',
     u'Anomit Ghosh', 'manual'),
]
man_pages = [
    ('index', 'flask-limiter', u'async_limits Documentation',
     [u'Anomit Ghosh'], 1)
]

texinfo_documents = [
    ('index', 'async_limits', u'async_limits Documentation',
     u'Ali-Akber Saifee', 'async_limits', 'One line description of project.',
     'Miscellaneous'),
]

intersphinx_mapping = {
    'python': ('http://docs.python.org/', None),
    'rediscluster': ('https://redis-py-cluster.readthedocs.io/en/latest/', None),
    'redis': ('https://redis-py.readthedocs.io/en/latest/', None),
    'pymemcache': ('https://pymemcache.readthedocs.io/en/latest/', None)
}

