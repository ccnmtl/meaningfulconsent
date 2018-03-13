# flake8: noqa
from meaningfulconsent.settings_shared import *

try:
    from meaningfulconsent.local_settings import *
except ImportError:
    pass
