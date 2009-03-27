from __future__ import absolute_import
from abc import ABCMeta, abstractproperty, abstractmethod
from collections import namedtuple, Iterable, Container

__all__ = (
    'CannotCommit', 'Abort',
    'Cursor', 'Journal', 'Memory', 'Change', 'Log'
)

class CannotCommit(RuntimeError): pass
class Abort(Exception): pass

class Cursor(object):
    __metaclass__ = ABCMeta
    __slots__ = ('__weakref__',)

    def __deepcopy__(self, memo):
	return self

class Journal(object):
    __metaclass__ = ABCMeta
    __slots__ = ()

    @abstractproperty
    def source(self):
	"""The journal this journal derives from."""

    @abstractmethod
    def allocate(self, cursor, state):
	"""Allocate a new state for cursor."""

    @abstractmethod
    def read_unsaved(self, cursor):
	"""Return the read-only unsaved state for cursor."""

    @abstractmethod
    def read_saved(self, cursor):
	"""Return the read-only saved state for cursor."""

    @abstractmethod
    def commit_changes(self, read, changed):
	"""Commit changes into the save-log."""

    @abstractmethod
    def write(self, cursor):
	"""Return a mutable state for cursor."""

    @abstractmethod
    def delete(self, cursor):
	"""Destroy the state associated with cursor."""

    @abstractmethod
    def save_state(self, cursor):
	"""Add any unsaved state for cursor to the save-log."""

    @abstractmethod
    def unsaved(self):
	"""Produce an iterator over cursors with unsaved state."""

    @abstractmethod
    def changed(self):
	"""Iterate over saved changes."""

    @abstractmethod
    def read(self):
	"""Produce an iterator over (cursor, state) pairs in the
	read-log."""

def needs_transaction(*args, **kwargs):
    raise NotImplementedError(
	'This operation needs to be run in a transaction.'
    )

class Memory(Journal):
    source = None

    def read_unsaved(self, cursor):
	return self.read_saved(cursor)

    write = needs_transaction
    delete = needs_transaction
    save_state = needs_transaction
    unsaved = needs_transaction
    changed = needs_transaction
    read = needs_transaction

class Change(object):
    __metaclass__ = ABCMeta
    __slots__ = ()

    @abstractproperty
    def cursor(self):
	"""The cursor associated with this change."""

    @abstractproperty
    def orig(self):
	"""The original state read from this journal's source."""

    @abstractproperty
    def state(self):
	"""The changed state."""

class Log(Iterable, Container):
    __metaclass__ = ABCMeta
    __slots__ = ()

    @abstractmethod
    def __delitem__(self, cursor):
	"""Remove cursor."""

    @abstractmethod
    def __getitem__(self, cursor):
	"""Return the state associated with cursor."""

    @abstractmethod
    def __setitem__(self, cursor, state):
	"""Associate new state with a cursor."""

    @abstractmethod
    def get(self, cursor, default=None):
	"""Return the state associated with cursor or default."""

    @abstractmethod
    def allocate(self, cursor, state):
	"""Associate cursor with state; raise a ValueError if cursor
	already has state."""

    @abstractmethod
    def update(self, seq):
	"""Update the log from a sequence of (cursor, state) items."""

    @abstractmethod
    def pop(self, cursor, *default):
	"""Remove cursor and return its state."""
