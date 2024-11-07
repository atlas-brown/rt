
#!/bin/sh

# Set the process name and threshold values
process_name="example_process"
cpu_threshold=80
memory_threshold=80

# Monitor the system for the specific process
while true
do
    # Get the process ID of the specific process
    pid=$(pgrep $process_name)

    # Check if the process exists
    if [ -n "$pid" ]
    then
        # Get the CPU and memory usage of the process
        cpu_usage=$(ps -p $pid -o %cpu | awk 'NR>1')
        memory_usage=$(ps -p $pid -o %mem | awk 'NR>1')

        # Check if the CPU or memory usage exceeds the threshold
        if [ $(echo "$cpu_usage > $cpu_threshold" | bc) -eq 1 ] || [ $(echo "$memory_usage > $memory_threshold" | bc) -eq 1 ]
        then
            # Log the details of the terminated process
            echo "Terminating process $process_name with PID $pid - CPU: $cpu_usage%, Memory: $memory_usage%"

            # Terminate the process
            kill $pid
        fi
    fi

    # Sleep for 1 second before checking again
    sleep 1
done
