#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
@name: app.py
@author: Aeiou
@time: 18-11-7 下午7:05
"""

import logging
import asyncio, os, json, time

from datetime import datetime
from aiohttp import web
from jinja2 import Environment, FileSystemLoader

import orm
from coroweb import add_routes, add_static

logging.basicConfig(level=logging.INFO)


def init_jinja2(app, **kwargs):
    logging.info('init jinja2...')
    options = dict(
        autoescape=kwargs.get('autoescape', True),
        block_start_string=kwargs.get('block_start_string', '{%'),
        block_end_string=kwargs.get('block_end_string', '%}'),
        variable_start_string=kwargs.get('variable_start_string', '{{'),
        variable_end_string=kwargs.get('variable_end_string', '}}'),
        auto_reload=kwargs.get('auto_reload', True)
    )
    path = kwargs.get('path', None)
    if path is None:
        path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'templates')
    logging.info('set jinja2 template path: %s' % path)
    env = Environment(loader=FileSystemLoader(path), **options)
    filters = kwargs.get('filters', None)
    if filters is not None:
        for name, func in filters.items():
            env.filters[name] = func
    app['__templating__'] = env


async def logger_factory(app, handler):
    async def logger(request):
        logging.info('Request: %s %s' % (request.method, request.path))
        return await handler(request)
    return logger


async def data_factory(app, handler):
    async def parse_data(request):
        if request.method == 'POST':
            if request.content_type.startwith('application/json'):
                request.__data__ = await request.json()
                logging.info('request json: %s' % str(request.__data__))
            elif request.conten_type.startwith('application/x-www-form-urlencoded'):
                request.__data__ = await request.post()
                logging.info('request form: %s' % request.__data__)
        return await handler(request)
    return parse_data


async def response_factory(app, handler):
    async def response(request):
        logging.info('Response handler...')
        r = await handler(request)
        if isinstance(r, web.StreamResponse):
            return r
        if isinstance(r, bytes):
            ret = web.Response(body=r)
            ret.content_type = 'application/octet-stream'
            return ret
        if isinstance(r, str):
            if r.startswith('redirect:'):
                return web.HTTPFound(r[9:])
            ret = web.Response(body=r.encode('utf-8'))
            ret.content_type = 'text/html;charset=utf-8'
            return ret
        if isinstance(r, dict):
            template = r.get('__template__')
            if template is None:
                ret = web.Response(
                    body=json.dumps(r, ensure_ascii=False, default=lambda o: o.__dict__).encode('utf-8')
                )
                ret.content_type = 'application/json;charset=utf-8'
                return ret
            else:
                ret = web.Response(
                    body=app['__templating__'].get_template(template).render(**r).encode('utf-8')
                )
                ret.content_type = 'text/html;charset=utf-8'
                return ret
        if isinstance(r, int) and 100 <= r < 600:
            return web.Response(r)
        if isinstance(r, tuple) and len(r) == 2:
            t, m = r
            if isinstance(t, int) and 100 <= t < 600:
                return web.Response(t, str(m))
        ret = web.Response(body=str(r).encode('utf-8'))
        ret.content_type = 'text/plain;charset=utf-8'
        return ret
    return response


def datetime_filter(t):
    delta = int(time.time() - t)
    if delta < 60:
        return u'one minute ago'
    if delta < 3600:
        return u'%s minutes ago' % (delta // 60)
    if delta < 86400:
        return u'%s minutes ago' % (delta // 3600)
    if delta < 604800:
        return u'%s minutes ago' % (delta // 86400)
    dt = datetime.fromtimestamp(t)
    return u'year:%s month:%s day:%s' % (dt.year, dt.month, dt.day)


async def init(loop):
    await orm.create_pool(
        loop=loop, host='127.0.0.1', port=3306, user='root',
        password='12345678', db='awesome'
    )
    app = web.Application(loop=loop, middlewares=[
        logger_factory, response_factory
    ])
    init_jinja2(app, filters=dict(datetime=datetime_filter))
    add_routes(app, 'handlers')
    add_static(app)
    srv = await loop.create_server(app.make_handler(), '127.0.0.1', 9000)
    logging.info('server started at http://127.0.0.1:9000...')
    return srv


if __name__ == '__main__':
    loop = asyncio.get_event_loop()
    loop.run_until_complete(init(loop))
    loop.run_forever()
