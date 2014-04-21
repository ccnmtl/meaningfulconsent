# flake8: noqa
from settings_shared import *

TEMPLATE_DIRS = (
    "/var/www/pipseq/pipseq/pipseq/templates",
)

MEDIA_ROOT = '/var/www/pipseq/uploads/'
# put any static media here to override app served static media
STATICMEDIA_MOUNTS = (
    ('/sitemedia', '/var/www/pipseq/pipseq/sitemedia'),
)

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql_psycopg2',
        'NAME': 'pipseq',
        'HOST': '',
        'PORT': 6432,
        'USER': '',
        'PASSWORD': '',
    }
}

COMPRESS_ROOT = "/var/www/pipseq/pipseq/media/"
DEBUG = False
TEMPLATE_DEBUG = DEBUG

STATSD_CLIENT = 'statsd.client'
STATSD_PREFIX = 'pipseq'
STATSD_HOST = '127.0.0.1'
STATSD_PORT = 8125
STATSD_PATCHES = ['django_statsd.patches.db', ]


if 'migrate' not in sys.argv:
    INSTALLED_APPS.append('raven.contrib.django.raven_compat')

    MIDDLEWARE_CLASSES.append(
        'django_statsd.middleware.GraphiteRequestTimingMiddleware')
    MIDDLEWARE_CLASSES.append(
        'django_statsd.middleware.GraphiteMiddleware')

try:
    from local_settings import *
except ImportError:
    pass
