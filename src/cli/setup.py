#!/usr/bin/env python
from setuptools import setup

setup(
    name='poseidon_cli',
    setup_requires=['pbr>=1.9', 'setuptools>=17.1'],
    python_requires='>=3.6',
    packages=['poseidon_cli'],
    package_dir={'poseidon_cli': 'cli'},
    pbr=True
)
