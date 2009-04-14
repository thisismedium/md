from __future__ import absolute_import
from md.expect import *
from md.annotate import annotating, compiler
from md.annotate.compiler import compile_annotations

__all__ = ('expected', 'expects', 'UnexpectedArgument')

@annotating
def expected(procedure):
    return expects(procedure)

@compiler()
def expects(procedure):
    return compile_annotations(
	procedure,
	check_expectation,
	expectable
    )

def expectable(name, ann):
    """Make sure each annotation can be used with expect() and binds
    it to its name."""
    return (name, expect(ann, is_expectable))

def check_expectation(procedure):
    def check(value, (name, ann)):
	if meets_expectation(value, ann):
	    return value
	else:
	    raise UnexpectedArgument(value, ann, procedure, name)
    return check

class UnexpectedArgument(UnexpectedType):
    def __init__(self, value, ann, proc, name, *args):
	super(UnexpectedArgument, self).__init__(
	    value, ann, proc, name, *args
	)
	self.procedure = proc
	self.name = name

    def __str__(self):
	return 'for %r in %s: %s' % (
	    self.name,
	    self.procedure,
	    super(UnexpectedArgument, self).__str__()
	)
