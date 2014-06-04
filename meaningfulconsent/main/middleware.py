from django.http import HttpResponseNotAllowed
from django.template import RequestContext, loader


class HttpResponseNotAllowedMiddleware(object):
    def process_response(self, request, response):
        if isinstance(response, HttpResponseNotAllowed):
            context = RequestContext(request)
            response.content = loader.render_to_string(
                "405.html", context_instance=context)
        return response
