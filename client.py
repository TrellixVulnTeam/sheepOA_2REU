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

    def __init__(self, thread, ser_ip, ser_port, username, passwd):
        self.thread = thread
        self.ser_ip = ser_ip
        self.ser_port = ser_port
        self.username = username
        self.passwd = passwd


    async def run(self):
        async with websockets.connect(''.join(
            ['ws://', self.ser_ip, ':',
             str(self.ser_port)]), timeout=1) as ws:

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
                    msg = util.js_to_msg(r)
                    if msg._type == 'auth' and msg.content:
                        # login secceed
                        self.thread.login_succeed_signal.emit()
                    elif msg._type == 'auth' and not msg.content:
                        # login failed
                        self.thread.login_failed_signal.emit()
                        # await ws.close(code=1000, reson='')
                    elif msg._type == 'notify' and msg.to == self.username:
                        # to my message
                        self.thread.recevied_notify_signal.emit(r)
                    recv_task = asyncio.ensure_future(ws.recv())

    def start(self):
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        asyncio.get_event_loop().run_until_complete(self.run())
