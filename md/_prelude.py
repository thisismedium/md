## Copyright (c) 2010, Coptix, Inc.  All rights reserved.
## See the LICENSE file for license terms and warranty disclaimer.

"""_prelude -- additional builtins for internal use (see prelude.py)"""

from __future__ import absolute_import
import copy, itertools as it, functools as fn, contextlib as ctx
import collections; from collections import *

__all__ = tuple(collections.__all__) + (
    'partial', 'wraps', 'closing', 'contextmanager',
    'chain', 'ichain', 'islice', 'izip', 'izipl', 'imap', 'takewhile',
    'extend',
    'keys', 'values', 'items', 'chain_items',
    'update', 'updated', 'setdefault',
    'base', 'sentinal', 'Sentinal', 'Undefined',
    'AdaptationFailure', 'adapt'
)


## Procedures

partial = fn.partial
wraps = fn.wraps
closing = ctx.closing
contextmanager = ctx.contextmanager


### Sequences

chain = it.chain
imap = it.imap
islice = it.islice
izip = it.izip
izipl = it.izip_longest
takewhile = it.takewhile

def ichain(seq):
    return (x for s in seq for x in s)

def extend(obj, seq):
    obj.extend(seq)
    return obj


### Mapping

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

def setdefault(obj, **kw):
    for (key, val) in kw.iteritems():
        obj.setdefault(key, val)
    return obj


### Types

def base(cls):
    return cls.__bases__[0]

class Sentinal(object):
    __slots__ = ('nonzero', )

    def __init__(self, nonzero=True):
        self.nonzero = nonzero

    def __nonzero__(self):
        return self.nonzero

    def __repr__(self):
        return '%s' % type(self).__name__

    def __copy__(self):
        return self

    def __deepcopy__(self, memo):
        return self

def sentinal(name, **kw):
    cls = type(name, (Sentinal,), {})
    return cls(**kw)

Undefined = sentinal('<undefined>', nonzero=False)


### Adaptation

class AdaptationFailure(TypeError, NotImplementedError):
    pass

def adapt(obj, cls, default=None):
    """Adapt (cast) obj to cls.

    This is an implementation of the PEAK adaptation interface:
      Adaptation <http://www.python.org/dev/peps/pep-0246/>
      PEAK Protocols <http://peak.telecommunity.com/protocol_ref/module-protocols.html>
    """

    if obj is None or isinstance(obj, cls):
        return obj

    try:
        conform = getattr(obj, '__conform__', None)
        value = conform and conform(cls)
        if value is not None:
            return value
    except TypeError:
        pass

    try:
        adapt = getattr(cls, '__adapt__', None)
        value = adapt and adapt(obj)
        if value is not None:
            return value
    except TypeError as exc:
        pass

    if default is not None:
        return default

    raise AdaptationFailure('Cannot adapt %r. %r does not implement %r.' % (
        obj, type(obj), cls
    ))
