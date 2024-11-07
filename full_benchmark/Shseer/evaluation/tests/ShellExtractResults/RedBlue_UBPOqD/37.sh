#!/bin/sh
USERNAME="dcfp"
PASSWORD="mk38qa9t@mp"
TXM_DATABASE="139.19.158.39"
TXM_PROXY="139.19.158.73"
TXM_USER="139.19.158.54"
TPCW_DIR="/home/dcfp/workspace/txmud_spd/src/applications/tpc-w-fenix"
TPCW_BIN="/tmp/dcfp/tpcw/dist"
TXMUD_JARS="/tmp/dcfp/txmud/dist"

PREPARE="cd $TPCW_DIR && ant clean dist -DdcId=0  -DproxyId=0 -Dnum.eb=10 -Dnum.items=1000 -Dlogicalclock=0-0 -Dbackend=mysql -Dmysql_host=$TXM_DATABASE -Dmysql_port=53306 -Dtopologyfile=tpcwtxmud_allblue.xml"
POPULATE="$TPCW_DIR/tpcwtxmud_setup.sh populate mysql localhost  53306 10 1000" 
IMAGES="cd $TPCW_DIR && ant genimg -Dnum.eb=10 -Dnum.items=1000"
INST="cd $TPCW_DIR && ant inst "
START_EXPERIMENT=""
if [ -n $2 ]
	then
	START_EXPERIMENT="cd $TPCW_BIN && ./rbe.sh -w http://$TXM_PROXY:8080/tpcw/ -b Mysql -u 60 -d 60 -i 300 -n $2"
else
	START_EXPERIMENT="cd $TPCW_BIN && ./rbe.sh -w http://$TXM_PROXY:8080/tpcw/ -b Mysql -u 60 -d 60 -i 300 -n 100"	
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
	python tpcwtxmud_remote_setup.py -d $TXM_DATABASE  -u $USERNAME -p "$PASSWORD" --run "$TPCW_DIR/tpcwtxmud_setup.sh install_proxy"
	#python tpcwtxmud_remote_setup.py -d $TXM_DATABASE  -u $USERNAME -p "$PASSWORD" --run "$TPCW_DIR/tpcwtxmud_setup.sh install_database" 
	python tpcwtxmud_remote_setup.py -d $TXM_PROXY  -u $USERNAME -p "$PASSWORD" --run "$TPCW_DIR/tpcwtxmud_setup.sh install_proxy"
	python tpcwtxmud_remote_setup.py -d $TXM_USER  -u $USERNAME -p "$PASSWORD" --run "$TPCW_DIR/tpcwtxmud_setup.sh install_proxy"
	
elif [ $1 = "get" ];	
	then 
	local_results="results_$TXM_USER"
	mkdir -p $local_results
	scp -r ${USERNAME}"@"${TXM_USER}":"${TPCW_BIN}"/results/*" ${local_results}
	
elif [ $1 = "configure" ]; #prepare all nodes with experiment parameters
	then
	python tpcwtxmud_remote_setup.py -d $TXM_DATABASE  -u $USERNAME -p "$PASSWORD" --run "$PREPARE"
	python tpcwtxmud_remote_setup.py -d $TXM_PROXY  -u $USERNAME -p "$PASSWORD" --run "$PREPARE"
	python tpcwtxmud_remote_setup.py -d $TXM_USER  -u $USERNAME -p "$PASSWORD" --run "$PREPARE"
elif [ $1 = "database" ]; #populate database
	then	
	python tpcwtxmud_remote_setup.py -d $TXM_DATABASE  -u $USERNAME -p "$PASSWORD" --run "$POPULATE"
	echo "python tpcwtxmud_remote_setup.py -d $TXM_DATABASE  -u $USERNAME -p \"$PASSWORD\" --run \"$POPULATE\""
	
elif [ $1 = "website" ]; #tpcw tomcat
	then
	python tpcwtxmud_remote_setup.py -d $TXM_PROXY  -u $USERNAME -p "$PASSWORD" --run "$IMAGES"
	python tpcwtxmud_remote_setup.py -d $TXM_PROXY  -u $USERNAME -p "$PASSWORD" --run "$INST"
elif [ $1 = "reset" ];
	then	
	python tpcwtxmud_remote_setup.py -d $TXM_DATABASE  -u $USERNAME -p "$PASSWORD" -r storage --command "reset"
	python tpcwtxmud_remote_setup.py -d $TXM_PROXY  -u $USERNAME -p "$PASSWORD" -r proxy --command "reset"
	python tpcwtxmud_remote_setup.py -d $TXM_USER  -u $USERNAME -p "$PASSWORD" -r user --command "reset"

elif [ $1 = "tomcat_start" ];
	then	
	python tpcwtxmud_remote_setup.py -d $TXM_PROXY  -u $USERNAME -p "$PASSWORD" -r proxy --run "cd $TPCW_DIR && ant tomcat-start"
elif [ $1 = "mysql_start" ];
	then	
	python tpcwtxmud_remote_setup.py -d $TXM_DATABASE  -u $USERNAME -p "$PASSWORD" -r storage --run "cd $TPCW_DIR && ant mysql-start"

elif [ $1 = "user_start" ];
	then	
	python tpcwtxmud_remote_setup.py -d $TXM_USER  -u $USERNAME -p "$PASSWORD" -r user --run "$START_EXPERIMENT"
elif [ $1 = "reset" ];
	then	
	python tpcwtxmud_remote_setup.py -d $TXM_DATABASE  -u $USERNAME -p "$PASSWORD" -r storage --command "reset"
	python tpcwtxmud_remote_setup.py -d $TXM_PROXY  -u $USERNAME -p "$PASSWORD" -r proxy --command "reset"
	python tpcwtxmud_remote_setup.py -d $TXM_USER  -u $USERNAME -p "$PASSWORD" -r user --command "reset"
else [ -n $1 ] || [ $1 = "-h" ] || [ $1 = "h" ] || [ $1 = "--help" ];
	help
fi



echo "done"
