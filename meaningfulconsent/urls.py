from django.conf import settings
from django.conf.urls import patterns, include, url
from django.contrib import admin
from django.contrib.auth.decorators import login_required
from django.contrib.auth.views import password_change, password_change_done
from django.views.decorators.csrf import ensure_csrf_cookie
from django.views.generic import TemplateView
from meaningfulconsent.main.mixins import is_facilitator
from meaningfulconsent.main.models import ParticipantViewSet
from meaningfulconsent.main.views import ArchiveParticipantView, \
    ClearParticipantView, CreateParticipantView, IndexView, LoginView, \
    LoginParticipantView, LogoutView, ParticipantLanguageView, \
    ParticipantNoteView, RestrictedEditView, TrackParticipantView, \
    ParticipantPrintView, ReportView
from pagetree.generic.views import PageView
from rest_framework import routers
import debug_toolbar
from django.contrib.auth import views as auth_views

admin.autodiscover()

router = routers.DefaultRouter()
router.register(r'participants', ParticipantViewSet)

redirect_after_logout = getattr(settings, 'LOGOUT_REDIRECT_URL', None)

auth_urls = (r'^accounts/', include('django.contrib.auth.urls'))

logout_page = (r'^accounts/logout/$',
               'django.contrib.auth.views.logout',
               {'next_page': redirect_after_logout})
admin_logout_page = (r'^accounts/logout/$',
                     'django.contrib.auth.views.logout',
                     {'next_page': '/admin/'})

if hasattr(settings, 'CAS_BASE'):
    auth_urls = (r'^accounts/', include('djangowind.urls'))
    logout_page = (r'^accounts/logout/$',
                   'djangowind.views.logout',
                   {'next_page': redirect_after_logout})
    admin_logout_page = (r'^admin/logout/$',
                         'djangowind.views.logout',
                         {'next_page': redirect_after_logout})


urlpatterns = patterns(
    '',
    logout_page,
    admin_logout_page,
    auth_urls,
    (r'^$', ensure_csrf_cookie(IndexView.as_view())),
    (r'^admin/', include(admin.site.urls)),
    (r'^accounts/login/$', LoginView.as_view()),
    (r'^accounts/logout/$', LogoutView.as_view()),

    # password change & reset. overriding to gate them.
    url(r'^password/change/$',
        is_facilitator(auth_views.password_change),
        name='password_change'),
    url(r'^password/change/done/$',
        is_facilitator(auth_views.password_change_done),
        name='password_change_done'),
    url(r'^password/reset/$',
        auth_views.password_reset,
        name='password_reset'),
    url(r'^password/reset/done/$',
        auth_views.password_reset_done,
        name='password_reset_done'),
    url(r'^password/reset/complete/$',
        auth_views.password_reset_complete,
        name='password_reset_complete'),
    url(r'^password/reset/confirm/(?P<uidb64>[0-9A-Za-z])-(?P<token>.)/$',
        auth_views.password_reset_confirm,
        name='password_reset_confirm'),
    url(r'^api/', include(router.urls)),

    url(r'^_impersonate/', include('impersonate.urls')),
    (r'^stats/$', TemplateView.as_view(template_name="stats.html")),
    (r'smoketest/', include('smoketest.urls')),
    (r'^uploads/(?P<path>.*)$',
     'django.views.static.serve', {'document_root': settings.MEDIA_ROOT}),
    (r'^pagetree/', include('pagetree.urls')),
    (r'^quizblock/', include('quizblock.urls')),

    (r'^participants/manage/$', is_facilitator(
        TemplateView.as_view(template_name="main/manage_participants.html"))),
    (r'^participants/report/$', ReportView.as_view()),

    (r'^participant/archive/$', ArchiveParticipantView.as_view()),
    (r'^participant/clear/$', ClearParticipantView.as_view()),
    (r'^participant/create/$', CreateParticipantView.as_view()),
    url(r'^participant/language/$', ParticipantLanguageView.as_view(),
        name='participant-language'),
    (r'^participant/login/$', LoginParticipantView.as_view()),
    (r'^participant/note/$', ParticipantNoteView.as_view()),
    (r'^participant/print/$', ParticipantPrintView.as_view()),
    (r'^participant/track/$', TrackParticipantView.as_view()),

    # English
    (r'^pages/en/edit/(?P<path>.*)$', RestrictedEditView.as_view(
        hierarchy_name="en", hierarchy_base="/pages/en/")),
    (r'^pages/en/(?P<path>.*)$', login_required(PageView.as_view(
        hierarchy_name="en", hierarchy_base="/pages/en/", gated=True)),
        {}, 'view-english-page'),

    # Spanish
    (r'^pages/es/edit/(?P<path>.*)$', RestrictedEditView.as_view(
        hierarchy_name="es", hierarchy_base="/pages/es/")),
    (r'^pages/es/(?P<path>.*)$', login_required(PageView.as_view(
        hierarchy_name="es", hierarchy_base="/pages/es/", gated=True)),
     {}, 'view-spanish-page')
)


if settings.DEBUG:
    urlpatterns += patterns('',
                            url(r'^__debug__/', include(debug_toolbar.urls)))
