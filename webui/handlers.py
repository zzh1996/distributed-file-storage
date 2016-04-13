#!/usr/bin/python -O
# -*- coding: utf-8 -*-
from __future__ import print_function, unicode_literals, with_statement, division

import os

from tornado.web import RequestHandler
from tornado.escape import url_unescape
from tornado.tcpserver import TCPServer
from tornado import iostream
from tornado import websocket
from tornado import gen

import json
import socket

CHUNK_SIZE = 1024 * 64

@gen.coroutine
def pipe(source, dest, size):

    toread = min(CHUNK_SIZE, size)
    while toread > 0:
        data = yield source.read_bytes(toread)
        yield dest.write(data)
        size -= CHUNK_SIZE
        toread = min(CHUNK_SIZE, size)
    source.close()
    dest.close()

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

        return True
        # raise NotImplementedError('Need to be override!')

    def handle_stream(self, stream, address):

        self.write_message(json.dumps(dict(host=address[0], port=address[1], event='connect')))
        stream.read_until(b'}', lambda data: self._on_header(data, stream, address))

    @gen.coroutine
    def _on_header(self, data, stream, addr):

        header = json.loads(data.decode('utf-8'))
        header['addr'] = addr
        handler = self._req_handlers[header.get('method', '')]
        yield handler(stream, header)

    @gen.coroutine
    def receive_from_remote(self, source, header):

        fp = os.path.join(self._storage, header.get('name', 'newfile'))
        to_file = open(fp, 'wb')
        dest = iostream.PipeIOStream(to_file.fileno())
        yield pipe(source, dest, header.get('size'))
        self.write_message(json.dumps(dict(name=header['name'], event='upload-success')))

    @gen.coroutine
    def push_to_remote(self, dest, header):

        fp = os.path.join(self._storage, header.get('name', 'newfile'))
        size = os.path.getsize(fp)
        yield dest.write(json.dumps({'size': size, 'method': 'download'}).encode('utf-8'))
        from_file = open(fp, 'rb')
        source = iostream.PipeIOStream(from_file.fileno())
        yield pipe(source, dest, size)
        self.write_message(json.dumps(dict(name=header['name'], event='download-success')))


class BaseHandler(RequestHandler):

    pass


class MainHandler(BaseHandler):

    def get(self):
        self.render('index.html', port=self.application.port)


class UploadHandler(BaseHandler):

    @gen.coroutine
    def get(self):

        @gen.coroutine
        def send_upload_request():
            d = {'name': name, 'size': size, 'method': 'upload'}
            yield stream.write(json.dumps(d).encode('utf-8'))
            f = open(path, 'rb')
            source = iostream.PipeIOStream(f.fileno())
            yield pipe(source, stream, size)

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
            stream = iostream.IOStream(sock)
            yield stream.connect((host, port))
            yield send_upload_request()
        else:
            self.set_status(400)
            return self.finish('Invalid args: $path, $host, $port')


class DownloadHandler(BaseHandler):

    @gen.coroutine
    def get(self):

        @gen.coroutine
        def send_download_request():
            d = {'name': name, 'method': 'download'}
            yield stream.write(json.dumps(d).encode('utf-8'))
            header = yield stream.read_until(b'}')
            header = json.loads(header.decode('utf-8'))
            fp = os.path.join(self.application.file_server._storage, path)
            f = open(fp , 'wb')
            dest = iostream.PipeIOStream(f.fileno())
            yield pipe(stream, dest, header.get('size'))

        path = self.get_query_argument('path', '')
        host = self.get_query_argument('host', '')
        port = self.get_query_argument('port', 18000)

        path = url_unescape(path)
        port = int(port)
        print(path, port, host)

        if all((path, host)) and os.path.isfile(path):
            print('{} -> {}:{}'.format(path, host, port))

            name = os.path.basename(path)
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            stream = iostream.IOStream(sock)
            yield stream.connect((host, port))
            yield send_download_request()
        else:
            self.set_status(400)
            return self.finish('Invalid args: $path, $host, $port')

