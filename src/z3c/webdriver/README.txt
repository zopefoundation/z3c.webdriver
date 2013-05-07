======
README
======

This package provides a setup and teardown concept for WSGI server
applications and a test headless Selenium Webdriver browser. This is
usefull for real application tests using an almost real browser.
We use Selenium Webdriver, which uses the HtmlBrowser headless browser
with the Rhino JavaScript engine. This can be set to use a "real" browser
like Firefox or IE with little more work.
Mechanize and other mechanize based zope testbrowser can not execute
javascript.

  >>> from z3c.webdriver.browser import SeleniumBrowser


Testing
-------

This test uses a realistic setup like you will us in your application tests.
Let's setup a WSGIBrowser and start accessing our server:

  >>> browser = SeleniumBrowser(driver)
  >>> appURL = 'http://localhost:9090/'
  >>> browser.open(appURL + 'test.html')

  >>> browser.url
  u'http://localhost:9090/test.html'

  >>> print browser.html
  <html>Test Response</html>


Let's setup a second browser before we close the first one:

  >>> browser2 = SeleniumBrowser(driver)
  >>> browser2.open(appURL + 'hello.html')
  >>> browser2.url
  u'http://localhost:9090/hello.html'

#Now close them:
#
#  >>> browser.close()
#
#  >>> browser2.close()
#
#As you can see, our browser is no available anymore. Another call after close
#a browser will end with a RuntimeError:
#
#  >>> browser.open(appURL + 'test.html')
#  Traceback (most recent call last):
#  ...
#  URLError: <urlopen error [Errno 111] Connection refused>
#
#Close a browser twice will not raise any error:
#
#Don't close unless the driver was started by this test
#
#  >>> browser.close()
