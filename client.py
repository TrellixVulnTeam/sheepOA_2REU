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
import queue
import asyncio
import websockets

msgq = queue.Queue()

user = {'shy': '12345'}


async def login():
    async with websockets.connect('ws://localhost:4096') as ws:
        # login
        print('==> Client send: {}'.format(user))
        await ws.send(json.dumps(user))
        await recv_notify(ws)


async def recv_notify(websocket):
    recv_task = asyncio.ensure_future(websocket.recv())
    while True:
        done, pendding = await asyncio.wait(
            [recv_task], return_when=asyncio.FIRST_COMPLETED)
        if recv_task in done:
            notify = recv_task.result()
            if notify is not None:
                print('==> Clinet recevied: {}'.format(notify))
                recv_task = asyncio.ensure_future(websocket.recv())


asyncio.get_event_loop().run_until_complete(login())
