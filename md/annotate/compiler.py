from __future__ import absolute_import
from collections import namedtuple
from ast import *
from inspect import getargspec
from functools import wraps
from .annotate import annotations, transfer
from .util import is_nested

__all__ = ('compile_annotations', )

def compile_annotations(procedure, unifier, prepare_ann=None, ast=False):
    """Compile the annotations of procedure using unifier and prepare_ann.

    The compiled procedure wraps procedure and has an identical
    signature.

    If there is some procedure defined like this:

        def procedure(foo: FooType) -> ResultType:
            pass

    Then `compile_annotations(procedure, unifier)' produces this:

        def compiled_procedure(foo):
            check = unifier(procedure)
            return check(procedure(check(foo, FooType)), ResultType)

    """

    prepare_ann = prepare_ann or map_ann_ident
    ann = annotations(procedure)

    if not ann:
	return None if ast else procedure
    else:
	_proc, _unify, _check = gensyms(procedure.__name__, 'unify', 'check')

	ns = { _proc: procedure, _unify: unifier }
	(expand_arg, ns) = make_checker(ann, prepare_ann, _check, ns)

	(unifier, ns) = expand_unifier(_check, _unify, _proc, ns)
	(result, ns) = expand_result(procedure, _proc, expand_arg, ns)
	(wrapper, ns) = expand_wrapper(procedure, _proc, unifier + result, ns)

	(mod, ns) = expand_module(procedure, _proc, wrapper, ns)
	return (mod, ns) if ast else compiled(procedure, wrapper, mod, ns)

def map_ann_ident(name, ann):
    return ann

def compiled(procedure, wrapper, mod, ns):
    exec(compile(mod, procedure.func_code.co_filename, 'exec'), ns)
    proc = ns[procedure.__name__]
    return transfer(procedure, wraps(procedure)(proc))


### Transformers

def make_checker(ann, prepare_ann, _check, ns):
    """Produce a expand_arg() procedure for checking individual arguments.

    The map_arg() procedure produces `check(arg, ArgType)' for each
    argument.
    """

    ## Call prepare_ann() on each annotation.  Keep the result for
    ## addition to the namespace.  Map the original name to the gensym
    ## for use by expand_arg() during expansion
    prepared = {}; syms = {}
    for (name, ann) in ann.iteritems():
	_sym = gensym(name, Load())
	prepared[_sym] = prepare_ann(name, ann)
	syms[name] = _sym

    def expand_arg(name, expr):
	try:
	    return Call(_check, [expr, syms[name]], [], None, None)
	except KeyError:
	    return expr

    return (expand_arg, updated(ns, prepared.iteritems()))

def expand_unifier(_check, _unify, _proc, ns):
    """Produce a expand_body() procedure that sets up a unifier.

    This produces `check = unifier(procedure)'.
    """

    ident = [Name(_check.id, Store())]
    check = Assign(ident, Call(_unify, [_proc], [], None, None))

    return ([check], ns)

def expand_result(procedure, _proc, expand_arg, ns):
    """Produce a return value.

    This produces `return check(procedure(...), ResultType)'
    """
    (args, vararg, kwarg) = map_argspec(expand_arg, procedure)
    result = Call(_proc, args, [], vararg, kwarg)
    return ([Return(expand_arg('return', result))], ns)

def expand_wrapper(procedure, _proc, body, ns):
    """Produce the definition of the wrapping procedure."""

    (args, vararg, kwarg, defaults) = getargspec(procedure)

    defaults = [
	(gensym('default-%d' % i, Load()), d)
	for (i, d) in enumerate(defaults or ())
    ]

    wrapper = FunctionDef(
        procedure.__name__,
        arguments(
            map_args(identity_argument, args, Store(), Param()),
            vararg,
            kwarg,
            defaults and ([n for (n, v) in defaults])
        ),
	body,
        []
    )

    return (wrapper, updated(ns, defaults))

def expand_module(procedure, _proc, wrapper, ns):
    ns = namespace_symbols(ns)
    wrapper.lineno = procedure.func_code.co_firstlineno
    mod = fix_missing_locations(Module([wrapper]))
    return (mod, ns)


### Utility

def map_argspec(proc, procedure):
    (args, vararg, kwarg, defaults) = getargspec(procedure)
    return (
	map_args(proc, args, Load(), Load()),
	vararg and proc(vararg, Name(vararg, Load())),
	kwarg and proc(kwarg, Name(kwarg, Load()))
    )

def map_args(proc, args, tuple_ctx, name_ctx):
    return [
        map_tuple(proc, a, tuple_ctx) if is_nested(a) else proc(a, Name(a, name_ctx))
        for a in args
    ]

def map_tuple(proc, args, ctx):
    return Tuple([
            map_tuple(proc, a, ctx) if is_nested(a) else proc(a, Name(a, ctx))
            for a in args
    ], ctx)

def identity_argument(name, expr):
    return expr


### Names

def updated(ns, bindings):
    ns = dict(ns)
    ns.update(bindings)
    return ns

def namespace_symbols(ns):
    return dict(
	(n.id if isinstance(n, Name) else n, v)
	for (n, v) in ns.iteritems()
    )

class Gensym(object):

    def __init__(self, template):
        self.template = template
        self.count = 0

    def __call__(self, id, ctx):
        self.count += 1
        return Name(self.template % (self.count, id), ctx)

gensym = Gensym('#g%d:%s')

def gensyms(*names, **kwargs):
    ctx = kwargs.pop('ctx', Load)
    return [gensym(n, ctx()) for n in names]
