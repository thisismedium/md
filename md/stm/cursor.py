from __future__ import absolute_import
import copy_reg
from .interfaces import Cursor
from .transaction import allocate, readable, writable

__all__ = ('cursor', 'reduce')

class cursor(Cursor):
    __slots__ = ()
    StateType = dict

    def __new__(cls, *args, **kwargs):
	return allocated(cls, cls.StateType())

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

    def __getstate__(self):
	return readable(self)


### Pickling

def reduce(cursor):
    return (allocated, (type(cursor), cursor.__getstate__()))

def allocated(cls, state):
    if not isinstance(state, cls.StateType):
	state = cls.StateType(state)
    return allocate(object.__new__(cls), state)

copy_reg.pickle(cursor, reduce)
