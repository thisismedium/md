from __future__ import absolute_import
from functools import wraps
from .annotate import annotate, unique

__all__ = ('annotating', 'annotated', 'compiler', 'compiled_with')

def annotating(decorate):
    """A decorator that can be used to produce annotating decorators."""
    def annotating_decorator(*args, **kwargs):
	def decorator(procedure):
	    return decorate(annotate(procedure, unique(procedure, args, kwargs)))
	return decorator
    return wraps(decorate)(annotating_decorator)

@annotating
def annotated(procedure):
    return procedure

def identity(obj):
    return obj

def compiler(optimize_away=True):
    """A decorator that can be used to create compiling decorators."""
    def decorator(decorate):
        if optimize_away and not __debug__:
            return wraps(decorate)(identity)
        else:
            @wraps(decorate)
            def compiler(procedure):
                proc = decorate(procedure)
                proc.__compiled_with__ = compiler
                return proc
            return compiler
    return decorator

def compiled_with(procedure):
    return getattr(procedure, '__compiled_with__', identity)
