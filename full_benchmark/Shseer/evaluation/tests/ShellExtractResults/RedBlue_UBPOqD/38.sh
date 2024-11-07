#!/bin/sh
USERNAME="root"
#AUTH_MODE="-p"
#CREDENTIAL=""
AUTH_MODE="-k"
CREDENTIAL="/home/dcfp/EU/tpcw-kf.pem"
TXM_DATABASE="ec2-79-125-40-176.eu-west-1.compute.amazonaws.com"  
TXM_PROXY="ec2-79-125-50-240.eu-west-1.compute.amazonaws.com"
TXM_USER="ec2-46-51-139-212.eu-west-1.compute.amazonaws.com"
TXM_COORDINATOR="ec2-46-51-167-8.eu-west-1.compute.amazonaws.com"
TXM_STORAGESHIM="ec2-46-51-141-1.eu-west-1.compute.amazonaws.com"

TPCW_DIR="/root/code/src/applications/tpc-w-fenix"
TXMUD_SRC="/root/code"
TPCW_BIN="/var/tmp/$USERNAME/output/tpcw/dist"
TXMUD_JARS="/var/tmp/$USERNAME/output/txmud/dist"

BACKEND="txmud"
##update the configuration files accordingly
TOPOLOGYXMLFILENAME="tpcwtxmud_allblue.xml"
DATABASEXMLFILENAME="tpcwtxmud_allbluedb.xml"
cat > $TOPOLOGYXMLFILENAME << EOF
<dataCenters dcNum="1">
	<dataCenter cdIP="$TXM_COORDINATOR" cdPort="50000">
		<storageShims ssNum="1">
			<storageShim ssIP="$TXM_STORAGESHIM" ssPort="50002"></storageShim>
		</storageShims>
		<webProxies wpNum="1">
			<webproxy wpIP="$TXM_PROXY" wpPort="50004"></webproxy>
	        </webProxies>
	</dataCenter>
</dataCenters>
EOF

cat > $DATABASEXMLFILENAME << EOF
<?xml version="1.0" encoding="UTF-8"?>
<databases dbNum="1">
        <database dcId="0" dbId="0" dbHost="$TXM_DATABASE" dbPort="53306" dbUser="sa" dbPwd=""
                dbName="mysql_redblue_semantics" tableList="address,author,cc_xacts,country,customer,item,order_line,orders,shopping_cart,shopping_cart_line" tableLWW="" redTable="" blueTable="address,author,cc_xacts,country,customer,item,order_line,orders,shopping_cart,shopping_cart_line" url_prefix="jdbc:mysql://">
        </database>
</databases>
EOF
##

DEPENDENCIES="$TPCW_DIR/tpcwtxmud_setup.sh deploy_dependencies"
PREPARE="cd $TPCW_DIR && ant clean dist -DdcId=0  -DproxyId=0 -Dnum.eb=10 -Dnum.items=1000 -Dlogicalclock=0-0 -Dbackend=$BACKEND -Dmysql_host=$TXM_DATABASE -Dmysql_port=53306 -Dtopologyfile=$TOPOLOGYXMLFILENAME"
POPULATE="$TPCW_DIR/tpcwtxmud_setup.sh populate $BACKEND localhost  53306 10 1000" 
IMAGES="cd $TPCW_DIR && ant genimg -Dnum.eb=10 -Dnum.items=1000"
INST="cd $TPCW_DIR && ant inst "
START_EXPERIMENT=""
if [ -n $2 ]
	then
	START_EXPERIMENT="cd $TPCW_BIN && ./rbe.sh -w http://$TXM_PROXY:8080/tpcw/ -b TxMudAllBlue -u 60 -d 60 -i 300 -n $2"
else
	START_EXPERIMENT="cd $TPCW_BIN && ./rbe.sh -w http://$TXM_PROXY:8080/tpcw/ -b TxMudAllBlue -u 60 -d 60 -i 300 -n 100"	
fi
# StubStorage config.xml db.xml dcId stroageId threadcount tcnnodelay scratchpadNum
START_STORAGESHIM="java -jar $TXMUD_JARS/storageshim-big.jar $TPCW_DIR/$TOPOLOGYXMLFILENAME $TPCW_DIR/$DATABASEXMLFILENAME 0 0 20 true 100 &> /tmp/s.out "

#Coordinator config.xml dcId coordinatorId threadCount tokensize tcpnodelay blueTimeOut
START_COORDINATOR="java -jar $TXMUD_JARS/coordinator-big.jar $TPCW_DIR/$TOPOLOGYXMLFILENAME 0 0 20 10000000 true 1000000  &>  /tmp/c.out "
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
	python tpcwtxmud_remote_setup.py -d $TXM_DATABASE  -u $USERNAME $AUTH_MODE "$CREDENTIAL" --run "$TPCW_DIR/tpcwtxmud_setup.sh install_proxy"
	#python tpcwtxmud_remote_setup.py -d $TXM_DATABASE  -u $USERNAME $AUTH_MODE "$CREDENTIAL" --run "$TPCW_DIR/tpcwtxmud_setup.sh install_database" 
	python tpcwtxmud_remote_setup.py -d $TXM_PROXY  -u $USERNAME $AUTH_MODE "$CREDENTIAL" --run "$TPCW_DIR/tpcwtxmud_setup.sh install_proxy"
	python tpcwtxmud_remote_setup.py -d $TXM_USER  -u $USERNAME $AUTH_MODE "$CREDENTIAL" --run "$TPCW_DIR/tpcwtxmud_setup.sh install_proxy"
	python tpcwtxmud_remote_setup.py -d $TXM_COORDINATOR  -u $USERNAME $AUTH_MODE "$CREDENTIAL" --run "$DEPENDENCIES"
	python tpcwtxmud_remote_setup.py -d $TXM_STORAGESHIM  -u $USERNAME $AUTH_MODE "$CREDENTIAL" --run "$DEPENDENCIES"
	
elif [ $1 = "get" ];	
	then 
	local_results="results_$TXM_USER"
	mkdir -p $local_results
	scp -i ${CREDENTIAL} -C -r ${USERNAME}"@"${TXM_USER}":"${TPCW_BIN}"/results/*" ${local_results}
	scp -i ${CREDENTIAL} -C -r ${USERNAME}"@"${TXM_COORDINATOR}":/tmp/c.out" ${local_results}
	scp -i ${CREDENTIAL} -C -r ${USERNAME}"@"${TXM_STORAGESHIM}":/tmp/s.out" ${local_results}
	
elif [ $1 = "configure" ]; #prepare all nodes with experiment parameters
	then
	# scp the topology and database files
	echo "updating configuration files"
	scp -i ${CREDENTIAL} $TOPOLOGYXMLFILENAME  $DATABASEXMLFILENAME ${USERNAME}"@"${TXM_USER}":"${TPCW_DIR}  
	scp -i ${CREDENTIAL} $TOPOLOGYXMLFILENAME  $DATABASEXMLFILENAME ${USERNAME}"@"${TXM_DATABASE}":"${TPCW_DIR} 
	scp -i ${CREDENTIAL} $TOPOLOGYXMLFILENAME  $DATABASEXMLFILENAME ${USERNAME}"@"${TXM_PROXY}":"${TPCW_DIR} 
	scp -i ${CREDENTIAL} $TOPOLOGYXMLFILENAME  $DATABASEXMLFILENAME ${USERNAME}"@"${TXM_COORDINATOR}":"${TPCW_DIR} 
	scp -i ${CREDENTIAL} $TOPOLOGYXMLFILENAME  $DATABASEXMLFILENAME ${USERNAME}"@"${TXM_STORAGESHIM}":"${TPCW_DIR} 
	echo "recompile source code"
	
	python tpcwtxmud_remote_setup.py -d $TXM_DATABASE  -u $USERNAME $AUTH_MODE "$CREDENTIAL" --run "$PREPARE"
	python tpcwtxmud_remote_setup.py -d $TXM_USER  -u $USERNAME $AUTH_MODE "$CREDENTIAL" --run "$PREPARE"
	python tpcwtxmud_remote_setup.py -d $TXM_PROXY  -u $USERNAME $AUTH_MODE "$CREDENTIAL" --run "$PREPARE"
	python tpcwtxmud_remote_setup.py -d $TXM_COORDINATOR  -u $USERNAME $AUTH_MODE "$CREDENTIAL" --run "$DEPENDENCIES"
	python tpcwtxmud_remote_setup.py -d $TXM_STORAGESHIM  -u $USERNAME $AUTH_MODE "$CREDENTIAL" --run "$DEPENDENCIES"
	
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
elif [ $1 = "coordinator_start" ];
	then	
	python tpcwtxmud_remote_setup.py -d $TXM_COORDINATOR  -u $USERNAME $AUTH_MODE "$CREDENTIAL" -r coordinator --run "$START_COORDINATOR "  &	
elif [ $1 = "storageshim_start" ];
	then	
	python tpcwtxmud_remote_setup.py -d $TXM_STORAGESHIM  -u $USERNAME $AUTH_MODE "$CREDENTIAL" -r mshim --run "$START_STORAGESHIM "  &	

elif [ $1 = "mysql_reset_clock" ];
	then	
	python tpcwtxmud_remote_setup.py -d $TXM_DATABASE  -u $USERNAME $AUTH_MODE "$CREDENTIAL" --run "$TPCW_DIR/tpcwtxmud_setup.sh reset_lc"
elif [ $1 = "reset" ];
	then
	python tpcwtxmud_remote_setup.py -d $TXM_STORAGESHIM  -u $USERNAME $AUTH_MODE "$CREDENTIAL" -r mshim --command "reset" 
	python tpcwtxmud_remote_setup.py -d $TXM_COORDINATOR  -u $USERNAME $AUTH_MODE "$CREDENTIAL" -r coordinator --command "reset" 
	python tpcwtxmud_remote_setup.py -d $TXM_DATABASE  -u $USERNAME $AUTH_MODE "$CREDENTIAL" -r storage --command "reset" 
	python tpcwtxmud_remote_setup.py -d $TXM_PROXY  -u $USERNAME $AUTH_MODE "$CREDENTIAL" -r proxy --command "reset" 
	python tpcwtxmud_remote_setup.py -d $TXM_USER  -u $USERNAME $AUTH_MODE "$CREDENTIAL" -r user --command "reset" 
elif [ $1 = "update" ];
	then
	python tpcwtxmud_remote_setup.py -d $TXM_STORAGESHIM  -u $USERNAME $AUTH_MODE "$CREDENTIAL" -r mshim --run "cd $TXMUD_SRC && svn up"
	python tpcwtxmud_remote_setup.py -d $TXM_COORDINATOR  -u $USERNAME $AUTH_MODE "$CREDENTIAL" -r coordinator --run "cd $TXMUD_SRC && svn up"
	python tpcwtxmud_remote_setup.py -d $TXM_DATABASE  -u $USERNAME $AUTH_MODE "$CREDENTIAL" -r storage --run "cd $TXMUD_SRC && svn up"
	python tpcwtxmud_remote_setup.py -d $TXM_PROXY  -u $USERNAME $AUTH_MODE "$CREDENTIAL" -r proxy --run "cd $TXMUD_SRC && svn up"
	python tpcwtxmud_remote_setup.py -d $TXM_USER  -u $USERNAME $AUTH_MODE "$CREDENTIAL" -r user --run "cd $TXMUD_SRC && svn up"
else [ -n $1 ] || [ $1 = "-h" ] || [ $1 = "h" ] || [ $1 = "--help" ];
	help
fi



echo "done"
