#!/bin/bash

echo "war pre_migrate"

curl "http://tomcat:tomcat@localhost:8080/manager/text/undeploy?path=/testWS"

# remove files
# TODO