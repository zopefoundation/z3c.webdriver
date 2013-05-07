z3c.webdriver
=============

This package provides tools and wrappers around ``selenium.webdriver``.

We specially care about ``selenium.webdriver.PhantomJS``, because:

  - it's easy to deploy, it's a single executable, ``gp.recipe.phantomjs`` works
  - it's built on ``webkit``
  - it can be debugged with a ``Chromium`` / ``Chrome`` browser, incl. breakpoints

Things to watch out for:

  - the headless browser is truly ``async``, that means an AJAX click does NOT
    wait for the AJAX request to complete, you explicitely need to wait for it
  - any single call to PhantomJS via selenium takes TIME
  - zope.testbrowser supporting methods like ``getControl`` are slow now

WARNING
========
This is WORK IN PROGRESS
