python setup.py egg_info --tag-date --tag-build=.build bdist_egg --exclude-source-files
cd dist
wheel convert *.egg
cd ..

