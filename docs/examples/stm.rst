===============================
 Software Transactional Memory
===============================

.. doctest::

   >>> from md.stm import *

Optimistic Concurrency
----------------------

This is a simple example that uses transactional memory to implement a
serial datatype.

.. doctest::
   :hide:

   >>> uninitialize()

.. doctest::

   >>> import time, threading

   >>> class serial(cursor):
   ...     def __init__(self, value=0):
   ...         self.value = value
   ...
   ...     def inc(self):
   ...         self.value += 1
   ...         return self.value

Concurrent operations on a shared :class:`serial` instance are
simulated by forcing a thread to become inactive after aquiring the
next value of a sequence, but before committing its transaction.

The ``worker1`` thread will aquire the value ``1`` and become
inactive.  In the meantime, ``worker2`` aquires the values ``1`` and
``2`` and commits its transaction.  When ``worker1`` reactivates, it
also gets the value ``2``, but when it tries to commit, a
:exc:`CannotCommit` exception is raised because ``worker2`` already
committed new state.  This forces the transaction in ``worker1`` to be
re-run.  The second time, it succeeds and aquires the values ``3`` and
``4``.

.. doctest::

   >>> def next2(ser, sleep=None):
   ...     first = ser.inc()
   ...     if sleep is not None:
   ...         time.sleep(sleep)
   ...     return (first, ser.inc())

   >>> def show(label, work):
   ...     print label, work

   >>> def worker1():
   ...     show('worker1', transactionally(next2, count, sleep=0.1))

   >>> def worker2():
   ...     show('worker2', transactionally(next2, count))

   >>> initialize()

   >>> with transaction():
   ...     count = serial()

   >>> t1 = threading.Thread(target=worker1)
   >>> t2 = threading.Thread(target=worker2)
   >>> t1.start(); t2.start(); t1.join()
   worker2 (1, 2)
   worker1 (3, 4)


:class:`shelf` -- Persistent Transactional Memory
-------------------------------------------------

This is a more advanced example.  :class:`cursor` is extended to have
a persistent identity and :class:`memory` is extended to fetch and
store persistent cursors from a shelf.

.. doctest::
   :hide:

   >>> uninitialize()

Basic Use
~~~~~~~~~

Here is a basic example.  Transactional memory is initialized with a
:class:`shelf` instead of the default (:class:`memory`).

.. doctest::

   >>> import gc
   >>> from docs.examples.stm_shelf import *

   >>> def collect():
   ...     gc.collect()

   >>> initialize(shelf('/tmp/stm.db'))

.. doctest::
   :hide:

   >>> current_memory().clear() # for the doctest

A :class:`pcursor` works like a cursor and optionally takes a keyword
argument, :obj:`__id__`, that will become the new cursor's persistent
id.  If :obj:`__id__` is not given, a unique persistent id will be
generated for the new object.

The operation :func:`fetch` can be used to retrive the cursor
associated with a persistent id.  The :func:`pid` operator returns the
persistent id associated with a cursor.

.. doctest::

   >>> with transaction():
   ...     foo = pcursor(__id__='foo')
   ...     foo.a = pcursor(); foo.a.value = 'A'
   >>> pid(foo)
   'foo'

   >>> del foo; collect()
   >>> foo = fetch('foo'); foo.a.value
   'A'

Unsaved or uncommitted changes are not written to the backing store.

.. doctest::

   >>> with transaction(autosave=False):
   ...     foo.a.value = 'changed'

   >>> del foo; collect()
   >>> fetch('foo').a.value
   'A'

Normal cursors and persistent cursors can be mixed.  When normal
cursors are used, they are persisted as "part of" the persistent
cursor rather than being given a unique persistent identity.

.. doctest::

   >>> with transaction():
   ...     bar = pcursor(__id__='bar')
   ...     bar.b = cursor(); bar.b.value = ['B']

   >>> del bar; collect()
   >>> fetch('bar').b.value
   ['B']

.. doctest::
   :hide:

   >>> current_memory().destroy()
   >>> uninitialize()

Implementation
~~~~~~~~~~~~~~

This rudimentary implementation is mainly concerned with tracking
persistent ids.

An interesting feature is the way :class:`pcursor` dereferencing is
handled.  If one :class:`pcursor` refers to another, a reference is
stored in the shelf.  When the outer :class:`pcursor` is loaded, the
reference it contains is dereferenced on demand rather than at load
time.  Weak references are used to track cursors so they can be
automatically collected when they are done being used.  If
:class:`pcursor` ``A`` refers to :class:`pcursor` ``B``, ``B`` can be
collected once it's no longer being directly referenced in code even
if ``A`` remains strongly referenced.  Since ``A`` contains a lazy
reference to ``B`` rather than a strong reference, ``B`` can be
re-loaded on demand.

Transaction journals use strong references, so anything fetched from
the backing store will not be released during the scope of the
transaction.  This makes transactions a sort of temporary object
cache; lazy references will only be loaded the first time they are
used in a transaction.

.. literalinclude:: stm_shelf.py

