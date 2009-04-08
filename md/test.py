from __future__ import absolute_import
import re, unittest, doctest, sys, inspect, os, glob, functools
from importlib import import_module
from os import path

__all__ = ('pkg_suite', 'pkg_suites', 'module_suites', 'docfile_suites')

## TEST_FOLDERS are relative to top_level_dirname()

UNITTEST_EXT = ('.py', )

DOCTEST_FOLDERS = ('../docs', )

DOCTEST_EXT = ('.rst', '.txt')

DOCTEST_OPTIONS = (
    doctest.ELLIPSIS
    | doctest.DONT_ACCEPT_TRUE_FOR_1
    | doctest.IGNORE_EXCEPTION_DETAIL
)


### Suites

def pkg_suites(*names, **kwargs):
    suites = (pkg_suite(n, **kwargs) for n in names)
    return unittest.TestSuite(have_tests(suites))

def pkg_suite(
    name, docprefix=None, docfolders=DOCTEST_FOLDERS, docext=DOCTEST_EXT,
    optionflags=DOCTEST_OPTIONS, unitext=UNITTEST_EXT
):
    result = unittest.TestSuite()

    (_, ext) = path.splitext(name)
    if ext in docext:
	result.addTests(docfile_suite([name], optionflags))
    else:
	mod = module(name)
	result.addTests(module_suites(mod, unitext, optionflags))
	result.addTests(
	    docfile_suites(mod, docprefix, docfolders, docext, optionflags)
	)

    return result

def suites(proc):
    def internal(*args, **kwargs):
	return have_tests(proc(*args, **kwargs))
    return functools.wraps(proc)(internal)

def have_tests(suites):
    return (s for s in suites if s and s._tests)

@suites
def module_suites(mod, ext=UNITTEST_EXT, optionflags=DOCTEST_OPTIONS):
    mod = module(mod)
    if is_package(mod):
	base = path.dirname(mod.__file__)
	prefix = mod.__name__
	for mod in module_candidates(base, prefix, ext):
	    yield doctest_suite(mod, optionflags)
	    yield unittest_suite(mod)
    else:
	yield doctest_suite(mod, optionflags)
	yield unittest_suite(mod)

@suites
def docfile_suites(
    mod, prefix=None, folders=DOCTEST_FOLDERS,
    ext=DOCTEST_EXT, optionflags=DOCTEST_OPTIONS
):
    mod = module(mod)
    project = top_level_dirname(mod)
    prefix = mod.__name__ if prefix is None else prefix

    for folder in find_test_folders(project, folders):
	yield docfile_suite(file_candidates(folder, prefix, ext), optionflags)

    if is_package(mod):
	folder = path.dirname(mod.__file__)
	yield docfile_suite(file_candidates(folder, '', ext), optionflags)


### Tests

def DOCTEST_GLOBALS():
    """See: http://bugs.python.org/issue5021"""
    return dict(__name__='BUG_5021')

def doctest_suite(mod, optionflags=DOCTEST_OPTIONS):
    try:
	return doctest.DocTestSuite(
	    module(mod),
	    optionflags=optionflags,
	    extraglobs=DOCTEST_GLOBALS()
	)
    except ValueError:
	## DocTestSuite raises a value error if it doesn't find
	## any tests.
	return None

def docfile_suite(paths, optionflags=DOCTEST_OPTIONS):
    return doctest.DocFileSuite(
	*list(paths),
	 module_relative=False,
	 optionflags=optionflags,
	 globs=DOCTEST_GLOBALS()
    )

def unittest_suite(mod):
    return unittest.defaultTestLoader.loadTestsFromModule(module(mod))


### Utility

def file_candidates(base, prefix, match_ext):
    """Produce a sequence of paths in base where the relative name
    starts with prefix."""
    return (
	p for (p, n) in candidates(base, match_ext)
	if n.startswith(prefix)
    )

def module_candidates(base, prefix, match_ext):
    """Produce sequence of module names in the prefix namespace
    located in the folder base."""
    for (filename, name) in candidates(base, match_ext):
	if name.endswith('__init__'):
	    name = name[:-9]
	yield '.'.join((prefix, name.replace('/', '.'))).strip('.')

def candidates(base, match_ext):
    """Produce sequence of (path, relative_name) items by scanning the
    subtree of base for files with a match_ext extension."""
    chop = len(base) + 1
    for (dirpath, dirnames, filenames) in os.walk(base):
	for filename in filenames:
	    qualified = path.join(dirpath, filename)
	    (name, ext) = path.splitext(qualified)
	    if ext in match_ext:
		relative = name[chop:]
		if not is_dotfile(relative):
		    yield (qualified, relative)

def module(name):
    """Return the module associated with name, importing it if
    necessary.  Assume absolute imports."""
    if inspect.ismodule(name):
	return name
    else:
	return import_module(name)

def top_level_dirname(mod):
    """Return the directory of the absolute top-level package of mod.

    If mod is bound to the module foo.bar.baz,
    top_level_dirname(mod) => '/path/to/foo/'.
    """
    top = module(mod.__name__.split('.', 1)[0])
    return path.dirname(top.__file__)

def is_package(mod):
    return path.splitext(mod.__file__)[0].endswith('__init__')

def find_test_folders(base, folders):
    for folder in folders:
	dirname = path.realpath(path.join(base, folder))
	if path.exists(dirname):
	    yield dirname

DOTFILE = re.compile(r'(?:^\.)|(?:/\.)')
def is_dotfile(path):
    return bool(DOTFILE.search(path))
