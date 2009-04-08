================================
 :mod:`fluid` -- Fluid Bindings
================================

.. module:: fluid
   :synopsis: Fluid bindings

The :mod:`fluid` module implements fluid bindings for Python.  `Fluid
cells`_ are bindings in the `dynamic environment`_.  The dynamic
environment is like the lexical environment, but the value of a
binding depends on the `dynamic extent`_ of a `runtime context`_
rather than lexical scope.  The dynamic environment interacts with
threads like the Unix shell environment interacts with processes:
fluid bindings may be inherited from the parent thread.

Fluid bindings are safer and more convenient than global variables.
They can often be used instead of a singleton.  Dynamic parameters are
described in more detail in `SRFI 39`_.

.. _`dynamic extent`: http://en.wikipedia.org/wiki/Common_Lisp#Dynamic
.. _`runtime context`: http://docs.python.org/reference/datamodel.html#context-managers
.. _`SRFI 39`: http://srfi.schemers.org/srfi-39/srfi-39.html

.. doctest::

   >>> from md import fluid

Fluid Cells
-----------

.. function:: cell(value[, validate, type]) -> Cell

   Create a new fluid :class:`Cell` with global ``value``.

   If ``validate`` is given, it should be a callable that accepts a
   new value and returns a value (maybe the same value or something
   derived from it) or raises an exception.

   The ``type`` parameter must be one of: :class:`shared`,
   :class:`copied`, :class:`private`.  The default is :class:`shared`.

   .. doctest::

      >>> def valid_base(value):
      ...     assert 2 <= value <= 36, 'base must be betwee 2 and 36'
      ...     return value

      >>> BASE = fluid.cell(10, validate=valid_base)

      >>> def convert(str):
      ...     return int(str, BASE.value)

      >>> convert("11")
      11

      >>> with BASE.let(2):
      ...     print convert("11"), '(a)'
      ...     with BASE.let(8):
      ...         print convert("11"), '(b)'
      ...     print convert("11"), '(c)'
      3 (a)
      9 (b)
      3 (c)

      >>> BASE.set(40)
      Traceback (most recent call last):
      ...
      AssertionError: base must be betwee 2 and 36

.. class:: Cell(value[, validate])

   A cell is assigned a default, global value when it is created.  If
   the optional ``validate`` is given, it should be a procedure that
   takes a value and returns another value.  This can be used to check
   or coerce values assigned to the cell.

   .. attribute:: value

      Get or set the current value of this cell.

      .. doctest::

      	 >>> BASE.value
	 10
	 >>> BASE.value = 16

   .. method:: let(value) -> context

      Bind the cell to ``value`` for the extent of the context.

      .. doctest::

      	 >>> with BASE.let(8):
	 ...     BASE.value
	 8
	 >>> BASE.value
	 16

Dynamic Environment
-------------------

The dynamic environment is propagated to threads when they are started
by snapshotting the environment of the parent thread.  The propagated
value depends on the type of the :func:`cell`.  There are three types,
:class:`shared` is the default.

.. doctest::

   >>> import threading, time

   >>> P1 = fluid.cell('apple')

   >>> def show(name, status):
   ...     print name, 'P1:', P1.value, '(%s)' % status

   >>> def worker1():
   ...     show('worker1', 'wait for change')
   ...     time.sleep(0.01)
   ...     show('worker1', 'after change')

   >>> def worker2():
   ...     time.sleep(0)
   ...     P1.value = 'banana'
   ...     show('worker2', 'changed')

   >>> def demo():
   ...     t1 = threading.Thread(target=worker1)
   ...     t2 = threading.Thread(target=worker2)
   ...     with P1.let('pineapple'):
   ...     	t1.start(); t2.start()
   ...     	t1.join()
   ...          show('parent', 'workers done')

.. class:: shared

   When a :func:`cell` is shared, it is bound to the same memory
   location in both the parent and child threads.

   .. doctest::

      >>> demo()
      worker1 P1: pineapple (wait for change)
      worker2 P1: banana (changed)
      worker1 P1: banana (after change)
      parent P1: banana (workers done)

.. class:: copied

   In this case, a copy is made of the parent's binding at
   snapshot-time.  The cell is bound to the copy in the child's
   dynamic environment.

   .. doctest::

      >>> P1 = fluid.cell('apple', type=fluid.copied)
      >>> demo()
      worker1 P1: pineapple (wait for change)
      worker2 P1: banana (changed)
      worker1 P1: pineapple (after change)
      parent P1: pineapple (workers done)

.. class:: private

   No binding is added to the child's dynamic environment.  The cell
   is bound to a copy of its global value.

   .. doctest::

      >>> P1 = fluid.cell('apple', type=fluid.private)
      >>> demo()
      worker1 P1: apple (wait for change)
      worker2 P1: banana (changed)
      worker1 P1: apple (after change)
      parent P1: pineapple (workers done)

Utilities
---------

.. function:: let(*bindings) -> context

   This is a shortcut for parameterizing several fluid cells at the
   same time.

   .. doctest::

      >>> MULTIPLIER = fluid.cell(2)
      >>> BASE.value = 10

      >>> def multiply(str):
      ...     return convert(str) * MULTIPLIER.value

      >>> multiply("11")
      22

      >>> with fluid.let((BASE, 2), (MULTIPLIER, 3)):
      ...     multiply("11")
      9

.. function:: accessor(name, cell, require=False) -> access

   The two most common actions on a fluid cell are getting its value
   or creating a binding in a new dynamic context.  An accessor closes
   over a cell.  When it is called with no arguments, the value of the
   cell is returned.  When called with one argument (a new value), a
   context manager is returned that binds the cell to the new value.
   If ``require=True`` and the value of the cell is accessed and it is
   still the default value, a value error is raised.

   .. doctest::

      >>> multiplier = fluid.accessor('multipler', MULTIPLIER)
      >>> with multiplier(20):
      ...    multiplier()
      20

Example: a parameterized database connection
--------------------------------------------

A database connection is a good use-case for a fluid cell.  Instead of
requiring each query-method to accept a connection parameter, the
connection is parameterized through the dynamic environment.

   .. doctest::

      >>> import sqlite3
      >>> from contextlib import contextmanager

      >>> CONNECTION = fluid.cell(None)
      >>> connection = fluid.accessor('connection', CONNECTION, require=True)

      >>> @contextmanager
      ... def autocommitted():
      ...     conn = connection()
      ...     yield conn.cursor()
      ...     conn.commit()

      >>> def create_schema():
      ...     with autocommitted() as cursor:
      ...         cursor.execute('CREATE TABLE data (value text);')

      >>> def add_data(values):
      ...     with autocommitted() as cursor:
      ...         cursor.executemany(
      ...             'INSERT INTO data VALUES (?);',
      ...             ((v,) for v in values)
      ...         )

      >>> def get_data():
      ...     cursor = connection().cursor()
      ...     cursor.execute('SELECT value from data ORDER BY value;')
      ...     return (r[0] for r in cursor)

      >>> @contextmanager
      ... def snapshot(dest):
      ...     exported = get_data()
      ...     with connection(dest):
      ...         create_schema()
      ...         add_data(exported)
      ...         yield

      >>> create_schema()
      Traceback (most recent call last):
      ...
      ValueError: missing value for current_connection

      >>> import sqlite3
      >>> with connection(sqlite3.connect(':memory:')):
      ...     create_schema()
      ...     add_data(['foo', 'bar', 'baz'])
      ...     with snapshot(sqlite3.connect(':memory:')):
      ...         add_data(['mumble', 'quux'])
      ...         print list(get_data()), '(nested)'
      ...     print list(get_data()), '(outer)'
      [u'bar', u'baz', u'foo', u'mumble', u'quux'] (nested)
      [u'bar', u'baz', u'foo'] (outer)
