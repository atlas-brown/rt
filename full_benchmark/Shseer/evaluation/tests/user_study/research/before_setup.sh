#!/bin/bash
secs=$((10))
Countdown() {
	tot=$(echo "scale=2; $secs/100" | bc)
	for i in $(seq 1 100)
	do
		sleep $tot
		echo $i
	done | whiptail --title "Setting up db$x" --gauge 'Running...' 6 60 0
}

install_docker() {
        sudo apt install -y docker.io
        sudo docker pull richarvey/nginx-php-fpm:latest
        sudo docker pull haproxy:latest
        sudo docker pull mariadb:10.4
        sudo docker pull mariadb/maxscale:latest
}

hosts_setup() {
        FILE=/etc/hosts.bak
        if [[ -f "$FILE" ]];
	then
        	sudo cp $FILE /etc/hosts
        else
		sudo cp /etc/hosts $FILE
        fi
        sudo /bin/sh -c 'echo 172.17.0.2 web1 >> /etc/hosts'
        sudo /bin/sh -c 'echo 172.17.0.3 web2 >> /etc/hosts'
        sudo /bin/sh -c 'echo 172.17.0.4 web3 >> /etc/hosts'
        sudo /bin/sh -c 'echo 172.17.0.5 haproxy >> /etc/hosts'
        sudo /bin/sh -c 'echo 172.17.0.6 dbgc1 >> /etc/hosts'
        sudo /bin/sh -c 'echo 172.17.0.7 dbgc2 >> /etc/hosts'
        sudo /bin/sh -c 'echo 172.17.0.8 dbgc3 >> /etc/hosts'
        sudo /bin/sh -c 'echo 172.17.0.9 maxscale >> /etc/hosts'
}

print_menu() {
	echo "1:Run all\n2:Install docker\n3:Setup hosts\n4:Setup Docker containers\n5:Clean all volumes - not included in Run all(1)."
}

clean_volumes() {
	sudo docker kill web1 web2 web3 lb db1 db2 db3 dbproxy
	sudo docker container rm web1 web2 web3 lb db1 db2 db3 dbproxy
	cd ~/
	sudo rm -rf volumes/
	sudo git clone 	https://github.com/Secretmud/volumes.git
	sudo mkdir -p volumes/db2/datadir/mysql
	sudo mkdir -p volumes/db3/datadir/mysql
		
}

setup_containers() {
	direc=$(pwd)
        for i in 1 2 3
        do
                sudo docker run --name web$i --hostname web$i  --add-host maxscale:172.17.0.9 -v ~/volumes/web$i/html/:/var/www/html -d richarvey/nginx-php-fpm
		sleep 1

        done

	sudo docker run -d --name lb -p 10.10.24.179:80:80 --add-host web1:172.17.0.2 --add-host web2:172.17.0.3 --add-host web3:172.17.0.4 --add-host maxscale:172.17.0.9 -v ~/volumes/lb:/usr/local/etc/haproxy:ro haproxy:latest
	echo "Web servers are set up. Setting up databases might take a while:"
	sudo docker run -d --name db1 --hostname dbgc1 \
 	-e MYSQL_ROOT_PASSWORD="rootpass" -e MYSQL_USER=maxscaleuser -e MYSQL_PASSWORD=maxscalepass -e MYSQL_USER=dats42 -e MYSQL_PASSWORD="stream doctor come" \
	-v ~/volumes/db1/datadir:/var/lib/mysql -v ~/volumes/db1/conf.d:/etc/mysql/mariadb.conf.d \
 	-v ~/volumes/db1/init.db/maxscaleuser.sql:/docker-entrypoint-initdb.d/maxscaleuser.sql:ro \
  	-v ~/volumes/db1/init.db/studentinfo.sql:/docker-entrypoint-initdb.d/studentinfo.sql:ro \
  	mariadb:10.4 

	echo "Setting up db1.."
       	secs=$((150))	
	x=$((1))
	Countdown
	sudo docker run -d --name db2 --hostname dbgc2 \
	  -e MYSQL_ROOT_PASSWORD="rootpass" \
	  -e MYSQL_USER=maxscaleuser \
	  -e MYSQL_PASSWORD=maxscalepass \
	  -v ~/volumes/db2/datadir:/var/lib/mysql \
	  -v ~/volumes/db2/conf.d:/etc/mysql/mariadb.conf.d \
	  mariadb:10.4

	echo "Setting up db2.."
       	secs=$((40))	
	x=$((2))
	Countdown
	sudo docker run -d --name db3 --hostname dbgc3 \
	  -e MYSQL_ROOT_PASSWORD="rootpass" \
	  -e MYSQL_USER=maxscaleuser \
	  -e MYSQL_PASSWORD=maxscalepass \
	  -v ~/volumes/db3/datadir:/var/lib/mysql \
	  -v ~/volumes/db3/conf.d:/etc/mysql/mariadb.conf.d \
	  mariadb:10.4

	echo "Setting up db3.."
       	secs=$((15))	
	x=$((3))
	Countdown
	sudo docker run -d --name dbproxy --hostname maxscale \
		--add-host dbgc1:172.17.0.6 \
		--add-host dbgc2:172.17.0.7 \
		--add-host dbgc3:172.17.0.8 \
		-v ~/volumes/dbproxy/my-maxscale.cnf:/etc/maxscale.cnf.d/my-maxscale.cnf mariadb/maxscale:latest
	echo "Setting up dbproxy.."
       	secs=$((10))	
	x='proxy'
	Countdown

}
: '
print_menu
echo "Enter numerical option"
read input
case $input in
        1)
                install_docker
                hosts_setup
                setup_containers
        ;;

        2)
                install_docker
        ;;

        3)
                hosts_setup
        ;;

        4)
                setup_containers
        ;;
	5)
		clean_volumes
	;;
esac
'
echo "Welcome to the docker setup script. Enjoy.."
clean_volumes
install_docker
hosts_setup
setup_containers
