#!/usr/bin/env python
# encoding: utf-8
#
# partially based on boost.py written by Gernot Vormayr
# written by Ruediger Sonderfeld <ruediger@c-plusplus.de>, 2008
# modified by Bjoern Michaelsen, 2008
# modified by Luca Fossati, 2008
# rewritten for waf 1.5.1, Thomas Nagy, 2008
# rewritten for waf 1.6.2, Sylvain Rouquette, 2011

'''
To add the boost tool to the waf file:
$ ./waf-light --tools=compat15,boost
	or, if you have waf >= 1.6.2
$ ./waf update --files=boost

The wscript will look like:

def options(opt):
	opt.load('compiler_cxx boost')

def configure(conf):
	conf.load('compler_cxx boost')
	conf.check_boost(lib='system filesystem', mt=True, static=True)

def build(bld):
	bld(source='main.cpp', target='bar', use='BOOST')
'''

import os, sys, re
from waflib import Options, Utils
from waflib.Configure import conf

BOOST_LIBS = ('/usr/lib', '/usr/local/lib', '/opt/local/lib', '/sw/lib', '/lib')
BOOST_INCLUDES = ('/usr/include', '/usr/local/include', '/opt/local/include', '/sw/include')
BOOST_VERSION_FILE = 'boost/version.hpp'
BOOST_VERSION_CODE = '''
#include <iostream>
#include <boost/version.hpp>
int main() { std::cout << BOOST_VERSION << std::endl; }
'''

# toolsets from {boost_dir}/tools/build/v2/tools/common.jam
detect_clang = lambda env: (Utils.unversioned_sys_platform() == 'darwin') and 'clang-darwin' or 'clang'
detect_mingw = lambda env: (re.search('MinGW', env.CXX[0])) and 'mgw' or 'gcc'
detect_intel = lambda env: (Utils.unversioned_sys_platform() == 'win32') and 'iw' or 'il'
BOOST_TOOLSET = {
	'borland':  'bcb',
	'clang':    detect_clang,
	'como':     'como',
	'cw':       'cw',
	'darwin':   'xgcc',
	'edg':      'edg',
	'g++':      detect_mingw,
	'gcc':      detect_mingw,
	'icpc':     detect_intel,
	'intel':    detect_intel,
	'kcc':      'kcc',
	'kylix':    'bck',
	'mipspro':  'mp',
	'mingw':    'mgw',
	'msvc':     'vc',
	'qcc':      'qcc',
	'sun':      'sw',
	'sunc++':   'sw',
	'tru64cxx': 'tru',
	'vacpp':    'xlc'
}

def options(opt):
	opt.add_option('--boost-includes', type='string', default='', dest='boost_includes',
				   help='''path to the boost directory where the includes are
				   e.g. /boost_1_45_0/include''')
	opt.add_option('--boost-libs', type='string', default='', dest='boost_libs',
				   help='''path to the directory where the boost libs are
				   e.g. /boost_1_45_0/stage/lib''')
	opt.add_option('--boost-static', action='store_true', default=False, dest='boost_static',
				   help='link static libraries')
	opt.add_option('--boost-mt', action='store_true', default=False, dest='boost_mt',
				   help='select multi-threaded libraries')
	opt.add_option('--boost-abi', type='string', default='', dest='boost_abi',
				   help='''select libraries with tags (dgsyp, d for debug),
				   see doc Boost, Getting Started, chapter 6.1''')
	opt.add_option('--boost-toolset', type='string', default='', dest='boost_toolset',
				   help='force a toolset e.g. msvc, vc90, gcc, mingw, mgw45 (default: auto)')
	opt.add_option('--boost-verbose', action='store_true', default=False, dest='boost_verbose',
				   help='display more informations')
	py_version = '%d%d' % (sys.version_info[0], sys.version_info[1])
	opt.add_option('--boost-python', type='string', default=py_version, dest='boost_python',
				   help='select the lib python with this version (default: %s)' % py_version)



@conf
def boost_get_version_file(self, dir):
	try:
		return self.root.find_dir(dir).find_node(BOOST_VERSION_FILE)
	except:
		return None

@conf
def boost_get_version(self, dir):
	"""silently retrieve the boost version number"""
	re_but = re.compile('^#define\\s+BOOST_VERSION\\s+(.*)$', re.M)
	try:
		val = re_but.search(self.boost_get_version_file(dir).read()).group(1)
	except:
		val = self.check_cxx(fragment=BOOST_VERSION_CODE, includes=[dir],
							 execute=True, define_ret=True)
	val = int(val)
	major = val // 100000
	minor = val // 100 % 1000
	minor_minor = val % 100
	if minor_minor == 0:
		return "%d_%d" % (major, minor)
	else:
		return "%d_%d_%d" % (major, minor, minor_minor)



@conf
def boost_get_includes(self, *k, **kw):
	includes = k and k[0] or kw.get('includes', None)
	if includes and self.boost_get_version_file(includes):
		return includes
	for dir in BOOST_INCLUDES:
		if self.boost_get_version_file(dir):
			return dir
	if includes:
		self.fatal('headers not found in %s' % includes)
	else:
		self.fatal('headers not found, use --boost-includes=/path/to/boost')



@conf
def boost_get_toolset(self, cc):
	toolset = cc
	if not cc:
		build_platform = Utils.unversioned_sys_platform()
		if build_platform in BOOST_TOOLSET:
			cc = build_platform
		else:
			cc = self.env.CXX_NAME
	if cc in BOOST_TOOLSET:
		toolset = BOOST_TOOLSET[cc]
	return (isinstance(toolset, str)) and toolset or toolset(self.env)

@conf
def __boost_get_libs_path(self, *k, **kw):
	if 'files' in kw:
		return self.root.find_dir('.'), kw['files']
	libs = k and k[0] or kw.get('libs', None)
	if libs:
		path = self.root.find_dir(libs)
		files = path.ant_glob('*boost_*')
	if not libs or not files:
		for dir in BOOST_LIBS:
			try:
				path = self.root.find_dir(dir)
				files = path.ant_glob('*boost_*')
				if files:
					break
				path = self.root.find_dir(dir + '64')
				files = path.ant_glob('*boost_*')
				if files:
					break
			except:
				path = None
				pass
	if not path:
		if libs:
			self.fatal('libs not found in %s' % libs)
		else:
			self.fatal('libs not found, use --boost-includes=/path/to/boost/lib')
	return path, files

@conf
def boost_get_libs(self, *k, **kw):
	path, files = self.__boost_get_libs_path(**kw)
	t = []
	if kw['mt']:
		t.append('mt')
	if kw['abi']:
		t.append(kw['abi'])
	tags = t and '(-%s)+' % '-'.join(t) or ''
	toolset = '(-%s[0-9]{0,3})+' % self.boost_get_toolset(kw['toolset'])
	version = '(-%s)+' % self.env.BOOST_VERSION
	def find_lib(re_lib, files):
		for file in files:
			if re_lib.search(file.name):
				return file
		return None
	def format_lib_name(name):
		if name.startswith('lib'):
			name = name[3:]
		return name.split('.')[0]
	libs = []
	for lib in (k and k[0] or kw.get('lib', None)).split():
		py = (lib == 'python') and '(-py%s)+' % kw['python'] or ''
		pattern = 'boost_%s%s%s%s%s' % (lib, toolset, tags, py, version)
		file = find_lib(re.compile(pattern), files)
		if file:
			libs.append(format_lib_name(file.name))
			continue
		# second pass with less condition
		pattern = 'boost_%s%s%s' % (lib, tags, py)
		file = find_lib(re.compile(pattern), files)
		if file:
			libs.append(format_lib_name(file.name))
			continue
		self.fatal('lib %s not found in %s' % (lib, path))
	return path.abspath(), libs



@conf
def check_boost(self, *k, **kw):
	"""
	initialize boost

	You can pass the same parameters as the command line,
	but the command line has the priority.
	"""
	if not self.env['CXX']:
		self.fatal('load a c++ compiler tool first, for example conf.load("compiler_cxx")')

	params = { 'lib': k and k[0] or kw.get('lib', None) }
	for key, value in self.options.__dict__.items():
		if not key.startswith('boost_'):
			pass
		key = key[len('boost_'):]
		params[key] = value and value or kw.get(key, '')

	self.start_msg('Checking boost includes')
	self.env.INCLUDES_BOOST = self.boost_get_includes(**params)
	self.env.BOOST_VERSION = self.boost_get_version(self.env.INCLUDES_BOOST)
	self.end_msg(self.env.BOOST_VERSION)
	if params['verbose']:
		self.start_msg('boost includes path')
		self.end_msg(self.env.INCLUDES_BOOST)

	if not params['lib']:
		return
	self.start_msg('Checking boost libs')
	suffix = params['static'] and 'ST' or ''
	path, libs = self.boost_get_libs(**params)
	self.env['%sLIBPATH_BOOST' % suffix] = [path]
	self.env['%sLIB_BOOST' % suffix] = libs
	self.end_msg('ok')
	if params['verbose']:
		self.start_msg('boost libs path')
		self.end_msg(path)
		self.start_msg('boost libs found')
		self.end_msg(libs)
