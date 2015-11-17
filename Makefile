MANAGE=./manage.py
APP=meaningfulconsent
FLAKE8=./ve/bin/flake8

jenkins: ./ve/bin/python check test flake8 jshint

./ve/bin/python: requirements.txt bootstrap.py virtualenv.py
	chmod +x manage.py bootstrap.py
	./bootstrap.py

jshint: node_modules/jshint/bin/jshint
	./node_modules/jshint/bin/jshint media/js/app/

jscs: node_modules/jscs/bin/jscs
	./node_modules/jscs/bin/jscs media/js/app/

node_modules/jshint/bin/jshint:
	npm install jshint --prefix .

node_modules/jscs/bin/jscs:
	npm install jscs --prefix .

test: ./ve/bin/python
	$(MANAGE) jenkins --pep8-exclude=migrations --enable-coverage --coverage-rcfile=.coveragerc

flake8: ./ve/bin/python
	$(FLAKE8) $(APP) --max-complexity=12

runserver: ./ve/bin/python check
	$(MANAGE) runserver

migrate: ./ve/bin/python check jenkins
	$(MANAGE) migrate

check: ./ve/bin/python
	$(MANAGE) check

shell: ./ve/bin/python
	$(MANAGE) shell_plus

clean:
	rm -rf ve
	rm -rf media/CACHE
	rm -rf reports
	rm celerybeat-schedule
	rm .coverage
	find . -name '*.pyc' -exec rm {} \;

pull:
	git pull
	make check
	make test
	make migrate
	make flake8

rebase:
	git pull --rebase
	make check
	make test
	make migrate
	make flake8

syncdb: ./ve/bin/python
	$(MANAGE) syncdb

collectstatic: ./ve/bin/python check
	$(MANAGE) collectstatic --noinput --settings=$(APP).settings_production

makemessages: ./ve/bin/python
	$(MANAGE) makemessages -l es --ignore="ve" --ignore="login.html" --ignore="password*.html"

compilemessages: ./ve/bin/python
	$(MANAGE) compilemessages

# run this one the very first time you check
# this out on a new machine to set up dev
# database, etc. You probably *DON'T* want
# to run it after that, though.
install: ./ve/bin/python check jenkins
	createdb $(APP)
	$(MANAGE) syncdb --noinput
	make migrate
