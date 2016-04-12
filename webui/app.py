#!/usr/bin/python -O
# -*- coding: utf-8 -*-
from __future__ import print_function, unicode_literals, with_statement, division

import sys
import os

from tornado.web import Application
from tornado.options import define, options, parse_command_line
import tornado.ioloop
import tornado.httpserver
import tornado.tcpserver

import socket
from handlers import (
    MainHandler,
    WsHandler,
    UploadHandler,
    DownloadHandler,
    FileServer
)

define('port', default=8000, help='run on the given port', type=int)
define(
    'listen',
    default=18000,
    help='tcp server listen on the given port',
    type=int)
HERE = os.path.dirname(os.path.realpath(__file__))


class MyApp(Application):

    def __init__(self, listen=18000, ioloop=None, **kwargs):

        Application.__init__(self, handlers=[
            (r'/', MainHandler),
            (r'/upload', UploadHandler),
            (r'/download', DownloadHandler),
            (r'/ws', WsHandler)],
            template_path=os.path.join(HERE, 'templates'),
            static_path=os.path.join(HERE, 'static'),
            debug=True)

        if not isinstance(listen, int):
            raise ValueError('tran_port need to be int')
        if ioloop is None:
            raise ValueError('Need to pass ioloop')

        self.ioloop = ioloop
        self.file_server = FileServer(io_loop=ioloop)
        self.file_server.bind(listen, None, socket.AF_INET)
        self.file_server.start()


def main():
    parse_command_line()
    ioloop = tornado.ioloop.IOLoop.instance()
    http_server = tornado.httpserver.HTTPServer(
        MyApp(options.listen, ioloop=ioloop))
    # local page
    http_server.listen(options.port, '127.0.0.1')
    try:
        print('listening on {}'.format(options.port))
        ioloop.start()
    except KeyboardInterrupt:
        sys.exit(0)


if __name__ == '__main__':
    main()
