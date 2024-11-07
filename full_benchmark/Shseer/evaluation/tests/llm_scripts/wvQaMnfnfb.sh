
#!/bin/sh

# Create a command that produces both stdout and stderr output
echo "This is a normal message" 
echo "This is an error message" >&2

# Redirect stdout to a file
echo "Redirecting stdout to file..."
echo "This is a normal message" > stdout.txt

# Redirect stderr to a file
echo "Redirecting stderr to file..."
echo "This is an error message" 2> stderr.txt
