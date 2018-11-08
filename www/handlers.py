#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
@name: handlers.py
@author: Aeiou
@time: 18-11-8 上午11:24
"""

import re
import time
import json
import logging
import hashlib
import base64
import asyncio

from coroweb import get, post
from models import User, Comment, Blog, next_id


@get('/')
async def index(request):
    summary = 'Lord, here please!'
    blogs = [
        Blog(id='1', name='Test Blog', summary=summary, created_at=time.time()-120),
        Blog(id='2', name='Something New', summary=summary, created_at=time.time()-3600),
        Blog(id='3', name='Learn Swift', summary=summary, created_at=time.time()-7200)
    ]
    return {
        '__template__': 'blogs.html',
        'blogs': blogs
    }


@get('/api/users')
async def users():
    users = await User.find_all(order_by='created_at desc')
    for user in users:
        user.password = '******'
    return dict(users=users)
