from __future__ import absolute_import
import threading
from weakref import WeakKeyDictionary
from contextlib import contextmanager
from abc import ABCMeta, abstractmethod

__all__ = ('cell', 'let', 'accessor', 'shared', 'copied', 'private')

def cell(value, validate=None, type=None):
    return (type or shared)(value, validate=validate)

def let(*bindings):
    return LOCAL_ENV.bind(*bindings)

def accessor(name, cell, require=False):
    """Decorate an accessor procedure to raise a ValueError if it
    returns default."""

    def access(*value):
	if value:
	    return cell.let(*value)
	elif require and cell.value == cell.original:
	    raise ValueError('%s: missing value' % name)
	return cell.get()

    access.__name__ = name
    return access


### Environmnent

class location(object):
    __slots__ = ('value',)

    def __init__(self, value):
	self.value = value

class env(threading.local):

    def __init__(self, make_top):
	"""Initialize the local environment for this thread.  The
	make_top procedure must return a single frame."""
	self.frames = [make_top(self)]

    def locate(self, cell, default=None):
	"""Return the value bound to cell in the current context."""
	for frame in reversed(self.frames):
	    try:
		return frame[cell]
	    except KeyError:
		pass
	return default

    def push(self, frame):
	"""Push a frame onto the stack."""
	self.frames.append(frame)

    def pop(self):
	"""Pop the last from pushed onto the stack."""
	self.frames.pop()

    @contextmanager
    def bind(self, *bindings):
	"""Dynamically bind bindings in a new context."""
	frame = self.frame((c, location(c.validate(v))) for (c, v) in bindings)
	self.push(frame)
	try:
	    yield
	finally:
	    self.pop()

    def frame(self, bindings=()):
	"""Create a frame."""
	return WeakKeyDictionary(bindings)

    def localize(self):
	"""Localize all dynamic binding and flatten them into a
	frame."""
	return self.frame(localize(f.iteritems() for f in self.frames))

def localize(frames):
    return (
	(c, loc) for (c, loc) in
	((c, c.__localize__(loc)) for f in frames for (c, loc) in f)
	if loc is not NotImplemented
    )


### Thread Integration

MONKEY_PATCH = True

if MONKEY_PATCH:
    try:
	RealThread = threading.RealThread
    except AttributeError:
	RealThread = threading.Thread
	threading.RealThread = RealThread
else:
    RealThread = threading.Thread

class Thread(RealThread):
    """Capture the current dynamic environment before running a new
    thread."""

    def start(self):
	self.localized = LOCAL_ENV.localize()
	RealThread.start(self)

    @classmethod
    def _parent_environment(cls, default):
	t = threading.currentThread()
	try:
	    frame = t.localized
	    del t.localized
	except AttributeError:
	    frame = default()
	return frame

LOCAL_ENV = env(lambda e: Thread._parent_environment(e.frame))

if MONKEY_PATCH:
    threading.Thread = Thread
    try:
	threading._RealDummyThread
    except AttributeError:
	RealDummyThread = threading._DummyThread
	threading._RealDummyThread = RealDummyThread
	class DummyThread(Thread, RealDummyThread): pass
	threading._DummyThread = DummyThread


### Cells

def identity(x):
    return x

class Cell(object):
    __slots__ = ('__weakref__', 'default', 'validate')
    __metaclass__ = ABCMeta

    ENV = LOCAL_ENV

    def __init__(self, value, validate=None):
	self.validate = validate or identity
	self.default = location(self.validate(value))
	self.original = value

    @abstractmethod
    def __localize__(self):
	"""Localize the cell for a new thread."""

    value = property(lambda s: s.get(), lambda s, v: s.set(v))

    def get(self):
	return self.ENV.locate(self, self.default).value

    def set(self, value):
	self.ENV.locate(self, self.default).value = self.validate(value)

    def let(self, value):
	return self.ENV.bind((self, value))

class private(Cell):
    def __localize__(self, loc):
	return location(self.original)

class shared(Cell):
    def __localize__(self, loc):
	return loc

class copied(Cell):
    def __localize__(self, loc):
	return location(loc.value)
