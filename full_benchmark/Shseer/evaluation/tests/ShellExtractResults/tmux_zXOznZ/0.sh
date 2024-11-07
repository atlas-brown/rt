#!/bin/sh

STATUSLINE_LOCK="${HOME}/.tmux.statusline.pid"
STATUSLINE="$(dirname $0)/tmux_statusline.py"
STDERR="/tmp/tmux.statusline.stderr"
STDOUT="/tmp/tmux.statusline.stdout"

if [ ! -r ${STATUSLINE_LOCK} ]; then
  ${STATUSLINE} >${STDOUT} 2>${STDERR} &
else
  pid=$(cat ${STATUSLINE_LOCK})
  ps -p ${pid} | grep -qi python
  if [ $? != 0 ]; then
    ${STATUSLINE} >${STDOUT} 2>${STDERR} &
  fi
  nc 127.0.0.1 61234
fi
