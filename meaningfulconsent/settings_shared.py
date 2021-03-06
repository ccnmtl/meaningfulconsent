# flake8: noqa
# Django settings for meaningfulconsent project.
import os.path
from ccnmtlsettings.shared import common

project = 'meaningfulconsent'
base = os.path.dirname(__file__)
locals().update(common(project=project, base=base))

PROJECT_APPS = [
    'meaningfulconsent.main',
]

USE_TZ = True
USE_I18N = True

TEMPLATES[0]['OPTIONS']['context_processors'].append(  # noqa
    'meaningfulconsent.main.views.context_processor'
)

MIDDLEWARE += [  # noqa
    'django.middleware.csrf.CsrfViewMiddleware',
    'meaningfulconsent.main.middleware.HttpResponseNotAllowedMiddleware'
]

INSTALLED_APPS += [  # noqa
    'bootstrap3',
    'typogrify',
    'bootstrapform',
    'django_extensions',
    'pagetree',
    'pageblocks',
    'quizblock',
    'meaningfulconsent.main',
    'rest_framework',
]

PAGEBLOCKS = [
    'pageblocks.TextBlock',
    'pageblocks.HTMLBlock',
    'quizblock.Quiz',
    'main.QuizSummaryBlock',
    'main.SimpleImageBlock',
    'main.YouTubeBlock']

THUMBNAIL_SUBDIR = "thumbs"

PARTICIPANT_SECRET = "something secret"  # nosec, changed in staging/prod

AUTHENTICATION_BACKENDS += [
    'meaningfulconsent.main.auth.ParticipantBackend'
]

REST_FRAMEWORK = {
    'DEFAULT_PERMISSION_CLASSES': (
        'meaningfulconsent.main.mixins.FacilitatorRestPermission',),
    'DEFAULT_PAGINATION_CLASS':
        'rest_framework.pagination.LimitOffsetPagination',
    'PAGE_SIZE': 20,
    'PAGE_SIZE_QUERY_PARAM': 'page_size',
}

LOCALE_PATHS = (
    'locale',
)

MEDIA_ROOT = 'uploads'
