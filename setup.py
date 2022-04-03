#!/usr/bin/env python

import setuptools

with open('README.md', 'r', encoding='utf-8') as fh:
    long_description = fh.read()

VERSION = '0.0.2'
PACKAGE_NAME = 'yamler'
DESCRIPTION = 'Yamler is a CLI tool that allows a YAML file to be validated against a schema'  # nopep8

setuptools.setup(
    name=PACKAGE_NAME,
    version=VERSION,
    description=DESCRIPTION,
    long_description=long_description,
    long_description_content_type='text/markdown',
    url='https://github.com/Ryan95Z/yamler',
    author='Ryan Flynn',
    packages=setuptools.find_packages(include=['yamler']),
    install_requires=[
        'lark==1.0.0',
        'PyYAML==6.0'
    ],
    python_requires='>=3.7',
    classifiers=[
        'License :: OSI Approved :: MIT License',
        'Programming Language :: Python',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.7',
        'Programming Language :: Python :: 3.8',
        'Programming Language :: Python :: 3.9',
        'Programming Language :: Python :: 3.10',
        'Operating System :: OS Independent'
    ],
    entry_points={
        'console_scripts': ['yamler=yamler.cmd:main']
    },
    package_data={'yamler': ['grammer/grammer.lark']}
)
