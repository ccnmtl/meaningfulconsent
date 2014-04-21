import os, sys, site

# enable the virtualenv
site.addsitedir('/var/www/meaningfulconsent/meaningfulconsent/ve/lib/python2.7/site-packages')

# paths we might need to pick up the project's settings
sys.path.append('/var/www/meaningfulconsent/meaningfulconsent/')

os.environ['DJANGO_SETTINGS_MODULE'] = 'meaningfulconsent.settings_staging'

import django.core.handlers.wsgi

application = django.core.handlers.wsgi.WSGIHandler()
