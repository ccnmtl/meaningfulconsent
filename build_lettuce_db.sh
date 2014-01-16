#!/bin/bash
rm -f lettuce.db
./manage.py syncdb --migrate --noinput --settings=pipseq.settings_lettuce
mv lettuce.db test_data/test.db
