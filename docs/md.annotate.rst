================================
 :mod:`annotate` -- Annotations
================================

.. module:: annotate
   :synopsis: Create and compile procedure annotations.

`PEP-3107`_ specifies function annotations for Python 3.0.  This
module implements decorators for annotating procedures in Python 2.x,
operators for reflecting on a procedure's annotations, and primitives
for compiling an annotated procedure into a wrapper procedure with an
identical signature.

.. _`PEP-3107`: http://www.python.org/dev/peps/pep-3107/

.. doctest::

   >>> from md.annotate import *

   >>> def show(proc):
   ...     return list(zip_annotations(proc, None))

Annotating
----------

.. function:: annotated(*args, **kwargs) -> decorator

   A decorator for annotating procedures.  The annotations given as
   ``args`` will be matched to the corresponding parameter in the
   procedure's argspec.  Annotations given in ``kwargs`` will be
   matched to the named parameter.

   To specify a return annotation, ``args`` should be one element
   longer than the number of parameters in the procedure or the
   special keyword argument ``__return__`` can be used.

   .. doctest::

      >>> @annotated(int, int, bool)
      ... def greater(a, b):
      ...     return a > b

      >>> show(greater)
      [('a', <type 'int'>), ('b', <type 'int'>), ('return', <type 'bool'>)]

      >>> @annotated(basestring, __return__=basestring)
      ... def join(glue, *args):
      ...     return glue.join(str(a) for a in args)

      >>> show(join)
      [('glue', <type 'basestring'>), ('args', None), ('return', <type 'basestring'>)]

.. function:: annotate(procedure, bindings) -> procedure

   Bind the (name, annotation) items given in ``bindings`` as
   annotations of ``procedure``.

   .. doctest::

      >>> def less(a, b):
      ...     return a < b

      >>> annotate(less, [('a', int), ('b', int), ('return', bool)])
      <function less ...>

      >>> show(less)
      [('a', <type 'int'>), ('b', <type 'int'>), ('return', <type 'bool'>)]

.. function:: transfer(source, dest) -> dest

   Copy the annotations of ``source`` onto ``dest``.  The parameter
   names don't have to match, but both procedures must have identical
   arity.

   .. doctest::

      >>> def lte(n1, n2):
      ...     return n1 <= n2

      >>> show(transfer(less, lte))
      [('n1', <type 'int'>), ('n2', <type 'int'>), ('return', <type 'bool'>)]

      >>> def product(*args):
      ...     from operator import mul
      ...     return reduce(mul, args, 1)

      >>> transfer(less, product)
      Traceback (most recent call last):
      ...
      TypeError: ('inconsistent structure', <function less ...>, <function product ...>)

.. function:: annotating(procedure) -> decorator

   This is a decorator for producing specialized annotating decorators
   like :func:`annotated`.  For example, :func:`annotated` could be
   implemented like this:

   .. code-block:: python

      >>> @annotating
      ... def annotated(procedure):
      ...     return procedure

   The decorator consumed by :func:`annotating` is transformed to have
   the same semantics as :func:`annotate` (it accepts annotation
   parameters and keyword annotations), but the implementation can be
   focused on what to do with an annotated procedure (see
   :doc:`examples/annotate` for an example).

Inspecting
----------

.. function:: annotations(procedure) -> dict

   Return the annotations of procedure.  An empty dictionary is
   returned if the procedure has not been annotated.

   .. doctest::

      >>> sorted(annotations(lte).items())
      [('n1', <type 'int'>), ('n2', <type 'int'>), ('return', <type 'bool'>)]

      >>> annotations(product)
      {}

.. function:: is_annotated(procedure) -> bool

   Return ``True`` if ``procedure`` is annotated.

   .. doctest::

       >>> is_annotated(less)
       True

       >>> is_annotated(product)
       False

.. function:: zip_annotations(procedure[, default]) -> Iterator

   Zip the annotated parameters of ``procedure`` to their annotations
   in parameter-order.  If ``default`` is given, unannotated
   parameters are zipped to this value.

   .. doctest::

      >>> @annotated(str)
      ... def partial(a, b):
      ...     pass

      >>> list(zip_annotations(partial))
      [('a', <type 'str'>)]

      >>> list(zip_annotations(partial, None))
      [('a', <type 'str'>), ('b', None), ('return', None)]

Compiling
---------

See :doc:`examples/annotate` for examples.

.. function:: compiler.compile_annotations(procedure, unifier[, prepare_ann, ast])

   Compile the annotations of ``procedure`` by producing a wrapper
   where each annotation is used to check an argument value or return
   value.  A ``unifier`` is a factory that produces a ``check``
   procedure.  The ``check`` procedure takes two arguments, a value
   and the corresponding annotation; it must return a good value or
   raise an exception.

   The biggest advantage of using :func:`compiler.compile_annotations`
   is it produces a wrapped procedure with an identical signature.
   This makes compilation transparent to other decorators or signature
   analysis.

   If there is some procedure defined like this,

   .. code-block:: python

       @annotated(FooType, ResultType)
       def procedure(foo)
           pass

   Then ``compile_annotations(procedure, unifier)`` produces something
   like this,

   .. code-block:: python

      __procedure = procedure

      def procedure(foo):
          check = unifier(procedure)
          return check(__procedure(check(foo, FooType)), ResultType)

.. function:: compiled(optimize_away=True) -> decorator

   A decorator that can be used to create decorators that compile
   annotations.  If ``optimize_away`` is true, the compiler will not
   be invoked when ``__debug__`` is ``False``.

.. function:: compiled_with(procedure) -> compiler

   When procedures are decorated with a decorator built with
   :func:`compiled`, the compiled procedure is tagged with the
   original compiler.  It's sometimes useful to have access to this
   information if the annotations need to be recompiled.







