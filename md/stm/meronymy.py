from __future__ import absolute_import
from md import fluid
from .interfaces import Cursor
from .log import weaklog

__all__ = ('partof', 'whole', 'wholes', 'MeronymicError')

def partof(whole, part):
    if isinstance(part, Cursor) and isinstance(whole, Cursor):
        register_part(MERONYMY, whole, part)
    return part

def whole(part, default=None):
    return MERONYMY.get(part, default)

def wholes(parts, default=None):
    return (MERONYMY.get(p, default) for p in parts)


###

class MeronymicError(Exception): pass

MERONYMY = weaklog()

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
