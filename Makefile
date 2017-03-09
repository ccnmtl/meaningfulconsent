MANAGE=./manage.py
APP=meaningfulconsent
JS_FILES=media/js/app/
MAX_COMPLEXITY=6

all: jenkins

include *.mk

makemessages: ./ve/bin/python
	$(MANAGE) makemessages -l es --ignore="ve" --ignore="login.html" --ignore="password*.html"

compilemessages: ./ve/bin/python
	$(MANAGE) compilemessages

eslint: $(JS_SENTINAL)
	$(NODE_MODULES)/.bin/eslint $(JS_FILES)

.PHONY: eslint
