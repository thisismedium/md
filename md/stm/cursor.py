from __future__ import absolute_import
import copy
from .. import abc
from ..prelude import *
from .interfaces import Cursor
from .transaction import allocate, readable, writable
from .journal import copy_state

__all__ = ('cursor', 'dict', 'tree', 'omap', 'list', 'set')

_dict = dict
_list = list
_set = set
_tree = tree
_omap = omap

@abc.implements(Cursor)
class _cursor(object):
    __slots__ = ('__weakref__', )
    StateType = _dict

    def __new__(cls, *args, **kwargs):
        return allocated(cls, cls.StateType())

    def __copy__(self):
        return allocated(type(self), copy_state(readable(self)))

    def __deepcopy__(self, memo):
        return self

    def __reduce__(self):
        return (allocated, (type(self), self.__getstate__()))

    def __getstate__(self):
        return readable(self)

    def __sizeof__(self):
        return object.__sizeof__(self) + readable(self).__sizeof__()

    def __repr__(self):
        return '<%s %s>' % (type(self).__name__, self.__id__)

    __id__ = property(id)

def allocated(cls, state):
    if not isinstance(state, cls.StateType):
        state = cls.StateType(state)
    return allocate(object.__new__(cls), state)


### Simple Cursor

class cursor(_cursor):

    def __getattr__(self, key):
        try:
            return readable(self)[key]
        except KeyError:
            raise AttributeError, key

    def __setattr__(self, key, value):
        try:
            writable(self)[key] = value
        except KeyError:
            raise AttributeError, key

    def __delattr__(self, key):
        try:
            del writable(self)[key]
        except KeyError:
            raise AttributeError, key


### Collections

class _collection(_cursor):

    def __contains__(self, item):
        return item in readable(self)

    def __iter__(self):
        return iter(readable(self))

    def __repr__(self):
        data = readable(self)
        if not data:
            return '%s()' % type(self).__name__
        return '%s([%s])' % (type(self).__name__, ', '.join(repr(x) for x in data))

    def __lt__(self, other):
        return readable(self) < self._cast(other)

    def __le__(self, other):
        return readable(self) <= self._cast(other)

    def __eq__(self, other):
        return readable(self) == self._cast(other)

    def __ne__(self, other):
        return readable(self) != self._cast(other)

    def __gt__(self, other):
        return readable(self) > self._cast(other)

    def __ge__(self, other):
        return readable(self) >= self._cast(other)

    __hash__ = None

    def __len__(self):
        return len(readable(self))

    def __getitem__(self, i):
        return readable(self)[i]

    def __setitem__(self, i, item):
        writable(self)[i] = item

    def __delitem__(self, i):
        del writable(self)[i]

@abc.implements(MutableSequence)
class list(_collection):
    StateType = _list

    def __init__(self, seq=()):
        if seq:
            self.extend(seq)

    def __getslice__(self, i, j):
        return allocated(type(self), readable(self).__getslice__(i, j))

    def __setslice__(self, i, j, other):
        return writable(self).__setslice__(i, j, self._coerce(other))

    def __delslice__(self, i, j):
        return writable(self).__delslice__(i, j)

    def __add__(self, other):
        return allocated(type(self), readable(self) + self._coerce(other))

    __radd__ = __add__

    def __iadd__(self, other):
        return writable(self).__iadd__(self._coerce(other))

    def __mul__(self, n):
        return allocated(type(self), readable(self) * n)

    __rmul__ = __mul__

    def __imul__(self, n):
        return writable(self).__imul__(n)

    def _cast(self, other):
        return readable(other) if isinstance(other, list) else other

    def _coerce(self, other):
        if isinstance(other, list):
            return readable(other)
        elif isinstance(other, self.StateType):
            return other
        else:
            return self.StateType(other)

    def append(self, item):
        return writable(self).append(item)

    def insert(self, i, item):
        return writable(self).insert(i, item)

    def pop(self, i=-1):
        return writable(self).pop(i)

    def remove(self, item):
        return writable(self).remove(item)

    def count(self, item):
        return readable(self).count(item)

    def index(item, *args):
        return readable(self).index(item, *args)

    def reverse(self):
        return writable(self).reverse()

    def sort(self, *args, **kwargs):
        return writable(self).sort(*args, **kwargs)

    def extend(self, other):
        return writable(self).extend(self._cast(other))

@abc.implements(MutableMapping)
class dict(_collection):

    def __init__(self, dict=None, **kwargs):
        if dict is not None or kwargs:
            self.update(dict, kwargs)

    def __repr__(self):
        data = readable(self)
        if not data:
            return '%s()' % type(self).__name__
        return '%s([%s])' % (type(self).__name__, ', '.join(repr(x) for x in data.iteritems()))

    def __getitem__(self, key):
        try:
            return readable(self)[key]
        except KeyError:
            if not hasattr(type(self), '__missing__'):
                raise
            return self.__missing__(key)

    def _cast(self, other):
        return readable(other) if isinstance(other, dict) else other

    def clear(self):
        return writable(self).clear()

    def copy(self):
        return copy.copy(self)

    @classmethod
    def fromkeys(cls, iterable, value=None):
        return allocated(cls, ((k, value) for k in iterable))

    def get(self, key, default=None):
        return readable(self).get(key, default)

    def has_key(self, key):
        return key in readable(self)

    def items(self, *args):
        return readable(self).items(*args)

    def iteritems(self, *args):
        return readable(self).iteritems(*args)

    def iterkeys(self, *args):
        return readable(self).iterkeys(*args)

    def itervalues(self, *args):
        return readable(self).itervalues(*args)

    def keys(self, *args):
        return readable(self).keys(*args)

    def pop(self, key, *args):
        return writable(self).pop(key, *args)

    def popitem(self):
        return writable(self).popitem()

    def setdefault(self, key, default=None):
        try:
            ## Only call writable() if necessary.
            return self[key]
        except KeyError:
            return writable(self).setdefault(key, default)

    def update(self, dict=None, **kwargs):
        if dict or kwargs:
            writable(self).update(dict, **kwargs)

    def values(self):
        return readable(self).values()

@abc.implements(MutableTree)
class tree(dict):
    StateType = _tree

@abc.implements(MutableOrderedMap)
class omap(dict):
    StateType = _omap

@abc.implements(MutableSet)
class set(_collection):
    StateType = _set

    def __init__(self, seq=None):
        if seq is not None:
            self.update(seq)

    def __and__(self, other):
        return readable(self) & self._coerce(other)

    __rand__ = __and__

    def __iand__(self, other):
        return writable(self).__iand__(self._coerce(other))

    def __or__(self, other):
        return readable(self) | self._coerce(other)

    __ror__ = __or__

    def __ior__(self, other):
        return writable(self).__ior__(self._coerce(other))

    def __sub__(self, other):
        return readable(self) - self._coerce(other)

    __rsub__ = __sub__

    def __isub__(self, other):
        return writable(self).__isub__(self._coerce(other))

    def __xor__(self, other):
        return readable(self) ^ self._coerce(other)

    __rxor__ = __xor__

    def __ixor__(self, other):
        return writable(self).__ixor__(self._coerce(other))

    def _cast(self, other):
        return readable(other) if isinstance(other, list) else other

    def _coerce(self, other):
        if isinstance(other, list):
            return readable(other)
        elif isinstance(other, self.StateType):
            return other
        else:
            return self.StateType(other)

    def add(self, *args):
        return writable(self).add(*args)

    def clear(self):
        return writable(self).clear()

    def copy(self):
        return copy.copy(self)

    def difference(self, *args):
        return readable(self).difference(*args)

    def difference_update(self, *args):
        return writable(self).difference_update(*args)

    def discard(self, elem):
        if elem in self:
            writable(self).discard(elem)

    def intersection(self, *args):
        return readable(self).intersection(*args)

    def intersection_update(self, *args):
        return writable(self).intersection_update(*args)

    def isdisjoint(self, *args):
        return readable(self).isdisjoint(*args)

    def issubset(self, *args):
        return readable(self).issubset(*args)

    def issuperset(self, *args):
        return readable(self).issuperset(*args)

    def pop(self, *args):
        return writable(self).pop(*args)

    def remove(self, *args):
        return writable(self).remove(*args)

    def symmetric_difference(self, *args):
        return readable(self).symmetric_difference(*args)

    def symmetric_difference_update(self, *args):
        return writable(self).symmetric_difference_update(*args)

    def union(self, *args):
        return readable(self).union(*args)

    def update(self, *args):
        return writable(self).update(*args)

