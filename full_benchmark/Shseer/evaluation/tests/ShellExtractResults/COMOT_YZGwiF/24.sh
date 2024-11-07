#!/bin/bash

#if comot deployed remotely, please change the IP below to one publicly accessible (e.g., floating IP)
#HOST_IP=10.0.0.1
HOST_IP=localhost

echo ""
echo "#############################################################"
echo "" 
echo 'Is COMOT deployed in an isolated machine/container? (i.e. not on "localhost")  Please select 1(No), 2(Yes), 3(Quit)'
options=("No" "Yes" "Quit")
select opt in "${options[@]}"
do
    case $opt in
         "${options[0]}")
            echo "Setting COMOT dashboard IP to $HOST_IP"
            break
            ;;
         "${options[1]}")
            if [[ -z $1 ]]
            then 
                echo "Please enter a PUBLICLY ACCESSIBLE IP for this machine/container to setup COMOT Dashboard accordingly"
                read inputIP
                HOST_IP=$(echo $inputIP | tr -d ' ') 
                echo "Setting COMOT dashboard IP to $HOST_IP"
            else
                echo "Detected argument $1. Will use for HOST_IP" 
                HOST_IP=$1 
                echo "Setting COMOT dashboard IP to $HOST_IP"
            fi 
            break
            ;;
        "${options[2]}")
            exit
            ;;
        *) echo invalid option;;
    esac
done
 

echo ""
echo "#############################################################"
echo ""


CURRENT_DIR=$(pwd)


wget http://128.130.172.215/repository/files/Misc/WorkloadGeneration.tar.gz
tar -xzf ./WorkloadGeneration.tar.gz
rm  ./WorkloadGeneration.tar.gz

echo "Downloading jre"
wget  http://128.130.172.215/repository/files/Misc/jre-7-linux-x64.tar.gz
echo "Unpacking JRE"
tar -xzf ./jre-7-linux-x64.tar.gz
rm  ./jre-7-linux-x64.tar.gz

JAVA=$CURRENT_DIR/jre1.7.0/bin/java

echo "Deploying COMOT"
echo "Downloading COMOT"
wget  http://128.130.172.215/repository/files/COMOTCompactPlatform/COMOT-Platform.tar.gz
echo "Unpacking COMOT"
tar -xzf ./COMOT-Platform.tar.gz
rm  ./COMOT-Platform.tar.gz
 
eval "sed -i 's#DAEMONDIR=.*#DAEMONDIR=$CURRENT_DIR/COMOT-Platform/#' $CURRENT_DIR/COMOT-Platform/comot-platform"
eval "sed -i 's#JAVA_HOME=.*#JAVA_HOME=$CURRENT_DIR/jre1.7.0/#' $CURRENT_DIR/COMOT-Platform/comot-platform"
LOCAL_IP=$(ifconfig eth0 | grep "inet addr" | awk -F: '{print $2}' | awk '{print $1}')
eval "sed -i 's#SALSA_CENTER_ENDPOINT_LOCAL=.*#SALSA_CENTER_ENDPOINT_LOCAL=http://$LOCAL_IP:8080/salsa-engine#' $CURRENT_DIR/COMOT-Platform/salsa.engine.properties"
eval "sed -i 's#SALSA_CENTER_ENDPOINT=.*#SALSA_CENTER_ENDPOINT=http://$LOCAL_IP:8080/salsa-engine#' $CURRENT_DIR/COMOT-Platform/salsa.engine.properties"
eval "sed -i 's#PIONEER_WEB=.*#PIONEER_WEB=http://$LOCAL_IP:8080/salsa-engine/rest/artifacts/pioneer#' $CURRENT_DIR/COMOT-Platform/salsa.engine.properties"

eval "sed -i 's#WORKING_DIR=.*#WORKING_DIR=$CURRENT_DIR/salsa-pioneer#' $CURRENT_DIR/COMOT-Platform/salsa.engine.properties"
eval "sed -i 's#SERVICE_STORAGE=.*#SERVICE_STORAGE=$CURRENT_DIR/salsa-engine/services#' $CURRENT_DIR/COMOT-Platform/salsa.engine.properties"
eval "sed -i 's#ARTIFACT_STORAGE=.*#ARTIFACT_STORAGE=$CURRENT_DIR/salsa-engine/artifacts#' $CURRENT_DIR/COMOT-Platform/salsa.engine.properties"
eval "sed -i 's#TOSCA_TEMPLATE_STORAGE=.*#TOSCA_TEMPLATE_STORAGE=$CURRENT_DIR/salsa-engine/tosca_templates#' $CURRENT_DIR/COMOT-Platform/salsa.engine.properties"
 
mkdir $CURRENT_DIR/salsa-engine/
mkdir $CURRENT_DIR/salsa-engine/services
mkdir $CURRENT_DIR/salsa-engine/artifacts
mkdir $CURRENT_DIR/salsa-engine/tosca_templates
 
echo "Checking if Ganglia exists"

if [[ -z $(which ganglia) ]]
  then
    echo "Installing Ganglia"
    sudo -S apt-get install ganglia-monitor gmetad -y
fi

echo "Configuring Ganglia"
wget  http://128.130.172.215/repository/files/Misc/GangliaCFG.tar.gz
tar -xzf ./GangliaCFG.tar.gz
rm ./GangliaCFG.tar.gz
sudo -S cp ./GangliaCFG/gmond.conf /etc/ganglia

sudo -S ifconfig lo:0 192.1.1.15

sudo -S service ganglia-monitor restart

echo "Configuring Docker"

if [[ -z $(which docker) ]]
  then
	sudo -S apt-key adv --keyserver hkp://keyserver.ubuntu.com:80 --recv-keys 36A1D7869245C8950F966E92D8576A8BA88D21E9
	sudo -S sh -c "echo deb http://get.docker.io/ubuntu docker main > /etc/apt/sources.list.d/docker.list"
	sudo -S apt-get -q update
	sudo -S apt-get -q -y install linux-image-extra-`uname -r` lxc-docker
fi

#update docker base image
sudo -S docker pull leduchung/salsa

eval "sed -i 's#HOST_IP#$HOST_IP#' $CURRENT_DIR/COMOT-Platform/config/modules.xml"
eval "sed -i 's#8080/rSYBL/#8280/rSYBL/#' $CURRENT_DIR/COMOT-Platform/config/modules.xml"
 
sudo -S chmod +x ./COMOT-Platform/comot-platform
sudo -S cp ./COMOT-Platform/comot-platform /etc/init.d/comot-platform
sudo -S chmod +x /etc/init.d/comot-platform
sudo -S update-rc.d comot-platform defaults

sudo -S service comot-platform start 


cd ./COMOT-Platform
CURRENT_DIR=$(pwd)

wget  http://128.130.172.215/repository/files/COMOTCompactPlatform/rSYBL.tar.gz
tar -xzf ./rSYBL.tar.gz
rm ./rSYBL.tar.gz

eval "sed -i 's#JAVA=.*#JAVA=$JAVA#' $CURRENT_DIR/rSYBL/rSYBL-service"
eval "sed -i 's#DAEMONDIR=.*#DAEMONDIR=$CURRENT_DIR/rSYBL#' $CURRENT_DIR/rSYBL/rSYBL-service"

sudo -S cp ./rSYBL/rSYBL-service /etc/init.d/rSYBL-service
sudo -S chmod +x /etc/init.d/rSYBL-service
sudo -S update-rc.d rSYBL-service defaults

sudo -S service rSYBL-service start

sleep 5
echo "Waiting for COMOT Dashboard to start "
#check that MELA Data Service started
curl -X GET http://localhost:8080/MELA-DataService/REST_WS/elasticservices 2>/dev/null >> /tmp/comot_deployment_status
#check that MELA Analysis Service started
curl -X GET http://localhost:8080/MELA-AnalysisService/REST_WS/elasticservices 2>/dev/null  >> /tmp/comot_deployment_status
#check that SALSA started
curl -X GET http://localhost:8080/salsa-engine/rest/viewgenerator/cloudservice/json/list 2>/dev/null  >> /tmp/comot_deployment_status
#check that rSYBL started
curl -X GET http://localhost:8080/COMOT 2>/dev/null  >> /tmp/comot_deployment_status
curl -X GET http://localhost:8280/rSYBL/restWS/elasticservices 2>/dev/null  >> /tmp/comot_deployment_status

echo "COMOT deployed. Please access COMOT Dashboard at http://$HOST_IP:8080/COMOT" 

