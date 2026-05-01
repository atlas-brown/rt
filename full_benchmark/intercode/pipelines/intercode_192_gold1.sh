# Query: Search for all the files in /testbed directory and its subdirectories that contain the word 'Hello' and replace it with 'Hi' in-place.

grep -rl "Hello" /testbed | xargs sed -i 's/Hello/Hi/g'