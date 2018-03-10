# pylint: disable=no-member, no-name-in-module, import-error

from __future__ import absolute_import
import glob
import os
import distutils.command.sdist
import distutils.log
import subprocess
from setuptools import Command, setup
import setuptools.command.sdist


# Patch setuptools' sdist behaviour with distutils' sdist behaviour
setuptools.command.sdist.sdist.run = distutils.command.sdist.sdist.run

VERSION_INFO = {}
CWD = os.path.abspath(os.path.dirname(__file__))
with open(os.path.join(CWD, "dxlbootstrap", "_version.py")) as f:
    exec(f.read(), VERSION_INFO) # pylint: disable=exec-used

class LintCommand(Command):
    """
    Custom setuptools command for running lint
    """
    description = 'run lint against project source files'
    user_options = []
    def initialize_options(self):
        pass
    def finalize_options(self):
        pass
    def run(self):
        self.announce("Running pylint for library source files and tests",
                      level=distutils.log.INFO)
        subprocess.check_call(["pylint", "dxlbootstrap", "tests"] +
                              glob.glob("*.py"))

class CiCommand(Command):
    """
    Custom setuptools command for running steps that are performed during
    Continuous Integration testing.
    """
    description = 'run CI steps (lint, test, etc.)'
    user_options = []
    def initialize_options(self):
        pass
    def finalize_options(self):
        pass
    def run(self):
        self.run_command("lint")
        self.run_command("test")

TEST_REQUIREMENTS = ["mock", "nose", "pylint"]

DEV_REQUIREMENTS = TEST_REQUIREMENTS + ["sphinx"]

setup(
    # Application name:
    name="dxlbootstrap",

    # Version number:
    version=VERSION_INFO["__version__"],

    # Requirements
    install_requires=[
        "dxlclient"
    ],

    tests_require=TEST_REQUIREMENTS,

    extras_require={
        "dev": DEV_REQUIREMENTS,
        "test": TEST_REQUIREMENTS
    },

    test_suite="nose.collector",

    # Application author details:
    author="McAfee, Inc.",

    # License
    license="Apache License 2.0",

    keywords=['opendxl', 'dxl', 'mcafee', 'bootstrap'],

    # Packages
    packages=[
        "dxlbootstrap",
        "dxlbootstrap.generate",
        "dxlbootstrap.generate.core",
        "dxlbootstrap.generate.templates",
        "dxlbootstrap.generate.templates.app",
        "dxlbootstrap.generate.templates.app.static",
        "dxlbootstrap.generate.templates.app.static.app",
        "dxlbootstrap.generate.templates.app.static.app.code",
        "dxlbootstrap.generate.templates.app.static.config",
        "dxlbootstrap.generate.templates.app.static.doc",
        "dxlbootstrap.generate.templates.app.static.doc.sdk",
        "dxlbootstrap.generate.templates.app.static.sample",
        "dxlbootstrap.generate.templates.app.static.sample.basic",
        "dxlbootstrap.generate.templates.app.static.sample.basic.code",
        "dxlbootstrap.generate.templates.client",
        "dxlbootstrap.generate.templates.client.static",
        "dxlbootstrap.generate.templates.client.static.client",
        "dxlbootstrap.generate.templates.client.static.client.code",
        "dxlbootstrap.generate.templates.client.static.sample",
        "dxlbootstrap.generate.templates.client.static.sample.basic",
        "dxlbootstrap.generate.templates.client.static.sample.basic.code",
        "dxlbootstrap.generate.templates.client.static.doc",
        "dxlbootstrap.generate.templates.client.static.doc.sdk"
    ],

    package_data={'': ['*.tmpl']},

    # Details
    url="http://www.mcafee.com/",

    description="OpenDXL Bootstrap Application",

    long_description=open('README').read(),

    classifiers=[
        "Development Status :: 4 - Beta",
        "Topic :: Software Development :: Libraries :: Python Modules",
        "License :: OSI Approved :: Apache Software License",
        "Programming Language :: Python",
        "Programming Language :: Python :: 2",
        "Programming Language :: Python :: 2.7",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.4",
        "Programming Language :: Python :: 3.5",
        "Programming Language :: Python :: 3.6"
    ],

    cmdclass={
        "ci": CiCommand,
        "lint": LintCommand
    }
)
