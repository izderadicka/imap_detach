#!/usr/bin/env python

from os.path import os
import re
import sys


try:
    from setuptools import setup
except ImportError:
    from distutils.core import setup
   
    
pkg_file= os.path.join(os.path.split(__file__)[0], 'src', 'imap_detach', '__init__.py')

m=re.search(r"__version__\s*=\s*'([\d.]+)'", open(pkg_file).read())
if not m:
    print >>sys.stderr, 'Cannot find version of package'
    sys.exit(1)

version= m.group(1)



setup(name='imap_detach',
      version='version',
      description='Sample package',
      package_dir={'':'src'},
      packages=['imap_detach', ],
      scripts=['src/detach.py'],
      author='Ivan Zderadicka',
      author_email='ivan.zderadicka@gmail.com',
#      requires= ['tabulate (>=0.7.3)',],
#     install_requires=['tabulate>=0.7.3',],
      provides=['imap_detach']
      )