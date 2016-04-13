#!/usr/bin/python -O
# -*- coding: utf-8 -*-
from __future__ import print_function, unicode_literals, with_statement, division

import socket
import json
import sys
import os

f = sys.argv[1] or 'app.py'
s = socket.socket()
s.connect(('127.0.0.1', 18000))
content = open(f, 'rb').read()
size = os.path.getsize(f)
name = os.path.basename(f)
d = json.dumps(dict(size=size, method='upload', name=name)).encode()
s.send(d + content)
