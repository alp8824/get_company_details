#!/usr/bin/env python

from crunchbase import Crunchbase

API_KEY = 'mq96jn265dfzs7bzzcnkdkdq'
API_VERSION = 1

cb = Crunchbase(API_KEY, API_VERSION)
print cb.company('Value Payment Systems')
