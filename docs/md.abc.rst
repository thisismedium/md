================================================
 :mod:`abc` -- Abstract Base Class Enhancements
================================================

.. module:: abc
   :synopsis: For use with ABCs

The :mod:`abc` module extends Python's built-in ``abc`` module with a
few additional operations.  For convenience, this module re-exports the
bindings from the built-in ``abc``.

.. doctest::

   >>> from md.abc import *

Decorators
----------

.. function:: registers(*subclasses) -> decorator

   A class decorator for declaring that the ABC being defined is
   already implemented by ``subclasses``.  This is a shortcut for
   calling the :meth:`register` method repeatedly.

   .. doctest::

      >>> from numbers import Number

      >>> @registers(type(None), basestring, Number, tuple)
      ... class Immutable(object):
      ...      __metaclass__ = ABCMeta

      >>> issubclass(tuple, Immutable)
      True

.. function:: implements(*abc) -> decorator

   A class decorator declaring that the class being defined implements
   one or more ABCs.  This is useful when you want to register a new
   concrete class with an ABC, but don't want to inherit from it
   directly.

   .. doctest::

      >>> class SpecialType(type):
      ...     ## Custom logic here
      ...     pass

      >>> @implements(Immutable)
      ... class special(object):
      ...     __metaclass__ = SpecialType

      >>> issubclass(special, Immutable)
      True


