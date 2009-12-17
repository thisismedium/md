from __future__ import absolute_import
import threading, copy
from weakref import WeakKeyDictionary
from contextlib import contextmanager
from abc import ABCMeta, abstractmethod

__all__ = (
    'cell', 'let', 'accessor',
    'shared', 'acquired', 'copied', 'deepcopied', 'private',
    'FluidError'
)

class UNDEFINED(object): pass
UNDEFINED = UNDEFINED()

def cell(value=UNDEFINED, validate=None, type=None):
    return (type or shared)(value, validate=validate)

def let(*bindings):
    return LOCAL.bind(*bindings)

def accessor(cell, name=None):
    """Decorate an accessor procedure to raise a ValueError if it
    returns default."""

    def access(*value):
        if value:
            return cell.let(*value)
        else:
            value = cell.get()
            if value is UNDEFINED:
                raise ValueError('%s is undefined' % (name or cell))
            return value

    return access


### Environmnent

class FluidError(Exception):
    pass

class location(object):
    __slots__ = ('value',)

    def __init__(self, value):
        self.value = value

class env(threading.local):
    FrameType = WeakKeyDictionary

    def __init__(self, global_frame, make_top):
        """Initialize the local environment for this thread.  The
        make_top procedure must return a single frame."""

        self._global = global_frame
        self.frames = [global_frame, make_top(self)]

    def define(self, cell, location):
        result = self._global.setdefault(cell, location)
        if result is not location:
            raise FluidError('already defined', cell, result)
        return result

    def locate(self, cell):
        """Return the value bound to cell in the current context."""

        frame = self.frames[-1]
        try:
            ## Quickly look in the current frame.
            return frame[cell]
        except KeyError:
            ## Fall back on _find()
            result = frame[cell] = self._find(len(self.frames) - 2, cell)
        if not result:
            raise FluidError('locate: unbound cell', cell)
        return result

    def _find(self, index, cell):
        """Search through the frames for cell, memoizing the result in
        each frame if the next frame must be searched.."""

        if index < 0:
            return None
        frame = self.frames[index]
        try:
            return frame[cell]
        except KeyError:
            result = frame[cell] = self._find(index - 1, cell)
        return result

    def push(self, frame):
        """Push a frame onto the stack."""

        self.frames.append(frame)

    def pop(self):
        """Pop the last from pushed onto the stack."""

        if len(self.frames) < 1:
            raise FluidError('Cannot pop() the global frame.')
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

    @classmethod
    def frame(cls, bindings=()):
        """Create a frame."""

        return cls.FrameType(bindings)

    def localize(self):
        """Localize all dynamic binding and flatten them into a
        frame."""

        return self.frame(localize(f.iteritems() for f in self.frames))

def localize(frames):
    return (
        (c, loc) for (c, orig, loc) in
        ((c, loc, c.localize(loc)) for f in frames for (c, loc) in f)
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
        self.localized = LOCAL.localize()
        RealThread.start(self)

if MONKEY_PATCH:
    threading.Thread = Thread
    try:
        threading._RealDummyThread
    except AttributeError:
        RealDummyThread = threading._DummyThread
        threading._RealDummyThread = RealDummyThread
        class DummyThread(Thread, RealDummyThread): pass
        threading._DummyThread = DummyThread

def parent_environment(missing):
    t = threading.currentThread()
    try:
        frame = t.localized
        del t.localized
    except AttributeError:
        frame = missing()
    return frame

GLOBAL = env.FrameType()
LOCAL = env(GLOBAL, lambda e: parent_environment(e.frame))


### Cells

def identity(x):
    return x

class Cell(object):
    __slots__ = ('__weakref__', 'default', 'validate')
    __metaclass__ = ABCMeta

    ENV = LOCAL

    def __init__(self, value=UNDEFINED, validate=None):
        self.validate = validate or identity
        if value is not UNDEFINED:
            value = self.validate(value)
        self._global = self.ENV.define(self, self.make_location(value))

    value = property(lambda s: s.get(), lambda s, v: s.set(v))

    @abstractmethod
    def localize(self, loc):
        """Localize the cell for a new thread."""

    def bind(self, value):
        return self.make_location(self.validate(value))

    def make_location(self, value):
        return location(value)

    def get(self):
        return self.ENV.locate(self).value

    def set(self, value):
        self.ENV.locate(self).value = self.validate(value)

    def let(self, value):
        return self.ENV.bind((self, value))

class private(Cell):
    def localize(self, loc):
        return self.make_location(self._global.value)

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
