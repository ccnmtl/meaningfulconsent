# flake8: noqa
from settings_shared import *
from ccnmtlsettings.production import common

locals().update(
    common(
        project=project,
        base=base,
        INSTALLED_APPS=INSTALLED_APPS,
        STATIC_ROOT=STATIC_ROOT,
    ))

LOCALE_PATHS = ('/var/www/meaningfulconsent/meaningfulconsent/locale',)

try:
    from meaningfulconsent.local_settings import *
except ImportError:
    pass
