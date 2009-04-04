from __future__ import absolute_import
import copy, threading
from collections import namedtuple
from .interfaces import Cursor, Journal, Memory, Change, CannotCommit
from .log import log, weaklog

__all__ = (
    'memory', 'journal',
    'alloc', 'dealloc', 'read_unsaved', 'read_saved', 'commit_changes', 'write',
    'save_state', 'revert_state', 'change_state'
)

class change(namedtuple('changes', 'cursor orig state'), Change):
    pass

class memory(Memory):
    LogType = weaklog

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

    def allocate(self, cursor, state):
	self.mem.allocate(cursor, state)

    def read_saved(self, cursor):
	return self.mem[cursor]

    def commit_changes(self, read, changed):
	with self.write_lock:
	    self.verify_read(read)
	    self.write_changes(self.verify_write(changed))

    def verify_read(self, read):
	if self.check_read:
	    verify_read(self.mem, read)

    def verify_write(self, changed):
	if self.check_write:
	    return verify_write(self.mem, changed)
	else:
	    return unverified_write(changed)

    def write_changes(self, changed):
	self.mem.update(changed)

class journal(Journal):
    LogType = log
    source = None

    def __init__(self, name, source):
	self.source = source
	self.read_log = self.LogType()
	self.commit_log = self.LogType()
	self.write_log = self.LogType()

    def __repr__(self):
	return '<%s %s>' % (type(self).__name__, str(self))

    def __str__(self):
	return self.name

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
	    try:
		return self.read_log[cursor]
	    except KeyError:
		return log_read(self, cursor)

    def write(self, cursor):
	try:
	    return self.write_log[cursor]
	except:
	    return log_write(self, cursor)

    def delete(self, cursor):
	log_delete(self, cursor)

    def save_state(self, cursor):
	log_commit(self, cursor)

    def revert_state(self, cursor):
	self.write_log.pop(cursor, None)

    def commit_changes(self, read_log, changed):
	## A journal is single-threaded; state can be blindly copied
	## in.
	for (cursor, orig, state) in changed:
	    commit_log(self, cursor, state)

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


### Generic Operations

def alloc(journal, cursor, state):
    journal.allocate(cursor, state)
    return cursor

def dealloc(journal, cursor, state):
    journal.delete(cursor, state)

def read_unsaved(journal, cursor):
    return good_value(cursor, journal.read_unsaved(cursor))

def read_saved(journal, cursor, *default):
    return good_value(cursor, journal.read_saved(cursor), *default)

def commit_changes(source, nested):
    if source is nested:
	raise RuntimeError("A journal can't be committed to itself.")
    source.commit_changes(nested.read(), nested.changed())

def write(journal, cursor):
    return good_value(cursor, journal.write(cursor))

def save_state(journal, cursor):
    journal.save_state(cursor)

def revert_state(journal, cursor):
    journal.revert_state(cursor)

def change_state(op, journal, what):
    if isinstance(what, Cursor):
	op(journal, what)
    else:
	## cache cursors in a list so the log can be modified.
	for cursor in list(what):
	    op(journal, cursor)


### State

copy_state = copy.deepcopy

class sentinal(object):
    __slots__ = ()

    def __deepcopy__(self, memo):
	return self

INSERTED = sentinal()
DELETED = sentinal()

def good_value(cursor, value, *default):
    if value is INSERTED or value is DELETED:
	if default:
	    return default[0]
	else:
	    raise ValueError, cursor
    else:
	return value


### Logged Operations

def log_read(journal, cursor):
    state = read_saved(journal.source, cursor, INSERTED)
    read_log(journal, cursor, state)
    return state

def log_write(journal, cursor):
    state = copy_state(read_saved(journal, cursor))
    write_log(journal, cursor, state)
    return state

def log_delete(journal, cursor):
    write_log(journal, cursor, DELETED)

def log_commit(journal, cursor):
    try:
	state = journal.write_log.pop(cursor)
    except KeyError:
	return
    else:
	commit_log(journal, cursor, state)

def read_log(journal, cursor, state):
    journal.read_log[cursor] = state

def write_log(journal, cursor, state):
    journal.write_log[cursor] = state

def commit_log(journal, cursor, state):
    journal.commit_log[cursor] = copy_state(state)


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
    return ((c, s) for (c, o, s) in changed)

def partition_conflicts(log, changed):
    good = []; bad = []
    for (cursor, orig, state) in changed:
	current = get_state(log, cursor)
	(good if current is orig else bad).append((cursor, state))
    return good, bad
