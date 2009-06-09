from __future__ import absolute_import
import copy, threading
from collections import namedtuple
from .interfaces import Cursor, Static, Journal, Memory, Change, CannotCommit
from .log import log, weaklog

__all__ = (
    'memory', 'journal',
    'alloc', 'dealloc', 'read_unsaved', 'read_saved', 'commit_changes', 'write',
    'save_state', 'revert_state', 'change_state'
)


### Generic Operations

def alloc(journal, cursor, state):
    journal.allocate(cursor, state)
    return cursor

def dealloc(journal, cursor):
    journal.delete(cursor)

def read_unsaved(journal, cursor):
    return good_value(cursor, journal.read_unsaved(cursor))

def read_saved(journal, cursor, *default):
    return good_value(cursor, journal.read_saved(cursor), *default)

def commit_changes(source, nested):
    if source is nested:
        raise RuntimeError("A journal can't be committed to itself.")
    source.commit_changes(nested)

def write(journal, cursor):
    return good_value(cursor, journal.write(cursor))

def save_state(journal, cursor, force=False):
    return journal.save_state(cursor, force)

def revert_state(journal, cursor):
    journal.revert_state(cursor)

def change_state(op, journal, what, *args, **kwargs):
    if isinstance(what, Cursor):
        op(journal, what, *args, **kwargs)
    else:
        ## cache cursors in a list so the log can be modified.
        for cursor in list(what):
            op(journal, cursor, *args, **kwargs)


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
        self.commit_log = self.LogType()
        self.write_log = self.LogType()

        ## Aggressively notify even though there's no activity yet.
        ## This simplifies weird situations like insert-only or
        ## delete-only transactions.
        self.begun = False; self.notify()

    def __repr__(self):
        return '<%s %s>' % (type(self).__name__, str(self))

    def __str__(self):
        return self.name

    def begin(self, nested):
        self.notify()

    def notify(self):
        if not self.begun:
            self.source.begin(self)
            self.begun = True

    def committed(self):
        self.begun = False

    def make_journal(self, name):
        return type(self)(name, self)

    def allocate(self, cursor, state):
        self.commit_log.allocate(cursor, state)

    def read_unsaved(self, cursor):
        try:
            return self.write_log[cursor]
        except KeyError:
            return self.read_saved(cursor)

    def read_saved(self, cursor):
        try:
            return self.commit_log[cursor]
        except KeyError:
            return self.read_source(cursor)

    def read_source(self, cursor):
        try:
            return self.read_log[cursor]
        except KeyError:
            self.notify()
            return log_read(self, cursor)

    def write(self, cursor):
        try:
            return self.write_log[cursor]
        except:
            return log_write(self, cursor)

    def delete(self, cursor):
        log_delete(self, cursor)

    def save_state(self, cursor, force=False):
        try:
            state = self.write_log.pop(cursor)
        except KeyError:
            ## There's nothing to write; just return.
            if force:
                self.commit_log[cursor] = self.read_saved(cursor)
                return True
            else:
                return False
        else:
            self.update_commit_log(cursor, state)
            return True

    def revert_state(self, cursor):
        self.write_log.pop(cursor, None)

    def commit_changes(self, nested):
        ## A journal is single-threaded; state can be blindly copied
        ## in.
        for (cursor, orig, state) in nested.changed():
            self.update_commit_log(cursor, state)
        nested.committed()

    def unsaved(self):
        return (
            k for (k, v) in self.write_log
            if read_saved(self, k, None) is not v
        )

    def changed(self):
        return (
            change(k, get_state(self.read_log, k), v)
            for (k, v) in self.commit_log
        )

    def read(self):
        return iter(self.read_log)

    def update_read_log(self, cursor, state):
        self.read_log[cursor] = state

    def update_write_log(self, cursor, state):
        self.write_log[cursor] = state

    def update_commit_log(self, cursor, state):
        self.commit_log[cursor] = copy_state(state)

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

    def __contains__(self, cursor):
        return cursor in self.mem

    def begin(self, nested):
        pass

    def committed(self):
        pass

    def make_journal(self, name):
        return self.JournalType(name, self)

    def allocate(self, cursor, state):
        self.mem.allocate(cursor, state)

    def read_saved(self, cursor):
        return self.mem[cursor]

    def commit_changes(self, nested):
        self.with_changes(nested, nested.changed(), self.write_changes)

    def with_changes(self, trans, changed, op):
        with self.write_lock:
            self.verify_read(trans.read())
            op(trans, self.verify_write(changed))
            trans.committed()

    def verify_read(self, read):
        if self.check_read:
            verify_read(self.mem, read)

    def verify_write(self, changed):
        if self.check_write:
            return verify_write(self.mem, changed)
        else:
            return unverified_write(changed)

    def write_changes(self, nested, changed):
        for (cursor, state) in changed:
            if is_deleted(state):
                self.expire(cursor)
            else:
                self.mem[cursor] = state

    def expire(self, cursor):
        if isinstance(cursor, Cursor):
            self.mem.pop(cursor, None)
        elif callable(cursor):
            for cur in self.mem.keys():
                if cursor(cur):
                    del self.mem[cur]
        else:
            raise TypeError('expecting cursor or callable', cursor)

    def expire_all(self, cursors=None):
        if cursors:
            for cursor in cursors:
                self.expire(cursor)
        else:
            self.mem.clear()


### State

copy_state = copy.deepcopy

class sentinal(object):
    __slots__ = ('name')

    def __init__(self, name):
        self.name = name

    def __repr__(self):
        return '<%s %s>' % (type(self).__name__, self.name)

    def __copy__(self):
        return self

    def __deepcopy__(self, memo):
        return self

INSERTED = sentinal('inserted')
DELETED = sentinal('deleted')

def good_value(cursor, value, *default):
    if value is INSERTED or value is DELETED:
        if default:
            return default[0]
        else:
            raise ValueError, id(cursor)
    else:
        return value

def is_deleted(obj):
    return obj is DELETED

def is_inserted(obj):
    return obj is INSERTED


### Logged Operations

def log_read(journal, cursor):
    state = read_saved(journal.source, cursor, INSERTED)
    journal.update_read_log(cursor, state)
    return state

def log_write(journal, cursor):
    if isinstance(cursor.__id__, Static):
        raise TypeError('static cursors are not writable', cursor)
    state = copy_state(read_saved(journal, cursor))
    journal.update_write_log(cursor, state)
    return state

def log_delete(journal, cursor):
    if isinstance(cursor.__id__, Static):
        raise TypeError('static cursors are not writable', cursor)
    journal.update_write_log(cursor, DELETED)


### Operations on Logs

def get_state(log, cursor):
    return log.get(cursor, INSERTED)

def verify_read(log, read):
    conflicts = [(c, s) for (c, s) in read if log.get(c) != s]
    if conflicts:
        raise CannotCommit, conflicts

def verify_write(log, changed):
    changed, conflicts = partition_conflicts(log, changed)
    if conflicts:
        raise CannotCommit, conflicts
    return changed

def unverified_write(changed):
    return list((c, s) for (c, o, s) in changed)

def partition_conflicts(log, changed):
    good = []; bad = []
    for (cursor, orig, state) in changed:
        current = get_state(log, cursor)
        (good if current is orig else bad).append((cursor, state))
    return good, bad
