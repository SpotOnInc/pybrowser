#!/usr/bin/env python

import os
import sys

import pydrvr

try:
    from setuptools import setup
except ImportError:
    from distutils.core import setup

if sys.argv[-1] == 'publish':
    os.system('python setup.py sdist upload')
    sys.exit()

packages = [
    'pydrvr',
]

requires = [
    'requests'
]

with open('README.md') as f:
    readme = f.read()

setup(
    name='pydrvr',
    version=pydrvr.__version__,
    description='WebDriver for Pythonistas',
    long_description=readme + '\n\n',
    author='Andrei Z',
    author_email='andrei@spoton.com',
    url='http://github.com/SpotOnInc/pydrvr',
    packages=packages,
    package_data={},
    package_dir={'pydrvr': 'pydrvr'},
    include_package_data=True,
    install_requires=requires,
    license='Apache 2.0',
    zip_safe=False,
    classifiers=(
        'Development Status :: 3 - Alpha',
        'Intended Audience :: Developers',
        'Natural Language :: English',
        'License :: OSI Approved :: Apache Software License',
        'Programming Language :: Python',
        'Programming Language :: Python :: 2.6',
        'Programming Language :: Python :: 2.7',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.3',
        'Topic :: Internet :: WWW/HTTP',
        'Topic :: Internet :: WWW/HTTP :: Browsers'
    ),
)
