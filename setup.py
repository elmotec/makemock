#!/usr/bin/env python
# encoding: utf-8

"""Packaging script."""

import os
import sys

from setuptools import setup

here = os.path.abspath(os.path.dirname(__file__))
readme = open(os.path.join(here, "README.rst")).read()

if sys.version_info < (3, 3):
    tests_require = ["mock"]
else:
    tests_require = []


setup(
    name="makemock",
    version="0.5",
    author="elmotec",
    author_email="elmotec@gmx.com",
    description="regex based mock generator for googletest",
    license="MIT",
    keywords="regex mock generator googletest",
    url="http://github.com/elmotec/makemock",
    py_modules=["makemock"],
    entry_points={"console_scripts": ["makemock=makemock:main"]},
    long_description=readme,
    test_suite="tests",
    setup_requires=[],
    tests_require=tests_require,
    classifiers=[
        "Development Status :: 5 - Production/Stable",
        "License :: OSI Approved :: MIT License",
        "Environment :: Console",
        "Natural Language :: English",
        "Programming Language :: Python :: 3.6",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.8",
        "Topic :: Software Development",
        "Topic :: Software Development :: Code Generators",
        "Topic :: Text Editors :: Text Processing",
        "Topic :: Text Processing :: Filters",
        "Topic :: Utilities",
        "Intended Audience :: Developers",
    ],
)
