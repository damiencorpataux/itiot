"""
Packaging.

Editable project installation for development: `pip install -e .`

We follow semver: https://semver.org/

from: https://stackoverflow.com/a/50194143
"""

from setuptools import setup, find_packages

setup(name='itiot', version='0.0.0', packages=find_packages())
