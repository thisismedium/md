from __future__ import absolute_import
import weakref
from itertools import chain, ifilter
from inspect import getargspec
from collections import Callable
from md.expect import expect
from .util import *

__all__ = (
    'annotate', 'annotations', 'is_annotated',
    'transfer', 'zip_annotations'
)

UNDEFINED = object()

def annotate(procedure, bindings):
    """Annotate a procedure with bindings."""
    annotations(procedure).update(bind(procedure, bindings))
    return procedure

def annotations(procedure):
    """Return the annotations of procedure."""

    procedure = annotatable(procedure)

    try:
	ann = procedure.func_annotations
	if ann.are_for(procedure):
	    return ann
    except AttributeError:
	pass

    ann = procedure.func_annotations = Annotations(procedure)
    return ann

def is_annotated(procedure):
    """Return True if procedure is annotated."""
    procedure = annotatable(procedure)
    try:
	ann = procedure.func_annotations
	return ann.are_for(procedure) and bool(ann)
    except AttributeError:
	return False

def zip_annotations(procedure, default=UNDEFINED):
    """Zip each argument name of procedure to its annotation."""
    if default is not UNDEFINED:
	ann = annotations(procedure)
	return ((n, ann.get(n, default)) for n in annotatable_names(procedure))
    else:
	ann = annotations(procedure)
	return (
	    (n, ann[n])
	    for n in annotatable_names(procedure)
	    if n in ann
	)

def transfer(source, dest):
    """Transfer the annotations from source to dest.  The two
    procedures must have identical arity."""

    s_ann = annotations(source)
    d_ann = annotations(dest)
    d_ann.clear()

    if s_ann:
	d_ann.update(
	    (d_name, s_ann[s_name])
	    for (s_name, d_name) in zip_annotatable(source, dest)
	    if s_name in s_ann
	)

    return dest


### Implementation

def annotatable(procedure):
    ## Handle MethodType arguments
    return getattr(procedure, 'im_func', procedure)

class Annotations(dict):
    """A dictionary of annotations for some procedure.

    This implementation keeps a weak reference to the annotated
    procedure.  When annotated procedures are wrapped or copied, a
    reference to the original annotations may be carried over.
    Keeping this reference to the original procedure allows
    annotations() to detect this situation.
    """
    def __init__(self, procedure):
	super(Annotations, self).__init__()
	self.procedure = weakref.ref(expect(procedure, Callable))

    def are_for(self, procedure):
	return procedure is self.procedure()

def bind(procedure, ann):
    return check(procedure, fix(mapping(ann)))

def fix(ann):
    """Fix special annotation names.

    >>> fix(dict(__return__=1))
    {'return': 1}
    """
    try:
	## The syntactic keyword `return' cannot be used as a keyword
        ## argument.  To work around this it can be given as
        ## annotation(__return__=FOO).
	ann[name('return')] = ann.pop(name('__return__'))
    except KeyError:
	pass
    return ann

def check(procedure, bindings):
    """Ensure that all names in bindings are annotatable for
    procedure."""
    bad = set(bindings.iterkeys()) - set(annotatable_names(procedure))
    if bad:
	raise NameError(
	    'These %s are not parameters of %r' % (bad, procedure)
	)
    return bindings

def unique(procedure, ann_args, ann_kwargs):
    """Make sure the bindings given in ann_args and ann_kwargs are unique.

    >>> def foo(a, (b, c), *args, **kwargs): pass
    >>> sorted(unique(foo, [1, (2, 3)], dict(__return__=4)).iteritems())
    [('a', 1), ('b', 2), ('c', 3), ('return', 4)]
    """
    params = annotatable_spec(procedure)
    ann = dict(ziptree_shallow(params, ann_args, is_nested))
    ann_kwargs = fix(ann_kwargs)

    duplicate = set(ann.iterkeys()) & set(ann_kwargs.iterkeys())
    if duplicate:
	raise NameError(
	    'Keyword arguments duplicate these parameters: %r' % duplicate
	)

    ann.update(ann_kwargs)
    return ann
