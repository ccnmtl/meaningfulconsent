from django.conf import settings
from django.conf.urls import patterns, include, url
from django.contrib import admin
from django.contrib.auth.decorators import login_required
from django.contrib.auth.views import password_change, password_change_done
from django.views.decorators.csrf import ensure_csrf_cookie
from django.views.generic import TemplateView
from meaningfulconsent.main.mixins import is_facilitator
from meaningfulconsent.main.views import CreateParticipantView, \
    LoginParticipantView, LanguageParticipantView, RestrictedEditView, \
    ClearParticipantView, IndexView, LoginView, LogoutView
from pagetree.generic.views import PageView
import debug_toolbar
admin.autodiscover()


auth_urls = (r'^accounts/', include('django.contrib.auth.urls'))
if hasattr(settings, 'WIND_BASE'):
    auth_urls = (r'^accounts/', include('djangowind.urls'))


urlpatterns = patterns(
    '',
    (r'^$', ensure_csrf_cookie(IndexView.as_view())),
    (r'^admin/', include(admin.site.urls)),
    (r'^accounts/login/$', LoginView.as_view()),
    (r'^accounts/logout/$', LogoutView.as_view()),

    # password change & reset
    # the djangowind urls need an update
    url(r'^accounts/password_change/$',
        is_facilitator(password_change),
        name='password_change'),
    url(r'^accounts/password_change/done/$',
        is_facilitator(password_change_done),
        name='password_change_done'),
    url(r'^accounts/password_reset/$',
        'django.contrib.auth.views.password_reset',
        name='password_reset'),
    url(r'^accounts/password_reset/done/$',
        'django.contrib.auth.views.password_reset_done',
        name='password_reset_done'),
    url(r'^accounts/reset/(?P<uidb64>[0-9A-Za-z_\-]+)/'
        '(?P<token>[0-9A-Za-z]{1,13}-[0-9A-Za-z]{1,20})/$',
        'django.contrib.auth.views.password_reset_confirm',
        name='password_reset_confirm'),
    url(r'^accounts/reset/done/$',
        'django.contrib.auth.views.password_reset_complete',
        name='password_reset_complete'),

    auth_urls,

    url(r'^_impersonate/', include('impersonate.urls')),
    (r'^stats/$', TemplateView.as_view(template_name="stats.html")),
    (r'smoketest/', include('smoketest.urls')),
    (r'^uploads/(?P<path>.*)$',
     'django.views.static.serve', {'document_root': settings.MEDIA_ROOT}),
    (r'^pagetree/', include('pagetree.urls')),
    (r'^quizblock/', include('quizblock.urls')),

    (r'^participant/create/$', CreateParticipantView.as_view()),
    (r'^participant/login/$', LoginParticipantView.as_view()),
    url(r'^participant/language/$', LanguageParticipantView.as_view(),
        name='participant-language'),
    (r'^participant/clear/$', ClearParticipantView.as_view()),

    # English
    (r'^pages/en/edit/(?P<path>.*)$', RestrictedEditView.as_view(
        hierarchy_name="en", hierarchy_base="/pages/en/",
        template_name="main/edit_page.html")),
    (r'^pages/en/(?P<path>.*)$', login_required(PageView.as_view(
        hierarchy_name="en", hierarchy_base="/pages/en/",
        gated=True, template_name="main/page.html")),
        {}, 'view-english-page'),

    # Spanish
    (r'^pages/es/edit/(?P<path>.*)$', RestrictedEditView.as_view(
        hierarchy_name="es", hierarchy_base="/pages/es/",
        template_name="main/edit_page.html")),
    (r'^pages/es/(?P<path>.*)$', login_required(PageView.as_view(
        hierarchy_name="es", hierarchy_base="/pages/es/",
        gated=True, template_name="main/page.html")),
     {}, 'view-spanish-page')
)


if settings.DEBUG:
    urlpatterns += patterns('',
                            url(r'^__debug__/', include(debug_toolbar.urls)))
