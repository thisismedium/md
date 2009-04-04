from __future__ import absolute_import
from weakref import ref
from collections import namedtuple
from .interfaces import Log

__all__ = ('log', 'weaklog')

class entry(namedtuple('entry', 'cursor state')):
    pass

class log(Log):
    __slots__ = ('entries',)

    DataType = dict

    def __init__(self, seq=()):
	self.entries = self.DataType()
	self.update(seq)

    def __contains__(self, cursor):
	return cursor.__id__ in self.entries

    def __iter__(self):
	return self.entries.itervalues()

    def __delitem__(self, cursor):
	del self.entries[cursor.__id__]

    def __getitem__(self, cursor):
	return self.entries[cursor.__id__].state

    def __setitem__(self, cursor, state):
	self.entries[cursor.__id__] = entry(cursor, state)

    def get(self, cursor, default=None):
	try:
	    return self[cursor]
	except KeyError:
	    return default

    def allocate(self, cursor, state):
	if cursor in self:
	    raise ValueError('alread allocated', cursor, state)
	else:
	    self[cursor] = state

    def pop(self, cursor, *default):
	try:
	    state = self[cursor]
	except KeyError:
	    if not default:
		raise
	    return default[0]
	else:
	    del self[cursor]
	    return state

    def update(self, seq):
	for (cursor, state) in seq:
	    self[cursor] = state

    def clear(self):
	self.entries.clear()

class weakentry(ref):
    __slots__ = ('id', 'state')

    def __new__(cls, cursor, state, callback):
	self = ref.__new__(cls, cursor, callback)
	self.id = cursor.__id__
	self.state = state
	return self

    def __init__(self, cursor, state, callback):
	super(weakentry, self).__init__(cursor, callback)

class weaklog(log):
    __slots__ = ('_remove',)

    def __init__(self, seq=()):
	def remove(entry, selfref=ref(self)):
	    self = selfref()
	    if self is not None:
		del self.entries[entry.id]
	self._remove = remove
	super(weaklog, self).__init__(seq)

    def __contains__(self, cursor):
	try:
	    return self.entries[cursor.__id__]() is not None
	except KeyError:
	    return False

    def __iter__(self):
	for entry in self.entries.itervalues():
	    cursor = entry()
	    if cursor is not None:
		yield (cursor, entry.state)

    def __getitem__(self, cursor):
	entry = self.entries[cursor.__id__]
	if entry() is not None:
	    return entry.state
	else:
	    raise KeyError, cursor

    def __setitem__(self, cursor, state):
	self.entries[cursor.__id__] = weakentry(cursor, state, self._remove)

