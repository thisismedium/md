from __future__ import absolute_import
import threading, copy
from weakref import WeakKeyDictionary
from contextlib import contextmanager
from abc import ABCMeta, abstractmethod

__all__ = (
    'cell', 'let', 'accessor',
    'shared', 'acquired', 'copied', 'deepcopied', 'private'
)

class UNDEFINED(object): pass
UNDEFINED = UNDEFINED()

def cell(value=UNDEFINED, validate=None, type=None):
    return (type or shared)(value, validate=validate)

def let(*bindings):
    return LOCAL_ENV.bind(*bindings)

def accessor(cell, name=None):
    """Decorate an accessor procedure to raise a ValueError if it
    returns default."""

    def access(*value):
        if value:
            return cell.let(*value)
        else:
            value = cell.value
            if value is UNDEFINED:
                raise ValueError('%s is undefined' % (name or cell))
            return value

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
        frame = self.frame((c, c.bind(v)) for (c, v) in bindings)
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
        ((c, c.localize(loc)) for f in frames for (c, loc) in f)
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

    def __init__(self, value=UNDEFINED, validate=None):
        self.validate = validate or identity
        if value is not UNDEFINED:
            value = self.validate(value)
        self.default = location(value)

    value = property(lambda s: s.get(), lambda s, v: s.set(v))

    @abstractmethod
    def localize(self):
        """Localize the cell for a new thread."""

    def bind(self, value):
        return self.make_location(self.validate(value))

    def make_location(self, value):
        return location(value)

    def get(self):
        return self.ENV.locate(self, self.default).value

    def set(self, value):
        self.ENV.locate(self, self.default).value = self.validate(value)

    def let(self, value):
        return self.ENV.bind((self, value))

class private(Cell):
    def localize(self, loc):
        return location(self.default.value)

class shared(Cell):
    def localize(self, loc):
        return loc

class acquired(Cell):
    def localize(self, loc):
        return self.make_location(loc.value)

class copied(Cell):
    def localize(self, loc):
        return self.make_location(copy.copy(loc.value))

class deepcopied(Cell):
    def localize(self, loc):
        return self.make_location(copy.deepcopy(loc.value))
