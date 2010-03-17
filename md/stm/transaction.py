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
    'rollback', 'commit', 'abort',
    'changed'
)


### Transasctional Data Type Operations

def allocate(cursor, state):
    return current_journal().allocate(cursor, state)

def readable(cursor):
    return readable_state(current_journal(), cursor)

def writable(cursor):
    return writable_state(current_journal(), cursor)

def delete(cursor):
    current_journal().delete_state(cursor)


### Transactions

def use(mem=None):
    assert isinstance(mem, Memory), 'mem: %s' % mem
    return current_journal(mem or memory())

@contextmanager
def transaction(name='*nested*', autocommit=True):
    try:
        with current_journal(current_journal().make_journal(name)):
            yield
            if autocommit:
                autocommit() if callable(autocommit) else commit()
    except Abort:
        pass

def transactionally(proc, *args, **kwargs):
    limit = kwargs.pop('__attempts__', 3)
    autocommit = kwargs.pop('autocommit', True)

    for attempt in xrange(limit):
        try:
            with transaction(autocommit=autocommit):
                return proc(*args, **kwargs)
        except CannotCommit as exc:
            pass
    raise exc

def commit(journal=None):
    journal = journal or current_journal()
    return commit_transaction(journal.source, journal)

def rollback(what=None):
    change_state(current_journal().rollback_state, what or changed())
    return what

def abort():
    raise Abort

def changed():
    return (c.cursor for c in current_journal().changed())


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
