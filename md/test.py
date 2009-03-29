from __future__ import absolute_import
import unittest, doctest, sys, inspect, os, glob, functools
from os import path

__all__ = ('pkg_suite', 'pkg_suites')

## TEST_FOLDERS are relative to top_level_dirname()

UNITTEST_EXT = ('.py', )

DOCTEST_FOLDERS = ('../docs', )

DOCTEST_EXT = ('.rst', '.txt')

DOCTEST_OPTIONS = (
    doctest.ELLIPSIS
    | doctest.DONT_ACCEPT_TRUE_FOR_1
    | doctest.IGNORE_EXCEPTION_DETAIL
)


### Construct Suites

def pkg_suites(*names, **kwargs):
    suites = (pkg_suite(n, **kwargs) for n in names)
    return unittest.TestSuite(have_tests(suites))

def pkg_suite(
    name, docfolders=DOCTEST_FOLDERS, docext=DOCTEST_EXT,
    optionflags=DOCTEST_OPTIONS, unitext=UNITTEST_EXT
):
    result = unittest.TestSuite()

    mod = module(name)
    result.addTests(docfile_suites(mod, docfolders, docext, optionflags))
    result.addTests(doctest_suites(mod, docext, optionflags))
    result.addTests(unittest_suites(mod, unitext))

    return result

def suites(proc):
    def internal(*args, **kwargs):
	return have_tests(proc(*args, **kwargs))
    return functools.wraps(proc)(internal)

def have_tests(suites):
    return (s for s in suites if s and s._tests)

@suites
def doctest_suites(mod, docext=DOCTEST_EXT, optionflags=DOCTEST_OPTIONS):
    if is_package(mod):
	base = path.dirname(mod.__file__)

	yield docfile_suite(
	    (p for (p, n, e) in candidates(base, docext)),
	    optionflags
	)

	for (filename, name, ext) in candidates(base, ('.py', )):
	    qualified = join_module_names(mod.__name__, name)
	    yield doctest_suite(qualified, optionflags)
    else:
	yield doctest_suite(mod, optionflags)

@suites
def docfile_suites(
    mod, folders=DOCTEST_FOLDERS,
    ext=DOCTEST_EXT, optionflags=DOCTEST_OPTIONS
):
    mod = module(mod)
    project = top_level_dirname(mod)

    for folder in find_test_folders(project, folders):
	yield docfile_suite(
	    (p for (p, n, e) in candidates(folder, ext)
	     if n.startswith(mod.__name__)),
	    optionflags
	)

    if is_package(mod):
	yield docfile_suite(
	    (p for (p, n, e) in candidates(path.dirname(mod.__file__), ext)),
	    optionflags
	)

@suites
def unittest_suites(mod, ext=UNITTEST_EXT):
    if is_package(mod):
	base = path.dirname(mod.__file__)
	for (filename, name, ext) in candidates(base, ext):
	    qualified = join_module_names(mod.__name__, name)
	    yield unittest_suite(qualified)
    else:
	yield unittest_suite(mod)


### tests

def DOCTEST_GLOBALS():
    """See: http://bugs.python.org/issue5021"""
    return dict(__name__='BUG_5021')

def doctest_suite(mod, optionflags=DOCTEST_OPTIONS):
    try:
	return doctest.DocTestSuite(
	    module(mod),
	    optionflags=optionflags,
	    globs=DOCTEST_GLOBALS()
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

def candidates(base, match_ext):
    chop = len(base) + 1
    for (dirpath, dirnames, filenames) in os.walk(base):
	for filename in filenames:
	    qualified = path.join(dirpath, filename)
	    (name, ext) = path.splitext(qualified)
	    if ext in match_ext:
		name = name[chop:]
		if not name.startswith('.'):
		    yield (qualified, name.replace('/', '.'), ext)

def module(name):
    """Return the module associated with name, importing it if
    necessary.  Assume absolute imports."""
    if inspect.ismodule(name):
	mod = name
    elif name in sys.modules:
	mod = sys.modules[name]
    elif '.' in name:
	(package, module) = name.rsplit('.', 1)
	mod = getattr(
	    __import__(package, fromlist=[module], level=0),
	    module
	)
    else:
	mod = __import__(name)

    return mod

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

def join_module_names(base, name):
    name = name[:-9] if name.endswith('__init__') else name
    return '.'.join((base, name)) if name else base
