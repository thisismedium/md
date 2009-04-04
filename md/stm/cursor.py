from __future__ import absolute_import
from .interfaces import Cursor
from .transaction import allocate, readable, writable

__all__ = ('cursor', )

class cursor(Cursor):
    __slots__ = ()
    StateType = dict

    def __new__(cls, *args, **kwargs):
	return allocated(cls, cls.StateType())

    def __getattr__(self, key):
	try:
	    return readable(self)[key]
	except KeyError:
	    raise AttributeError, key

    def __setattr__(self, key, value):
	try:
	    writable(self)[key] = value
	except KeyError:
	    raise AttributeError, key

    def __delattr__(self, key):
	try:
	    del writable(self)[key]
	except KeyError:
	    raise AttributeError, key

    def __reduce__(self):
	return (allocated, (type(self), self.__getstate__()))

    def __getstate__(self):
	return readable(self)


### Pickling

def allocated(cls, state):
    if not isinstance(state, cls.StateType):
	state = cls.StateType(state)
    return allocate(object.__new__(cls), state)
