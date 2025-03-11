#!/bin/bash
# https://stackoverflow.com/questions/50609285/issues-while-redirecting-output-to-file

# ---
# tags:   buggy, unclear
# intent: send an email when free memory drops below 500mb
# bug:    when scheduled with 'cron', part of the expected output is missing (not sure why)
# ---

# too many unimplemented commands (ifconfig, free, ps, mailx)

ip=`ifconfig | grep -oP '(?<=inet addr:)\d+\.\d+\.\d+\d+'`

free=$(free -mt | grep Total | awk '{print $4}')

if [[ "$free" -le 500 ]]; then
    ps -eo pid,ppid,cmd,%mem,%cpu --sort=-%mem | head > /home/utilization.txt

   echo -e "******************************************************************" >> /home/utilization.txt
   echo -e "******************************************************************\n" >> /home/utilization.txt
   echo -e  "Current active Process and open files\n" >> /home/utilization.txt

   ps -A -opid | sudo xargs -n1 -I{} /bin/bash -c 'echo {} $(ls /proc/{}/fd | wc -l);' >> /home/utilization.txt

   file=/home/utilization.txt

   echo -e "memory is running low on $ip Available memory: $free MB" | mailx -a "$file" -s "Check memory Status" myemail@gmail.com
fi
exit 0
