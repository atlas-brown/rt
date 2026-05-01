# Query: Print the last five lines of /system/folder1/data.csv

tail -n 1 /system/folder1/data.csv | rev | cut -d',' -f1-5 | rev