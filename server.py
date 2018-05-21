#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
@Author: yushuibo
@Copyright (c) 2018 yushuibo. All rights reserved.
@Licence: GPL-2
@Email: hengchen2005@gmail.com
@File: server.py
@Create: 2018-05-20 19:11:41
@Last Modified: 2018-05-20 19:11:41
@Desc: --
"""

import sys
import json
import queue
import asyncio

import websockets

import util


msg_queue = queue.Queue()

class GraceFuture(asyncio.Future):
    def __init__(self):
        super(GraceFuture, self).__init__()

    def set_result_default(self, result):
        if not self.done():
            self.set_result(result)
        return self.result()


class Client(object):
    users = {'shy': '12345', 'tom': 'test'}

    def __init__(self, cid, ws):
        self.cid = cid
        self.ws = ws
        self.username = None
        self.islogin = False
        self.isalive = True
        self.future = GraceFuture()

    async def produce(self):
        print('==> Server client produce a future!')
        await self.future
        result = self.future.result()
        self.future = GraceFuture()
        return result

    def login(self, d_msg):
        print('==> Server client login: {}'.format(d_msg))
        if d_msg['name'] in Client.users and d_msg['passwd'] == Client.users[d_msg['name']]:
            self.islogin = True
        else:
            self.islogin = False
        self.username = d_msg['name']

    def pre_send(self, message):
        print('==> Server client pre_send: {}'.format(message))
        self.future.set_result_default([]).append(message)


class Server(object):
    def __init__(self):
        self.ra_to_client = {}  # remote-address -> client mapping

    def get_clients(self):
        #  print('==> Server clients: {}'.format(self.ra_to_client))
        return self.ra_to_client.values()

    def auth_resp(self, client):
        clients = self.get_clients()
        resp = util.ResponseMsg('auth', None, client.username,
                                client.islogin).to_json()
        for client in clients:
            print('==> Server response message to client: {}-->{}'.format(
                resp, client.username))
            client.pre_send(resp)

    def ws_message_handle(self, ws, message):
        print('==> Server handle message: {}'.format(message))
        ra = ws.remote_address
        client = self.ra_to_client.get(ra, None)
        d_msg = json.loads(message)
        if client is not None and d_msg['type'] == 'auth':
            client.login(d_msg)
            self.auth_resp(client)

    async def ws_handler(self, ws, path):
        ra = ws.remote_address
        client = Client(len(self.ra_to_client), ws)
        self.ra_to_client[ra] = client
        print('==> Server accept client: {}'.format(ra))

        presend_task = asyncio.ensure_future(client.produce())
        recevied_task = asyncio.ensure_future(ws.recv())

        while client.isalive:
            done, pendding = await asyncio.wait(
                [presend_task, recevied_task],
                return_when=asyncio.FIRST_COMPLETED)

            # send message
            if presend_task in done:
                messages = presend_task.result()
                if ws.open:
                    for m in messages:
                        await ws.send(m)
                        print('==> Server send: {}'.format(m))
                    presend_task = asyncio.ensure_future(client.produce())
                else:
                    client.isalive = False

            # recevied message
            if recevied_task in done:
                message = recevied_task.result()
                if message is None:
                    client.isalive = False
                else:
                    print('==> Server recevied: {}'.format(message))
                    self.ws_message_handle(ws, message)
                    recevied_task = asyncio.ensure_future(ws.recv())

        del self.ra_to_client[ra]

    def run(self):
        start_server = websockets.serve(self.ws_handler, '127.0.0.1', 4096)
        asyncio.get_event_loop().run_until_complete(start_server)
        asyncio.get_event_loop().run_forever()


if __name__ == '__main__':
    ser = Server()
    ser.run()
    sys.exit(ser)
