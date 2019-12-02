from django.contrib.auth.decorators import login_required, user_passes_test
from django.http.response import HttpResponseNotAllowed, HttpResponse
from django.utils.decorators import method_decorator
from rest_framework.permissions import BasePermission
import json


class JSONResponseMixin(object):
    def dispatch(self, *args, **kwargs):
        if not self.request.is_ajax():
            return HttpResponseNotAllowed(self._allowed_methods())

        return super(JSONResponseMixin, self).dispatch(*args, **kwargs)

    def render_to_json_response(self, context, **response_kwargs):
        """
        Returns a JSON response, transforming 'context' to make the payload.
        """
        return HttpResponse(json.dumps(context),
                            content_type='application/json',
                            **response_kwargs)


class LoggedInMixin(object):
    @method_decorator(login_required)
    def dispatch(self, *args, **kwargs):
        return super(LoggedInMixin, self).dispatch(*args, **kwargs)


class LoggedInFacilitatorMixin(object):
    def dispatch(self, *args, **kwargs):
        user = self.request.user
        if user.is_anonymous or user.profile.is_participant():
            return HttpResponseNotAllowed('')

        return super(LoggedInFacilitatorMixin, self).dispatch(*args, **kwargs)


class LoggedInMixinSuperuser(object):
    @method_decorator(user_passes_test(lambda u: u.is_superuser))
    def dispatch(self, *args, **kwargs):
        return super(LoggedInMixinSuperuser, self).dispatch(*args, **kwargs)


class FacilitatorRestPermission(BasePermission):

    def has_permission(self, request, view):
        return request.is_ajax() and not request.user.is_anonymous and not (
            request.user.profile.is_participant())
