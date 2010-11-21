# -*- coding: utf-8 -*-
#
# waf documentation build configuration file, created by
# sphinx-quickstart on Sat Nov  6 20:46:09 2010.
#
# This file is execfile()d with the current directory set to its containing dir.
#
# Note that not all possible configuration values are present in this
# autogenerated file.
#
# All configuration values have a default; values that are commented out
# serve to show the default.

import sys, os

# If extensions (or modules to document with autodoc) are in another directory,
# add these directories to sys.path here. If the directory is relative to the
# documentation root, use os.path.abspath to make it absolute, like shown here.
sys.path.insert(0, os.path.abspath(os.path.join('..', "..")))
sys.path.append(os.path.abspath('.'))

# monkey patch a few waf classes for documentation purposes!
#-----------------------------------------------------------

from waflib import TaskGen
from waflib.TaskGen import task_gen, feats

def taskgen_method(func):
	setattr(task_gen, func.__name__, func)
	fix_fun_doc(func)
	return func

def fix_fun_doc(fun):
	try:
		if not fun.__doc__.startswith('\tTask generator method'):
			fun.__doc__ = '\tTask generator method\n\t\n' + (fun.__doc__ or '')
	except:
		print("Undocumented function", fun.__name__)
		raise

def fixmeth(x):
	if x == 'process_source':
		return ":py:func:`waflib.TaskGen.process_source`"
	if x == 'process_rule':
		return ":py:func:`waflib.TaskGen.process_rule`"
	return ":py:func:`%s`" % x

def fixfeat(x):
	return "`%s <../featuremap.html#feature-%s>`_" % (x=='*' and 'all' or x, x)

def append_doc(fun, keyword, meths):

	if keyword == "feature":
		meths = [fixfeat(x) for x in meths]
	else:
		meths = [fixmeth(x) for x in meths]

	dc = ", ".join(meths)
	fun.__doc__ += '\n\t:%s: %s' % (keyword, dc)

def feature(*k):
	def deco(func):
		setattr(task_gen, func.__name__, func)
		for name in k:
			feats[name].update([func.__name__])
		fix_fun_doc(func)
		append_doc(func, 'feature', k)
		#print "feature", name, k
		return func
	return deco
TaskGen.feature = feature


def before(*k):
	def deco(func):
		setattr(task_gen, func.__name__, func)
		for fun_name in k:
			if not func.__name__ in task_gen.prec[fun_name]:
				task_gen.prec[fun_name].append(func.__name__)
		fix_fun_doc(func)
		append_doc(func, 'before', k)
		return func
	return deco
TaskGen.before = before

def after(*k):
	def deco(func):
		setattr(task_gen, func.__name__, func)
		for fun_name in k:
			if not fun_name in task_gen.prec[func.__name__]:
				task_gen.prec[func.__name__].append(fun_name)
		fix_fun_doc(func)
		append_doc(func, 'after', k)
		return func
	return deco
TaskGen.after = after

# replay existing methods
TaskGen.taskgen_method(TaskGen.to_nodes)
TaskGen.feature('*')(TaskGen.process_source)
TaskGen.feature('*')(TaskGen.process_rule)
TaskGen.before('process_source')(TaskGen.process_rule)
TaskGen.feature('seq')(TaskGen.sequence_order)
TaskGen.extension('.pc.in')(TaskGen.add_pcfile)
TaskGen.feature('subst')(TaskGen.process_subst)
TaskGen.before('process_source','process_rule')(TaskGen.process_subst)

from waflib.Task import Task

Task.__dict__['run'].__doc__ = """
		Execute the task (executed by threads). Override in subclasses.

		:rtype: int
		"""
Task.__dict__['post_run'].__doc__ = "Update the cache files (executed by threads). Override in subclasses."


from waflib import Configure, Build
def conf(f):
	def fun(*k, **kw):
		mandatory = True
		if 'mandatory' in kw:
			mandatory = kw['mandatory']
			del kw['mandatory']

		try:
			return f(*k, **kw)
		except Errors.ConfigurationError as e:
			if mandatory:
				raise e

	f.__doc__ = "\tConfiguration Method bound to :py:class:`waflib.Configure.ConfigurationContext`\n" + (f.__doc__ or '')
	setattr(Configure.ConfigurationContext, f.__name__, fun)
	setattr(Build.BuildContext, f.__name__, fun)
	return f
Configure.conf = conf

Configure.ConfigurationContext.__doc__ = """
	Configure the project.

	Waf tools may bind new methods to this class::

		from waflib.Configure import conf
		@conf
		def myhelper(self):
			print("myhelper")

		def configure(ctx):
			ctx.myhelper()
"""


import os
lst = [x.replace('.py', '') for x in os.listdir('../../waflib/Tools/') if x.endswith('.py')]
for x in lst:
	if x == '__init__':
		continue
	__import__('waflib.Tools.%s' % x)

lst = list(TaskGen.feats.keys())
lst.sort()

accu = []
for z in lst:
	meths = TaskGen.feats[z]
	links = []

	allmeths = set([])
	for x in meths:
		for y in TaskGen.task_gen.prec.get(x, []):
			links.append((x, y))
			allmeths.add(x)
			allmeths.add(y)

	color = ',fillcolor="#fffea6",style=filled'
	ms = []
	for x in allmeths:
		try:
			m = TaskGen.task_gen.__dict__[x]
		except:
			raise ValueError("undefined method %r" % x)

		k = "%s.html#%s.%s" % (m.__module__.split('.')[-1], m.__module__, m.__name__)
		if str(m.__module__).find('.Tools') > 0:
			k = 'tools/' + k

		ms.append('\t"%s" [style="setlinewidth(0.5)",URL="%s",fontname=Vera Sans, DejaVu Sans, Liberation Sans, Arial, Helvetica, sans,height=0.25,shape=box,fontsize=10%s];' % (x, k, x in TaskGen.feats[z] and color or ''))

	for x, y in links:
		ms.append('\t"%s" -> "%s" [arrowsize=0.5,style="setlinewidth(0.5)"];' % (x, y))

	rs = '\tdigraph feature_%s {\n\tsize="8.0, 12.0";\n\t%s\n\t}\n' % (z == '*' and 'all' or z, '\n'.join(ms))
	title = "Feature %s" % z
	title += "\n" + len(title) * '='

	accu.append("%s\n\n.. graphviz::\n\n%s\n\n" % (title, rs))

f = open('tmpmap', 'w')
f.write(""".. _featuremap:

Feature map
===========

""")
f.write("\n".join(accu))
f.close()

#print("Path: %s" % sys.path)

# -- General configuration -----------------------------------------------------

# If your documentation needs a minimal Sphinx version, state it here.
#needs_sphinx = '1.0'

# Add any Sphinx extension module names here, as strings. They can be extensions
# coming with Sphinx (named 'sphinx.ext.*') or your custom ones.
extensions = ['sphinx.ext.autodoc', 'sphinx.ext.todo', 'sphinx.ext.pngmath', 'sphinx.ext.inheritance_diagram', 'sphinx.ext.graphviz']

# Add any paths that contain templates here, relative to this directory.
templates_path = ['_templates']

# The suffix of source filenames.
source_suffix = '.rst'

# The encoding of source files.
#source_encoding = 'utf-8-sig'

# The master toctree document.
master_doc = 'index'

# General information about the project.
project = u'Waf'
copyright = u'2010, Thomas Nagy'

# The version info for the project you're documenting, acts as replacement for
# |version| and |release|, also used in various other places throughout the
# built documents.
#
# The short X.Y version.
version = '1.6.1'
# The full version, including alpha/beta/rc tags.
release = '1.6.1'

# The language for content autogenerated by Sphinx. Refer to documentation
# for a list of supported languages.
#language = None

# There are two options for replacing |today|: either, you set today to some
# non-false value, then it is used:
#today = ''
# Else, today_fmt is used as the format for a strftime call.
#today_fmt = '%B %d, %Y'

# List of patterns, relative to source directory, that match files and
# directories to ignore when looking for source files.
exclude_patterns = []

# The reST default role (used for this markup: `text`) to use for all documents.
#default_role = None

# If true, '()' will be appended to :func: etc. cross-reference text.
#add_function_parentheses = True

# If true, the current module name will be prepended to all description
# unit titles (such as .. function::).
#add_module_names = True

# If true, sectionauthor and moduleauthor directives will be shown in the
# output. They are ignored by default.
#show_authors = False

# The name of the Pygments (syntax highlighting) style to use.
pygments_style = 'sphinx'

# A list of ignored prefixes for module index sorting.
#modindex_common_prefix = []


# -- Options for HTML output ---------------------------------------------------

# The theme to use for HTML and HTML Help pages.  See the documentation for
# a list of builtin themes.
html_theme = 'default'

# Theme options are theme-specific and customize the look and feel of a theme
# further.  For a list of options available for each theme, see the
# documentation.
#html_theme_options = {}

# Add any paths that contain custom themes here, relative to this directory.
#html_theme_path = []

# The name for this set of Sphinx documents.  If None, it defaults to
# "<project> v<release> documentation".
#html_title = None

# A shorter title for the navigation bar.  Default is the same as html_title.
#html_short_title = None

# The name of an image file (relative to this directory) to place at the top
# of the sidebar.
html_logo = '_images/waf-64x64.png'

# The name of an image file (within the static path) to use as favicon of the
# docs.  This file should be a Windows icon file (.ico) being 16x16 or 32x32
# pixels large.
#html_favicon = None

# Add any paths that contain custom static files (such as style sheets) here,
# relative to this directory. They are copied after the builtin static files,
# so a file named "default.css" will overwrite the builtin "default.css".
html_static_path = ['_static']

# If not '', a 'Last updated on:' timestamp is inserted at every page bottom,
# using the given strftime format.
#html_last_updated_fmt = '%b %d, %Y'

# If true, SmartyPants will be used to convert quotes and dashes to
# typographically correct entities.
#html_use_smartypants = True

# Custom sidebar templates, maps document names to template names.
#html_sidebars = {}

# Additional templates that should be rendered to pages, maps page names to
# template names.
html_additional_pages = {'index':'indexcontent.html'}

# If false, no module index is generated.
#html_domain_indices = True

# If false, no index is generated.
#html_use_index = True

# If true, the index is split into individual pages for each letter.
#html_split_index = False

# If true, links to the reST sources are added to the pages.
#html_show_sourcelink = True

# If true, "Created using Sphinx" is shown in the HTML footer. Default is True.
html_show_sphinx = False

# If true, "(C) Copyright ..." is shown in the HTML footer. Default is True.
#html_show_copyright = True

# If true, an OpenSearch description file will be output, and all pages will
# contain a <link> tag referring to it.  The value of this option must be the
# base URL from which the finished HTML is served.
#html_use_opensearch = ''

# This is the file name suffix for HTML files (e.g. ".xhtml").
#html_file_suffix = None

# Output file base name for HTML help builder.
htmlhelp_basename = 'wafdoc'


# -- Options for LaTeX output --------------------------------------------------

# The paper size ('letter' or 'a4').
#latex_paper_size = 'letter'

# The font size ('10pt', '11pt' or '12pt').
#latex_font_size = '10pt'

# Grouping the document tree into LaTeX files. List of tuples
# (source start file, target name, title, author, documentclass [howto/manual]).
latex_documents = [
  ('index', 'waf.tex', u'waf Documentation',
   u'Thomas Nagy', 'manual'),
]

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

# Additional stuff for the LaTeX preamble.
#latex_preamble = ''

# Documents to append as an appendix to all manuals.
#latex_appendices = []

# If false, no module index is generated.
#latex_domain_indices = True


# -- Options for manual page output --------------------------------------------

# One entry per manual page. List of tuples
# (source start file, name, description, authors, manual section).
man_pages = [
	('index', 'waf', u'waf Documentation',
	 [u'Thomas Nagy'], 1)
]

autodoc_default_flags = ['members', 'no-undoc-members', 'show-inheritance']
autodoc_member_order = 'bysource'

def maybe_skip_member(app, what, name, obj, skip, options):
	if name == 'Nod3':
		return True
	if what == 'class' and name in 'process_source sequence_order process_rule add_pcfile to_nodes'.split():
		return True

def setup(app):
	app.connect('autodoc-skip-member', maybe_skip_member)


#from waflib import Task
#def after(*k, **kw):
#	print "gnirf!"
#TaskGen.after = after
