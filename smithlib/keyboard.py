#!/usr/bin/python
# Martin Hosken 2011

from subprocess import Popen, PIPE
import os, uuid
import package

class Keyboard(object) :

	def __init__(self, *k, **kw) :
		base = os.path.basename(kw['source'])
		if not 'target' in kw : kw['target'] = os.path.join('keyboards', base)
		if not 'kmx' in kw : kw['kmx'] = base.replace('.kmn', '.kmx')
		if not 'svg' in kw : kw['svg'] = base.replace('.kmn', '.svg')
		if not 'xml' in kw : kw['xml'] = base.replace('.kmn', '.xml')
		if not 'pdf' in kw : kw['pdf'] = base.replace('.kmn', '.pdf')
#        if not 'fontname' in kw : kw['fontname'] = Popen(r"ttfeval -e 'print scalar $f->{q/name/}->read->find_name(2)' " + kw['font'], shell = True, stdout=PIPE).communicate()[0]
		if not 'fontsize' in kw : kw['fontsize'] = 18
		if not 'fontdir' in kw : kw['fontdir'] = 'kbdfonts'
		if not 'kbdfont' in kw : kw['kbdfont'] = os.path.join(kw['fontdir'], os.path.split(kw['font'])[1])
		for k, v in kw.items() : setattr(self, k, v)
		if not hasattr(self, 'package') :
			self.package = package.global_package()
		self.package.add_kbd(self)

	def get_build_tools(self, ctx) :
		res = set(['kmn2xml', 'kmnxml2svg', 'inkscape', 'ttfeval', 'cp'])
		if hasattr(self, 'mskbd') : res.update(self.mskbd.get_build_tools(ctx))
		try: ctx.find_program('kmcomp', var = 'KMCOMP')
		except:
			path = os.path.join(os.getenv('HOME'), '.wine', 'drive_c', 'Program Files', 'Tavultesoft', 'Keyman Developer', 'kmcomp.exe')
			if os.path.exists(path) : ctx.env['KMCOMP'] = 'wine "' + path + '"'
		fdir = ctx.bldnode.make_node(self.fontdir)
		fdir.mkdir()
		fconf = fdir.make_node('fonts.conf')
		if not os.path.exists(fconf.bldpath()) :
			dat = '''<fontconfig>

	<include ignore_missing="yes">/etc/fonts/fonts.conf</include>
	<dir>%s</dir>
	<cachedir>%s</cachedir>

</fontconfig>
''' % (fdir.abspath(), fdir.abspath())
			fconf.write(dat)

		return res

	def build(self, bld) :
		if bld.env['KMCOMP'] :
			bld(rule = '${KMCOMP} ${SRC} ${TGT}', source = self.source, target = self.kmx)
		bld(rule = "${CP} ${SRC} ${TGT}", source = self.source, target = self.target)
		self.build_pdf(bld)
		if hasattr(self, 'mskbd') : self.mskbd.build(bld, self)

	def build_pdf(self, bld) :
		self.build_svg(bld)
		bld(rule = 'FONTCONFIG=' + bld.bldnode.find_or_declare(self.fontdir).bldpath() + " ${INKSCAPE} -f ${SRC[0].bldpath()} -A ${TGT} -T -d 2400", shell = 1, source = [self.svg, self.kbdfont], target = bld.bldnode.find_or_declare(self.pdf))

	def build_svg(self, bld) :
		bld(rule = '${KMN2XML} ${SRC} > ${TGT}', shell = 1, source = self.source, target = self.xml)
		bld(rule = '${CP} ${SRC} ${TGT}', source = self.font, target = self.kbdfont)
		bld(rule = '${KMNXML2SVG} -s ' + str(self.fontsize) + ' -f "' + self.fontname + '" ${SRC} ${TGT}', source = self.xml, target = self.svg)

class MSKBD(object) :

	arches = ('i586', 'amd64')

	def __init__(self, *k, **kw) :
		if not 'lid' in kw : kw['lid'] = 0xC00
		if not 'guid' in kw : kw['guid'] = str(uuid.uuid4())
		for k, v in kw.items() : setattr(self, k, v)

	def get_build_tools(self, ctx) :
		for p in self.arches :
			for a in ('gcc', 'windres') :
				try : ctx.find_program(p + '-mingw32msvc-' + a, var = (p + a).upper())
				except : pass
		return set(('kmn2c', ))

	def build(self, bld, parent) :
		base = os.path.basename(parent.source)
		if not hasattr(self, 'source') : self.source = parent.source
		if not hasattr(self, 'c_file') : self.c_file = base.replace('.kmn', '.c')
		if not hasattr(self, 'rc_file') : self.rc_file = base.replace('.kmn', '.rc')
		if not hasattr(self, 'o_file') : self.o_file = base.replace('.kmn', '.o')
		if not hasattr(self, 'dll') : self.dll = base.replace('.kmn', '.dll')

		bld(rule = '${KMN2C} -o ${TGT[0]} ${SRC}', source = self.source, target = [self.c_file, self.rc_file])
		for p in self.arches :
			if bld.env[(p+'gcc').upper()] :
				ofile = self.o_file.replace('.', '-'+p[-2:]+'.', 1)        # p[-2:] is 86 or 64, which is a bit sneaky
				bld(rule = '${' + (p+'windres').upper() + '} ${SRC} ${TGT}', source = self.rc_file, target = ofile)
				bld(rule = '${' + (p+'gcc').upper() + '} -o ${TGT} -shared -Wl,--dll -Wl,--kill-at -Wl,--disable-stdcall-fixup -Wl,-entry,0 -s -nostdlib -Wl,${SRC[1]} ${SRC[0]}', source = [self.c_file, ofile], target = self.dll.replace('.', '-'+p[-2:]+'.', 1))

def onload(ctx) :
	varmap = { 'kbd' : Keyboard, 'mskbd' : MSKBD }
	for k, v in varmap.items() :
		if hasattr(ctx, 'wscript_vars') :
			ctx.wscript_vars[k] = v
		else :
			setattr(ctx.g_module, k, v)