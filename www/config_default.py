#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
@name: config_default.py
@author: Aeiou
@time: 18-11-8 上午11:13
"""


configs = {
    'debug': True,
    'db': {
        'host': '127.0.0.1',
        'port': 3306,
        'user': 'root',
        'password': '12345678',
        'db': 'awesome'
    },
    'session': {
        'secret': 'Awesome'
    }
}