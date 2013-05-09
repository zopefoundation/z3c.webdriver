##############################################################################
#
# Copyright (c) 2007-2009 Zope Foundation and Contributors.
# All Rights Reserved.
#
# This software is subject to the provisions of the Zope Public License,
# Version 2.1 (ZPL).  A copy of the ZPL should accompany this distribution.
# THIS SOFTWARE IS PROVIDED "AS IS" AND ANY AND ALL EXPRESS OR IMPLIED
# WARRANTIES ARE DISCLAIMED, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED
# WARRANTIES OF TITLE, MERCHANTABILITY, AGAINST INFRINGEMENT, AND FITNESS
# FOR A PARTICULAR PURPOSE.
#
##############################################################################
"""Setup
"""
import os
from setuptools import setup, find_packages


def read(*rnames):
    text = open(os.path.join(os.path.dirname(__file__), *rnames)).read()
    if isinstance(text, bytes):
        text = text.decode('utf-8')
    return text.encode('ascii', 'xmlcharrefreplace').decode()


def alltests():
    import os
    import sys
    import unittest
    # use the zope.testrunner machinery to find all the
    # test suites we've put under ourselves
    import zope.testrunner.find
    import zope.testrunner.options
    here = os.path.abspath(os.path.join(os.path.dirname(__file__), 'src'))
    args = sys.argv[:]
    defaults = ["--test-path", here]
    options = zope.testrunner.options.get_options(args, defaults)
    suites = list(zope.testrunner.find.find_suites(options))
    return unittest.TestSuite(suites)


TESTS_REQUIRE = [
    'zope.testing',
    'lxml',
]


setup(
    name='z3c.webdriver',
    version='0.0.1.dev0',
    author="Adam Groszer and the Zope Community",
    author_email="zope-dev@zope.org",
    description="A wrapper around selenium webdriver and some tools",
    long_description=(
        read('README.txt')
        + '\n\n'
        + read('CHANGES.txt')),
    license="ZPL 2.1",
    keywords="selenium webdriver phantomjs",
    classifiers=[
        'Development Status :: 3 - Alpha',
        'Environment :: Web Environment',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: Zope Public License',
        'Programming Language :: Python',
        'Programming Language :: Python :: 2',
        'Programming Language :: Python :: 2.6',
        'Programming Language :: Python :: 2.7',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.3',
        'Programming Language :: Python :: Implementation :: CPython',
        'Natural Language :: English',
        'Operating System :: OS Independent',
        'Topic :: Internet :: WWW/HTTP',
        'Topic :: Software Development :: Testing'],
    url='https://pypi.python.org/pypi/z3c.webdriver',
    packages=find_packages('src'),
    include_package_data=True,
    package_dir={'': 'src'},
    namespace_packages=['z3c'],
    extras_require=dict(
        extra=[
        ],
        test=TESTS_REQUIRE,
        docs=['z3c.recipe.sphinxdoc'],
    ),
    install_requires=[
        'setuptools',
        'selenium',
    ],
    tests_require = TESTS_REQUIRE,
    test_suite = '__main__.alltests',
    zip_safe=False,
)
