


#xgettext -i */*.py -i -klang -o locale/messages.pot --from-code=UTF-8 --copyright-holder="LANCMS and it's creators" --package-name='LANCMS' --msgid-bugs-address='bugs.launchpad.net' --package-version='2.0-alpha'

#./manage.py makemessages --all -e html -e py -l en-us
./manage.py makemessages -l en_US -d django -s
cp locale/en_US/LC_MESSAGES/django.po locale/django.pot
cp -u locale/nb.po locale/nb_NO/LC_MESSAGES/django.po
./manage.py compilemessages
