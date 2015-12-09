# flake8: noqa
from settings_shared import *
from ccnmtlsettings.staging import common

locals().update(
    common(
        project=project,
        base=base,
        STATIC_ROOT=STATIC_ROOT,
        INSTALLED_APPS=INSTALLED_APPS,
    ))

LOCALE_PATHS = ('/var/www/meaningfulconsent/meaningfulconsent/locale',)

try:
    from meaningfulconsent.local_settings import *
except ImportError:
    pass
