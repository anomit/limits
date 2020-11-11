"""
setup.py for async_limits


"""
__author__ = "Anomit Ghosh"
__email__ = "anomit.ghosh@gmail.com"
__copyright__ = "Copyright 2020, Anomit Ghosh"

import os
from setuptools import setup, find_packages
import versioneer

THIS_DIR = os.path.abspath(os.path.dirname(__file__))
REQUIREMENTS = [
    k for k in open(
        os.path.join(THIS_DIR, 'requirements', 'main.txt')
    ).read().splitlines() if k.strip()
]

setup(
    name='async_limits',
    author=__author__,
    author_email=__email__,
    license="MIT",
    # url="https://limits.readthedocs.org",
    zip_safe=False,
    version=versioneer.get_version(),
    cmdclass=versioneer.get_cmdclass(),
    install_requires=REQUIREMENTS,
    classifiers=[k for k in open('CLASSIFIERS').read().split('\n') if k],
    description='Rate limiting utilities',
    long_description=open('README.rst').read(),
    packages=find_packages(exclude=['google.*', 'google', 'tests*']),
)
