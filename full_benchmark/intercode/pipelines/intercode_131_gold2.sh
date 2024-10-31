# Query: Make directories for each unique file path in "/workspace/files.txt"

cat /workspace/files.txt | xargs -I {} dirname {}| sort -u | xargs -I{} mkdir -p "{}"