#!/usr/bin/env python
# encoding: utf-8
# Thomas Nagy, 2010 (ita)

"""
Base classes (mostly abstract)
"""

import traceback, os, imp, sys
from waflib import Utils, Errors, Logs
import waflib.Node

# the following 3 constants are updated on each new release (do not touch)
HEXVERSION=0x1060100
"""Constant updated on new releases"""

WAFVERSION="1.6.1"
"""Constant updated on new releases"""

WAFREVISION="10307"
"""Constant updated on new releases"""

ABI = 98
"""Version of the build data cache file format (used in :py:const:`waflib.Context.DBFILE`)"""

DBFILE = '.wafpickle-%d' % ABI
"""Name of the pickle file for storing the build data"""

APPNAME = 'APPNAME'
"""Default application name (used by ``waf dist``)"""

VERSION = 'VERSION'
"""Default application version (used by ``waf dist``)"""

TOP  = 'top'
"""The variable name for the top-level directory in wscript files"""

OUT  = 'out'
"""The variable name for the output directory in wscript files"""

WSCRIPT_FILE = 'wscript'
"""Name of the waf script files"""


launch_dir = ''
"""Directory from which waf has been called"""
run_dir = ''
"""Location of the wscript file to use as the entry point"""
top_dir = ''
"""Location of the project directory (top), if the project was configured"""
out_dir = ''
"""Location of the build directory (out), if the project was configured"""
waf_dir = ''
"""Directory containing the waf modules"""

local_repo = ''
"""Local repository containing additional Waf tools (plugins)"""
remote_repo = 'http://waf.googlecode.com/svn/'
"""
Remote directory containing downloadable waf tools. The missing tools can be downloaded by using::

	$ waf configure --download
"""

remote_locs = ['branches/waf-%s/waflib/extras' % WAFVERSION, 'trunk/waflib/extras']
"""
Remote directories for use with :py:const:`waflib.Context.remote_repo`
"""

g_module = None
"""
Module representing the main wscript file (see :py:const:`waflib.Context.run_dir`)
"""

STDOUT = 1
STDERR = -1
BOTH   = 0

classes = []
"""
List of :py:class:`waflib.Context.Context` subclasses that can be used as waf commands. The classes
are added automatically by a metaclass.
"""


def create_context(cmd_name, *k, **kw):
	"""
	Create a new :py:class:`waflib.Context.Context` instance corresponding to the given command.
	Used in particular by :py:func:`waflib.Scripting.run_command`

	:param cmd_name: command
	:type cmd_name: string
	:param k: arguments to give to the context class initializer
	:type k: list
	:param k: keyword arguments to give to the context class initializer
	:type k: dict
	"""
	global classes
	for x in classes:
		if x.cmd == cmd_name:
			return x(*k, **kw)
	ctx = Context(*k, **kw)
	ctx.fun = cmd_name
	return ctx

class store_context(type):
	"""
	Metaclass for storing the command classes into the list :py:const:`waflib.Context.classes`
	Context classes must provide an attribute 'cmd' representing the command to execute
	"""
	def __init__(cls, name, bases, dict):
		super(store_context, cls).__init__(name, bases, dict)
		name = cls.__name__

		if name == 'ctx' or name == 'Context':
			return

		try:
			cls.cmd
		except AttributeError:
			raise Errors.WafError('Missing command for the context class %r (cmd)' % name)

		if not getattr(cls, 'fun', None):
			cls.fun = cls.cmd

		global classes
		classes.insert(0, cls)

ctx = store_context('ctx', (object,), {})
"""Base class for the :py:class:`waflib.Context.Context` classes"""

class Context(ctx):
	"""
	Base class for command contexts. Those objects are passed as the arguments
	of user functions (commands) defined in Waf scripts.

	Subclasses must provide the attribute 'cmd':

	:param cmd: command to execute as in ``waf cmd``
	:type cmd: string
	:param fun: function name to execute when the command is called
	:type fun: string
	"""

	errors = Errors
	"""
	Shortcut to :py:mod:`waflib.Errors` provided for convenience
	"""

	tools = {}
	"""
	A cache for modules (wscript files) read by :py:meth:`Context.Context.load`
	"""

	def __init__(self, **kw):
		try:
			rd = kw['run_dir']
		except KeyError:
			global run_dir
			rd = run_dir

		# binds the context to the nodes in use to avoid a context singleton
		class node_class(waflib.Node.Node):
			pass
		self.node_class = node_class
		self.node_class.__module__ = "waflib.Node"
		self.node_class.__name__ = "Nod3"
		self.node_class.ctx = self

		self.root = self.node_class('', None)
		self.cur_script = None
		self.path = self.root.find_dir(rd)

		self.stack_path = []
		self.exec_dict = {'ctx':self, 'conf':self, 'bld':self, 'opt':self}
		self.logger = None

	def __hash__(self):
		"""
		Return a hash value for storing context objects in dicts or sets. The value is not persistent.

		:return: hash value
		:rtype: int
		"""
		return id(self)

	def load(self, tool_list, *k, **kw):
		"""
		Load a Waf tool as a module, and try calling the function named :py:const:`waflib.Context.Context.fun` from it.
		A ``tooldir`` value may be provided as a list of module paths.

		:type tool_list: list of string or space-separated string
		:param tool_list: list of Waf tools to use
		"""
		tools = Utils.to_list(tool_list)
		path = Utils.to_list(kw.get('tooldir', ''))

		for t in tools:
			module = load_tool(t, path)
			fun = getattr(module, self.fun, None)
			if fun:
				fun(self)

	def execute(self):
		"""
		Execute the command. Redefine this method in subclasses.
		"""
		global g_module
		self.recurse([os.path.dirname(g_module.root_path)])

	def pre_recurse(self, node):
		"""
		Method executed immediately before a folder is read by :py:meth:`waflib.Context.Context.recurse`. The node given is set
		as an attribute ``self.cur_script``, and as the current path ``self.path``
		"""
		self.stack_path.append(self.cur_script)

		self.cur_script = node
		self.path = node.parent

	def post_recurse(self, node):
		"""
		Restore ``self.cur_script`` and ``self.path`` right after :py:meth:`waflib.Context.Context.recurse` terminates.
		"""
		self.cur_script = self.stack_path.pop()
		if self.cur_script:
			self.path = self.cur_script.parent

	def recurse(self, dirs, name=None, mandatory=True):
		"""
		Run user code from the supplied list of directories.
		The directories can be either absolute, or relative to the directory
		of the wscript file. The methods :py:meth:`waflib.Context.Context.pre_recurse` and :py:meth:`waflib.Context.Context.post_recurse`
		are called immediately before and after a script has been executed.

		:param dirs: List of directories to visit
		:type dirs: list of string or space-separated string
		:param name: Name of function to invoke from the wscript
		:type  name: string
		:param mandatory: whether sub wscript files are required to exist
		:type  mandatory: bool
		"""
		for d in Utils.to_list(dirs):

			if not os.path.isabs(d):
				# absolute paths only
				d = os.path.join(self.path.abspath(), d)

			WSCRIPT     = os.path.join(d, WSCRIPT_FILE)
			WSCRIPT_FUN = WSCRIPT + '_' + (name or self.fun)

			node = self.root.find_node(WSCRIPT_FUN)
			if node:
				self.pre_recurse(node)
				try:
					function_code = node.read('rU')
					exec(compile(function_code, node.abspath(), 'exec'), self.exec_dict)
				finally:
					self.post_recurse(node)

			else:
				node = self.root.find_node(WSCRIPT)
				if not node:
					if not mandatory:
						continue
					raise Errors.WafError('No wscript file in directory %s' % d)
				self.pre_recurse(node)
				try:
					wscript_module = load_module(node.abspath())
					user_function = getattr(wscript_module, (name or self.fun), None)
					if not user_function:
						if not mandatory:
							continue
						raise Errors.WafError('No function %s defined in %s' % (name or self.fun, node.abspath()))
					user_function(self)
				finally:
					self.post_recurse(node)

	def exec_command(self, cmd, **kw):
		"""
		Execute a command and return the exit status. If the context has the attribute 'log',
		capture and log the process stderr/stdout for logging purposes::

			def run(tsk):
				ret = tsk.generator.bld.exec_command('touch foo.txt')
				return ret

		Do not confuse this method with :py:meth:`waflib.Context.Context.cmd_and_log` which is used to
		return the standard output/error values.

		:param cmd: command argument for subprocess.Popen
		:param kw: keyword arguments for subprocess.Popen
		"""
		subprocess = Utils.subprocess
		kw['shell'] = isinstance(cmd, str)
		Logs.debug('runner: %r' % cmd)
		Logs.debug('runner_env: kw=%s' % kw)

		try:
			if self.logger:
				# warning: may deadlock with a lot of output (subprocess limitation)

				self.logger.info(cmd)

				kw['stdout'] = kw['stderr'] = subprocess.PIPE
				p = subprocess.Popen(cmd, **kw)
				(out, err) = p.communicate()
				if out:
					self.logger.debug('out: %s' % out.decode('utf-8'))
				if err:
					self.logger.error('err: %s' % err.decode('utf-8'))
				return p.returncode
			else:
				p = subprocess.Popen(cmd, **kw)
				return p.wait()
		except OSError:
			return -1

	def cmd_and_log(self, cmd, **kw):
		"""
		Execute a command and return stdout if the execution is successful.
		An exception is thrown when the exit status is non-0. In that case, both stderr and stdout
		will be bound to the WafError object::

			def configure(conf):
				out = conf.cmd_and_log(['echo', 'hello'], stdout=waflib.Context.STDOUT)
				(out, err) = conf.cmd_and_log(['echo', 'hello'], stdout=waflib.Context.BOTH)
				try:
					conf.cmd_and_log(['which', 'someapp'], stdout=waflib.Context.BOTH)
				except Exception as e:
					print(e.out, e.err)

		:param cmd: args for subprocess.Popen
		:param kw: keyword arguments for subprocess.Popen
		"""
		subprocess = Utils.subprocess
		kw['shell'] = isinstance(cmd, str)
		Logs.debug('runner: %r' % cmd)

		if 'quiet' in kw:
			quiet = kw['quiet']
			del kw['quiet']
		else:
			quiet = None

		if 'output' in kw:
			to_ret = kw['output']
			del kw['output']
		else:
			to_ret = STDOUT

		kw['stdout'] = kw['stderr'] = subprocess.PIPE
		if quiet is None:
			self.to_log(cmd)
		try:
			p = subprocess.Popen(cmd, **kw)
			(out, err) = p.communicate()
		except Exception as e:
			try:
				self.to_log(str(err))
			except:
				pass
			raise Errors.WafError('Execution failure', ex=e)

		if not isinstance(out, str):
			out = out.decode('utf-8')
		if not isinstance(err, str):
			err = err.decode('utf-8')

		if out and quiet != STDOUT and quiet != BOTH:
			self.to_log('out: %s' % out)
		if err and quiet != STDERR and quiet != BOTH:
			self.to_log('err: %s' % err)

		if p.returncode:
			e = Errors.WafError('command %r returned %r' % (cmd, p.returncode))
			e.returncode = p.returncode
			e.stderr = err
			e.stdout = out
			raise e

		if to_ret == BOTH:
			return (out, err)
		elif to_ret == STDERR:
			return err
		return out

	def fatal(self, msg, ex=None):
		"""
		Raise a configuration error to interrupt the execution immediately::

			def configure(conf):
				conf.fatal('a requirement is missing')

		:param msg: message to display
		:type msg: string
		:param ex: optional exception object
		:type ex: exception
		"""
		if self.logger:
			self.logger.info('from %s: %s' % (self.path.abspath(), msg))
		try:
			msg = '%s\n(complete log in %s)' % (msg, self.logger.handlers[0].baseFilename)
		except:
			pass
		raise self.errors.ConfigurationError(msg, ex=ex)

	def to_log(self, msg):
		"""
		Log some information to the logger (if present), or to stderr::

			def build(bld):
				bld.to_log('starting the build')

		:param msg: message
		:type msg: string
		"""
		if not msg:
			return
		if self.logger:
			self.logger.info(msg)
		else:
			sys.stderr.write(str(msg))


	def msg(self, msg, result, color=None):
		"""
		Print a configuration message of the form ``msg: result``.
		The second part of the message will be in colors. The output
		can be disabled easly by setting ``in_msg`` to a positive value::

			def configure(conf):
				self.in_msg = 1
				conf.msg('Checking for library foo', 'ok')
				# no output

		:param msg: message to display to the user
		:type msg: string
		:param result: result to display
		:type result: string or boolean
		:param color: color to use, see :py:const:`waflib.Logs.colors_lst`
		:type color: string
		"""
		self.start_msg(msg)

		if not isinstance(color, str):
			color = result and 'GREEN' or 'YELLOW'

		self.end_msg(result, color)

	def start_msg(self, msg):
		"""
		Print the beginning of a 'Checking for xxx' message. See :py:meth:`waflib.Context.Context.msg`
		"""
		try:
			if self.in_msg:
				self.in_msg += 1
				return
		except:
			self.in_msg = 0
		self.in_msg += 1

		try:
			self.line_just = max(self.line_just, len(msg))
		except AttributeError:
			self.line_just = max(40, len(msg))
		for x in (self.line_just * '-', msg):
			self.to_log(x)
		Logs.pprint('NORMAL', "%s :" % msg.ljust(self.line_just), sep='')

	def end_msg(self, result, color=None):
		"""Print the end of a 'Checking for' message. See :py:meth:`waflib.Context.Context.msg`"""
		self.in_msg -= 1
		if self.in_msg:
			return

		defcolor = 'GREEN'
		if result == True:
			msg = 'ok'
		elif result == False:
			msg = 'not found'
			defcolor = 'YELLOW'
		else:
			msg = str(result)

		self.to_log(msg)
		Logs.pprint(color or defcolor, msg)


cache_modules = {}
"""
Dictionary holding already loaded modules, keyed by their absolute path.
The modules are added automatically by :py:func:`waflib.Context.load_module`
"""

def load_module(path):
	"""
	Load a source file as a python module.

	:param path: file path
	:type path: string
	:return: Loaded Python module
	:rtype: module
	"""
	try:
		return cache_modules[path]
	except KeyError:
		pass

	module = imp.new_module(WSCRIPT_FILE)
	try:
		code = Utils.readf(path, m='rU')
	except (IOError, OSError):
		raise Errors.WafError('Could not read the file %r' % path)

	module_dir = os.path.dirname(path)
	sys.path.insert(0, module_dir)

	exec(compile(code, path, 'exec'), module.__dict__)
	sys.path.remove(module_dir)

	cache_modules[path] = module

	return module

def load_tool(tool, tooldir=None):
	"""
	Import a Waf tool (python module), and store it in the dict :py:const:`waflib.Context.Context.tools`

	:type  tool: string
	:param tool: Name of the tool
	:type  tooldir: list
	:param tooldir: List of directories to search for the tool module
	"""
	tool = tool.replace('++', 'xx')
	tool = tool.replace('java', 'javaw')
	tool = tool.replace('compiler_cc', 'compiler_c')

	if tooldir:
		assert isinstance(tooldir, list)
		sys.path = tooldir + sys.path
		try:
			__import__(tool)
			ret = sys.modules[tool]
			Context.tools[tool] = ret
			return ret
		finally:
			for d in tooldir:
				sys.path.remove(d)
	else:
		global waf_dir
		try:
			os.stat(os.path.join(waf_dir, 'waflib', 'Tools', tool + '.py'))
			d = 'waflib.Tools.%s' % tool
		except:
			try:
				os.stat(os.path.join(waf_dir, 'waflib', 'extras', tool + '.py'))
				d = 'waflib.extras.%s' % tool
			except:
				d = tool # user has messed with sys.path

		__import__(d)
		ret = sys.modules[d]
		Context.tools[tool] = ret
		return ret
