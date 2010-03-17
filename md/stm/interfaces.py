from __future__ import absolute_import
from abc import ABCMeta, abstractproperty, abstractmethod
from collections import namedtuple, Iterable, Container

__all__ = (
    'CannotCommit', 'Abort', 'NeedsTransaction',
    'Cursor', 'Journal', 'Memory', 'Change', 'Log'
)

class CannotCommit(RuntimeError): pass
class Abort(Exception): pass
class NeedsTransaction(Exception): pass

class Cursor(object):
    __metaclass__ = ABCMeta
    __slots__ = ('__weakref__',)

    def __deepcopy__(self, memo):
        return self

    def __repr__(self):
        return '<%s %s>' % (type(self).__name__, self.__id__)

    __id__ = property(id)

class Journal(object):
    __metaclass__ = ABCMeta
    __slots__ = ()

    @abstractproperty
    def name(self):
        """The name of this transaction."""

    @abstractproperty
    def source(self):
        """The journal this journal derives from."""

    @abstractmethod
    def make_journal(self):
        """Create a new journal with this journal as the source."""

    @abstractmethod
    def allocate(self, cursor, state):
        """Allocate a new state for cursor."""

    @abstractmethod
    def readable_state(self, cursor):
        """Return whatever state is readable for a cursor."""

    @abstractmethod
    def original_state(self, cursor):
        """Return the original state of the cursor.  This may or may
        not be the same as the readable state."""

    @abstractmethod
    def writable_state(self, cursor):
        """Return whatever state is writable for a cursor."""

    @abstractmethod
    def delete_state(self, cursor):
        """Destroy the state associated with cursor."""

    @abstractmethod
    def rollback_state(self, cursor):
        """Return a cursor to it's original state."""

    @abstractmethod
    def commit_transaction(self, nested):
        """Commit a journal into the write-log."""

    @abstractmethod
    def original(self):
        """Iterate over (cursor, original-state) items in the
        read-log"""

    @abstractmethod
    def changed(self):
        """Iterate over (cursor, original-state, changed-state) items
        in the write-log."""


def needs_transaction(*args, **kwargs):
    raise NeedsTransaction(
        'This operation needs to be run in a transaction.'
    )

class Memory(Journal):
    source = None

    def original_state(self):
        return self.readable_state(self)

    writable_state = needs_transaction
    delete_state = needs_transaction
    rollback_state = needs_transaction
    original = needs_transaction
    changed = needs_transaction

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

    @abstractmethod
    def clear(self):
        """Clear all state information."""
