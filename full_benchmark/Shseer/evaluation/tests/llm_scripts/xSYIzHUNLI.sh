
if [ -f file1.txt ] && [ -f file2.txt ] && [ -f file3.txt ]; then
    cat file1.txt file2.txt file3.txt > combined.txt
fi
