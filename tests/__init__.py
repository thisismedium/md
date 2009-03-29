from __future__ import absolute_import
import unittest, doctest
from md import test

__all__ = ('all', )

def all():
    suite = test.pkg_suites('md', docprefix='')
    suite.addTests(test.module_suites(__name__))
    return suite
