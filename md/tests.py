## Copyright (c) 2010, Coptix, Inc.  All rights reserved.
## See the LICENSE file for license terms and warranty disclaimer.

"""tests -- unit tests"""

from __future__ import absolute_import
import unittest
from pickle import dumps, loads
from .collections import *

class Foo(struct('foo', 'a b')):
    pass

class TestStruct(unittest.TestCase):

    def test_relops(self):
        self.assertEqual(Foo(1, 2), Foo(1, 2))
        self.assertNotEqual(Foo(1, 2), Foo(2, 1))

    def test_pickle(self):
        foo = Foo(1, 2)
        bar = loads(dumps(foo, -1))
        self.assert_(foo is not bar)
        self.assertEqual(foo, bar)

    def test_syntax(self):
        self.assertRaises(ValueError, lambda: struct('s', 'a a'))
        self.assertRaises(ValueError, lambda: struct('s', 'is'))
        self.assertRaises(ValueError, lambda: struct('s', '_a'))
