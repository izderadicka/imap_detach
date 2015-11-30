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
      version=version,
      description='A tool to automatically download attachments from IMAP mailbox',
      url='http://zderadicka.eu/projects/python/imap_detach-tool-download-email-attachments/',
      package_dir={'':'src'},
      packages=['imap_detach', ],
      scripts=['src/detach.py'],
      author='Ivan Zderadicka',
      author_email='ivan.zderadicka@gmail.com',
      license = 'GPL v3',
      install_requires=['six>=1.10.0',
                        'imapclient==1.0.0',  # seems to be still moving target so fixing the version
                        'parsimonious>=0.6.2'
                        ],
      provides=['imap_detach'],
      keywords=['email', 'IMAP', 'attachment'],
      classifiers=['Development Status :: 4 - Beta',
                   'Environment :: Console',
                   'License :: OSI Approved :: GNU General Public License v3 (GPLv3)',
                   'Natural Language :: English',
                   'Operating System :: POSIX',
                   'Programming Language :: Python :: 2.7',
                   'Programming Language :: Python :: 3.4', 
                   'Topic :: Communications :: Email']
      
      )