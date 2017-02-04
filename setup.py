# -*- coding: utf-8 -*
from setuptools import setup, find_packages
import os
import codecs
import sys


if sys.version_info < (3, 5):
    sys.stderr.write("HitchHttp will not run in python versions lower than 3.5.0, this version is {0}.\n".format(sys.version_info))
    exit(1)


def read(*parts):
    # intentionally *not* adding an encoding option to open
    # see here: https://github.com/pypa/virtualenv/issues/201#issuecomment-3145690
    return codecs.open(os.path.join(os.path.abspath(os.path.dirname(__file__)), *parts), 'r').read()

long_description = read('README.rst')

setup(name="hitchhttp",
      version=read('VERSION').replace('\n', ''),
      description="Mock HTTP server and example code generator for the Hitch testing framework",
      long_description=long_description,
      classifiers=[
          'Development Status :: 3 - Alpha',
          'Intended Audience :: Developers',
          'License :: OSI Approved :: GNU Affero General Public License v3 or later (AGPLv3+)',
          'Topic :: Software Development :: Quality Assurance',
          'Topic :: Software Development :: Testing',
          'Topic :: Software Development :: Libraries',
          'Operating System :: Unix',
          'Environment :: Console',
          #'Programming Language :: Python :: 2',
          #'Programming Language :: Python :: 2.6',
          #'Programming Language :: Python :: 2.7',
          'Programming Language :: Python :: 3',
          'Programming Language :: Python :: 3.2',
          'Programming Language :: Python :: 3.3',
          'Programming Language :: Python :: 3.4',
          'Programming Language :: Python :: 3.5',
      ],
      keywords='hitch testing framework bdd tdd declarative tests testing api http',
      author='Colm O\'Connor',
      author_email='colm.oconnor.github@gmail.com',
      url='https://hitchtest.readthedocs.org/',
      license='AGPL',
      install_requires=[
          'xeger',
          'strictyaml',
          'click',
          'hitchserve',
          'hitchtest',
          'requests',
          'tornado',
          'lxml',
          'path.py',
          'peewee>=2.1.0',
          'sanic',
      ],
      packages=find_packages(exclude=[]),
      entry_points=dict(console_scripts=['hitchhttp=hitchhttp:main', ]),
      zip_safe=False,
      include_package_data=True,
)
