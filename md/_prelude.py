## Copyright (c) 2010, Coptix, Inc.  All rights reserved.
## See the LICENSE file for license terms and warranty disclaimer.

"""_prelude -- additional builtins for internal use (see prelude.py)"""

from __future__ import absolute_import
import copy, collections as coll, itertools as it, functools as fn, \
    contextlib as ctx

__all__ = (
    'partial', 'wraps', 'closing',
    'Iterator', 'Sequence', 'chain', 'ichain', 'islice', 'takewhile',
    'Mapping', 'MutableMapping', 'keys', 'values', 'items', 'chain_items',
    'update', 'updated',
    'namedtuple', 'deque', 'sentinal', 'Undefined'
)


## Procedures

partial = fn.partial
wraps = fn.wraps
closing = ctx.closing


### Sequences

Iterator = coll.Iterator
Sequence = coll.Sequence
chain = it.chain
islice = it.islice
takewhile = it.takewhile

def ichain(seq):
    return (x for s in seq for x in s)


### Mapping

Mapping = coll.Mapping
MutableMapping = coll.MutableMapping

def keys(obj):
    if isinstance(obj, Mapping):
        return obj.iterkeys()
    return (i[0] for i in obj)

def values(obj):
    if isinstance(obj, Mapping):
        return obj.itervalues()
    return (i[1] for i in obj)

def items(obj):
    return obj.iteritems() if isinstance(obj, Mapping) else obj

def chain_items(*obj):
    return ichain(items(o) for o in obj if o is not None)

def update(obj, *args, **kwargs):
    obj.update(*args, **kwargs)
    return obj

def updated(obj, *args, **kw):
    return update(copy.copy(obj), *args, **kw)


### Types

namedtuple = coll.namedtuple
deque = coll.deque

class Sentinal(object):
    __slots__ = ('nonzero', )

    def __init__(self, nonzero=True):
        self.nonzero = nonzero

    def __nonzero__(self):
        return self.nonzero

    def __repr__(self):
        return '%s' % type(self).__name__

def sentinal(name, **kw):
    cls = type(name, (Sentinal,), {})
    return cls(**kw)

Undefined = sentinal('<undefined>', nonzero=False)
