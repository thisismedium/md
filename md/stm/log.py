from __future__ import absolute_import
from weakref import ref
from collections import namedtuple
from .interfaces import Log

__all__ = ('log', 'weaklog', 'idlog', 'weakidlog')

class entry(namedtuple('entry', 'cursor state')):
    pass

class weakentry(ref):
    __slots__ = ('id', 'state')

    def __new__(cls, cursor, id, state, callback):
        self = ref.__new__(cls, cursor, callback)
        self.id = id
        self.state = state
        return self

    def __init__(self, cursor, id, state, callback):
        super(weakentry, self).__init__(cursor, callback)

class log(Log):
    __slots__ = ('entries',)

    DataType = dict

    def __init__(self, seq=()):
        self.entries = self.DataType()
        self.update(seq)

    def __contains__(self, cursor):
        return self.has_key(self._key(cursor))

    def __iter__(self):
        return self.entries.itervalues()

    def __delitem__(self, cursor):
        del self.entries[self._key(cursor)]

    def __getitem__(self, cursor):
        return self._get_entry(self._key(cursor)).state

    def __setitem__(self, cursor, state):
        key = self._key(cursor)
        self.entries[key] = self._entry(cursor, key, state)

    def _key(self, cursor):
        return cursor.__id__

    def _entry(self, cursor, key, state):
        return entry(cursor, state)

    def _get_entry(self, key):
        return self.entries[key]

    def has_key(self, key):
        return key in self.entries

    def get_cursor(self, key):
        return self._get_entry(key).cursor

    def get(self, cursor, default=None):
        try:
            return self[cursor]
        except KeyError:
            return default

    def allocate(self, cursor, state):
        if cursor in self:
            raise ValueError('already allocated', self._key(cursor), state)
        else:
            self[cursor] = state

    def setdefault(self, cursor, state):
        try:
            return self[cursor]
        except KeyError:
            self[cursor] = state
            return state

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

    def iterkeys(self):
        return (e.cursor for e in self.entries.itervalues())

    def keys(self):
        return list(self.iterkeys())

class idlog(log):
    __slots__ = ()
    _key = staticmethod(id)

class weaklog(log):
    __slots__ = ('_remove',)

    def __init__(self, seq=()):
        def remove(entry, selfref=ref(self)):
            self = selfref()
            if self is not None:
                del self.entries[entry.id]
        self._remove = remove
        super(weaklog, self).__init__(seq)

    def __iter__(self):
        for entry in self.entries.itervalues():
            cursor = entry()
            if cursor is not None:
                yield (cursor, entry.state)

    def _entry(self, cursor, key, state):
        return weakentry(cursor, key, state, self._remove)

    def _get_entry(self, key):
        entry = self.entries[key]
        if entry() is not None:
            return entry
        else:
            raise KeyError, key

    def has_key(self, key):
        try:
            self._get_entry(key)
            return True
        except KeyError:
            return False

    def iterkeys(self):
        for entry in self.entries.values():
            cursor = entry()
            if cursor:
                yield cursor

class weakidlog(weaklog):
    __slots__ = ()
    _key = staticmethod(id)



