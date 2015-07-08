# flake8: noqa
from settings_shared import *

try:
    from meaningfulconsent.local_settings import *
except ImportError:
    pass
