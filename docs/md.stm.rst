==============================================
:mod:`stm` -- Software Transactional Memory
==============================================

.. module:: stm
   :synopsis: An optimistically concurrent transactional memory implementation.

The :mod:`stm` module is a simple, optimistically concurrent
transactional memory_ implementation.  Transactions_ are designed to
operate against a common memory and use copy-on-write to isolate
changes in state from each other.  `Transactional data types`_
participate by declaring how each of their methods will affect
instance state.

.. doctest::

   >>> import __builtin__
   >>> from md.stm import *

.. doctest::
   :hide:

   >>> initialize()

Memory
------

.. function:: initialize([mem])

   Initialize transactional memory; any existing transactional memory
   is destroyed.  This is done automatically by the :mod:`stm` module.
   With no arguments, the default :class:`memory` implementation is
   used.  To use a custom :class:`Memory`, pass the custom instance as
   the first argument.

.. function:: use([mem])

   A context manager that temporarily shadows the active memory for
   the dynamic extent of the context.

.. class:: memory([name, check_read=True, check_write=True])

   The default :class:`Memory` implementation.  The ``name`` argument
   is a simple label.  The ``check_read`` and ``check_write``
   parameters indicate whether or not to verify the read-log and
   write-log of a journal when it is committed to the :class:`memory`.

Transactional Data Types
------------------------

A transactional data type implements :class:`Cursor` and is designed
to cooperate with transactional memory by using four instance
operators: :func:`readable`, :func:`writable`, :func:`allocate`, and
:func:`delete`.  Each operator declares how an instance's state is
about to be affected by a method.  Classes implemented using these
operators are called "cursors" because they act as fixed interfaces
that operate against different transactional states depending on the
context.

Instance Operators
~~~~~~~~~~~~~~~~~~

.. function:: allocate(self, state) -> state

   Initialize the state for a particular instance.  This is typically
   done in ``__new__``.

.. function:: readable(self) -> state

   Return and instance's current readable state.  This value should be
   treated as a read-only value.  Returning the entire readable state
   from a method is poor design because it may be modified by client
   code.

.. function:: writable(self) -> state

   Return an instance's current writable state.  The first time this
   is called in the current context, the readable state is copied to
   become the new writable state.  If a method needs to return the
   entire state for some reason, it is best to return a writable state
   in case it is externally modified.

.. function:: delete(self)

   Destroy the state for a particular instance.  To closely mimic
   Python's normal behavior, this may be done in `__del__`.

Default :class:`Cursor` Implementation
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. class:: cursor

   A simple :class:`Cursor` implementation is provided by :mod:`stm`.
   It defines :meth:`__new__`, :meth:`__getattr__`,
   :meth:`__setattr__`, and :meth:`__delattr__`.  Simply inherit from
   :class:`cursor` instead of :class:`object`.

   >>> class cell(cursor):
   ...     def __init__(self, value):
   ...         self.value = value
   ...
   ...     def __repr__(self):
   ...         return '<cell %r>' % self.value

   The type of state given to :func:`allocate` can be overridden by
   redefining the :attr:`cursor.StateType` attribute.

   >>> class sequence(cursor):
   ...     StateType = __builtin__.list
   ...
   ...     def __init__(self, seq=()):
   ...         self.extend(seq)
   ...
   ...     def __repr__(self):
   ...         return '<sequence %r>' % readable(self)
   ...
   ...     def __getitem__(self, key):
   ...         return readable(self)[key]
   ...
   ...     def __setitem__(self, key, value):
   ...         writable(self)[key] = value
   ...
   ...     def __delitem__(self, key):
   ...         del writable(self)[key]
   ...
   ...     def extend(self, seq):
   ...         writable(self).extend(seq)

.. class:: dict(dict=None, **kwargs)

   A transactional :class:`dict`.

.. class:: tree(seq=None, **kwargs)

   A transactional :class:`tree`.

.. class:: omap(seq=None, **kwargs)

   A transactional :class:`omap`.

.. class:: list(seq=None)

   A transactional :class:`list`.

.. class:: set(seq=None)

   A transactional :class:`set`.

Transactions
------------

.. function:: transaction([name], autocommit=True)

   A transaction provides a context for transactional memory
   operations.  Committing a transaction writes changes to the outer
   transaction or memory.  Transactions may be nested.

.. function:: transactionally(proc, *args, **kwargs)

   This is a basic optimistic concurrency operator.  It attempts to
   run ``proc(*args, **kwargs)`` inside a transaction several times
   before giving up.  See :doc:`examples/stm` for examples.  The
   :func:`transactionally` operator accepts three optional keyword
   arguments and returns the result of calling :obj:`proc`.

   :param __attempts__: The number of attempts to make (default: ``3``)
   :param autocommit: Passed to :func:`transaction` (default: ``True``)

.. function:: rollback([what]) -> what

   Revert a cursor to its original state.

   .. doctest::

      >>> with transaction():
      ...     c1 = cell(list(['a', 'b', 'c']))

      >>> with transaction():
      ...     print c1.value, '(originally)'
      ...     c1.value[0] = 'Z'
      ...     print c1.value, '(modified)'
      ...     print rollback(c1.value), '(rollback)'
      list(['a', 'b', 'c']) (originally)
      list(['Z', 'b', 'c']) (modified)
      list(['a', 'b', 'c']) (rollback)

.. function:: commit()

   Manually commit a transaction if ``autocommit`` is ``False``.

.. function:: abort()

   Terminates the current transaction.  Any uncommitted changes are
   discarded.

   .. doctest::

      >>> with transaction():
      ...    c3 = cell('apple')
      ...    with transaction():
      ...        c3.value = 'banana'
      ...        abort()

      >>> c3.value
      'apple'

.. function:: changed()

   Produce an iterator over items that have been changed in the
   current transaction.

   .. doctest::

      >>> with transaction():
      ...     c1.value[1] = 'B'
      ...     print '\\n'.join(repr(c) for c in changed())
      list(['a', 'B', 'c'])

Persistence
-----------

A :class:`cursor` does not have a built-in persistent identity;
dumping and loading a cursor produces a copy.  Subclasses of
:class:`cursor` may override :meth:`__getstate__` to specialize the
state that is reduced; by default ``readable(self)`` is returned.
Pickling a :class:`cursor` in the middle of a transaction could lead
to unexpected results if the cursor is unsaved or the transaction is
uncommitted.

See the examples in :doc:`examples/stm` for a simple persistent memory
implementation.

.. doctest::

   >>> from cPickle import dumps, loads

   >>> with transaction():
   ...     o1 = cursor(); o2 = cursor()
   ...     o1.foo = o2
   ...     o2.bar = 1

   >>> o3 = loads(dumps(o1, -1))
   >>> o3 is not o1; o3.foo is not o2; o3.foo.bar
   True
   True
   1
