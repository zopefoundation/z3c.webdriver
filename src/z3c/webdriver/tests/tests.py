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
import re
import os
import os.path
import doctest
import unittest
from zope.testing import renormalizing

from selenium.webdriver import PhantomJS

import z3c.webdriver
import z3c.webdriver.server
import z3c.webdriver.testing


JQUERY_VERSION = '1.7.1'

JQUERY_FILENAME = 'jquery-%s.js' % JQUERY_VERSION

JQUERY_URL = 'http://localhost:9090/%s' % JQUERY_FILENAME


HERE = os.path.dirname(__file__)
JQUERY = os.path.join(HERE, JQUERY_FILENAME)


# test application
SEARCH_HTML = """<!DOCTYPE html PUBLIC "-//W3C//DTD XHTML 1.0 Strict//EN" "http://www.w3.org/TR/xhtml1/DTD/xhtml1-strict.dtd">
<html xmlns="http://www.w3.org/1999/xhtml">
<head>
  <script type="text/javascript" src="%(jQueryURL)s"></script>
  <script type="text/javascript">
    var state = 'initialized';
    $(document).ready(function() {
      state = 'ready';
      $('#form-widgets-text').val('search something');
      $('#form-widgets-submit').click(function() {
        $('#form').submit();
      });
    });
  </script>
</head>
<body>
  <form action="./search.html" method="POST" id="form">
    <label>text
    <input type="text"
           id="form-widgets-text"
           name="form.widgets.text" value="" /></label>
    <label for="form-widgets-submit">submit</label>
    <input type="button"
           id="form-widgets-submit"
           value="submit me" />

    %(result)s
  </form>
</body>
</html>
"""

SEARCH_RESULT = """
<div id="result">
  <strong>Result</strong>
  <div class="item">here comes your search result</div>
</div>
"""

POST_HTML = """<!DOCTYPE html PUBLIC "-//W3C//DTD XHTML 1.0 Strict//EN" "http://www.w3.org/TR/xhtml1/DTD/xhtml1-strict.dtd">
<html xmlns="http://www.w3.org/1999/xhtml">
<head>
  <script type="text/javascript" src="%(jQueryURL)s"></script>
  <script type="text/javascript">
    var state = null;
    $(document).ready(function() {
      // load asap
      $.ajax({
        url: "http://localhost:9090/post-first.html",
        type: 'POST',
        dataType: 'json',
        processData: false,
        async: false,
        success: function(data, textStatus) {
          $('#result').html(data.result);
          $('#status').html(textStatus);
        },
        error: function(jqXHR, textStatus, errorThrown) {
          $('#result').html("FIRST ERROR");
          $('#status').html(textStatus);
        }
      });
      // clickable json loader
      $('#clickable').click(function() {
        $.ajax({
          url: "http://localhost:9090/post-second.html",
          type: 'POST',
          dataType: 'json',
          processData: false,
          async: false,
          success: function(data, textStatus) {
            $('#result').html(data.result);
            $('#status').html(textStatus);
          },
          error: function(jqXHR, textStatus, errorThrown) {
            $('#result').html("SECOND ERROR");
            $('#status').html(textStatus);
          }
        });
      });
    });
  </script>
</head>
<body>
  <form action="http://localhost:9090/post-nada.html" method="POST" id="form">
    <input type="button"
           id="clickable"
           value="clickable" />
    <div id="result">nada</div>
    <div id="status">nada</div>
  </form>
</body>
</html>
"""
POST_INIT = '{"id":"jsonid", "result": "FIRST DATA", "error":""}'
POST_RESULT = '{"id":"jsonid", "result": "SECOND DATA", "error":""}'

UPLOAD_HTML = """<!DOCTYPE html PUBLIC "-//W3C//DTD XHTML 1.0 Strict//EN" "http://www.w3.org/TR/xhtml1/DTD/xhtml1-strict.dtd">
<html xmlns="http://www.w3.org/1999/xhtml">
<head><title>title</title>
</head>
<body>
  <form action="upload.html" method="POST" id="form">
    <label for="Photo">Photo</label>
    <input type="file" name="Photo" id="Photo" value='' />
    <input type="submit" name="Add" id="Add" value="Add" />
  </form>
</body>
</html>
"""

CONTROLS_HTML = """<!DOCTYPE html PUBLIC "-//W3C//DTD XHTML 1.0 Strict//EN" "http://www.w3.org/TR/xhtml1/DTD/xhtml1-strict.dtd">
<html xmlns="http://www.w3.org/1999/xhtml">
<head>
</head>
<body>
  <form action="./search.html" method="POST" id="form">
    <label>text
    <input type="text"
           id="form-widgets-text"
           name="form.widgets.text" value="search something" /></label>
    <label for="form-widgets-submit">submit</label>
    <input type="button"
           id="form-widgets-submit"
           value="submit me" />

    Select some items:
    <input type="checkbox"
           id="form-widgets-checkMe-1"
           name="form.widgets.checkbox"
           value="1" /> Checkbox one<br />
    <input type="checkbox"
           id="form-widgets-checkMe-2"
           name="form.widgets.checkbox"
           value="2" /> Checkbox two<br />
    <input type="checkbox"
           id="form-widgets-checkMe-3"
           name="form.widgets.checkbox"
           checked="checked"
           value="3" /> Checkbox three<br />

    Select one:
    <input type="radio"
           id="form-widgets-radioMe-1"
           name="form.widgets.radio"
           checked="checked"
           value="1" /> Radio one<br />
    <input type="radio"
           id="form-widgets-radioMe-2"
           name="form.widgets.radio"
           value="2" /> Radio two<br />
    <input type="radio"
           id="form-widgets-radioMe-3"
           name="form.widgets.radio"
           value="3" /> Radio three<br />

    <label>password
    <input type="password"
           id="form-widgets-password"
           name="form.widgets.password" /></label>

    <label>textarea
    <textarea
           id="form-widgets-textarea"
           name="form.widgets.textarea">
           foobar
           </textarea>
    </label>

    <label for="form-widgets-select">select</label>
    <select id="form-widgets-select"
            name="form.widgets.select"
            size="1">
        <option value="">(nothing selected)</option>
        <option value="AFG">Afghanistan</option>
        <option value="ALB">Albania</option>
        <option value="DZA">Algeria</option>
    </select>

    <label for="form-widgets-multiselect">multiselect</label>
    <select id="form-widgets-multiselect"
            name="form.widgets.multiselect"
            multiple="multiple"
            size="1">
        <option value="">(nothing selected)</option>
        <option value="jane">Jane</option>
        <option value="john" selected="selected">John</option>
        <option value="dave">Dave</option>
    </select>

    <input id="LOGIN" type="submit" class="button" name="LOGIN" value="Log in" />
    <label for="ambiguous-widget1">multiple</label>
    <input type="submit" id="ambiguous-widget1" value="multiple1" name="multiple" />
    <label for="ambiguous-widget2">multiple</label>
    <input type="submit" id="ambiguous-widget2" value="multiple2" name="multiple" />

    %(result)s
  </form>

  <a href="search.html#link">Controller/In</a>
</body>
</html>
"""


class WSGITestApplication(object):
    """WSGI test application"""

    def __init__(self):
        self.counts = {}

    def __call__(self, environ, start_response):
        """Simple test application which can handle some urls"""
        path = environ['PATH_INFO']
        count = self.counts.setdefault(path, 0)
        self.counts[path] += 1

        # browser.txt test data
        if path.endswith('test.html'):
            start_response('200 Ok',
                           [('Content-Type', 'application/xhtml+xml; charset=utf-8'), ])
            return ['<html>Test Response</html>']
        elif path.endswith('hello.html'):
            q = environ.get('QUERY_STRING')
            if q:
                name = q.split('=')[1]
            else:
                name = 'not defined'
            start_response('200 Ok',
                           [('Content-Type', 'application/xhtml+xml; charset=utf-8'), ])
            return ['<html>Hello %s</html>' % name]
        elif path.endswith('counter.html'):
            start_response('200 Ok',
                           [('Content-Type', 'application/xhtml+xml; charset=utf-8'), ])
            return ['<html><p>Call %d, path %s</p></html>' % (count, path)]
        elif path.endswith('search.html'):
            if environ['CONTENT_TYPE'] == 'application/x-www-form-urlencoded':
                # this is a search form submit request
                result = SEARCH_RESULT
            else:
                result = '<!-- no result given -->'
            data = {'jQueryURL': JQUERY_URL,
                    'result': result}
            start_response('200 Ok',
                           [('Content-Type', 'application/xhtml+xml; charset=utf-8'), ])
            return [SEARCH_HTML % data]

        # uploads test
        elif path.endswith('upload.html'):
            start_response('200 Ok',
                           [('Content-Type', 'application/xhtml+xml; charset=utf-8'), ])
            return [UPLOAD_HTML]

        # getControl tests
        elif path.endswith('controls.html'):
            start_response('200 Ok',
                           [('Content-Type', 'application/xhtml+xml; charset=utf-8'), ])
            return [CONTROLS_HTML]

        # ajax.txt test data
        elif path.endswith('post.html'):
            data = {'jQueryURL': JQUERY_URL}
            start_response('200 Ok',
                           [('Content-Type', 'application/xhtml+xml; charset=utf-8'), ])
            return [POST_HTML % data]
        elif path.endswith('post-first.html'):
            start_response('200 Ok',
                           [('Content-Type', 'application/javascript'), ])
            return [POST_INIT]
        elif path.endswith('post-second.html'):
            start_response('200 Ok', [('Content-Type', 'application/json'), ])
            return [POST_RESULT]

        # js scripts
        elif path.endswith(JQUERY_FILENAME):
            res = open(JQUERY).read()
            start_response('200 Ok', [
                ('Content-Type', 'application/javascript'),
                ('Content-Length', str(len(res)))
            ])
            return [res]
        else:
            start_response('404 Not Found', [
                ('Content-Type', 'application/xhtml+xml; charset=utf-8'), ])
            return ['<div>Not Found</div>']


def setUpWSGITestApplication(test=None):
    app_factory = WSGITestApplication()
    # start a test WSGI server with our application
    z3c.webdriver.server.startWSGIServer('testing', app_factory)


def tearDownWSGITestApplication(test=None):
    # stop the test WSGI server serving our application
    z3c.webdriver.server.stopWSGIServer('testing')


checker = renormalizing.RENormalizing([
    (re.compile('\r\n'), '\n'),
])


def wsgiServerFactory(layer):
    app_factory = WSGITestApplication()
    # start a test WSGI server with our test application
    return z3c.webdriver.server.startWSGIServer('testing', app_factory)


def driverFactory(layer):
    args = ['--remote-debugger-port=9010']
    args = []
    here = os.path.dirname(__file__)
    phantomexec = os.path.join(here, '..', '..', '..', '..', 'bin', 'phantomjs')
    return PhantomJS(phantomexec, service_args=args)


def test_suite():
    optionflags = doctest.NORMALIZE_WHITESPACE | doctest.ELLIPSIS
    layer = z3c.webdriver.testing.SeleniumTestLayer(
        z3c.webdriver,
        wsgiServerFactory=wsgiServerFactory,
        driverFactory=driverFactory)

    readme = doctest.DocFileSuite('../README.txt',
                                  #setUp=setUpWSGITestApplication,
                                  #tearDown=tearDownWSGITestApplication,
                                  setUp=z3c.webdriver.testing.setUpDoctest,
                                  optionflags=optionflags,
                                  checker=checker)
    readme.layer = layer

    ajax = doctest.DocFileSuite('ajax.txt',
                                #setUp=setUpWSGITestApplication,
                                #tearDown=tearDownWSGITestApplication,
                                setUp=z3c.webdriver.testing.setUpDoctest,
                                optionflags=optionflags,
                                checker=checker)
    ajax.layer = layer
    browsert = doctest.DocFileSuite('browser.txt',
                                    #setUp=setUpWSGITestApplication,
                                    #tearDown=tearDownWSGITestApplication,
                                    setUp=z3c.webdriver.testing.setUpDoctest,
                                    optionflags=optionflags,
                                    checker=checker)
    browsert.layer = layer
    controlst = doctest.DocFileSuite('controls.txt',
                                     #setUp=setUpWSGITestApplication,
                                     #tearDown=tearDownWSGITestApplication,
                                     setUp=z3c.webdriver.testing.setUpDoctest,
                                     optionflags=optionflags,
                                     checker=checker)
    controlst.layer = layer
    # server.txt does not need selenium server, so not in SeleniumTestLayer:
    servert = doctest.DocFileSuite('server.txt',
                                   optionflags=optionflags,
                                   checker=checker)

    return unittest.TestSuite((
        ajax,
        readme,
        browsert,
        servert,
        controlst,
    ))


if __name__ == '__main__':
    unittest.main(defaultTest='test_suite')
