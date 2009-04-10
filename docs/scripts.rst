=========
 Scripts
=========

These scripts are included with the :mod:`md` module.

``pytest`` -- run :mod:`test` suites
------------------------------------

usage: pytest [options] module-or-file ...

This script runs tests found by :func:`test.pkg_suites` for the given
modules.  This makes running tests for any package or module very
easy.  Run ``pytest --help`` to see the options.  For example:

.. code-block:: sh

   %git clone git://github.com/thisismedium/md.git
   Initialized empty Git repository ...

   %cd md

   %python setup.py develop
   running develop
   ...

   %pytest -vv md
   Doctest: md.fluid.rst ... ok
   Doctest: md.rst ... ok
   Doctest: md.stm.rst ... ok

   ----------------------------------------------------------------------
   Ran 3 tests in 0.087s

Doctest files can be tested just as easily.

.. code-block:: sh

   %find docs -name '*.rst' | xargs pytest
   ----------------------------------------------------------------------
   Ran 9 tests in 1.683s

   OK

No special support is required by the modules being tested.  Here's an
example of testing the ``pickle`` and ``pickletools`` modules build
into Python.

.. code-block:: sh

   %pytest -vv pickle pickletools
   Doctest: pickle.decode_long ... ok
   Doctest: pickle.encode_long ... ok
   Doctest: pickletools.__test__.disassembler_memo_test ... ok
   Doctest: pickletools.__test__.disassembler_test ... ok
   Doctest: pickletools.read_decimalnl_long ... ok
   Doctest: pickletools.read_decimalnl_short ... ok
   Doctest: pickletools.read_float8 ... ok
   Doctest: pickletools.read_floatnl ... ok
   Doctest: pickletools.read_int4 ... ok
   Doctest: pickletools.read_long1 ... ok
   Doctest: pickletools.read_long4 ... ok
   Doctest: pickletools.read_string1 ... ok
   Doctest: pickletools.read_string4 ... ok
   Doctest: pickletools.read_stringnl ... ok
   Doctest: pickletools.read_stringnl_noescape_pair ... ok
   Doctest: pickletools.read_uint1 ... ok
   Doctest: pickletools.read_uint2 ... ok
   Doctest: pickletools.read_unicodestring4 ... ok
   Doctest: pickletools.read_unicodestringnl ... ok

   ----------------------------------------------------------------------
   Ran 19 tests in 0.056s

   OK


