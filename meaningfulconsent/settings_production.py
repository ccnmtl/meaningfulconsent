# flake8: noqa
from settings_shared import *

TEMPLATE_DIRS = (
    os.path.join(os.path.dirname(__file__), "templates"),
)

MEDIA_ROOT = '/var/www/meaningfulconsent/uploads/'

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

DEBUG = False
TEMPLATE_DEBUG = DEBUG
STAGING_ENV = False

STATSD_CLIENT = 'statsd.client'
STATSD_PREFIX = 'meaningfulconsent'
STATSD_HOST = '127.0.0.1'
STATSD_PORT = 8125
STATSD_PATCHES = ['django_statsd.patches.db', ]

if 'migrate' not in sys.argv:
    INSTALLED_APPS.append('raven.contrib.django.raven_compat')

    MIDDLEWARE_CLASSES.append(
        'django_statsd.middleware.GraphiteRequestTimingMiddleware')
    MIDDLEWARE_CLASSES.append(
        'django_statsd.middleware.GraphiteMiddleware')

LOCALE_PATHS = ('/var/www/meaningfulconsent/meaningfulconsent/locale',)

STATICFILES_DIRS = ("media/",)
STATIC_ROOT = "/tmp/meaningfulconsent/static"
AWS_STORAGE_BUCKET_NAME = "ccnmtl-meaningfulconsent-static-prod"
AWS_PRELOAD_METADATA = True
DEFAULT_FILE_STORAGE = 'storages.backends.s3boto.S3BotoStorage'
STATICFILES_STORAGE = 'cacheds3storage.CompressorS3BotoStorage'
S3_URL = 'https://%s.s3.amazonaws.com/' % AWS_STORAGE_BUCKET_NAME
STATIC_URL = 'https://%s.s3.amazonaws.com/media/' % AWS_STORAGE_BUCKET_NAME
COMPRESS_ENABLED = True
COMPRESS_OFFLINE = True
COMPRESS_ROOT = STATIC_ROOT
COMPRESS_URL = STATIC_URL
DEFAULT_FILE_STORAGE = 'cacheds3storage.MediaRootS3BotoStorage'
MEDIA_URL = S3_URL + '/media/'
COMPRESS_STORAGE = 'cacheds3storage.CompressorS3BotoStorage'
AWS_QUERYSTRING_AUTH = False

try:
    from local_settings import *
except ImportError:
    pass
