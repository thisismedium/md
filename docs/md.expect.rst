==============================================
 :mod:`expect` -- Primitive Type Expectations
==============================================

.. module:: expect
   :synopsis: Very primitive type checking.

This module implements a more declarative and unified interface for
these two scenarios:

.. code-block:: python

   if isinstance(foo, SomeType):
       pass ## do something
   else:
       pass ## handle exceptional situation

.. code-block:: python

   if some_assertion_holds(foo):
       pass ## do something
   else:
       pass ## handle exceptional situation

Some have noted that that :func:`isinstance` is `considered harmful`_.
Using :func:`expect` with :mod:`abc` Abstract Base Classes instead of
concrete classes will add flexibility to your code.

.. _`considered harmful`: http://www.canonical.org/~kragen/isinstance/

.. doctest::

   >>> from md.expect import *

Expectations
------------

.. function:: expect(obj, interface, cast=None)

   Declare the expectation that ``obj`` conforms to ``interface`` and
   return ``obj`` if it does.  If it does not and ``cast`` is given,
   return ``cast(obj)``; otherwise raise an :exc:`UnexpectedType`
   exception.  The ``interface`` may be a type, tuple of types, or a
   :class:`Callable` that must return ``True`` or ``False`` when
   ``interface(obj)`` is called.

   The two required arguments of this operation are intentionally
   similar to :func:`adapt` of `PEP-246`_.  This is to make it easy to
   use as a primitive for type-checking libraries that consume
   `function annotations`_.

   .. doctest::

      >>> from numbers import Number

      >>> expect(1, Number)
      1

      >>> expect("6F", Number)
      Traceback (most recent call last):
      ...
      UnexpectedType: expected Number, not <str '6F'>

      >>> expect("6F", Number, lambda hex: int(hex, 16))
      111

.. _`PEP-246`: http://www.python.org/dev/peps/pep-0246/
.. _`function annotations`: http://www.python.org/dev/peps/pep-3107/

.. function:: meets_expectation(obj, interface)

   Return ``True`` if ``expect(obj, interface)`` would succeed,
   ``False`` otherwise.  No exception is raised.

   .. doctest::

      >>> meets_expectation(1, Number)
      True

      >>> meets_expectation("6F", Number)
      False

.. function:: is_expectable(interface)

   Return ``True`` if ``interface`` is a suitable second argument to
   :func:`expect`.

   .. doctest::

      >>> is_expectable(basestring)
      True

      >>> is_expectable('foo')
      False

Errors
------

.. exception:: UnexpectedType(value, interface, *args)

   This subclass of :class:`TypeError` is raised when :func:`expect`
   fails.  It is guaranteed to have two additional properties defined:
   ``value`` and ``interface``, which were the first two arguments to
   :func:`expect`.

   .. doctest::

      >>> try:
      ...     print expect("6F", Number)
      ... except UnexpectedType as exc:
      ...     print 'Caught exception', exc.value, exc.interface
      Caught exception 6F <class 'numbers.Number'>

