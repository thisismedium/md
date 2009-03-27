from __future__ import absolute_import
from .interfaces import Cursor
from .transaction import allocate, readable, writable

__all__ = ('cursor',)

class cursor(Cursor):
    __slots__ = ()
    StateType = dict

    def __new__(cls, *args, **kwargs):
	return allocate(object.__new__(cls), cls.StateType())

    def __getattr__(self, key):
	try:
	    return self[key]
	except KeyError:
	    raise AttributeError, key

    def __setattr__(self, key, value):
	try:
	    self[key] = value
	except KeyError:
	    raise AttributeError, key

    def __delattr__(self, key):
	try:
	    del self[key]
	except KeyError:
	    raise AttributeError, key

    def __getitem__(self, key):
	return readable(self)[key]

    def __setitem__(self, key, value):
	writable(self)[key] = value

    def __delitem__(self, key):
	del writable(self)[key]
