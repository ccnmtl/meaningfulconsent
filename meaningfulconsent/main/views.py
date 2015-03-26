from django import http
from django.conf import settings
from django.contrib.auth import login, authenticate
from django.contrib.auth.forms import AuthenticationForm
from django.contrib.auth.models import User
from django.contrib.auth.views import logout as auth_logout_view
from django.contrib.contenttypes.models import ContentType
from django.contrib.sites.models import Site
from django.http.response import HttpResponseRedirect, HttpResponse
from django.shortcuts import get_object_or_404
from django.views.generic.base import TemplateView, View
from djangowind.views import logout as wind_logout_view
from meaningfulconsent.main.auth import generate_random_username, \
    generate_password, USERNAME_PREFIX
from meaningfulconsent.main.mixins import JSONResponseMixin, LoggedInMixin, \
    LoggedInMixinSuperuser, LoggedInFacilitatorMixin
from meaningfulconsent.main.models import UserVideoView, \
    MeaningfulConsentReport
from pagetree.generic.views import EditView
from pagetree.models import UserLocation, UserPageVisit, PageBlock, Hierarchy
from quizblock.models import Quiz
from zipfile import ZipFile
from StringIO import StringIO
import csv


def get_quiz_blocks(css_class):
    quiz_type = ContentType.objects.get_for_model(Quiz)
    blocks = PageBlock.objects.filter(css_extra=css_class,
                                      content_type=quiz_type)
    return blocks


def user_is_participant(user):
    return not user.is_anonymous() and user.profile.is_participant()


def user_is_facilitator(user):
    return not user.is_anonymous() and not user.profile.is_participant()


def context_processor(request):
    ctx = {}
    if user_is_participant(request.user):
        # djangowind delivers the form in un-authenticated situations
        ctx['login_form'] = AuthenticationForm(request)
    ctx['site'] = Site.objects.get_current()
    ctx['MEDIA_URL'] = settings.MEDIA_URL
    return ctx


class LoginView(JSONResponseMixin, View):

    def post(self, request):
        request.session.set_test_cookie()
        login_form = AuthenticationForm(request, request.POST)
        if login_form.is_valid():
            login(request, login_form.get_user())
            if request.user is not None:
                next_url = request.POST.get('next', '/')
                return self.render_to_json_response({'next': next_url})
        else:
            return self.render_to_json_response({'error': True})


class LogoutView(LoggedInMixin, View):

    def get(self, request):
        if request.user.profile.is_participant():
            url = request.user.profile.last_location_url()
            return HttpResponseRedirect(url)
        elif hasattr(settings, 'WIND_BASE'):
            return wind_logout_view(request, next_page="/")
        else:
            return auth_logout_view(request, "/")


class RestrictedEditView(LoggedInMixinSuperuser, EditView):
    template_name = "pagetree/edit_page.html"


class IndexView(TemplateView):
    def dispatch(self, *args, **kwargs):
        user = self.request.user
        if user_is_participant(user):
            return HttpResponseRedirect(user.profile.last_location_url())

        if user.is_anonymous():
            self.template_name = "main/splash.html"
        else:
            self.template_name = "main/facilitator.html"

        return super(IndexView, self).dispatch(*args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super(IndexView, self).get_context_data(**kwargs)

        if user_is_facilitator(self.request.user):
            context['participants'] = User.objects.filter(
                is_active=False,
                username__startswith=USERNAME_PREFIX)

        return context


class ClearParticipantView(LoggedInFacilitatorMixin, View):

    def get(self, request):
        # clear visits & saved locations
        UserLocation.objects.filter(user=request.user).delete()
        UserPageVisit.objects.filter(user=request.user).delete()
        UserVideoView.objects.filter(user=request.user).delete()

        # clear quiz responses & submission
        import quizblock
        quizblock.models.Submission.objects.filter(user=request.user).delete()

        url = request.user.profile.default_location().get_absolute_url()
        return HttpResponseRedirect(url)


class CreateParticipantView(LoggedInFacilitatorMixin, JSONResponseMixin, View):

    def post(self, request):
        username = generate_random_username()
        password = generate_password(username)

        user = User(username=username, is_active=False)
        user.set_password(password)
        user.save()

        user.profile.creator = request.user
        user.profile.save()

        context = {'user': {'username': user.username}}
        return self.render_to_json_response(context)


class LoginParticipantView(LoggedInFacilitatorMixin, View):

    def post(self, request):
        """
        Log in a special user as a participant
        """
        username = request.POST.get('username')
        password = generate_password(username)

        user = authenticate(username=username, password=password)
        if user is not None:
            login(request, user)
            if user.is_authenticated():
                return HttpResponseRedirect(user.profile.last_location_url())

        raise http.Http404


class ParticipantLanguageView(LoggedInMixin, TemplateView):
    template_name = "main/participant_language.html"

    def post(self, request):
        """
        Change the user's language. Redirect to alternate hierarchy
        """
        language = request.POST.get('language', 'en')
        request.user.profile.language = language
        request.user.profile.save()

        loc = request.user.profile.last_location()

        return HttpResponseRedirect(loc.get_absolute_url())


class TrackParticipantView(LoggedInMixin, JSONResponseMixin, View):

    def post(self, request):
        vid = request.POST.get('video_id', '')
        video_duration = int(request.POST.get('video_duration', 0))
        seconds_viewed = int(request.POST.get('seconds_viewed', 0))

        if vid == '':
            context = {'success': False, 'msg': 'Invalid video id'}
        elif video_duration < 1:
            context = {'success': False, 'msg': 'Invalid video duration'}
        else:
            uvv = UserVideoView.objects.get_or_create(user=request.user,
                                                      video_id=vid)
            uvv[0].video_duration = video_duration
            uvv[0].seconds_viewed += seconds_viewed
            uvv[0].save()

            context = {'success': True}

        return self.render_to_json_response(context)


class ArchiveParticipantView(LoggedInFacilitatorMixin,
                             JSONResponseMixin, View):

    def post(self, request):
        username = request.POST.get('username', '')
        participant = get_object_or_404(User.objects, username=username)

        participant.profile.archived = True
        participant.profile.save()

        context = {'success': True}

        return self.render_to_json_response(context)


class ParticipantPrintView(LoggedInFacilitatorMixin,
                           TemplateView):
    template_name = "main/participant_printout.html"

    def get_context_data(self, **kwargs):
        ctx = super(ParticipantPrintView, self).get_context_data(**kwargs)

        username = self.request.GET.get('username', '')
        ctx['participant'] = get_object_or_404(User.objects, username=username)
        return ctx


class ParticipantNoteView(LoggedInFacilitatorMixin,
                          JSONResponseMixin, View):
    def post(self, request):
        username = request.POST.get('username', '')
        participant = get_object_or_404(User.objects, username=username)

        notes = request.POST.get('notes', '')
        participant.profile.notes = notes
        participant.profile.save()

        context = {'success': True}

        return self.render_to_json_response(context)


class ReportView(LoggedInFacilitatorMixin, View):

    def get(self, request):
        report = MeaningfulConsentReport()

        # setup zip file for the key & value file
        response = HttpResponse(mimetype='application/zip')

        disposition = 'attachment; filename=meaningfulconsent.zip'
        response['Content-Disposition'] = disposition

        z = ZipFile(response, 'w')

        output = StringIO()  # temp output file
        writer = csv.writer(output)

        # report on all hierarchies
        hierarchies = Hierarchy.objects.all()

        # Key file
        for row in report.metadata(hierarchies):
            writer.writerow(row)

        z.writestr("meaningfulconsent_key.csv", output.getvalue())

        # Results file
        output.truncate(0)
        output.seek(0)

        writer = csv.writer(output)

        for row in report.values(hierarchies):
            writer.writerow(row)

        z.writestr("meaningfulconsent_values.csv", output.getvalue())

        return response
