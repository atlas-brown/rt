
#!/bin/sh

# List of services to check
services=("service1" "service2" "service3")

# Print table header
printf "%-20s %-10s\n" "Service" "Status"
printf "---------------------------------\n"

# Loop through the list of services
for service in "${services[@]}"
do
    # Check the status of the service
    status=$(systemctl is-active $service)

    # Print the service and its status in the table
    printf "%-20s %-10s\n" "$service" "$status"
done
