#/usr/bin/env python3
# -*- coding: utf-8 -*-


import orm
import asyncio

from models import User
from models import Blog
from models import Comment


async def create(loop):
    await orm.create_pool(loop=loop, user='root', password='12345678', db='awesome')

    u = User(name='Test', email='a@b.com', passwd='123456', image='about:blank')

    await u.save()


loop = asyncio.get_event_loop()
loop.run_until_complete(create(loop))
loop.run_forever()
