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

from aiohttp import web

from coroweb import get, post
from models import User, Comment, Blog, next_id
from apis import APIError, APIValueError, APIResourceNotFoundError, APIPermissionError
from config import configs

# cookie constants
COOKIE_NAME = 'session'
_COOKIE_KEY = configs.session.secret


# re constants
_RE_EMAIL = re.compile(r'^[a-z0-9\.-\_]+\@[a-z0-9\-\_]+(\.[a-z0-9\-\_]+){1,4}$')
_RE_SHA1 = re.compile(r'^[0-9a-f]{40}$')


def user2cookie(user, max_age):
    expires = str(int(time.time() + max_age))
    s = '%s-%s-%s-%s' % (user.id, user.password, expires, _COOKIE_KEY)
    lst = [user.id, expires, hashlib.sha1(s.encode('utf-8')).hexdigest()]
    return '-'.join(lst)


async def cookie2user(cookie_str):
    if not cookie_str:
        return None
    try:
        lst = cookie_str.split('-')
        if len(lst) != 3:
            return None
        uid, expires, sha1 = lst
        if int(expires) < time.time():
            return None
        user = await User.find(uid)
        if user is None:
            return None
        s = '%s-%s-%s-%s' % (uid, user.password, expires, _COOKIE_KEY)
        if sha1 != hashlib.sha1(s.encode('utf-8')).hexdigest():
            return None
        user.password = '******'
        return user
    except Exception as e:
        logging.exception(e)
        return None


@get('/register')
def register():
    return {
        '__template__': 'register.html'
    }


@get('/signin')
def sign_in():
    return {
        '__template__': 'signin.html'
    }


@post('/api/authenticate')
async def authenticate(*, email, password):
    if not email:
        raise APIValueError('email', 'Invalid email')
    if not password:
        raise APIValueError('password', 'Invalid password')
    users = await User.find_all('email=?', [email])
    if len(users) == 0:
        raise APIValueError('email', 'Email not exist')
    user = users[0]
    sha1 = hashlib.sha1()
    sha1.update(user.id.encode('utf-8'))
    sha1.update(b':')
    sha1.update(password.encode('utf-8'))
    if user.password != sha1.hexdigest():
        raise APIValueError('password', 'Invalid password')
    ret = web.Response()
    ret.set_cookie(COOKIE_NAME, user2cookie(user, 86400), max_age=86400, httponly=True)
    user.password = '******'
    ret.content_type = 'application/json'
    ret.body = json.dumps(user, ensure_ascii=False).encode('utf-8')
    return ret


@get('/signout')
def sign_out(request):
    referer = request.headers.get('Referer')
    ret = web.HTTPFound(referer or '/')
    ret.set_cookie(COOKIE_NAME, '-deleted', max_age=0, httponly=True)
    logging.info('user signed out')
    return ret


@post('/api/users')
async def api_register_user(*, email, name, password):
    if not name or not name.strip():
        raise APIValueError('name')
    if not email or not _RE_EMAIL.match(email):
        raise APIValueError('email')
    if not password or not _RE_SHA1.match(password):
        raise APIValueError('password')
    users = await User.find_all('email=?', [email])
    if len(users) > 0:
        raise APIError('register: failed', 'email', 'Email is already in use')
    uid = next_id()
    sha1_password = '%s:%s' % (uid, password)
    user = User(
        id=uid, name=name.strip(), email=email,
        password=hashlib.sha1(sha1_password.encode('utf-8')).hexdigest(),
        image='blank:about'
    )
    await user.save()
    ret = web.Response()
    ret.set_cookie(COOKIE_NAME, user2cookie(user, 86400), max_age=86400, httponly=True)
    user.password = '*******'
    ret.content_type = 'application/json'
    ret.body = json.dumps(user, ensure_ascii=False).encode('utf-8')
    return ret


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


def check_admin(request):
    if request.__user__ is None or not request.__user__.admin:
        raise APIPermissionError()


@get('/manage/blogs/create')
def manage_blog_create():
    return {
        '__template__': 'manage_blog_edit.html',
        'id': '',
        'action': '/api/blogs'
    }


@get('/api/blogs/{id}')
async def api_get_blog(*, id):
    blog = await Blog.find(id)
    return blog


@post('/api/blogs')
async def api_create_blog(request, *, name, summary, content):
    # check_admin(request)
    if not name or not name.strip():
        raise APIValueError('name', 'name cannot be empty')
    if not summary or not summary.strip():
        raise APIValueError('summary', 'summary cannot be empty')
    if not content or not content.strip():
        raise APIValueError('content', 'content cannot be empty')
    blog = Blog(
        user_id=request.__user__.id, user_name=request.__user__.name,
        user_image=request.__user__.image, name=name.strip(),
        summary=summary.strip(), content=content.strip()
    )
    await blog.save()
    return blog
