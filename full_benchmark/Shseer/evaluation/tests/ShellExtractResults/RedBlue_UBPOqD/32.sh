#!/bin/sh
USERNAME="dcfp"
PASSWORD="mk38qa9t@mp"
TXM_DATABASE="139.19.158.75"
TXM_PROXY="139.19.158.70"
TXM_USER="139.19.158.69"
TXM_COORDINATOR="139.19.158.72"
TXM_STORAGESHIM="139.19.158.74"

TPCW_DIR="/home/dcfp/workspace/txmud_spd/src/applications/tpc-w-fenix"
TPCW_BIN="/tmp/dcfp/tpcw/dist"
TXMUD_JARS="/tmp/dcfp/txmud/dist"

BACKEND="txmud"
PREPARE="cd $TPCW_DIR && ant clean dist -DdcId=0  -DproxyId=0 -Dnum.eb=10 -Dnum.items=1000 -Dlogicalclock=0-0 -Dbackend=$BACKEND -Dmysql_host=$TXM_DATABASE -Dmysql_port=53306 -Dtopologyfile=tpcwtxmud_redblue.xml"
POPULATE="$TPCW_DIR/tpcwtxmud_setup.sh populate $BACKEND localhost  53306 10 1000" 
IMAGES="cd $TPCW_DIR && ant genimg -Dnum.eb=10 -Dnum.items=1000"
INST="cd $TPCW_DIR && ant inst "
START_EXPERIMENT=""
if [ -n $2 ]
	then
	START_EXPERIMENT="cd $TPCW_BIN && ./rbe.sh -w http://$TXM_PROXY:8080/tpcw/ -b TxMudRedBlue -u 60 -d 60 -i 300 -n $2"
else
	START_EXPERIMENT="cd $TPCW_BIN && ./rbe.sh -w http://$TXM_PROXY:8080/tpcw/ -b TxMudRedBlue -u 60 -d 60 -i 300 -n 100"	
fi
# StubStorage config.xml db.xml dcId stroageId threadcount tcnnodelay scratchpadNum
START_STORAGESHIM="java -jar $TXMUD_JARS/storageshim-big.jar $TPCW_DIR/tpcwtxmud_redblue.xml $TPCW_DIR/tpcwtxmud_redbluedb.xml 0 0 20 true 100"

#Coordinator config.xml dcId coordinatorId threadCount tokensize tcpnodelay blueTimeOut
START_COORDINATOR="java -jar $TXMUD_JARS/coordinator-big.jar $TPCW_DIR/tpcwtxmud_redblue.xml 0 0 20 10000000 true 1000000"
#reset logical clock


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
	mysql_reset_clock # also restart mysql, 	mysql_start still works but wont clean the database
	coordinator_start
	storageshim_start
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
	python tpcwtxmud_remote_setup.py -d $TXM_DATABASE  -u $USERNAME -p "$PASSWORD" --run "$TPCW_DIR/tpcwtxmud_setup.sh install_database" 
	python tpcwtxmud_remote_setup.py -d $TXM_PROXY  -u $USERNAME -p "$PASSWORD" --run "$TPCW_DIR/tpcwtxmud_setup.sh install_proxy"
	python tpcwtxmud_remote_setup.py -d $TXM_USER  -u $USERNAME -p "$PASSWORD" --run "$TPCW_DIR/tpcwtxmud_setup.sh install_proxy"
	python tpcwtxmud_remote_setup.py -d $TXM_COORDINATOR  -u $USERNAME -p "$PASSWORD" --run "$TPCW_DIR/tpcwtxmud_setup.sh install_proxy"
	python tpcwtxmud_remote_setup.py -d $TXM_STORAGESHIM  -u $USERNAME -p "$PASSWORD" --run "$TPCW_DIR/tpcwtxmud_setup.sh install_proxy"
	
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
	python tpcwtxmud_remote_setup.py -d $TXM_STORAGESHIM  -u $USERNAME -p "$PASSWORD" --run "$PREPARE"
	python tpcwtxmud_remote_setup.py -d $TXM_COORDINATOR  -u $USERNAME -p "$PASSWORD" --run "$PREPARE"
	
elif [ $1 = "database" ]; #populate database
	then	
	python tpcwtxmud_remote_setup.py -d $TXM_DATABASE  -u $USERNAME -p "$PASSWORD" --run "$POPULATE"
	echo "python tpcwtxmud_remote_setup.py -d $TXM_DATABASE  -u $USERNAME -p \"$PASSWORD\" --run \"$POPULATE\""
	
elif [ $1 = "website" ]; #tpcw tomcat
	then
	python tpcwtxmud_remote_setup.py -d $TXM_PROXY  -u $USERNAME -p "$PASSWORD" --run "$IMAGES"
	python tpcwtxmud_remote_setup.py -d $TXM_PROXY  -u $USERNAME -p "$PASSWORD" --run "$INST"
elif [ $1 = "tomcat_start" ];
	then	
	python tpcwtxmud_remote_setup.py -d $TXM_PROXY  -u $USERNAME -p "$PASSWORD" -r proxy --run "cd $TPCW_DIR && ant tomcat-start"
elif [ $1 = "mysql_start" ];
	then	
	python tpcwtxmud_remote_setup.py -d $TXM_DATABASE  -u $USERNAME -p "$PASSWORD" -r storage --run "cd $TPCW_DIR && ant mysql-start"

elif [ $1 = "user_start" ];
	then	
	python tpcwtxmud_remote_setup.py -d $TXM_USER  -u $USERNAME -p "$PASSWORD" -r user --run "$START_EXPERIMENT"
elif [ $1 = "coordinator_start" ];
	then	
	python tpcwtxmud_remote_setup.py -d $TXM_COORDINATOR  -u $USERNAME -p "$PASSWORD" -r coordinator --run "$START_COORDINATOR 2>&1 > /tmp/$USERNAME/coordiantor.out"  &	
elif [ $1 = "storageshim_start" ];
	then	
	python tpcwtxmud_remote_setup.py -d $TXM_STORAGESHIM  -u $USERNAME -p "$PASSWORD" -r mshim --run "$START_STORAGESHIM 2>&1 > /tmp/$USERNAME/storageshim.out "  &	

elif [ $1 = "mysql_reset_clock" ];
	then	
	python tpcwtxmud_remote_setup.py -d $TXM_DATABASE  -u $USERNAME -p "$PASSWORD" --run "$TPCW_DIR/tpcwtxmud_setup.sh reset_lc"
elif [ $1 = "reset" ];
	then
	python tpcwtxmud_remote_setup.py -d $TXM_STORAGESHIM  -u $USERNAME -p "$PASSWORD" -r mshim --command "reset"
	python tpcwtxmud_remote_setup.py -d $TXM_COORDINATOR  -u $USERNAME -p "$PASSWORD" -r coordinator --command "reset"
	python tpcwtxmud_remote_setup.py -d $TXM_DATABASE  -u $USERNAME -p "$PASSWORD" -r storage --command "reset"
	python tpcwtxmud_remote_setup.py -d $TXM_PROXY  -u $USERNAME -p "$PASSWORD" -r proxy --command "reset"
	python tpcwtxmud_remote_setup.py -d $TXM_USER  -u $USERNAME -p "$PASSWORD" -r user --command "reset"
	
else [ -n $1 ] || [ $1 = "-h" ] || [ $1 = "h" ] || [ $1 = "--help" ];
	help
fi



echo "done"
