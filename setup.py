from distutils.core import setup
from numpy.distutils.core import setup
from numpy.distutils.misc_util import Configuration
from numpy.distutils.core import Extension
import os
import numpy as np
from Cython.Build import cythonize
import subprocess
# Capture the current git commit to use as version

try:
    slalib_path = os.environ['SLALIB_LIBS']
except KeyError:
    slalib_path = '/star/lib' # default path of Manchester machines
    print('Warning: No SLALIB_LIBS environment variable set, assuming: {}'.format(slalib_path))

pysla = Extension(name = 'Tools.pysla', 
                  sources = ['Tools/pysla.f90','Tools/sla.f'],
                  f2py_options = [])
                                      
config = {'name':'COMAPPointingLevel1',
          'version':'1.0',
          'packages':['Tools'],
          'include_package_data':False,
          'ext_modules':cythonize([pysla],compiler_directives={'language_level':"3"})}

subprocess.run(['f2py','sla.f','pysla.f90','-m','pysla','-h','pysla.pyf','--overwrite-signature'],cwd='Tools')
subprocess.call(['f2py','-c','pysla.pyf','sla.f','pysla.f90'],cwd='Tools')

#setup(**config)
