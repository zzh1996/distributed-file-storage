#!/usr/bin/python -O
# -*- coding: utf-8 -*-
from __future__ import print_function, unicode_literals, with_statement, division

import socket
import json
import os

s = socket.socket()
s.connect(('127.0.0.1', 18000))
content = open('app.py', 'rb').read()
size = os.path.getsize('app.py')
d = json.dumps(dict(size=size, method='upload', name='app.py')).encode()
s.send(d + content)
