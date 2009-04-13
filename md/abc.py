from __future__ import absolute_import
from abc import *

__all__ = (
    'abstractmethod', 'abstractproperty', 'ABCMeta',
    'registers', 'register', 'implements', 'implement'
)

def registers(*subclasses):
    def decorator(cls):
	register(cls, *subclasses)
	return cls
    return decorator

def register(abc, *subclasses):
    for cls in subclasses:
	abc.register(cls)

def implements(*abc):
    def decorator(cls):
	implement(cls, *abc)
	return cls
    return decorator

def implement(cls, *abc):
    for mcls in abc:
	mcls.register(cls)
