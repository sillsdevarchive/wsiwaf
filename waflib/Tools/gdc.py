#!/usr/bin/env python
# encoding: utf-8
# Carlos Rafael Giani, 2007 (dv)

import sys
from waflib.Tools import ar, d
from waflib.Configure import conf

@conf
def find_gdc(conf):
	conf.find_program('gdc', var='D')

@conf
def common_flags_gdc(conf):
	v = conf.env

	# _DFLAGS _DIMPORTFLAGS

	# for mory info about the meaning of this dict see dmd.py
	v['DFLAGS']            = []

	v['D_SRC_F']           = ''
	v['D_TGT_F']           = ['-c', '-o', '']

	# linker
	v['D_LINKER']          = v['D']
	v['DLNK_SRC_F']        = ''
	v['DLNK_TGT_F']        = ['-o', '']
	v['DINC_ST'] = '-I%s'

	v['DSHLIB_MARKER'] = v['DSTLIB_MARKER'] = ''
	v['DSTLIB_ST'] = v['DLIB_ST']           = '-l%s'
	v['DSTLIBPATH_ST'] = v['DLIBPATH_ST']   = '-L%s'

	v['LINKFLAGS_dshlib'] = ['-shared']

	v['DHEADER_ext']       = '.di'
	v['D_HDR_F']           = '-fintfc -fintfc-file='

def configure(conf):
	conf.find_gdc()
	conf.imp('ar')
	conf.imp('d')
	conf.common_flags_gdc()
	conf.d_platform_flags()
