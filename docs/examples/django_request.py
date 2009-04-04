

### Settings

ROOT_URLCONF = __name__

MIDDLEWARE_CLASSES = (
    'django.middleware.common.CommonMiddleware',
    'docs.examples.request_middleware.RequestMiddleware'
)


### Views

from django.http import HttpResponse

def example(request):
    return HttpResponse(logic())


### Urls

from django.conf.urls.defaults import patterns

urlpatterns = patterns(
    '',
    (r'^example', example)
)


### Business Logic

from docs.examples.request_middleware import current_request

def logic():
    request = current_request()
    return '%s %s' % (request.method, request.get_full_path())
