from setuptools import setup
import distutils.command.sdist

import setuptools.command.sdist

# Patch setuptools' sdist behaviour with distutils' sdist behaviour
setuptools.command.sdist.sdist.run = distutils.command.sdist.sdist.run

VERSION = __import__('dxlbootstrap').get_version()

dist = setup(
    # Application name:
    name="dxlbootstrap",

    # Version number:
    version=VERSION,

    # Requirements
    install_requires=[
    ],

    # Application author details:
    author="McAfee, Inc.",

    # License
    license="Apache License 2.0",

    keywords=['opendxl', 'dxl', 'mcafee', 'bootstrap'],

    # Packages
    packages=[
        "dxlbootstrap",
        "dxlbootstrap.base",
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
        "dxlbootstrap.generate.templates.app.static.sample.basic.code"
    ],

    package_data={'': ['*.tmpl']},

    # Details
    url="http://www.mcafee.com/",

    description="McAfee DXL Bootstrap Application",

    long_description=open('README').read(),

    classifiers=[
        "Development Status :: 4 - Beta",
        "Topic :: Software Development :: Libraries :: Python Modules",
        "License :: OSI Approved :: Apache Software License",
        "Programming Language :: Python",
        "Programming Language :: Python :: 2.7",
    ],
)
