=============
 Annotations
=============

A Simple Typechecker
--------------------

This is a simple typechecker using the annotation compiler with
:mod:`expect`.

An example use is

.. doctest::

   >>> from md.annotate import *
   >>> from docs.examples.expected import *

   >>> @expected(int, int, bool)
   ... def greater(a, b):
   ...     return a > b

   >>> list(zip_annotations(greater))
   [('a', <type 'int'>), ('b', <type 'int'>), ('return', <type 'bool'>)]

   >>> compiled_with(greater)
   <function expects ...>

   >>> greater(2, 1)
   True

   >>> greater(2, 1.5)
   Traceback (most recent call last):
   ...
   UnexpectedArgument: for 'b' in <function greater ...>: expected int, not <float 1.5>

Here is the implementation.

.. literalinclude:: expected.py

