from __future__ import absolute_import
from collections import Mapping
from itertools import chain, ifilter, izip, izip_longest
from inspect import getargspec
from md.expect import expect

__all__ = (
    'mapping', 'name', 'flatten', 'is_nested',
    'annotatable_names', 'annotatable_spec',
    'zip_annotatable', 'zip_argspec', 'ziptree_shallow', 'ziptree_exact',
)

UNDEFINED = object()

def mapping(obj):
    return expect(obj, Mapping, dict)

def name(obj):
    return expect(obj, basestring)

def is_nested(param):
    return isinstance(param, (list, tuple))

def flatten(sequence, is_tree=is_nested):
    """Produce an iterator over a flat sequence of atoms in sequence.

    >>> list(flatten([(1, (2, 3)), [(4,), 5]]))
    [1, 2, 3, 4, 5]
    """
    for item in sequence:
	if is_tree(item):
	    for x in flatten(item, is_tree): yield x
	else:
	    yield item

def annotatable_names(procedure):
    """Produce an iterator over the annotatable names of procedure.

    >>> def foo(a, (b, c), *args, **kwargs): pass
    >>> list(annotatable_names(foo))
    ['a', 'b', 'c', 'args', 'kwargs', 'return']
    """
    return flatten(annotatable_spec(procedure))

def annotatable_spec(procedure):
    (args, varargs, kwargs, defaults) = getargspec(procedure)
    return ifilter(bool, chain(args, (varargs, kwargs, 'return')))

def zip_annotatable(procedure_a, procedure_b):
    """Zip the annotatable names of procedure_a and procedure_b
    together.

    >>> def foo(a): pass
    >>> def bar(b): pass
    >>> list(zip_annotatable(foo, bar))
    [('a', 'b'), ('return', 'return')]
    """
    return chain(zip_argspec(procedure_a, procedure_b), (('return', 'return'),))

def zip_argspec(proc_a, proc_b):
    """Zip the argspecs of proc_a and proc_b together.

    >>> def foo(a, (b, c), *fa, **fk): pass
    >>> def bar(x, (y, z), *ba, **bk): pass
    >>> list(zip_argspec(foo, bar))
    [('a', 'x'), ('b', 'y'), ('c', 'z'), ('fa', 'ba'), ('fk', 'bk')]
    """
    (ap, av, ak, _) = getargspec(proc_a)
    (bp, bv, bk, _) = getargspec(proc_b)

    if (bool(av) ^ bool(bv)) or (bool(ak) ^ bool(bk)):
	raise TypeError('inconsistent structure', proc_a, proc_b)

    for x in ziptree_exact(ap, bp, is_nested):
	yield x
    if av or bv:
	yield (av, bv)
    if ak or bk:
	yield (ak, bk)

def ziptree_shallow(spec_a, spec_b, is_tree=is_nested):
    """Require elements of spec_b to have identical structural arity to
    elements of spec_a that are nested.

    >>> zts = ziptree_shallow
    >>> list(zts([1, [2], 3, [4]], ['a', ['b'], ['c']], is_nested))
    [(1, 'a'), (2, 'b'), (3, ['c'])]
    """
    for (av, bv) in izip(spec_a, spec_b):
	if is_tree(av):
	    for x in ziptree_exact(av, bv, is_tree):
		yield x
	else:
	    yield (av, bv)

def ziptree_exact(spec_a, spec_b, is_tree):
    """Require spec_a and spec_b to have idential structural arity.

    >>> zte = ziptree_exact
    >>> list(zte([1, [2, 3]], ['a', ['b', 'c']], is_nested))
    [(1, 'a'), (2, 'b'), (3, 'c')]
    >>> list(zte([1, [2]], [['a'], 'b'], is_nested))
    Traceback (most recent call last):
    ...
    TypeError: ('inconsistent structure', [1, [2]], [['a'], 'b'])
    """
    for (av, bv) in izip_longest(spec_a, spec_b, fillvalue=UNDEFINED):
	at = is_tree(av); bt = is_tree(bv)
	if av is UNDEFINED or bv is UNDEFINED or (at ^ bt):
	    raise TypeError('inconsistent structure', spec_a, spec_b)
	elif not (at or bt):
	    yield (av, bv)
	else:
	    for x in ziptree_exact(av, bv, is_tree): yield x
