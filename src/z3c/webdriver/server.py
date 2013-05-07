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
import threading
import logging
import time
import wsgiref.simple_server
from urlparse import urlparse
from SocketServer import ThreadingMixIn
from zope.testing import cleanup

LOGGER = logging.getLogger('z3c.webdriver.server')


class WSGIRequestHandler(wsgiref.simple_server.WSGIRequestHandler):
    """WSGI request handler with HTTP/1.1 and automatic keepalive"""

    # set to HTTP/1.1 to enable automatic keepalive
    protocol_version = "HTTP/1.1"

    def address_string(self):
        """Return the client address formatted for logging.

        We only use host and port without socket.getfqdn(host) for a
        simpler test output.

        """
        host, port = self.client_address[:2]
        return '%s:%s' % (host, port)

    #######################################
    # comment those log methods to write the access log to stderr!
    def _log(self, level, msg):
        """write log to our logger"""
        LOGGER.log(level, msg)

    def log_error(self, format, *args):
        """Write error message log to our logger using ERROR level"""
        msg = "%s - - [%s] %s\n" % (self.address_string(),
                                    self.log_date_time_string(), format % args)
        self._log(logging.ERROR, msg)

    def log_message(self, format, *args):
        """Write simple message log to our logger using INFO level"""
        msg = "%s - - [%s] %s\n" % (self.address_string(),
                                    self.log_date_time_string(), format % args)
        self._log(logging.INFO, msg)
    #
    #######################################


# Must mix here ThreadingMixIn, otherwise quick concurrent requests
# seem to lock up the server
class MyWSGIServer(ThreadingMixIn, wsgiref.simple_server.WSGIServer):
    pass


class ServerThread(threading.Thread):
    """ Run WSGI server on a background thread.

    Pass in WSGI app object and serve pages from it for Selenium browser.
    """

    def __init__(self, app, url):
        threading.Thread.__init__(self)
        self.app = app
        self.url = url
        self.srv = None

    def run(self):
        """
        Open WSGI server to listen to HOST_BASE address
        """
        parts = urlparse(self.url)
        domain, port = parts.netloc.split(":")
        self.srv = wsgiref.simple_server.make_server(
            domain, int(port), self.app,
            server_class=MyWSGIServer,
            handler_class=WSGIRequestHandler)
        self.srv.timeout = 0.5
        try:
            self.srv.serve_forever()
        except:
            import traceback
            traceback.print_exc()
            # Failed to start
            self.srv = None

    def quit(self):
        """
        """
        if self.srv:
            self.srv.shutdown()
            self.srv.server_close()
            time.sleep(0.1)  # give it a bit of time to stop
            self.srv = None


def start_server(app, url='http://localhost:9090'):
    server = ServerThread(app, url)
    server.daemon = True  # don't hang on exceptions
    server.start()
    time.sleep(0.1)  # give it a bit of time to start
    return server


WSGI_SERVERS = None


def startWSGIServer(name, app, url='http://localhost:9090'):
    """Serve a WSGI aplication on the given host and port referenced by name"""
    global WSGI_SERVERS
    if WSGI_SERVERS is None:
        WSGI_SERVERS = {}
    server = start_server(app, url)
    WSGI_SERVERS[name] = {'url': url, 'server': server}
    return server


def stopWSGIServer(name):
    """Stop WSGI server by given name reference"""
    global WSGI_SERVERS
    if WSGI_SERVERS is not None:
        server = WSGI_SERVERS[name]['server']
        server.quit()
        server.join(1)
        del WSGI_SERVERS[name]


def getWSGIApplication(name):
    """Returns the application refenced by name"""
    global WSGI_SERVERS
    if WSGI_SERVERS is not None:
        server = WSGI_SERVERS[name]['server']
        return server.app


def stopServers():
    global WSGI_SERVERS
    if WSGI_SERVERS is not None:
        names = list(WSGI_SERVERS.keys())
        for n in names:
            stopWSGIServer(n)
cleanup.addCleanUp(stopServers)
