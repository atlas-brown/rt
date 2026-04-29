# Query: Display a long listing of the oldest file under '/workspace' directory tree

# @assume "find /workspace -type f -exec stat --format '%Y %n' {} \;" --> "([0-9]+ [^\n]+\n)+"
# @assume "head -n 1" --> "[0-9]+ [^\n]+"
# @expect "[0-9]+ [^\n]+" --> "cut -d' ' -f2-"
find /workspace -type f -exec stat --format '%Y %n' {} \; | sort -n | head -n 1 | cut -d' ' -f2- | xargs ls -l
