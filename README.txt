z3c.webdriver
=============

This package provides tools and wrappers around ``selenium.webdriver``.

We specially care about ``selenium.webdriver.PhantomJS``, because:

  - it's easy to deploy, it's a single executable, ``gp.recipe.phantomjs`` works
  - it's built on ``webkit``
  - it can be debugged with a ``Chromium`` / ``Chrome`` browser, incl. breakpoints

Things to watch out for:

  - any single instance of PhantomJS acts as a single browser instance
    that means cookies and whatnot are *shared* if you intantiate more
    browsers for a single driver.
    Workaround could be to start more drivers.
  - the headless browser is truly ``async``, that means an AJAX click does NOT
    wait for the AJAX request to complete, you explicitely need to wait for it
  - any single call to PhantomJS via selenium takes TIME
  - zope.testbrowser supporting methods like ``getControl`` are slow now
  - there are 2 options for setUp/tearDown, either the driver is started and torn
    down with the layer or with each test. Starting and stopping takes around
    1.5-2 secs, so you decide whether you need separation or speed.

WARNING
========
This is WORK IN PROGRESS
