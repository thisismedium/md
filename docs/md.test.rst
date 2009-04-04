===========================
 :mod:`test` -- Unit Tests
===========================

.. module:: test
   :synopsis: High-level :class:`TestSuite` constructors.

The :mod:`test` module implements several high-level
:class:`TestSuite` constructors.  The goal of these constructors is to
greedily discover as many tests as possible for a particular module or
package.

Suites
------

.. function:: pkg_suites(*names, **kwargs) -> TestSuite

   Given a series of module names, return a suite with the
   :func:`pkg_suite` tests for each name.  Any keyword arguments are
   passed along to :func:`pkg_suite`.

.. function:: pkg_suite(name[, docprefix, docfolders, docext, optionflags, unitext]) -> TestSuite

   Given the name of a module or package, return a suite with all
   :func:`module_suites` and :func:`docfile_suites`.

.. function:: module_suites(mod[, ext, optionflags]) -> suites

   Return a sequence of doctest and unittest suites for the module
   ``mod``.  If ``mod`` is a package, recursively search for tests in
   all submodules.  By default, files with an extension ``['.py']``
   are searched for.

.. function:: docfile_suites(mod[, prefix, folders, ext, optionflags]) -> suites

   Find docfiles in ``folders`` relative to the absolute top-level
   package of ``mod``.  Only yield suites for files with a name
   beginning with ``prefix``.

   If mod itself is a package, also search for docfiles inside the
   folder containing ``mod``.  When searching within a module's
   directory structure, ``prefix`` is ignored.

   :param prefix: only use files matching this prefix (default: ``mod.__name__``)
   :param folders: search in these folders (relative to top-level module, default: ['../docs'])
   :param ext: search for files with these extensions (default: ['.rst', '.txt'])
   :param optionflags: use these optionflags rather than the default.

   The default ``optionflags`` are ``(ELLIPSIS |
   DONT_ACCEPT_TRUE_FOR_1 | IGNORE_EXCEPTION_DETAIL)``.

   For example, ``docfile_suites('md.stm')`` will search in
   ``dirname(md.stm.__file__)`` because ``md.stm`` is a package.  Any
   files ending in ``.txt`` or ``.rst`` will be used.  The folder
   ``join(dirname(md.__file__), '../docs')`` will also be searched
   because ``md`` is the absolute top-level package of ``md.stm``.
   Only files beginning with ``md.stm``, ``md/stm``, or ``md/stm/``
   and ending with ``.rst`` or ``.txt`` will be used.

Example
-------

The :mod:`md` module uses these suite constructors to make a "test
all" suite for ``setup.py``.  Here are the contents of
``tests/__init__.py`` in the source distribution:

.. literalinclude:: ../tests/__init__.py

