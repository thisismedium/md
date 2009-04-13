from __future__ import absolute_import
from collections import Callable

__all__ = (
    'expect', 'meets_expectation', 'is_expectable', 'UnexpectedType'
)

def expect(obj, interface, cast=None):
    """Raise an UnexpectedType exception if obj does not conform to
    interface."""
    if meets_expectation(obj, interface):
	return obj
    elif cast is not None:
	try:
	    return cast(obj)
	except TypeError:
	    pass
    raise UnexpectedType(obj, interface)

def meets_expectation(obj, interface):
    if isinstance(interface, (tuple, type)):
	if isinstance(obj, interface):
	    return True
    elif isinstance(interface, Callable):
	if interface(obj):
	    return True
    return False

def is_expectable(obj):
    """Return True if obj may be used as the second argument to
    expect."""
    return isinstance(obj, (tuple, type, Callable))

class UnexpectedType(TypeError):
    """A type-assertion exception."""

    def __init__(self, value, interface, *args):
	super(UnexpectedType, self).__init__(value, interface, *args)
	self.value = value
	self.interface = interface

    def __str__(self):
	return 'expected %s, not <%s %r>' % (
	    interface_name(self.interface),
	    type(self.value).__name__,
	    self.value
	)

def interface_name(obj):
    if isinstance(obj, tuple):
	return '(%s)' % ', '.join(interface_name(o) for o in obj)
    else:
	return obj.__name__
