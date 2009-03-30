from __future__ import print_function
import __builtin__, sys, contextlib, StringIO
from md import fluid

__all__ = (
    'display', 'read', 'current_input_port', 'current_output_port',
    'output_to_string', 'input_from_string',
    'output_to_file', 'input_from_file'
)

CURRENT_OUTPUT_PORT = fluid.cell(sys.stdout, type=fluid.copied)
CURRENT_INPUT_PORT = fluid.cell(sys.stdin, type=fluid.copied)

def current_output_port():
    return CURRENT_OUTPUT_PORT.value

def current_input_port():
    return CURRENT_INPUT_PORT.value

def display(*args, **kwargs):
    kwargs.setdefault('file', current_output_port())
    return __builtin__.print(*args, **kwargs)

def read(*args):
    return current_input_port().read(*args)

@contextlib.contextmanager
def output_to_string(*args):
    with contextlib.closing(StringIO.StringIO(*args)) as port:
	with CURRENT_OUTPUT_PORT.let(port):
	    yield

@contextlib.contextmanager
def input_from_string(*args):
    with contextlib.closing(StringIO.StringIO(*args)) as port:
	with CURRENT_INPUT_PORT.let(port):
	    yield

@contextlib.contextmanager
def output_to_file(filename, mode='w'):
    with contextlib.closing(open(filename, mode)) as port:
	with CURRENT_OUTPUT_PORT.let(port):
	    yield

@contextlib.contextmanager
def input_from_file(filename, mode='r'):
    with contextlib.closing(open(filename, mode)) as port:
	with CURRENT_INPUT_PORT.let(port):
	    yield
