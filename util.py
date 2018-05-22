#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
@Author: yushuibo
@Copyright (c) 2018 yushuibo. All rights reserved.
@Licence: GPL-2
@Email: hengchen2005@gmail.com
@Create: util.py
@Last Modified: 2018/5/21 上午 10:58
@Desc: --
"""

import json
from functools import wraps

class ResponseMsg(object):

    def __init__(self, _type, _from, to, content):
        self._type = _type
        self._from = _from
        self.to = to
        self.content = content

    def to_json(self):
        return json.dumps(
            {'type': self._type, 'from': self._from, 'to': self.to,
             'content': self.content})


def js_to_msg(js):
    d = json.loads(js)
    return ResponseMsg(d['type'], d['from'], d['to'], d['content'])


def signaleton(cls):
    _instance = {}

    @wraps(cls)
    def getinstance(*args, **kwargs):
        if cls not in _instance:
            _instance[cls] = cls(*args, **kwargs)
        return _instance[cls]
    return getinstance


@signaleton
class A(object):
    def out(self):
        print(self)


if __name__ == '__main__':
    a = A()
    a1 = A()
    a.out()
    a1.out()