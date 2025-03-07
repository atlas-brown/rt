#!/bin/sh
# https://stackoverflow.com/questions/49626693/shell-script-executes-fail

# ---
# tags:   buggy, line_annot, stream_annot, awk
# intent: kill a process called 'celery' by grepping 'ps' and then restart it,
#         while  avoid killing the 'grep' process itself
# bug:    'grep -v grep' receives numeric input (pids)
# ---

# stream enable
# @assert "awk '{print $2}'" --> "([0-9]+)?"
# @assert "awk '{print $2}'" --> "(([0-9]+)\n)*"
# @assume "ps -ef" --> "[^ \t]+ +(PID|[0-9]+) +.*"
ps -ef | grep celery | awk '{print $2}' | grep -v grep | xargs kill -9;
celery -A loan_app.tasks worker --loglevel=info  --workdir=`pwd` --logfile=/tmp/celery.log --pidfile=/var/run/celery_pid -D
