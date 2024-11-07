#!/bin/bash

    # NOTE: This script assumes Ansible is being executed where the environment
    # variables needed for Boto have already been set:

    # export AWS_ACCESS_KEY_ID='AK123'
    # export AWS_SECRET_ACCESS_KEY='abc123'

    # This script also assumes there is an ec2.ini file alongside it.  To specify a
    # different path to ec2.ini, define the EC2_INI_PATH environment variable:

    export EC2_URL=https://ec2.us-west-1.amazonaws.com
    export EC2_INI_PATH=/usr/local/bin/ec2.ini

    instances=`/usr/local/bin/ec2inventory | jq -r "to_entries|map(\"\(.key)=\(.value|tostring)\")|.[]" | grep -A 1 tag_Name_ | sed -e 's/--//g' -e 's/"//g' -e 's/tag_Name_//g' -e 's/\[//;s/]//g'`

    echo > ~/.ssh/config

    for i in $instances; do
      instanceName=$(echo $i | cut -f1 -d=)
      ipAddress=$(echo $i | cut -f2 -d=)

      echo "Host $instanceName" >> ~/.ssh/config
      echo "    HostName $ipAddress" >> ~/.ssh/config
      echo "    User ec2-user" >> ~/.ssh/config
    done
