from django.http import HttpResponseNotAllowed
from django.template import loader


class HttpResponseNotAllowedMiddleware(object):
    def process_response(self, request, response):
        if isinstance(response, HttpResponseNotAllowed):
            response.content = loader.render_to_string("405.html")
        return response
