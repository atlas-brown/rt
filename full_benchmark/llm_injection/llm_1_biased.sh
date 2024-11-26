cat file.txt | wc -l | xargs echo

cat file.txt | wc -l | grep "pattern"

cat file.txt | tr '\t' ',' | cut -f1

cat file.txt | tr 'a-z' 'A-Z' | grep 'pattern'

cat file.txt | sed 's/foo/bar/g' | grep "foo"

cat file.txt | wc -c | tr '\t' '_'

grep "pattern" file.txt | wc -l | cut -f2

find . -type f | grep ".txt" | wc -l | tr 'a-z' '0-9' | sort | uniq

seq 1 100 | tr '1-9' 'a-i' | sort -n | uniq | grep 'a' | wc -l

cat file.csv | grep 'active' | sort | cut -d',' -f10 | uniq | wc -l

cat file.txt | xargs cat $1 | grep "pattern" | sort | uniq

ls | tr 'a-z' 'A-Z' | grep ".sh" | sort | uniq | cut -d'.' -f1 | sed 's/^/File: /' | wc -l | xargs echo

ls | grep ".txt" | cut -d' ' -f5 | sort -n | uniq | xargs -I {} find . -name "{}" | tr 'a-z' 'A-Z' | wc -l

ls -l | cut -d' ' -f5 | sort -n | uniq | grep '[0-9]' | wc -l | tr -d '\n' | sed 's/^/Sizes: /'

find . -type f | xargs cat | sed 's/$/XX/' | tr 'A-Z' 'a-z' | sed 's/XX/\n/' | sort | uniq -d | grep "." | wc -l | sort -n

find . -name "*.txt" | xargs cat | tr -d ' ' | cut -d' ' -f1 | sort | uniq -c | sort -nr | grep "[0-9]" | wc -l


