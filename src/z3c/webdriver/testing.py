###############################################################################
#
# Copyright (c) 2013 Zope Foundation and Contributors.
# All Rights Reserved.
#
# This software is subject to the provisions of the Zope Public License,
# Version 2.1 (ZPL).  A copy of the ZPL should accompany this distribution.
# THIS SOFTWARE IS PROVIDED "AS IS" AND ANY AND ALL EXPRESS OR IMPLIED
# WARRANTIES ARE DISCLAIMED, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED
# WARRANTIES OF TITLE, MERCHANTABILITY, AGAINST INFRINGEMENT, AND FITNESS
# FOR A PARTICULAR PURPOSE.
#
###############################################################################
import time
import logging
import re
import sys
import os
import pprint
import subprocess
import urllib
from tempfile import mkdtemp
import shutil

UPLOAD_FILE_TEMPFOLDER = ''


class RENormalizer(object):
    """Normalizer which can convert text based on regex patterns"""

    def __init__(self, patterns):
        self.patterns = patterns
        self.transformers = map(self._cook, patterns)

    def _cook(self, pattern):
        if callable(pattern):
            return pattern
        regexp, replacement = pattern
        return lambda text: regexp.sub(replacement, text)

    def addPattern(self, pattern):
        patterns = list(self.patterns)
        patterns.append(pattern)
        self.transformers = map(self._cook, patterns)
        self.patterns = patterns

    def __call__(self, data):
        """Normalize a dict or text"""
        if not isinstance(data, basestring):
            data = pprint.pformat(data)
        for normalizer in self.transformers:
            data = normalizer(data)
        return data

    def pprint(self, data):
        """Pretty print data"""
        if isinstance(data, list):
            for item in data:
                print self(item)
        else:
            print self(data)


reNormalizer = RENormalizer([
   (re.compile(u"[0-9]+/[a-zA-Z]+/[0-9]+ [0-9]+:[0-9]+:[0-9]+"),
               r".../.../... ...:...:..."),
   (re.compile(u":[0-9]+ "),  r":... "),
   ])


class LoggingHandler(logging.Handler):
    """Simple logging handler which will temporary install itself"""

    def __init__(self, name, level=1, normalizer=None):
        logging.Handler.__init__(self)
        self.name = name
        if normalizer is None:
            normalizer = reNormalizer
        self.reNormalizer = normalizer
        self.records = []
        self.setLoggerLevel(level)
        self.install()

    def setLoggerLevel(self, level=1):
        self.level = level
        self.oldlevels = {}

    def emit(self, record):
        self.records.append(record)

    def clear(self):
        del self.records[:]

    def install(self):
        """Uninstall current logger if any and install our logger"""
        logger = logging.getLogger(self.name)
        self.oldlevels[self.name] = logger.level
        logger.setLevel(self.level)
        logger.addHandler(self)

    def uninstall(self):
        """Uninstall our logger and install previous installed logger"""
        logger = logging.getLogger(self.name)
        logger.setLevel(self.oldlevels[self.name])
        logger.removeHandler(self)

    def getLines(self, record):
        """Returns the message lines for a given record"""
        return '\n'.join([line
                          for line in record.getMessage().split('\n')
                          if line.strip()])

    def __str__(self):
        return '\n'.join(
            ["%s %s" % (record.levelname, self.getLines(record))
             for record in self.records]
            )

    @property
    def normalized(self):
        """Returns the normalized output"""
        return self.reNormalizer(str(self))


def getLogger(name, level=1, normalizer=None):
    return LoggingHandler(name, level=1, normalizer=None)


# taken from zope.component:
class LayerBase(object):
    """Sane layer base class.

    zope.testing implements an advanced mechanism so that layer setUp,
    tearDown, testSetUp and testTearDown code gets called in the right
    order. These methods are supposed to be @classmethods and should
    not use super() as the test runner is supposed to take care of that.

    In practice, this mechanism turns out not to be useful and
    overcomplicated.  It becomes difficult to pass information into
    layers (such as a ZCML file to load), because the only way to pass
    in information is to subclass, and subclassing these layers leads
    to a range of interactions that is hard to reason about.

    We'd rather just use Python and the super mechanism, as we know how
    to reason about that. This base class is a hack to make this
    possible.

    The hack requires us to set __bases__, __module__ and
    __name__. This fools zope.testing into thinking that this layer
    instance is a class it can work with.

    It'd be better if zope.testing just called a minimal API and
    didn't try to be fancy. Fancy layer inheritance mechanisms can
    then be implemented elsewhere if people want to. But unfortunately
    it does implement a fancy mechanism and we need to fool it.
    """

    __bases__ = ()

    def __init__(self, package, name=None):
        if name is None:
            name = self.__class__.__name__
        self.__name__ = name
        self.__module__ = package.__name__
        self.package = package

    def setUp(self):
        pass

    def tearDown(self):
        pass

    def testSetUp(self):
        pass

    def testTearDown(self):
        pass


# too bad that there's no way to transfer data between a layer and it's tests
# ``testSetUp`` would be ideal, but it does not get the actual test passed :-S
WEBDRIVER = None
WSGISERVER = None


class SeleniumTestLayer(LayerBase):
    """
    Start up and shut down the Selenium server only once
    for each round of tests.
    Set the layer attribute of the test or suite to this class.
    """
    def __init__(self, package, name=None,
                 wsgiServerFactory=None,
                 driverFactory=None):
        super(SeleniumTestLayer, self).__init__(package, name)
        self.wsgiServerFactory = wsgiServerFactory
        self.driverFactory = driverFactory

    def setUp(self):
        self.wsgi = None
        if self.wsgiServerFactory is not None:
            self.wsgi = self.wsgiServerFactory(self)
            global WSGISERVER
            WSGISERVER = self.wsgi

        self.driver = None
        if self.driverFactory is not None:
            # if we want a real clean webdriver for each test
            # we need to start and stop it for each
            self.driver = self.driverFactory(self)
            global WEBDRIVER
            WEBDRIVER = self.driver

    def tearDown(self):
        if self.driver is not None:
            global WEBDRIVER
            WEBDRIVER = None

            self.driver.quit()

        if self.wsgi is not None:
            global WSGISERVER
            WSGISERVER = None

            self.wsgi.quit()


def setUpDoctest(test):
    if WSGISERVER is not None:
        test.globs['wsgi'] = WSGISERVER

    if WEBDRIVER is not None:
        driver = test.globs['driver'] = WEBDRIVER
        # trying to clean up our mess -- PhantomJS keeps state
        # XXX: what else could we clean?
        driver.delete_all_cookies()


#def setUpDoctest(test):
#    if WSGISERVER is None:
#        start_server(test)
#        test.stopWSGIServerOnTearDown = True
#    else:
#        test.stopWSGIServerOnTearDown = False
#
#    if WEBDRIVER is None:
#        args = ['--remote-debugger-port=9011']
#        driver = test.globs['driver'] = create_phantom_driver(args)
#        test.stopWebDriverOnTearDown = True
#    else:
#        driver = test.globs['driver'] = WEBDRIVER
#        # XXX, big one:
#        #      phantomjs behaves as ONE browser instance
#        #      that means cookies and ANY state is kept between invocations
#        #      unless the driver is stopped and started again
#        #      here we're trying to clear at least the cookies
#        #      OTOH, starting and stopping phantomjs takes around 1.5 secs
#        driver.delete_all_cookies()
#        test.stopWebDriverOnTearDown = False
#    # test.globs['browser'] = browser.SeleniumBrowser(test.globs['driver'])
#
#    def wait():
#        while driver.execute_script("return (document.ajaxRequestsInProcess | 0)") != 0:
#            time.sleep(0.01)
#
#    test.globs['waitForAjax'] = wait
#
#
#def tearDownDoctest(test):
#    if test.stopWebDriverOnTearDown:
#        test.globs['driver'].quit()
#    if test.stopWSGIServerOnTearDown:
#        stop_server(test)
