#!/usr/bin/env python
# -*- coding: utf-8 -*-

from setuptools import setup, find_packages

import os.path
import sys

sys.path.insert(0, os.path.abspath('.'))
from exopy_hqc_legacy.version import __version__


def long_description():
    """Read the project description from the README file.

    """
    with open(os.path.join(os.path.dirname(__file__), 'README.rst')) as f:
        return f.read()


setup(
    name='exopy_hqc_legacy',
    description='Transitional package between HQCMeas and Exopy',
    long_description=long_description(),
    version=__version__,
    author='see AUTHORS',
    author_email='m.dartiailh@gmail.com',
    url='https://github.com/exopy/exopy_hqc_legacy',
    download_url='https://github.com/exopy/exopy_hqc_legacy/tarball/master',
    keywords='experiment automation GUI',
    license='BSD',
    classifiers=[
        'Development Status :: 3 - Alpha',
        'License :: OSI Approved :: BSD License',
        'Natural Language :: English',
        'Operating System :: OS Independent',
        'Topic :: Scientific/Engineering :: Physics',
        'Programming Language :: Python :: 3.6',
        'Programming Language :: Python :: 3.7',
        'Programming Language :: Python :: 3.8',
        ],
    zip_safe=False,
    packages=find_packages(exclude=['tests', 'tests.*']),
    package_data={'': ['*.enaml']},
    python_requires='>=3.6',
    setup_requires=['setuptools'],
    install_requires=['exopy', 'pyvisa', 'h5py>=2.5.0', 'numpy', 'pyclibrary'],
    entry_points={
        'exopy_package_extension':
        'exopy_hqc_legacy = exopy_hqc_legacy:list_manifests'}
)
