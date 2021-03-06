#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
@name: config.py
@author: Aeiou
@time: 18-11-8 上午11:16
"""

import config_default


class Dict(dict):

    def __init__(self, names=(), values=(), **kwargs):
        super(Dict, self).__init__(**kwargs)
        for k, v in zip(names, values):
            self[k] = v

    def __getattr__(self, item):
        try:
            return self[item]
        except KeyError:
            raise AttributeError(r"'Dict' object has no attribute: %s" % item)

    def __setattr__(self, key, value):
        self[key] = value


def merge(defaults, override):
    r = {}
    for k, v in defaults.items():
        if k in override:
            if isinstance(v, dict):
                r[k] = merge(v, override[k])
            else:
                r[k] = override[k]
        else:
            r[k] = v
    return r


def to_dict(d):
    dt = Dict()
    for k, v in d.items():
        dt[k] = to_dict(v) if isinstance(v, dict) else v
    return dt


configs = config_default.configs


try:
    import config_override
    configs = merge(configs, config_override.configs)
except ImportError:
    pass


configs = to_dict(configs)
