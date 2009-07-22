from __future__ import absolute_import
import threading
from contextlib import contextmanager
from md import fluid
from .interfaces import *
from .journal import *

__all__ = (
    'initialize', 'current_journal', 'current_memory',
    'allocate', 'readable', 'writable', 'delete',
    'use', 'transaction', 'transactionally',
    'save', 'rollback', 'commit', 'abort',
    'saved', 'unsaved'
)


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
    assert isinstance(mem, Memory), 'mem: %s' % mem
    return current_journal(mem or memory())

@contextmanager
def transaction(name='*nested*', autocommit=True, autosave=True):
    try:
        with current_journal(current_journal().make_journal(name)):
            yield
            if autosave:
                autosave() if callable(autosave) else save()
            if autocommit:
                autocommit() if callable(autocommit) else commit()
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

def save(what=None, force=False):
    change_state(save_state, current_journal(), what or unsaved(), force)
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

class acquire_memory(fluid.acquired):
    def localize(self, loc):
        if isinstance(loc.value, Journal):
            return self.make_location(find_memory(loc.value))
        else:
            return super(acquire_memory, self).localize(loc)

def find_memory(journal):
    while journal.source:
        journal = journal.source
    return journal

JOURNAL = fluid.cell(type=acquire_memory)

current_journal = fluid.accessor(JOURNAL, name='current_journal')

def current_memory():
    return find_memory(current_journal())

def initialize(mem=None):
    journal = JOURNAL.value
    if isinstance(journal, Journal) and not isinstance(journal, Memory):
        raise RuntimeError('Cannot uninitialize a transaction', journal)
    JOURNAL.value = mem or memory()
