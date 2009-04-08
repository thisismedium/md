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
   ...     StateType = list
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

.. class:: tdict(dict=None, **kwargs)

   A transactional :class:`dict`.

.. class:: tlist(seq=None)

   A transactional :class:`list`.

.. class:: tset(seq=None)

   A transactional :class:`set`.

Transactions
------------

.. function:: transaction([name], autocommit=True, autosave=True)

   A transaction provides a context for transactional memory
   operations.  Saving changed data writes the changes to a
   transaction's save-log.  Committing a transaction writes saved
   changes to the outer transaction's save-log.  A top-level
   transaction operates against the transactional memory store.
   Transactions may be nested.

.. function:: transactionally(proc, *args, **kwargs)

   This is a basic optimistic concurrency operator.  It attempts to
   run ``proc(*args, **kwargs)`` inside a transaction several times
   before giving up.  See :doc:`examples/stm` for examples.  The
   :func:`transactionally` operator accepts three optional keyword
   arguments and returns the result of calling :obj:`proc`.

   :param __attempts__: The number of attempts to make (default: ``3``)
   :param autosave: Passed to :func:`transaction` (default: ``True``)
   :param autocommit: Passed to :func:`transaction` (default: ``True``)

.. function:: save([what]) -> what

   Transactions auto-commit and auto-save by default.  Use
   :func:`save` to add changes that will be committed when auto-save
   is disabled or before calling a nested transaction.  Unsaved
   changes are discarded when the transaction is completed.  Without
   any arguments, all :func:`unsaved` changes are saved.  Otherwise,
   ``what`` may be a cursor or sequence of cursors.

   .. doctest::

      >>> with transaction(autosave=False):
      ...     s1 = save(tlist([1, 2, 3]))
      ...     c1 = save(cell(s1))
      >>> c1.value
      tlist([1, 2, 3])

      >>> with transaction(autosave=False):
      ...     c1.value[1] = 20
      >>> c1.value
      tlist([1, 2, 3])

   Save must be called on the cursor that's changed.  Calling save on
   a cursor referring to a changed cursor won't work.

   .. doctest::

      >>> with transaction(autosave=False):
      ...     c1.value[1] = 20
      ...     save(c1.value)
      tlist([1, 20, 3])
      >>> c1.value
      tlist([1, 20, 3])

      >>> with transaction(autocommit=False, autosave=False):
      ...     c1.value[2] = 30
      ...     save(c1)
      <cell tlist([1, 20, 30])>
      >>> c1
      <cell tlist([1, 20, 3])>

   Leaving the ``autosave`` argument set to ``True`` is convenient for
   "always commit everything" transactions.

   .. doctest::

      >>> with transaction():
      ...     c2 = cell(tlist(['a', 'b', 'c']))
      >>> c2.value
      tlist(['a', 'b', 'c'])

.. function:: rollback([what]) -> what

   Revert a cursor to its last saved state (the opposite of
   :func:`save`).  When called with no arguments, all :func:`unsaved`
   cursors are reverted.

   .. doctest::

      >>> with transaction(autosave=False):
      ...     c2.value[0] = 'A'
      ...     with transaction(autosave=False):
      ...         print c2.value, '(nested)'
      ...         c2.value[0] = 'Z'
      ...     print c2.value, '(after nested; no save)'
      ...     print rollback(c2.value), '(rollback)'
      ...     c2.value[0] = 'Z'
      ...     print save(c2.value), '(saved)'
      ...     with transaction(autosave=False):
      ...         print c2.value, '(nested2)'
      ...         c2.value[1] = 'Y'
      ...         print save(c2.value), '(nested2 save)'
      ...     print c2.value, '(after nested2 save)'
      tlist(['a', 'b', 'c']) (nested)
      tlist(['A', 'b', 'c']) (after nested; no save)
      tlist(['a', 'b', 'c']) (rollback)
      tlist(['Z', 'b', 'c']) (saved)
      tlist(['Z', 'b', 'c']) (nested2)
      tlist(['Z', 'Y', 'c']) (nested2 save)
      tlist(['Z', 'Y', 'c']) (after nested2 save)

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

.. function:: saved()

   Produce an iterator over the items in a transaction's save-log.

.. function:: unsaved()

   Produce an iterator over the items that need to be added to a
   transaction's save-log.

   .. doctest::

      >>> with transaction(autosave=False):
      ...     c1.value[0] = 10
      ...     c2.value[1] = 'B'
      ...     print list(saved()), list(unsaved())
      ...     save()
      ...     print list(saved()), list(unsaved())
      [] [tlist([10, 20, 3]), tlist(['Z', 'B', 'c'])]
      [tlist([10, 20, 3]), tlist(['Z', 'B', 'c'])] []

      >>> c2.value
      tlist(['Z', 'B', 'c'])

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
