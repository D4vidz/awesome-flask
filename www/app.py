#!/usr/bin/env python
# -*- coding: utf-8 -*-


import asyncio
import aiomysql
import os
import json
import time
import logging

from aiohttp import web

logging.basicConfig(level=logging.DEBUG)


def index(request):
    return web.Response(body=b'<h1>hello world</h1>', content_type='text/html')


@asyncio.coroutine
def init(loop):
    app = web.Application(loop=loop)
    app.router.add_route('GET', '/', index)
    srv = yield from loop.create_server(app.make_handler(), '127.0.0.1', 9000)
    logging.info('server started at http://127.0.0.1:9000...')
    return srv


@asyncio.coroutine
def create_pool(loop, **kw):
    logging.info('create database connection pool...')
    global __pool
    __pool = yield from aiomysql.create_pool(
        host=kw.get('host', 'localhost'),
        port=kw.get('port', 3306),
        user=kw.get('user'),
        password=kw.get('password'),
        db=kw.get('db'),
        charset=kw.get('charset', 'utf8'),
        autocommit=kw.get('autocommit', True),
        maxsize=kw.get('maxsize', 10),
        minsize=kw.get('minsize', 1),
        loop=loop
    )


@asyncio.coroutine
def select(sql, args, size=None):
    logging.debug('sql：%s, args：%s' % (sql, args))
    global __pool
    with (yield from __pool) as conn:
        cursor = yield from conn.cursor(aiomysql.DictCursor)
        yield from cursor.execute(sql.replace('?', '%s'), args or ())
        if size:
            rs = yield from cursor.fetchmany(size)
        else:
            rs = yield from cursor.fetchall()
        yield from cursor.close()
        logging.info('rows returned: %s' % len(rs))
        return rs


@asyncio.coroutine
def execute(sql, args):
    logging.debug('sql: %s, args: %s' % (sql, args))
    with (yield from __pool) as conn:
        try:
            cursor = yield from conn.cursor()
            yield from cursor.execute(sql.replace('?', '%s'), args)
            affected = cursor.rowcount
            yield from cursor.close()
        except BaseException as e:
            raise
        return affected


if __name__ == '__main__':
    loop = asyncio.get_event_loop()
    loop.run_until_complete(init(loop))
    loop.run_forever()
