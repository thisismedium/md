from md import fluid

CURRENT_REQUEST = fluid.cell(None, type=fluid.private)
current_request = fluid.accessor(CURRENT_REQUEST, 'request')

class RequestMiddleware(object):
    def process_request(self, request):
	CURRENT_REQUEST.value = request


