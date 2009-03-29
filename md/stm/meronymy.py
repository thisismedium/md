from __future__ import absolute_import
from md import fluid
from .interfaces import Cursor
from .log import weaklog

__all__ = ('partof', 'whole')

def partof(whole, part):
    if isinstance(part, Cursor) and isinstance(whole, Cursor):
	register_part(current_meronymy(), whole, part)
    return part

def whole(parts, default=None):
    return resolve_whole(current_meronymy(), parts, default=None)


###

class MeronymicError(Exception): pass

CURRENT_MERONYMY = fluid.cell(weaklog())

def current_meronymy():
    return CURRENT_MERONYMY.value

def resolve_whole(meronymy, parts, default=None):
    return ((p, meronymy.get(p, default)) for p in parts)

def register_part(meronymy, whole, part):
    ## Resolve whole to a real whole if it is part of something else.
    whole = meronymy.get(whole, whole)

    try:
	holon = meronymy[part]
	if holon is whole:
	    return
	else:
	    raise MeronymicError(
		'whole=%r does not match existing holon=%r '
		'for part=%r' % (whole, holon, part)
	    )
    except KeyError:
	try:
	    meronymy.allocate(part, whole)
	except ValueError:
	    raise MeronymicError(
		'%r is already part of %r '
		'(not whole=%r)' % (part, meronomy[part], whole)
	    )
