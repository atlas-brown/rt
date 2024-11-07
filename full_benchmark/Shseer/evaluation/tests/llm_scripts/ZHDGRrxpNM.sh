
#!/bin/bash

# List all running processes and their IDs
ps

# Prompt the user to enter the process ID to terminate
read -p "Enter the process ID to terminate: " process_id

# Use the kill command to terminate the specific process
kill $process_id
