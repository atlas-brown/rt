
#!/bin/sh

services=("service1" "service2" "service3")

echo "Service Status"
echo "--------------"
for service in "${services[@]}"
do
    status=$(service $service status)
    echo "$service | $status"
done
