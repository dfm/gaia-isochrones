#!/usr/bin/env python

import os
import sys
from setuptools import setup

dirname = os.path.dirname(os.path.realpath(__file__))
sys.path.insert(0, os.path.join(dirname, "gaia_isochrones"))
from gaia_isochrones_version import __version__  # NOQA

with open(os.path.join(dirname, "requirements.txt"), "r") as f:
    install_requires = f.read().splitlines()

with open(os.path.join(dirname, "README.md"), encoding="utf-8") as f:
    readme = f.read()

setup(
    name="gaia_isochrones",
    version=__version__,
    author="Daniel Foreman-Mackey",
    author_email="foreman.mackey@gmail.com",
    url="https://github.com/dfm/gaia-isochrones",
    license="MIT",
    packages=["gaia_isochrones"],
    description="Quicklook isochrone fits using Gaia data",
    long_description=readme,
    long_description_content_type="text/markdown",
    install_requires=install_requires,
    package_data={"": ["README.md", "LICENSE"]},
    include_package_data=True,
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "Intended Audience :: Science/Research",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Programming Language :: Python",
    ],
    zip_safe=True,
)
