# flake8: noqa
from settings_shared import *

TEMPLATE_DIRS = (
    "/var/www/meaningfulconsent/meaningfulconsent/meaningfulconsent/templates",
)

MEDIA_ROOT = '/var/www/meaningfulconsent/uploads/'
# put any static media here to override app served static media
STATICMEDIA_MOUNTS = (
    ('/sitemedia', '/var/www/meaningfulconsent/meaningfulconsent/sitemedia'),
)

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql_psycopg2',
        'NAME': 'meaningfulconsent',
        'HOST': '',
        'PORT': 6432,
        'USER': '',
        'PASSWORD': '',
    }
}

COMPRESS_ROOT = "/var/www/meaningfulconsent/meaningfulconsent/media/"
DEBUG = False
TEMPLATE_DEBUG = DEBUG
STAGING_ENV = True

STATSD_CLIENT = 'statsd.client'
STATSD_PREFIX = 'meaningfulconsent'
STATSD_HOST = '127.0.0.1'
STATSD_PORT = 8125
STATSD_PATCHES = ['django_statsd.patches.db', ]

STATICFILES_DIRS = ()
STATIC_ROOT = "/var/www/meaningfulconsent/meaningfulconsent/media/"

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
