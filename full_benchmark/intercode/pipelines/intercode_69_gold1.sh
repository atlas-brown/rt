# Query: Print the last five lines of /system/folder1/data.csv

cat /system/folder1/data.csv | rev | cut -d, -f-5 | rev