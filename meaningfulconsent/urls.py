from django.conf import settings
from django.conf.urls import patterns, include, url
from django.contrib import admin
from django.contrib.auth.decorators import login_required
from django.views.generic import TemplateView
from meaningfulconsent.main import views
from pagetree.generic.views import PageView, EditView
admin.autodiscover()


redirect_after_logout = getattr(settings, 'LOGOUT_REDIRECT_URL', None)
auth_urls = (r'^accounts/', include('django.contrib.auth.urls'))
logout_page = (
    r'^accounts/logout/$',
    'django.contrib.auth.views.logout',
    {'next_page': redirect_after_logout})
if hasattr(settings, 'WIND_BASE'):
    auth_urls = (r'^accounts/', include('djangowind.urls'))
    logout_page = (
        r'^accounts/logout/$',
        'djangowind.views.logout',
        {'next_page': redirect_after_logout})

urlpatterns = patterns(
    '',
    auth_urls,
    logout_page,
    (r'^$', views.IndexView.as_view()),
    (r'^admin/', include(admin.site.urls)),
    url(r'^_impersonate/', include('impersonate.urls')),
    (r'^stats/$', TemplateView.as_view(template_name="stats.html")),
    (r'smoketest/', include('smoketest.urls')),
    (r'^uploads/(?P<path>.*)$',
     'django.views.static.serve', {'document_root': settings.MEDIA_ROOT}),
    (r'^pagetree/', include('pagetree.urls')),
    (r'^quizblock/', include('quizblock.urls')),

    # English
    (r'^pages/en/edit/(?P<path>.*)$', login_required(EditView.as_view(
        hierarchy_name="en",
        hierarchy_base="/pages/en/")),
     {}, 'edit-page'),
    (r'^pages/en/(?P<path>.*)$', PageView.as_view(
        hierarchy_name="en",
        hierarchy_base="/pages/en/")),

    # Spanish
    (r'^pages/es/edit/(?P<path>.*)$', login_required(EditView.as_view(
        hierarchy_name="es",
        hierarchy_base="/pages/es/")),
     {}, 'edit-page'),
    (r'^pages/es/(?P<path>.*)$', PageView.as_view(
        hierarchy_name="es",
        hierarchy_base="/pages/es/"))
)

if settings.DEBUG:
    import debug_toolbar
    urlpatterns += patterns('',
        url(r'^__debug__/', include(debug_toolbar.urls)),
    )
