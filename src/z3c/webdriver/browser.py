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

#
#
# BIG NOTE: make as LESS calls to any WebElement/WebDriver object,
# because every call goes to the java browser
#
#

import re
import time
from urllib2 import URLError
import os.path

from selenium import webdriver
from selenium.webdriver.support.ui import Select
from selenium.common.exceptions import NoSuchElementException


RE_CHARSET = re.compile('.*;charset=(.*)')
UPLOAD_FILE_TEMPFOLDER = '/tmp'


class AmbiguityError(ValueError):
    pass


def _getControlElementFactory(elements, driver, index):
    if elements[0].tag_name == 'input':
        typ = elements[0].get_attribute('type').lower()
        if typ == 'checkbox':
            return WrappedSeleniumCheckboxes(elements, driver)
        elif typ == 'radio':
            return WrappedSeleniumRadios(elements, driver)
    if len(elements) > 1 and index is None:
        raise AmbiguityError('Ambiguity: Multiple elements found')
    else:
        elements = elements[index or 0]
    return WrappedSeleniumElement(elements, driver)


def _getControl(base, driver, label=None, name=None, index=None):
    """
    Mimic zope.testbrowser's getControl
    """
    assert ((label is not None) or (name is not None)), 'Either label or name must be specified'

    if name is not None:
        elements = base.find_elements_by_name(name)
        return _getControlElementFactory(elements, driver, index)
    if label is not None:
        # find all <label...
        elements = base.find_elements_by_tag_name('label')
        elements = [(e.text, e, 'label') for e in elements]
        # also find <input type="submit' value=".. + type="button" value="...
        for e in base.find_elements_by_tag_name('input'):
            typ = e.get_attribute('type')
            if typ in ('submit', 'button'):
                elements.append((e.get_attribute('value'), e, typ))
        for e in base.find_elements_by_tag_name('button'):
            typ = e.get_attribute('type')
            if typ in ('submit', 'button'):
                elements.append((e.text, e, typ))
        found = []
        for element in elements:
            value = element[0]  # the text of the element, e.text above
            if value and label in value:  # XXX: implement REGEX
                found.append(element)
        if found:
            if len(found) > 1 and index is None:
                raise AmbiguityError('Ambiguity: Multiple elements found')
            element = found[index or 0]
            if element[2] == 'label':
                target = element[1].get_attribute('for')
                if target:
                    child = driver.find_element_by_id(target)
                else:
                    types = ('input', 'select', 'textarea', 'button', 'submit')
                    child = None
                    for typ in types:
                        try:
                            child = element[1].find_element_by_tag_name(typ)
                            break
                        except NoSuchElementException:
                            pass
                    if child is None:
                        raise AttributeError('No contained input found')
            else:
                #button or whatever that itself has the label
                child = element[1]
        else:
            raise AssertionError('control not found (got the right label?)')
        return _getControlElementFactory([child], driver, 0)


class WrappedSeleniumCheckboxes(object):
    def __init__(self, elements, driver):
        self.elements = elements
        self.driver = driver

    def getControl(*args):
        raise RuntimeError('getControl().getControl() not supported, use getControl().value() or implement yourself')

    def __getitem__(self, idx):
        return WrappedSeleniumElement(self.elements[idx], self.driver)

    @apply
    def value():
        """See zope.testbrowser.interfaces.IControl"""

        def fget(self):
            if (len(self.elements) == 1 and not
                self.elements[0].get_attribute('value')):
                return bool(self.elements[0].get_attribute('checked'))
            return [x.get_attribute('value')
                    for x in self.elements if x.get_attribute('checked')]

        def fset(self, value):
            if len(self.elements) == 1:
                state = self.element.get_attribute('checked')
                if bool(value) != bool(state):
                    self.element.click()
            else:
                if not isinstance(value, list):
                    value = [value]
                for box in self.elements:
                    boxvalue = box.get_attribute('value')
                    checked = box.get_attribute('checked')
                    if boxvalue in value:
                        if not checked:
                            box.click()
                    else:
                        if checked:
                            box.click()
        return property(fget, fset)


class WrappedSeleniumRadios(object):
    def __init__(self, elements, driver):
        self.elements = elements
        self.driver = driver

    def getControl(*args):
        raise RuntimeError('getControl().getControl() not supported, use getControl().value() or implement yourself')

    def __getitem__(self, idx):
        return WrappedSeleniumElement(self.elements[idx], self.driver)

    @apply
    def value():
        """See zope.testbrowser.interfaces.IControl"""

        def fget(self):
            for r in self.elements:
                if r.is_selected():
                    return r.get_attribute('value')
            return None

        def fset(self, value):
            for r in self.elements:
                rvalue = r.get_attribute('value')
                if rvalue == value:
                    r.click()

        return property(fget, fset)


class WrappedSeleniumElement(object):
    """
    Wrap a selenium webdriver element, so we can add some methods
    that we expect from porting over the zope.testbrowser based tests.
    """
    def __init__(self, element, driver):
        self.element = element
        self.driver = driver

    def __getattr__(self, name):
        return getattr(self.element, name)

    @apply
    def value():
        """See zope.testbrowser.interfaces.IControl"""

        def fget(self):
            if self.element.tag_name.lower() == 'select':
                select = Select(self.element)
                rv = []
                for opt in select.options:
                    if opt.is_selected():
                        rv.append(opt.get_attribute('value'))
                if self.element.get_attribute('multiple'):
                    return rv
                else:
                    return rv[0] if rv else None
            return self.element.get_attribute('value')

        def fset(self, value):
            if self.element.tag_name.lower() == 'file':
                pass
            # if self.mech_control.type == 'file':
                # self.mech_control.add_file(value,
                                           # content_type=self.content_type,
                                           # filename=self.filename)
            # select
            elif self.element.tag_name.lower() == 'select':
                select = Select(self.element)
                if self.element.get_attribute('multiple'):
                    select.deselect_all()
                else:
                    value = [value]

                for opt in select.options:
                    v = opt.get_attribute('value')
                    if v in value:
                        value.remove(v)
                        if not opt.is_selected():
                            opt.click()
                if value:
                    raise AttributeError('Options not found: %s' % ','.join(value))
            else:
                # textarea, input type=text
                self.element.clear()
                self.element.send_keys(value)

        return property(fget, fset)

    def add_file(self, stringio, contentType, fileName):
        try:
            # assert that we have the right input type
            assert (self.element.tag_name.lower() == 'input' and
                    self.element.get_attribute('type') == 'file')
        except AssertionError:
            raise AssertionError('File upload works only on input type=file')
        path = os.path.join(UPLOAD_FILE_TEMPFOLDER, fileName)
        # write stringio to temp file
        with open(path, 'w') as tmpfile:
            tmpfile.write(stringio.getvalue())
        self.value = path

    def getControl(self, label=None, name=None, index=None):
        return _getControl(base=self.element, driver=self.driver,
                           label=label, name=name, index=index)


def passthrough(func):
    name = "find_elements_%s" % func.__name__

    def inner(self, *args, **kw):
        els = getattr(self.driver, name)(*args, **kw)
        return els._wrap_returned(els)

    inner.__name__ = func.__name__
    return inner


class SeleniumBrowser(object):
    """
    We add a layer of translation around a Selenium Webdriver
    to make transition from mechanize tests easier.
    """

    def __init__(self, driver, time_to_wait=0.5):
        """
        Implicitly wait for page elements to turn up:
        This means that when you do a browser.get('#selector'),
        the driver will wait some seconds for this thing to turn up if
        it isn't there. This is meant so that any js that might manipulate
        it has time to do its job. It makes testing for not-existing
        elements slow though.
        """
        self.driver = driver
        self.driver.implicitly_wait(time_to_wait)
        self.driver.set_page_load_timeout(10)
        self.driver.set_script_timeout(10)
        # lxml support
        self.xmlStrict = False
        self._etree = None

    def open(self, url):
        return self.driver.get(url)

    def close(self):
        return self.driver.quit()
    quit = close

    @property
    def url(self):
        return self.driver.current_url

    @property
    def html(self):
        return self.driver.page_source

    @property
    def contents(self):
        return self.driver.page_source.encode('utf-8')

    ########################################
    # zope.testbrowser -ish support
    def getLink(self, text):
        return self.driver.find_element_by_partial_link_text(text)

    def getControl(self, label=None, name=None, index=None):
        return _getControl(base=self.driver, driver=self.driver,
                           label=label, name=name, index=index)
    #
    ########################################

    ########################################
    # shorter names for webdriver methods
    # returns:
    # - single element if there's ONE element
    # - list of elements if there are MORE
    # because in tests you'll anyway except a specific number of elements
    def _wrap_returned(self, items):
        # XXX: wrap the result with a WrappedSeleniumElement,
        #      mostly input elements
        if len(items) == 1:
            return items[0]
        return items

    def by_class_name(self, name):
        """Finds elements by class name.
        """
        els = self.driver.find_elements_by_class_name(name)
        return self._wrap_returned(els)

    def by_css_selector(self, css_selector):
        """Finds elements by css selector.
        """
        els = self.driver.find_elements_by_css_selector(css_selector)
        return self._wrap_returned(els)

    def by_id(self, id):
        """Finds multiple elements by id.
        """
        els = self.driver.find_elements_by_id(id)
        return self._wrap_returned(els)

    def by_link_text(self, text):
        """Finds elements by link text.
        """
        els = self.driver.find_elements_by_link_text(text)
        return self._wrap_returned(els)

    def by_name(self, name):
        """Finds elements by name.
        """
        els = self.driver.find_elements_by_name(name)
        return self._wrap_returned(els)

    def by_partial_link_text(self, link_text):
        """Finds elements by a partial match of their link text.
        """
        els = self.driver.find_elements_by_partial_link_text(link_text)
        return self._wrap_returned(els)

    def by_tag_name(self, name):
        """Finds elements by tag name.
        """
        els = self.driver.find_elements_by_tag_name(name)
        return self._wrap_returned(els)

    def by_xpath(self, xpath):
        """Finds multiple elements by xpath.
        """
        els = self.driver.find_elements_by_xpath(xpath)
        return self._wrap_returned(els)
    #
    ########################################

    ########################################
    # handy shortcuts -- who wants to type
    get = by_css_selector
    __getitem__ = by_css_selector
    #
    ########################################

    def getForm(self, id=None, name=None, action=None, index=None):
        pass
        #  >>> hrmanager.getForm(name='filterform').submit()

    def getCookies(self):
        return self.driver.get_cookies()

    def addCookie(self, cookie):
        return self.driver.add_cookie(cookie)

    def delCookie(self, name):
        return self.driver.delete_cookie(name)
    deleteCookie = delCookie

    def delAllCookies(self):
        return self.driver.delete_all_cookies()
    deleteAllCookies = delAllCookies

    def addHeader(self, name, value):
        """
        Selenium Webdriver does not support adding headers,
        we can fake it for Accept-Language to 'en-us', because
        that's the default for Selenium Webdriver.
        """
        try:
            assert(name == 'Accept-Language')
            assert(value in ['en-us', 'en-us,en'])
        except AssertionError:
            raise AssertionError('No addHeader support, except for Accept-Language/en-us')

    # lxml API
    @property
    def etree(self):
        # import lxml only if used... just in case we do not want to have lxml
        # as a dependency
        import lxml.etree
        import lxml.html

        if self._etree is not None:
            return self._etree
        if self.xmlStrict:
            self._etree = lxml.etree.fromstring(self.html,
                parser=lxml.etree.XMLParser(resolve_entities=False))
        else:
            encoding = 'utf-8'
            # currently we can't get the headers from Selenium Webdriver:
            contentType = None # self.headers.get('Content-Type')
            if contentType is not None:
                match = RE_CHARSET.match(contentType)
                if match is not None:
                    encoding = match.groups()[0]
            parser = lxml.etree.HTMLParser(encoding=encoding,
                remove_blank_text=True, remove_comments=True, recover=True)
            html_as_utf8 = self.html.encode('utf-8')
            self._etree = lxml.etree.fromstring(html_as_utf8, parser=parser)
        return self._etree

    def js(self, command):
        rv = self.driver.execute_script(command)
        return rv
