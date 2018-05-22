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
import asyncio

import websockets

import util


class WebSocketClient(object):

    def __init__(self, ser_ip, ser_port, username, passwd):
        self.ser_ip = ser_ip
        self.ser_port = ser_port
        self.username = username
        self.passwd = passwd


    async def run(self):
        ws = None
        try:
            ws = await websockets.connect(''.join(['ws://', self.ser_ip, ':', str(self.ser_port)]), timeout=1)
        finally:
            ws.close()

        # login request
        # message format: {'type': 'auth', 'name': 'shy', 'passwd': '12345'}
        auth_msg = {
            'type': 'auth',
            'name': self.username,
            'passwd': self.passwd
        }
        print('==> Client send: {}'.format(auth_msg))
        await ws.send(json.dumps(auth_msg))
        await self.recevied(ws)

    async def recevied(self, ws):
        recv_task = asyncio.ensure_future(ws.recv())
        while True:
            done, pendding = await asyncio.wait(
                [recv_task], return_when=asyncio.FIRST_COMPLETED)
            if recv_task in done:
                r = recv_task.result()
                if r is not None:
                    print('==> Clinet recevied message: {}'.format(r))
                    recv_task = asyncio.ensure_future(ws.recv())

    def start(self):
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        asyncio.get_event_loop().run_until_complete(self.run())

if __name__ == '__main__':
    c = WebSocketClient('127.0.0.1', 4096, 'shy', '12345')
    c.start()