from __future__ import absolute_import
import unittest, doctest
from md import test

__all__ = ('all', )

def all():
    return test.pkg_suites('md', __name__)
