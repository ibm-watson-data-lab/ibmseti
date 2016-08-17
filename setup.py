#!/usr/bin/env python
# Copyright (c) 2016 IBM. All rights reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
"""
_setup.py_

ibmseti 

A set of tools developed for SETI analysis of ATA data in partnership with IBM.

"""

from setuptools import setup, find_packages
from ibmseti.__info__ import __version__

requirements_file = open('requirements.txt')
requirements = requirements_file.read().strip().split('\n')

setup_args = {
    'description': 'SETI ATA data analysis tools',
    'include_package_data': True,
    'install_requires': requirements,
    'name': 'ibmseti',
    'version': __version__,
    'author': 'gadamc',
    'author_email': 'adamcox@us.ibm.com',
    'url': 'https://github.com/ibm-cds-labs/ibmseti',
    'packages': ['ibmseti'],
    'classifiers': [
          'Intended Audience :: Developers',
          'Natural Language :: English',
          'License :: OSI Approved :: Apache Software License',
          'Topic :: Software Development :: Libraries',
          'Development Status :: 4 - Beta',
          'Programming Language :: Python',
          'Programming Language :: Python :: 2',
          'Programming Language :: Python :: 2.7'
      ]
}

setup(**setup_args)
