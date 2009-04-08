from __future__ import absolute_import
import threading
from contextlib import contextmanager
from md import fluid
from .interfaces import *
from .journal import *

__all__ = (
    'initialize',
    'allocate', 'readable', 'writable', 'delete',
    'use', 'transaction', 'transactionally',
    'save', 'rollback', 'commit', 'abort',
    'saved', 'unsaved'
)

def initialize(mem=None):
    journal = JOURNAL.value
    if journal is not None and not isinstance(journal, Memory):
	raise RuntimeError('Cannot uninitialize a transaction', journal)
    JOURNAL.value = mem or memory()


### Transasctional Data Type Operations

def allocate(cursor, state):
    return alloc(current_journal(), cursor, state)

def readable(cursor):
    return read_unsaved(current_journal(), cursor)

def writable(cursor):
    return write(current_journal(), cursor)

def delete(cursor):
    return dealloc(current_journal(), cursor)


### Transactions

def use(mem=None):
    assert isinstance(mem, Memory)
    return current_journal(mem or memory())

@contextmanager
def transaction(name='*nested*', autocommit=True, autosave=True):
    try:
	with current_journal(journal(name, current_journal())):
	    yield
	    if autosave: save()
	    if autocommit: commit()
    except Abort:
	pass

def transactionally(proc, *args, **kwargs):
    limit = kwargs.pop('__attempts__', 3)
    autocommit = kwargs.pop('autocommit', True)
    autosave = kwargs.pop('autosave', True)

    for attempt in xrange(limit):
	try:
	    with transaction(autocommit=autocommit, autosave=autosave):
		return proc(*args, **kwargs)
	except CannotCommit as exc:
	    pass
    raise exc

def save(what=None):
    change_state(save_state, current_journal(), what or unsaved())
    return what

def commit(journal=None):
    journal = journal or current_journal()
    return commit_changes(journal.source, journal)

def rollback(what=None):
    change_state(revert_state, current_journal(), what or unsaved())
    return what

def abort():
    raise Abort

def saved():
    return (c.cursor for c in current_journal().changed())

def unsaved():
    return current_journal().unsaved()


### Journal

JOURNAL = fluid.cell(None, type=fluid.private)
current_journal = fluid.accessor('fluid', JOURNAL, require=True)

def current_memory():
    journal = current_journal()
    while journal.source:
	journal = journal.source
    return journal

