#!/usr/bin/env python3
# encoding: utf-8

#usage: telnet localhost 8888

import socket

s=socket.socket()
s.bind(('127.0.0.1',8888))
s.listen(5)
print('Server Listening')

try:
    while True:
        c,addr=s.accept()
        print(addr)
        c.send(b'Hello\n')
        c.close()
finally:
    s.close()
    print('Server closed')


