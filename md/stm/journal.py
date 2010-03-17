from __future__ import absolute_import
import copy, threading
from ..prelude import *
from .interfaces import Cursor, Journal, Memory, Change, CannotCommit
from .log import log, weaklog

__all__ = (
    'memory', 'journal',
    'readable_state', 'original_state', 'writable_state',
    'change_state', 'copy_state', 'commit_transaction',
    'change', 'Deleted', 'Inserted',
    'good', 'verify_read', 'verify_write', 'unverified_write'
)


### Generic Operations

def readable_state(journal, cursor, *default):
    return good(journal.readable_state, cursor, *default)

def original_state(journal, cursor, *default):
    return good(journal.original_state, cursor, *default)

def writable_state(journal, cursor):
    return good(journal.writable_state, cursor)

def change_state(method, what, *args, **kwargs):
    if isinstance(what, Cursor):
        method(what, *args, **kwargs)
    else:
        ## cache cursors in a list so the log can be modified.
        for cursor in list(what):
            method(cursor, *args, **kwargs)

def commit_transaction(source, nested):
    if source is nested:
        raise RuntimeError("A journal can't be committed to itself.")
    source.commit_transaction(nested)


### Journals

class change(namedtuple('changes', 'cursor orig state'), Change):
    pass

class journal(Journal):
    LogType = log
    name = None
    source = None

    def __init__(self, name, source):
        self.name = name
        self.source = source
        self.read_log = self.LogType()
        self.write_log = self.LogType()

    def __repr__(self):
        return '<%s %s>' % (type(self).__name__, str(self))

    def __str__(self):
        return self.name

    def make_journal(self, name):
        return type(self)(name, self)

    def allocate(self, cursor, state):
        self.write_log.allocate(cursor, state)
        return cursor

    def readable_state(self, cursor):
        try:
            return self.write_log[cursor]
        except KeyError:
            return self.original_state(cursor)

    def original_state(self, cursor):
        try:
            return self.read_log[cursor]
        except KeyError:
            state = good(self.source.readable_state, cursor, Inserted)
            self.read_log[cursor] = state
            return state

    def writable_state(self, cursor):
        try:
            return self.write_log[cursor]
        except KeyError:
            state = copy_state(self.original_state(cursor))
            self.write_log[cursor] = state
            return state

    def delete_state(self, cursor):
        self.write_log[cursor] = Deleted

    def rollback_state(self, cursor):
        self.write_log.pop(cursor, None)

    def commit_transaction(self, trans):
        ## A journal is single-threaded; state can be blindly copied
        ## in.
        for (cursor, orig, state) in trans.changed():
            self._write_log[cursor] = state

    def original(self):
        return iter(self.read_log)

    def changed(self):
        return (
            change(k, get_state(self.read_log, k), v)
            for (k, v) in self.write_log
        )

class memory(Memory):
    JournalType = journal
    LogType = weaklog
    name = None

    def __init__(self, name='*memory*', check_read=True, check_write=True):
        self.name = name
        self.write_lock = threading.RLock()
        self.check_read = check_read
        self.check_write = check_write
        self.mem = self.LogType()

    def __repr__(self):
        return '<%s %s>' % (type(self).__name__, str(self))

    def __str__(self):
        return self.name

    def make_journal(self, name):
        return self.JournalType(name, self)

    def allocate(self, cursor, state):
        self.mem.allocate(cursor, state)
        return cursor

    def readable_state(self, cursor):
        return self.mem[cursor]

    def commit_transaction(self, trans):
        with self.write_lock:
            self._read(trans.original())
            self._commit(self._write(trans.changed()))

    def _read(self, read):
        if self.check_read:
            verify_read(self.mem, read)

    def _write(self, changed):
        if self.check_write:
            return verify_write(self.mem, changed)
        else:
            return unverified_write(changed)

    def _commit(self, changed):
        for (cursor, state) in changed:
            if state is Deleted:
                self.mem.pop(cursor, None)
            else:
                self.mem[cursor] = state


### State

copy_state = copy.deepcopy

Inserted = sentinal('<inserted>')
Deleted = sentinal('<deleted>')

def good(method, cursor, *default):
    try:
        value = method(cursor)
        if not isinstance(value, Sentinal):
            return value
    except KeyError:
        value = Undefined

    if default:
        return default[0]

    raise ValueError(
        '%s object %s %r.' % (type(cursor).__name__, id(cursor), value)
    )


### Operations on Logs

def get_state(log, cursor):
    return log.get(cursor, Inserted)

def verify_read(log, read):
    conflicts = [(c, s) for (c, s) in read if log.get(c) != s]
    if conflicts:
        raise CannotCommit(conflicts)

def verify_write(log, changed):
    changed, conflicts = partition_conflicts(log, changed)
    if conflicts:
        raise CannotCommit(conflicts)
    return changed

def unverified_write(changed):
    return list((c, s) for (c, o, s) in changed)

def partition_conflicts(log, changed):
    good = []; bad = []
    for (cursor, orig, state) in changed:
        current = get_state(log, cursor)
        (good if current is orig else bad).append((cursor, state))
    return good, bad
