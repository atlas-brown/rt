#!/bin/sh
case "$1" in
  start) start_service ;;
  stop)  stop_service ;;
  restart|reload|force-reload)
    stop_service;
    start_service;;
esac