#!/usr/bin/env python
# encoding: utf-8
# Thomas Nagy, 2006-2010 (ita)

"intltool support"

import os, re
from waflib import Configure, TaskGen, Task, Utils, Runner, Options, Build
import waflib.Tools.ccroot
from waflib.TaskGen import feature, before
from waflib.Logs import error

"""
Usage:

bld(features='intltool_in', source='a.po b.po', podir='po', cache='.intlcache', flags='')
"""

@before('process_source')
@feature('intltool_in')
def iapply_intltool_in_f(self):
	try: self.meths.remove('process_source')
	except ValueError: pass

	if not self.env.LOCALEDIR:
		self.env.LOCALEDIR = self.env.PREFIX + '/share/locale'

	for i in self.to_list(self.source):
		node = self.path.find_resource(i)

		podir = getattr(self, 'podir', 'po')
		podirnode = self.path.find_dir(podir)
		if not podirnode:
			error("could not find the podir %r" % podir)
			continue

		cache = getattr(self, 'intlcache', '.intlcache')
		self.env['INTLCACHE'] = os.path.join(self.path.bldpath(self.env), podir, cache)
		self.env['INTLPODIR'] = podirnode.srcpath(self.env)
		self.env['INTLFLAGS'] = getattr(self, 'flags', ['-q', '-u', '-c'])

		task = self.create_task('intltool', node, node.change_ext(''))
		inst = getattr(self, 'install_path', '${LOCALEDIR}')
		if inst:
			self.install_files(inst, task.outputs)

@feature('intltool_po')
def apply_intltool_po(self):
	try: self.meths.remove('process_source')
	except ValueError: pass

	if not self.env.LOCALEDIR:
		self.env.LOCALEDIR = self.env.PREFIX + '/share/locale'

	appname = getattr(self, 'appname', 'set_your_app_name')
	podir = getattr(self, 'podir', '')
	inst = getattr(self, 'install_path', '${LOCALEDIR}')

	linguas = self.path.find_resource(os.path.join(podir, 'LINGUAS'))
	if linguas:
		# scan LINGUAS file for locales to process
		file = open(linguas.abspath())
		langs = []
		for line in file.readlines():
			# ignore lines containing comments
			if not line.startswith('#'):
				langs += line.split()
		file.close()
		re_linguas = re.compile('[-a-zA-Z_@.]+')
		for lang in langs:
			# Make sure that we only process lines which contain locales
			if re_linguas.match(lang):
				node = self.path.find_resource(os.path.join(podir, re_linguas.match(lang).group() + '.po'))
				task = self.create_task('po', node, node.change_ext('.mo'))

				if inst:
					filename = task.outputs[0].name
					(langname, ext) = os.path.splitext(filename)
					inst_file = inst + os.sep + langname + os.sep + 'LC_MESSAGES' + os.sep + appname + '.mo'
					self.bld.install_as(inst_file, task.outputs[0], chmod=getattr(self, 'chmod', Utils.O644), env=task.env)

	else:
		Utils.pprint('RED', "Error no LINGUAS file found in po directory")

class po(Task.Task):
	run_str = '${MSGFMT} -o ${TGT} ${SRC}'
	color   = 'BLUE'

Task.task_factory('intltool', '${INTLTOOL} ${INTLFLAGS} ${INTLCACHE} ${INTLPODIR} ${SRC} ${TGT}', color='BLUE', ext_in=['.bin'])

def configure(conf):
	conf.find_program('msgfmt', var='MSGFMT')
	# NOTE: it is possible to set INTLTOOL in the environment, but it must not have spaces in it

	conf.find_perl_program('intltool-merge', var='INTLTOOL')

	def getstr(varname):
		return getattr(Options.options, varname, '')

	prefix  = conf.env['PREFIX']
	datadir = getstr('datadir')
	if not datadir: datadir = os.path.join(prefix,'share')

	conf.define('LOCALEDIR', os.path.join(datadir, 'locale'))
	conf.define('DATADIR', datadir)

	if conf.env['CC'] or conf.env['CXX']:
		# Define to 1 if <locale.h> is present
		conf.check(header_name='locale.h')

def options(opt):
	opt.add_option('--want-rpath', type='int', default=1, dest='want_rpath', help='set rpath to 1 or 0 [Default 1]')
	opt.add_option('--datadir', type='string', default='', dest='datadir', help='read-only application data')
