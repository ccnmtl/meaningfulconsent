from django import http
from django.conf import settings
from django.contrib.auth import login, authenticate
from django.contrib.auth.decorators import user_passes_test, login_required
from django.contrib.auth.models import User
from django.contrib.auth.views import logout as auth_logout_view
from django.http.response import HttpResponse, HttpResponseRedirect
from django.utils.decorators import method_decorator
from django.views.generic.base import TemplateView, View
from meaningfulconsent.main.auth import generate_random_username, \
    generate_password
from meaningfulconsent.main.models import UserProfile, Clinic
from pagetree.generic.views import EditView
from pagetree.models import UserLocation, UserPageVisit
import djangowind
import json


def logout(request):
    if request.user.profile.is_participant:
        return  # don't do anything
    elif hasattr(settings, 'WIND_BASE'):
        return djangowind.views.logout(request)
    else:
        return auth_logout_view(request, "/")


class JSONResponseMixin(object):
    """
    A mixin that can be used to render a JSON response.
    """
    def render_to_json_response(self, context, **response_kwargs):
        """
        Returns a JSON response, transforming 'context' to make the payload.
        """
        return HttpResponse(
            self.convert_context_to_json(context),
            content_type='application/json',
            **response_kwargs
        )

    def convert_context_to_json(self, context):
        "Convert the context dictionary into a JSON object"
        # Note: This is *EXTREMELY* naive; in reality, you'll need
        # to do much more complex handling to ensure that arbitrary
        # objects -- such as Django model instances or querysets
        # -- can be serialized as JSON.
        return json.dumps(context)


class LoggedInMixin(object):
    @method_decorator(login_required)
    def dispatch(self, *args, **kwargs):
        return super(LoggedInMixin, self).dispatch(*args, **kwargs)


class LoggedInFacilitatorMixin(object):
    @method_decorator(user_passes_test(lambda u: not u.profile.is_participant))
    def dispatch(self, *args, **kwargs):
        return super(LoggedInFacilitatorMixin, self).dispatch(*args, **kwargs)


class LoggedInMixinSuperuser(object):
    @method_decorator(user_passes_test(lambda u: u.is_superuser))
    def dispatch(self, *args, **kwargs):
        return super(LoggedInMixinSuperuser, self).dispatch(*args, **kwargs)


class IndexView(TemplateView):
    template_name = "main/index.html"

    def dispatch(self, *args, **kwargs):
        if (not self.request.user.is_anonymous and
                self.user.profile.is_participant):
            if self.user.profile.language is None:
                return HttpResponseRedirect('/participant/language')
            else:
                url = self.user.profile.last_location().get_absolute_url()
                return HttpResponseRedirect(url)
        else:
            return super(IndexView, self).dispatch(*args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super(IndexView, self).get_context_data(**kwargs)

        user = self.request.user
        if not user.is_anonymous() and not user.profile.is_participant:
            context['participants'] = User.objects.filter(
                profile__is_participant=True)

        return context


class CreateParticipantView(LoggedInFacilitatorMixin, JSONResponseMixin, View):

    def post(self, request):
        username = generate_random_username()
        password = generate_password(username)

        user = User(username=username)
        user.set_password(password)
        user.is_active = False  # regular login does not allow inactive users
        user.save()

        # @todo - when more than one clinic exists, create a profile
        # page for participants. for the moment, just pick the first one
        clinic = Clinic.objects.all()[0]
        profile = UserProfile(user=user, is_participant=True, clinic=clinic)
        profile.save()

        context = {'user': {'username': user.username}}
        return self.render_to_json_response(context)


class LoginParticipantView(LoggedInFacilitatorMixin, JSONResponseMixin, View):

    def post(self, request):
        """
        Log in a special user as a participant
        """
        username = request.POST.get('username')

        user = authenticate(username=username)
        if user is not None:
            login(request, user)
            if user.is_authenticated():
                last_location = user.profile.last_location()
                if last_location == user.profile.default_location():
                    return HttpResponseRedirect("/participant/language/")
                else:
                    url = last_location.get_absolute_url()
                    return HttpResponseRedirect(url)

        raise http.Http404


class LanguageParticipantView(LoggedInMixin, TemplateView):
    template_name = "main/language.html"

    def post(self, request):
        """
        Log in a user as a participant without requiring credentials
        """
        language = request.POST.get('language', 'en')
        request.user.profile.language = language
        request.user.profile.save()

        url = request.user.profile.last_location().get_absolute_url()
        return HttpResponseRedirect(url)


class RestrictedEditView(LoggedInMixinSuperuser, EditView):
    template_name = "pagetree/edit_page.html"


class ClearParticipantView(LoggedInMixinSuperuser, View):

    def get(self, request):
        # clear visits & saved locations
        UserLocation.objects.filter(user=request.user).delete()
        UserPageVisit.objects.filter(user=request.user).delete()

        # clear quiz responses & submission
        import quizblock
        quizblock.models.Submission.objects.filter(user=request.user).delete()

        url = request.user.profile.default_location().get_absolute_url()
        return HttpResponseRedirect(url)

