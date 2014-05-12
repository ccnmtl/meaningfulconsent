from django.conf import settings
from django.conf.urls import patterns, include, url
from django.contrib import admin
from django.contrib.auth.decorators import login_required
from django.views.decorators.csrf import ensure_csrf_cookie
from django.views.generic import TemplateView
from meaningfulconsent.main.views import CreateParticipantView, \
    LoginParticipantView, LanguageParticipantView, RestrictedEditView, \
    ClearParticipantView, IndexView, LoginView, LogoutView
from pagetree.generic.views import PageView
admin.autodiscover()


auth_urls = (r'^accounts/', include('django.contrib.auth.urls'))
if hasattr(settings, 'WIND_BASE'):
    auth_urls = (r'^accounts/', include('djangowind.urls'))

urlpatterns = patterns(
    '',
    (r'^accounts/login/$', LoginView.as_view()),
    (r'^accounts/logout/$', LogoutView.as_view()),
    auth_urls,
    (r'^$', ensure_csrf_cookie(IndexView.as_view())),
    (r'^admin/', include(admin.site.urls)),
    url(r'^_impersonate/', include('impersonate.urls')),
    (r'^stats/$', TemplateView.as_view(template_name="stats.html")),
    (r'smoketest/', include('smoketest.urls')),
    (r'^uploads/(?P<path>.*)$',
     'django.views.static.serve', {'document_root': settings.MEDIA_ROOT}),
    (r'^pagetree/', include('pagetree.urls')),
    (r'^quizblock/', include('quizblock.urls')),

    (r'^participant/create/$', CreateParticipantView.as_view()),
    (r'^participant/login/$', LoginParticipantView.as_view()),
    (r'^participant/language/$', LanguageParticipantView.as_view()),
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
    import debug_toolbar
    urlpatterns += patterns('',
                            url(r'^__debug__/', include(debug_toolbar.urls)))
