#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
@Author: yushuibo
@Copyright (c) 2018 yushuibo. All rights reserved.
@Licence: GPL-2
@Email: hengchen2005@gmail.com
@File: client.py
@Create: 2018-05-19 23:57:45
@Last Modified: 2018-05-19 23:57:45
@Desc: --
"""

import json
import threading
import asyncio

import websockets

import util


class WebSocketClient(object):

    def __init__(self, ser_ip, ser_port, username, passwd):
        self.ser_ip = ser_ip
        self.ser_port = ser_port
        self.username = username
        self.passwd = passwd
        self.handlers = {}  # handler -> event mapping

    def add_handler(self, event, funcs):
        self.handlers[event] = funcs

    async def run(self):
        async with websockets.connect(''.join(
                ['ws://', self.ser_ip, ':', str(self.ser_port)])) as ws:
            # login request
            # message format: {'type': 'auth', 'name': 'shy', 'passwd': '12345'}
            auth_msg = {'type': 'auth', 'name': self.username,
                        'passwd': self.passwd}
            print('==> Client send: {}'.format(auth_msg))
            await ws.send(json.dumps(auth_msg))
            await self.recevied(ws)

    async def recevied(self, ws):
        recv_task = asyncio.ensure_future(ws.recv())
        while True:
            done, pendding = await asyncio.wait([recv_task],
                                                return_when=asyncio.FIRST_COMPLETED)
            if recv_task in done:
                r = recv_task.result()
                if r is not None:
                    print('==> Clinet recevied notify: {}'.format(r))
                    msg = util.js_to_msg(r)
                    if msg._type == 'auth' and msg.content:
                        login_succeed(r)
                        # login secceed
                        for handle in self.handlers['login_succeed']:
                            await handle(r)
                    elif msg._type == 'auth' and not msg.content:
                        # login failed
                        for handle in self.handlers['login_failed']:
                            handle(r)
                    elif msg._type == 'notify' and msg.to == self.username:
                        # to my message
                        for handle in self.handlers['recevied_notify']:
                            await handle(r)
                    recv_task = asyncio.ensure_future(ws.recv())

    def start(self):
        loop = asyncio.new_event_loop()
        loop.run_until_complete(self.run())


def login_succeed(r):
    print('==> Login succeed!')


def login_failed(r):
    print('==> Login failed!')


def recevied_notify(r):
    print('==> Recevied notify!')


if __name__ == '__main__':
    client = WebSocketClient('127.0.0.1', 4096, 'shy', '12345')
    client.add_handler('login_succeed', [login_succeed])
    client.add_handler('login_failed', [login_failed])
    client.add_handler('recevied_notify', [recevied_notify])
    client.start()
