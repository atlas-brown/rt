#!/usr/bin/env bash
# brings up the monitoring stock
stack=( prometheusdev grafanadev alertmanagerdev )


function tryresume () {
  # check if it's running already
  running=$(docker inspect -f '{{.State.Running}}' "$1" 2>&1)
  [ "$running" == "true" ] && echo "  - ${1} already running" && return 0

  # try to resume
  exit_code=$(docker inspect -f '{{.State.ExitCode}}' "$1" 2>&1)
  [ "$running" == "false" ] && [ $exit_code -eq 0 ] && printf "  - resuming ${1}... " && $(docker start $1 >/dev/null 2>&1) && echo "OK" && return 0

  #else
  return 1
}

function trystart () {
  case "$1" in
    prometheusdev)
      printf "  - starting prometheus... "
      prom_cmd="docker run -d --name prometheusdev --network promstack -p 9090:9090 -v $(pwd)/configs/prometheus:/etc/prometheus prometheusdev"
      $prom_cmd >/dev/null 2>&1 && echo "OK" && return 0
      # failed.. run the command again so they can see the issue
      echo FAIL
      echo "    try removing any existing failed prometheusdev containers (ie.. \`docker ps -a\` && \`docker rm <containername>\`)"
      return 1
    ;;
    grafanadev)
      printf "  - starting grafana... "
      graf_cmd="docker run -d --name grafanadev --network promstack -p 3000:3000 --env-file $(pwd)/docker/grafana/grafana.env -v $(pwd)/configs/grafana:/etc/grafana grafanadev"
      $graf_cmd >/dev/null 2>&1 && echo "OK" && return 0
      # failed.. run the command again so they can see the issue
      echo FAIL
      echo "    try removing any existing failed grafanadev containers (ie.. \`docker ps -a\` && \`docker rm <containername>\`)"
      return 1
    ;;
    alertmanagerdev)
      printf "  - starting alertmanager... " && echo OK
      am_cmd="docker run -d --name alertmanagerdev --network promstack -p 9093:9093 -v $(pwd)/configs/alertmanager:/etc/alertmanager alertmanagerdev"
      $am_cmd >/dev/null 2>&1 && echo "OK" && return 0
      # failed.. run the command again so they can see the issue
      echo FAIL
      echo "    try removing any existing failed alertmanagerdev containers (ie.. \`docker ps -a\` && \`docker rm <containername>\`)"
      return 1
    ;;
  esac
}

# is docker running?
docker info >/dev/null 2>&1
[ $? -ne 0 ] && echo "Error launching stack.. is Docker running?" && exit 1

# network exist?
docker network create promstack >/dev/null 2>&1
[ $? -ne 0 ] && docker network create promstack >/dev/null 2>&1

echo "Bringing up the stack:"
for i in "${stack[@]}"; do
  # first try to start/resume stopped containers
  tryresume $i || trystart $i
done

# test to ensure each container is running
for i in "${stack[@]}"; do
  running=$(docker inspect -f '{{.State.Running}}' "$i" 2>&1)
  [ "$running" != "true" ] && echo "Failed to start $i" && exit 1
done
# pause for a second or two to allow grafana to come up (else they will get a 404)
sleep 2

# else all is well, display links
echo
echo "Links:"
echo "  grafana      => http://localhost:3000 user 'admin' password 'grafana'"
echo "  prometheus   => http://localhost:9090"
echo "  alertmanager => http://localhost:9093"  
