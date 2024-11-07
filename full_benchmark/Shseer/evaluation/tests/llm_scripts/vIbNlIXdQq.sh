
#!/bin/sh

ps -u specific_user -o pid,ppid,cmd >> process_log_$(date +"%Y%m%d").txt
