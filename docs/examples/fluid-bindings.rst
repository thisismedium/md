================
 Fluid Bindings
================

Database Connection
-------------------

See :doc:`../md.fluid` for an example of a fluid database connection.

Fluid :func:`print`
-------------------

Writing to standard output and reading from standard input are good
use-cases for fluid bindings.  This example implements context
managers similar to ``with-input-from-file`` / ``with-output-to-file``
(defined in R5RS_) and ``with-input-from-string`` /
``with-output-to-string`` (defined in `Gambit-C`_).  These allow
methods using "generic" :func:`read` and :func:`display` operations to
have their input and output redirected by the caller.  If
:obj:`__future__.print_function` is being used, a better
implementation would be to override it instead of defining a
:func:`display` function.

.. _R5RS: http://www.schemers.org/Documents/Standards/R5RS/
.. _`Gambit-C`: http://dynamo.iro.umontreal.ca/~gambit/wiki/index.php/Main_Page

.. doctest::

   >>> import os, time, threading
   >>> from docs.examples.fluidprint import *

   >>>

   >>> def hello():
   ...     display("Hello, world!")

   >>> def capture(thunk):
   ...     with output_to_string():
   ...         thunk()
   ...         return current_output_port().getvalue()

   >>> def show():
   ...     port = current_input_port()
   ...     display("showing %s:" % port, read().strip())

   >>> hello()
   Hello, world!

   >>> TEMP = "/tmp/fluid-bindings-example.txt"
   >>> with output_to_file(TEMP):
   ...     hello()

   >>> capture(hello)
   'Hello, world!\n'

   >>> with input_from_file(TEMP):
   ...     t1 = threading.Thread(target=lambda: time.sleep(0.01) or show())
   ...     t1.start()
   ...     with input_from_string("main thread has different input"):
   ...         show()
   ...         t1.join()
   showing <StringIO.StringIO instance ...>: main thread has different input
   showing <open file '/tmp/fluid-bindings-example.txt', ...>: Hello, world!

   >>> os.unlink(TEMP)

And the implementation:

.. literalinclude:: fluidprint.py

Transactions
------------

The :mod:`md.stm` module uses fluid bindings to track which journal is
currently in scope for a :func:`transaction`.

.. literalinclude:: ../../md/stm/transaction.py
