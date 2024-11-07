#!/bin/bash
DOCKER_PS=`docker ps -a |awk '{print$1}'`
DOCKER_IMAGES=`docker images |awk '{print$3}'`

#To stop and delete all containers
for cont in $DOCKER_PS;
do
docker stop $cont
docker rm -f $cont
done

#Delete all images
for im in $DOCKER_IMAGES;
do
docker rmi -f $im
done

function MIX() {

#To stop and delete all containers
for cont in $(docker ps -a |awk '{print$1}');
do
docker stop $cont
docker rm -f $cont
done

#Delete all images
for im in $(docker images |awk '{print$3}');
do
docker rmi -f $im
done

#Web content location in the container for HTTPD, NGINX AND TOMCAT
HTTPD: /usr/local/apache2/htdocs/
NGINX: /usr/share/nginx/html/
TOMCAT: /usr/local/tomcat/webapps/


# docker system prune --all


COPY index1.html /usr/share/nginx/html
COPY index2.html /usr/local/apache2/htdocs
COPY ./pebble.war /usr/local/tomcat/webapps


How To Open A Port In CentOS / RHEL 6?
$ vim /etc/sysconfig/iptables
-A INPUT -m state --state NEW -m tcp -p tcp --dport 22 -j ACCEPT
$ sudo iptables restart


How To Open A Port In Ubuntu?
syntax:
ufw allow port-number/protocol
example:
$ sudo ufw allow 8080/tcp
$ sudo ufw allow 80/tcp
Ubuntu reload / restart iptables service command
$ sudo ufw reload

How To Open A Port In CentOS / RHEL 7 through CLI?
$ sudo firewall-cmd --zone=public --add-port=80/tcp --permanent
$ sudo firewall-cmd --reload


#!/bin/bash
## How to install iptable on CentOS / RHEL 7?
systemctl stop firewalld
systemctl disable firewalld
systemctl mask --now firewalld
yum -y install iptables-services
systemctl start iptables


#!/bin/bash
sudo -i 
yum -y install httpd
systemctl enable httpd
systemctl restart httpd
 
yum install git -y
cd /var/www/html
git clone https://leonardtia57@bitbucket.org/leonardtia57/covid19.git
cp -r covid19/* .
rm -rf covid19




#!/bin/bash
sudo -i 
yum -y install httpd
systemctl enable httpd
systemctl restart httpd
 
yum install git -y
cd /var/www/html
git clone https://leonardtia57@bitbucket.org/leonardtia57/qentelli.com.git
cp -r qentelli.com/* .
rm -rf qentelli.com


