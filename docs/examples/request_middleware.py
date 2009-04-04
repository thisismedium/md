from md import fluid

CURRENT_REQUEST = fluid.cell(None, type=fluid.private)

@fluid.accessor(CURRENT_REQUEST.value)
def current_request():
    return CURRENT_REQUEST.value

class RequestMiddleware(object):
    def process_request(self, request):
	CURRENT_REQUEST.value = request


