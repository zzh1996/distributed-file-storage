#!/usr/bin/python -O
# -*- coding: utf-8 -*-
from __future__ import print_function, unicode_literals, with_statement, division

import os

from tornado.web import RequestHandler
from tornado.escape import url_unescape
from tornado.tcpserver import TCPServer
from tornado import iostream
from tornado import websocket

import json
import socket

CHUNK_SIZE = 10240

class WsHandler(websocket.WebSocketHandler):

    def __init__(self, *args, **kwargs):

        super().__init__(*args, **kwargs)
        self.application.file_server.write_message = self.write_message

    def open(self):
        # print("WebSocket opened")
        pass

    def on_message(self, message):
        self.write_message(json.dumps({"msg": message}))

    def on_close(self):
        print("WebSocket closed")

    def check_origin(self, origin):
        return True

class FileServer(TCPServer):

    def __init__(self, storage=None, *args, **kwargs):

        super().__init__(*args, **kwargs)

        if storage is None:
            storage = os.path.expanduser('~/.storage')
        else:
            storage = os.path.expanduser(storage)
            storage = os.path.expandvars(storage)
        if os.path.isfile(storage):
            raise ValueError('{} must be folder'.format(storage))
        if not os.path.isdir(storage):
            os.makedirs(storage)
        self._storage = storage
        self._req_handlers = {
                '': lambda *x :x,
                'upload': self.receive_from_remote,
                'download': self.push_to_remote
                }

    # will be override by WsHandler
    def write_message(*args, **kwargs):

        raise NotImplementedError('Need to be override!')

    def handle_stream(self, stream, address):

        self.write_message(json.dumps(dict(host=address[0], port=address[1], event='connect')))
        stream.read_until(b'}', lambda data: self._on_header(data, stream, address))

    def _on_header(self, data, stream, addr):

        header = json.loads(data.decode('utf-8'))
        header['addr'] = addr
        handler = self._req_handlers[header.get('method', '')]
        stream.read_bytes(header.get('size', CHUNK_SIZE),
                lambda data: handler(data, header, stream))

    def receive_from_remote(self, data, header, stream):

        fp = os.path.join(self._storage, header.get('name', 'newfile'))
        to_file = open(fp, 'wb')
        save = iostream.PipeIOStream(to_file.fileno(), io_loop=self.io_loop)
        save.write(data)
        save.close()
        stream.close()
        self.write_message(json.dumps(dict(name=header['name'], event='upload-success')))

    def push_to_remote(self, data, header, stream):

        def worker(data):
            stream.write(data)
            source.read_bytes(CHUNK_SIZE, worker)

        fp = os.path.join(self._storage, header.get('name', 'newfile'))
        from_file = open(fp, 'rb')
        source = iostream.PipeIOStream(from_file.fileno(), io_loop=self.io_loop)
        stream.set_close_callback(lambda : source.close())
        source.read_bytes(CHUNK_SIZE, worker)


class BaseHandler(RequestHandler):

    pass


class MainHandler(BaseHandler):

    def get(self):
        self.render('index.html')


class UploadHandler(BaseHandler):

    def get(self):

        def send_upload_request():
            d = {'name': name, 'size': size, 'method': 'upload'}
            stream.write(json.dumps(d))
            f = open(path, 'rb')
            source = iostream.PipeIOStream(f.fileno())
            source.read_bytes(size, lambda data: send_file(data, source))

        def send_file(data, source):

            stream.write(data)
            source.close()
            stream.close()


        path = self.get_query_argument('path', '')
        host = self.get_query_argument('host', '')
        port = self.get_query_argument('port', 18000)

        path = url_unescape(path)
        port = int(port)
        print(path, port, host)

        if all((path, host)) and os.path.isfile(path):
            print('{} -> {}:{}'.format(path, host, port))

            name = os.path.basename(path)
            size = os.path.getsize(path)
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            stream = iostream.IOStream(sock, io_loop=self.application.ioloop)
            stream.connect((host, port), send_upload_request)
        else:
            self.set_status(400)
            return self.finish('Invalid args: $path, $host, $port')


class DownloadHandler(BaseHandler):

    def get(self):

        path = self.get_query_argument('path', '')
        host = self.get_query_argument('host', '')
        port = self.get_query_argument('port', 18000)

        path = url_unescape(path)
        port = int(port)

        if all((path, host)):
            self.write('{} -> {}:{}'.format(path, host, port))
        else:
            self.set_status(400)
            return self.finish('Invalid args: $path, $host, $port')

