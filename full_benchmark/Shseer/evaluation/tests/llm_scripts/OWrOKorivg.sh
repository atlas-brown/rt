
#!/bin/bash

# Check if the correct number of arguments are provided
if [ $# -ne 1 ]; then
  echo "Usage: $0 <output_file>"
  exit 1
fi

# Gather system information
hostname=$(hostname)
kernel_version=$(uname -r)
cpu_info=$(lscpu)
memory_info=$(free -h)
disk_info=$(df -h)

# Format the data
report="System Information Report\n\n"
report+="Hostname: $hostname\n"
report+="Kernel Version: $kernel_version\n\n"
report+="CPU Information:\n$cpu_info\n\n"
report+="Memory Information:\n$memory_info\n\n"
report+="Disk Information:\n$disk_info\n"

# Output the data to a file
echo -e "$report" > $1

# Send the data to a remote server (example)
# Replace <remote_server> with the actual remote server address
# Replace <username> with the actual username
# Replace <password> with the actual password
# scp $1 <username>@<remote_server>:<password>/path/to/save/report

echo "System information report generated and saved to $1"
