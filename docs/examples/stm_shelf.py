from __future__ import absolute_import
import os, shelve, uuid, weakref, copy
from collections import Iterator
from md import stm
from md.stm.transaction import current_memory
from md.stm.journal import alloc, copy_state, is_deleted

__all__ = (
    'pid', 'pcursor', 'pdict', 'plist', 'pset',
    'fetch', 'shelf', 'current_memory'
)


### Persistent Cursor

def pid(cursor):
    return cursor.__pid__

class PCursor(object):
    __slots__ = ()

    def __new__(cls, *args, **kwargs):
	return allocated(cls, cls.StateType(), kwargs.get('__id__'))

    def __copy__(self):
	return allocated(type(self), copy_state(readable(self)))

    def __reduce__(self):
	return (delayed, (type(self), pid(self)))

    __id__ = property(pid)

def persist(name, base):
    """Create a persistent type from any transactional type."""

    def __init__(self, *args, **kwargs):
	kwargs.pop('__id__', None)
	base.__init__(self, *args, **kwargs)

    return type(name, (PCursor, base), dict(
	    __slots__ = ('__pid__', ),
	    __module__ = __name__,
	    __init__ = __init__,
    ))

pcursor = persist('pcursor', stm.cursor)
pdict = persist('pdict', stm.tdict)
plist = persist('plist', stm.tlist)
pset = persist('pset', stm.tset)

def allocated(cls, state, id=None):
    return stm.allocate(set_pid(object.__new__(cls), id), state)

def set_pid(cursor, id=None):
    object.__setattr__(cursor, '__pid__', id or uuid.uuid4().hex)
    return cursor


### Persistent Memory

def delayed(cls, id):
    return current_memory().delayed(cls, id)

def fetch(id):
    return current_memory().fetch(id)

class shelf(stm.memory):
    def __init__(self, path, check_read=True, check_write=True):
	super(shelf, self).__init__(path, check_read, check_write)
	self.pcursors = weakref.WeakValueDictionary()
	self.store = None
	self.open()

    def open(self):
	if self.store is None:
	    self.store = shelve.open(self.name, protocol=-1)

    def close(self):
	if self.store is not None:
	    self.store.close()
	    self.store = None

    def destroy(self):
	self.close()
	os.unlink(self.name)

    def clear(self):
	if self.store:
	    self.store.clear(); self.store.sync()
	    self.mem.clear()
	    self.pcursors.clear()

    def read_saved(self, cursor):
	try:
	    return super(shelf, self).read_saved(cursor)
	except KeyError:
	    return load_state(self, cursor)

    def write_changes(self, nested, changed):
	if isinstance(changed, Iterator):
	    changed = list(changed)
	super(shelf, self).write_changes(nested, changed)
	self.store_changes(nested, changed)

    def store_changes(self, nested, changed):
	## Store (cls, state) tuples rather than directly pickling a
	## cursor.  Pickling it would only make a lazy reference.
	for (cursor, state) in changed:
	    if isinstance(cursor, PCursor):
		key = verify_pid(self, cursor)
		if is_deleted(state):
		    del self.store[key]
		else:
		    self.store[key] = (type(cursor), state)
	self.store.sync()

    def delayed(self, cls, id):
	"""Return a persistent cursor, but do not load its state."""
	with self.write_lock:
	    try:
		return self.pcursors[id]
	    except KeyError:
		return identify(self, cls, id)

    def fetch(self, id):
	"""Return a persistent cursor; make sure its state is
	loaded."""
	with self.write_lock:
	    try:
		## At least a lazy reference exists.  State is
		## unknown.
		cursor = self.pcursors[id]
		state = None
	    except KeyError:
		## No reference of any kind exists.  Make one.
		(cls, state) = self.store[id]
		cursor = identify(self, cls, id)

	    try:
		## State is already loaded for this cursor.  Use
		## super() here to maybe avoid loading state twice.
		super(shelf, self).read_saved(cursor)
	    except KeyError:
		## No state is loaded.  Load it (possibly using state
		## already retrived from the store).
		load_state(self, cursor, state)

	return cursor

def identify(memory, cls, id):
    """Associate a new cursor with a persistent id."""
    memory.pcursors[id] = cursor = object.__new__(cls)
    return set_pid(cursor, id)

def verify_pid(memory, cursor):
    """Verify that the cursor is identical to the one associated with
    its persistent id in memory.  This is a sanity check."""
    key = pid(cursor)
    memory.pcursors.setdefault(key, cursor)
    if memory.pcursors[key] is not cursor:
	raise ValueError(
	    'This persistent id is already associated with another cursor',
	    id, cursor
	)
    return key

def load_state(memory, cursor, state=None):
    """Allocate the state for the cursor, loading it from the backing
    store if necessary."""
    with memory.write_lock:
	if state is None:
	    (cls, state) = memory.store[pid(cursor)]
	alloc(memory, cursor, state)
	return state

