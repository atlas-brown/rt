# Query: Count the number of regular files in directory tree ${DIRECTORY} that contain a vowel in their names

find ${DIRECTORY} -type f -print | sed -e 's@^.*/@@' | grep '[aeiouyAEIOUY]' | wc -l