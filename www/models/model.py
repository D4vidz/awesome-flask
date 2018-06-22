#!/usr/bin/env python
# -*- coding: utf-8 -*-


class ModelMetaclass(type):
    pass


class Model(dict, metaclass=ModelMetaclass):
    pass


class Field(object):

    def __init__(self):
        pass

    def __str__(self):
        pass


class StringField(Field):
    pass


class IntegerField(Field):
    pass


class User(Model):
    pass
