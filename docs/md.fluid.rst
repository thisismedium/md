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

.. function:: cell([value, validate, type]) -> Cell

   Create a new fluid :class:`Cell` with global ``value``.  If no
   ``value`` is given, the cell is bound to an undefined value.

   If ``validate`` is given, it should be a callable that accepts a
   new value and returns a value (maybe the same value or something
   derived from it) or raises an exception.

   The ``type`` can be used to specialize the type of cell created.
   The default is :class:`shared`.

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

.. class:: Cell([value, validate])

   A cell is assigned a (possibly undefined) value when it is created.
   If the optional ``validate`` is given, it should be a procedure
   that takes a value and returns another value.  This can be used to
   check or coerce values assigned to the cell.

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
value depends on the type of the :func:`cell`; :class:`shared` is the
default.

.. doctest::

   >>> import threading, time

   >>> def show(name, status, *cells):
   ...     print name, (' '.join(str(c.value) for c in cells)), '(%s)' % status

   >>> def worker1(cell):
   ...     show('worker1', 'wait for change', cell)
   ...     time.sleep(0.01)
   ...     show('worker1', 'after change', cell)

   >>> def worker2(cell):
   ...     time.sleep(0)
   ...     cell.value = 'banana'
   ...     show('worker2', 'changed', cell)

   >>> def demo(cell):
   ...     t1 = threading.Thread(target=lambda: worker1(cell))
   ...     t2 = threading.Thread(target=lambda: worker2(cell))
   ...     with cell.let('pineapple'):
   ...     	t1.start(); t2.start()
   ...     	t1.join()
   ...          show('parent', 'workers done', cell)

.. class:: shared

   The current binding in the dynamic environment is shared with the
   new environment.  Mutating any cell with this shared binding
   affects all cells using that binding.  This is most similar to a
   global variable.

   .. doctest::

      >>> P1 = fluid.cell('apple')
      >>> demo(P1)
      worker1 pineapple (wait for change)
      worker2 banana (changed)
      worker1 banana (after change)
      parent banana (workers done)

.. class:: acquired

   The current value is acquired from the dynamic environment, but the
   cell is bound to a new location containing the value.  Mutations of
   the original location will have no effect on the new location.

   .. doctest::

      >>> P2 = fluid.cell('apple', type=fluid.acquired)
      >>> demo(P2)
      worker1 pineapple (wait for change)
      worker2 banana (changed)
      worker1 pineapple (after change)
      parent pineapple (workers done)

.. class:: private

   No binding is acquired from the dynamic environment.  The cell is
   bound to a new location containing its global value.

   .. doctest::

      >>> P3 = fluid.cell('apple', type=fluid.private)
      >>> demo(P3)
      worker1 apple (wait for change)
      worker2 banana (changed)
      worker1 apple (after change)
      parent pineapple (workers done)

.. class:: copied
.. class:: deepcopied

   These types behave like :class:`acquired`, but they also copy (or
   deepcopy) the *value* of the binding in addition to creating a new
   location.  This is useful if the value of the cell is mutable and
   the new environment should acquire a snapshot of the value.

   .. doctest::

      >>> P4 = fluid.cell(type=fluid.acquired)
      >>> P5 = fluid.cell(type=fluid.copied)

      >>> def worker3(a, b):
      ...     a.value[0] = 'radish'
      ...     b.value[0] = 'mango'
      ...     show('worker3', 'changed', a, b)

      >>> with fluid.let((P4, ['acorn']), (P5, ['grape'])):
      ...     t3 = threading.Thread(target=lambda: worker3(P4, P5))
      ...     t3.start(); t3.join()
      ...     show('parent', 'workers done', P4, P5)
      worker3 ['radish'] ['mango'] (changed)
      parent ['radish'] ['grape'] (workers done)

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

.. function:: accessor(cell[, name]) -> access

   The two most common actions on a fluid cell are getting its value
   or creating a binding in a new dynamic context.  An accessor closes
   over a cell.  When it is called with no arguments, the value of the
   cell is returned.  When called with one argument (a new value), a
   context manager is returned that binds the cell to the new value.

   When a cell is accessed and it has never been assigned a value, a
   :exc:`ValueError` is raised.  The optional ``name`` parameter is
   used to enhance the :exc:`ValueError`.

   .. doctest::

      >>> multiplier = fluid.accessor(MULTIPLIER, name='multiplier')
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

      >>> connection = fluid.accessor(fluid.cell(), name='CONNECTION')

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
      ValueError: CONNECTION is undefined

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
