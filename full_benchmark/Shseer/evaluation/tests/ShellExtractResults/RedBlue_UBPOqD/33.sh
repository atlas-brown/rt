#!/bin/sh
USERNAME="root"
#AUTH_MODE="-p"
#CREDENTIAL=""
AUTH_MODE="-k"
CREDENTIAL="/home/dcfp/EU/tpcw-kf.pem"

TPCW_DIR="/root/code/src/applications/tpc-w-fenix"
TXMUD_SRC="/root/code"
TPCW_BIN="/var/tmp/$USERNAME/output/tpcw/dist"
TXMUD_JARS="/var/tmp/$USERNAME/output/txmud/dist"
BACKEND="mysql"

####DATACENTER
TXM_DATABASE="ec2-46-137-56-4.eu-west-1.compute.amazonaws.com"  
TXM_PROXY="ec2-46-51-136-186.eu-west-1.compute.amazonaws.com"
TXM_USER="ec2-46-137-11-179.eu-west-1.compute.amazonaws.com"
####TXM_COORDINATOR="ec2-46-137-128-165.eu-west-1.compute.amazonaws.com"
###TXM_STORAGESHIM="ec2-79-125-52-10.eu-west-1.compute.amazonaws.com"

DEPENDENCIES="$TPCW_DIR/tpcwtxmud_setup.sh deploy_dependencies"
EB=50
ITEM=10000
DATABASETGZ="mysql-5.5.15.zero.2db.lc0-0-0.50eb10kitem.tgz"
PREPARE="cd $TPCW_DIR && ant clean dist -DdcId=0  -DproxyId=0 -Dnum.eb=$EB -Dnum.items=$ITEM -Dlogicalclock=0-0-0 -Dbackend=$BACKEND -Dmysql_host=$TXM_DATABASE -Dmysql_port=53306"
POPULATE="$TPCW_DIR/tpcwtxmud_setup.sh populate $BACKEND localhost  53306 $EB $ITEM" 
IMAGES="cd $TPCW_DIR && ant genimg -Dnum.eb=10 -Dnum.items=1000"
INST="cd $TPCW_DIR && ant inst "
START_EXPERIMENT=""
if [ -n $2 ]
	then
	START_EXPERIMENT="cd $TPCW_BIN && ./rbe.sh -w http://$TXM_PROXY:8080/tpcw/ -b Mysql -l 0 -u 60 -d 60 -i 300 -n $2"
else
	START_EXPERIMENT="cd $TPCW_BIN && ./rbe.sh -w http://$TXM_PROXY:8080/tpcw/ -b Mysql -l 0 -u 60 -d 60 -i 300 -n 100"	
fi



help()
{
  cat <<HELP
Remember to edit this file first!!
Configuration parameters:
	install_all
	configure
	website
	database

execute experiment
	reset		
	mysql_start
	tomcat_start
	user_start [num users]
	get


if you want to change the experiment configuration edit this file	
	
	
HELP
  exit 0
}


if [ $1 = "install_all" ];	
	then 
	python tpcwtxmud_remote_setup.py -d $TXM_DATABASE  -u $USERNAME $AUTH_MODE "$CREDENTIAL" --run "$TPCW_DIR/tpcwtxmud_setup.sh install_proxy"
	#python tpcwtxmud_remote_setup.py -d $TXM_DATABASE  -u $USERNAME $AUTH_MODE "$CREDENTIAL" --run "$TPCW_DIR/tpcwtxmud_setup.sh install_database" 
	python tpcwtxmud_remote_setup.py -d $TXM_PROXY  -u $USERNAME $AUTH_MODE "$CREDENTIAL" --run "$TPCW_DIR/tpcwtxmud_setup.sh install_proxy"
	python tpcwtxmud_remote_setup.py -d $TXM_USER  -u $USERNAME $AUTH_MODE "$CREDENTIAL" --run "$TPCW_DIR/tpcwtxmud_setup.sh install_proxy"
	
elif [ $1 = "get" ];	
	then 
	local_results="results_$TXM_USER"
	mkdir -p $local_results
	scp -i ${CREDENTIAL} -C -r ${USERNAME}"@"${TXM_USER}":"${TPCW_BIN}"/results/*" ${local_results}
	
elif [ $1 = "configure" ]; #prepare all nodes with experiment parameters
	then
	echo "recompile source code"
	
	python tpcwtxmud_remote_setup.py -d $TXM_DATABASE  -u $USERNAME $AUTH_MODE "$CREDENTIAL" --run "$PREPARE"
	python tpcwtxmud_remote_setup.py -d $TXM_USER  -u $USERNAME $AUTH_MODE "$CREDENTIAL" --run "$PREPARE"
	python tpcwtxmud_remote_setup.py -d $TXM_PROXY  -u $USERNAME $AUTH_MODE "$CREDENTIAL" --run "$PREPARE"

elif [ $1 = "database" ]; #populate database
	then	
	python tpcwtxmud_remote_setup.py -d $TXM_DATABASE  -u $USERNAME $AUTH_MODE "$CREDENTIAL" --run "$POPULATE"
	echo "python tpcwtxmud_remote_setup.py -d $TXM_DATABASE  -u $USERNAME $AUTH_MODE \"$CREDENTIAL\" --run \"$POPULATE\""
	
elif [ $1 = "website" ]; #tpcw tomcat
	then
	python tpcwtxmud_remote_setup.py -d $TXM_PROXY  -u $USERNAME $AUTH_MODE "$CREDENTIAL" --run "$DEPENDENCIES"
	python tpcwtxmud_remote_setup.py -d $TXM_PROXY  -u $USERNAME $AUTH_MODE "$CREDENTIAL" --run "$IMAGES"
	python tpcwtxmud_remote_setup.py -d $TXM_PROXY  -u $USERNAME $AUTH_MODE "$CREDENTIAL" --run "$INST"
elif [ $1 = "tomcat_start" ];
	then	
	python tpcwtxmud_remote_setup.py -d $TXM_PROXY  -u $USERNAME $AUTH_MODE "$CREDENTIAL" -r proxy --run "cd $TPCW_DIR && ant tomcat-start"
elif [ $1 = "mysql_start" ];
	then	
	python tpcwtxmud_remote_setup.py -d $TXM_DATABASE  -u $USERNAME $AUTH_MODE "$CREDENTIAL" -r storage --run "cd $TPCW_DIR && ant mysql-start"

elif [ $1 = "user_start" ];
	then	
	python tpcwtxmud_remote_setup.py -d $TXM_USER  -u $USERNAME $AUTH_MODE "$CREDENTIAL" -r user --run "$START_EXPERIMENT"
elif [ $1 = "reset" ];
	then
	python tpcwtxmud_remote_setup.py -d $TXM_DATABASE  -u $USERNAME $AUTH_MODE "$CREDENTIAL" -r storage --command "reset" 
	python tpcwtxmud_remote_setup.py -d $TXM_PROXY  -u $USERNAME $AUTH_MODE "$CREDENTIAL" -r proxy --command "reset" 
	python tpcwtxmud_remote_setup.py -d $TXM_USER  -u $USERNAME $AUTH_MODE "$CREDENTIAL" -r user --command "reset" 
elif [ $1 = "update" ];
	then
	python tpcwtxmud_remote_setup.py -d $TXM_DATABASE  -u $USERNAME $AUTH_MODE "$CREDENTIAL" -r storage --run "cd $TXMUD_SRC && svn up"
	python tpcwtxmud_remote_setup.py -d $TXM_PROXY  -u $USERNAME $AUTH_MODE "$CREDENTIAL" -r proxy --run "cd $TXMUD_SRC && svn up"
	python tpcwtxmud_remote_setup.py -d $TXM_USER  -u $USERNAME $AUTH_MODE "$CREDENTIAL" -r user --run "cd $TXMUD_SRC && svn up"
else [ -n $1 ] || [ $1 = "-h" ] || [ $1 = "h" ] || [ $1 = "--help" ];
	help
fi



echo "done"
