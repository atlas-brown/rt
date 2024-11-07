#!/usr/bin/env bash
##  @copyright 2018 DennyZhang.com
## Licensed under MIT 
##   https://www.dennyzhang.com/wp-content/mit_license.txt
##
## File: delete_all_containers.sh
## Author : Denny <https://www.dennyzhang.com/contact>
## Description : https://cheatsheet.dennyzhang.com/cheatsheet-docker-A4
## --
## Created : <2018-07-10>
## Updated: Time-stamp: <2018-11-23 21:39:06>
##-------------------------------------------------------------------
# curl -L https://raw.githubusercontent.com/dennyzhang/cheatsheet-docker-A4/master/delete-all-containers.sh | bash
set -e
echo "Before deleting containers"
docker ps -a
docker ps -aq | xargs docker stop
docker ps -aq | xargs docker rm

echo "After deleting containers"
docker ps -a
## File: delete_all_containers.sh ends
