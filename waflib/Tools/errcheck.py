#! /usr/bin/env python
# encoding: utf-8
# Thomas Nagy, 2010 (ita)

"""
Search for common mistakes

There is a performance hit, so this tool must be loaded manually
"""

typos = {
'feature':'features',
'sources':'source',
'targets':'target',
'include':'includes',
'export_include':'export_includes',
'define':'defines',
'importpath':'includes',
'installpath':'install_path',
}

meths_typos = ['__call__', 'program', 'shlib', 'stlib', 'objects']

from waflib import Logs, Build, Node, Task
import waflib.Tools.ccroot

def replace(m):
	"""
	We could add properties, but they would not work in some cases:
	bld.program(...) requires 'source' in the attributes
	"""
	oldcall = getattr(Build.BuildContext, m)
	def call(self, *k, **kw):
		for x in typos:
			if x in kw:
				kw[typos[x]] = kw[x]
				del kw[x]
				Logs.error('typo %r -> %r' % (x, typos[x]))
		return oldcall(self, *k, **kw)
	setattr(Build.BuildContext, m, call)

def enhance_lib():
	for m in meths_typos:
		replace(m)

	# catch '..' in ant_glob patterns
	old_ant_glob = Node.Node.ant_glob
	def ant_glob(self, *k, **kw):
		for x in k[0].split('/'):
			if x == '..':
				Logs.error("In ant_glob pattern %r: '..' means 'two dots', not 'parent directory'" % k[0])
		return old_ant_glob(self, *k, **kw)
	Node.Node.ant_glob = ant_glob

	# catch conflicting ext_in/ext_out/before/after declarations
	old = Task.is_before
	def is_before(t1, t2):
		ret = old(t1, t2)
		if ret and old(t2, t1):
			Logs.error('Contradictory order constraints in classes %r %r' % (t1, t2))
		return ret
	Task.is_before = is_before

	# TODO: catch c files without any c or cxx feature
	def c_without_feature(self):
		pass
	TaskGen.feature('*')(c_without_feature)

def options(opt):
	"""
	Add a few methods
	"""
	enhance_lib()

def configure(conf):
	pass
