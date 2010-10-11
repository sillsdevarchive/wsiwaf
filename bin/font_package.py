#!/usr/bin/python

from waflib import Context, Build
import font, templater
import os

globalpackage = None
def global_package() :
	global globalpackage
	if not globalpackage :
		globalpackage = Package()
	return globalpackage

class Package(object) :

	packages = []
	def __init__(self, **kw) :
		for k in ('COPYRIGHT', 'LICENSE', 'VERSION', 'APPNAME', 'DESC_SHORT',
					'DESC_LONG') :
			setattr(self, k, getattr(Context.g_module, k, None))
		for k, v in kw.items() :
			setattr(self, k, v)
		self.packages.append(self)
		self.fonts = []

	def add_font(self, font) :
		self.fonts.append(font)

	def add_reservedofls(self, *reserved) :
		if hasattr(self, 'reservedofl') :
			self.reservedofl.update(reserved)
		else :
			self.reservedofl = set(reserved)

	def make_ofl_license(self, task) :
		bld = task.generator.bld
		font.make_ofl(task.outputs[0].srcpath(), self.reservedofl, getattr(self, 'ofl_version', '1.1'), copyright = getattr(self, 'COPYRIGHT', ''))
		return 0

	def build(self, bld) :

		def methodwrapofl(tsk) :
			return self.make_ofl_license(tsk)

		for f in self.fonts :
			f.build(bld)
		if hasattr(self, 'reservedofl') :
			if not hasattr(self, 'LICENSE') : self.LICENSE = 'OFL.txt'
			bld(name = 'Package OFL', rule = methodwrapofl, target = bld.bldnode.find_or_declare(self.LICENSE))

	def build_exe(self, bld) :
		thisdir = os.path.dirname(__file__)
		env =   {
			'project' : self,
			'fonts' : self.fonts,
			'basedir' : thisdir
				}
		# create a taskgen to expand the installer.nsi
		bname = 'installer_' + self.APPNAME
		task = templater.Copier(prj = self, fonts = self.fonts, basedir = thisdir, env = bld.env)
		task.set_inputs(bld.root.find_resource(os.path.join(thisdir, 'installer.nsi')))
		task.set_outputs(bld.bldnode.find_or_declare(bname + '.nsi'))
		bld.add_to_group(task)
		bld(rule='makensis -O' + bname + '.log ${SRC}', source = bname + '.nsi', target = '%s-%s.exe' % (getattr(self, 'DESC_NAME', self.APPNAME).title(), self.VERSION))

class exeContext(Build.BuildContext) :
	cmd = 'exe'

	def pre_build(self) :
		self.add_group('exe')
		for p in Package.packages :
			p.build_exe(self)
