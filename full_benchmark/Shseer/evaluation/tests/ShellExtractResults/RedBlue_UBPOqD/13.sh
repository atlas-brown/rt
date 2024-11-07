#!/bin/bash
USERNAME="root"
#to use in thor nodes first use ssh-keygen to generate the key, then use ssh-copy-id to localhost to enable login using key file
AUTH_MODE="-k" #AUTH_MODE="-k"
CREDENTIAL[0]="/home/dcfp/Downloads/eurosys-uspk.pem" #CREDENTIAL[0]="/home/$USERNAME/.ssh/id_rsa" #CREDENTIAL0="/home/$USERNAME/aws-credentials/US/tpcw-kf.pem"
CREDENTIAL[1]="/home/dcfp/Downloads/eurosys-eupk.pem" #CREDENTIAL[1]="/home/$USERNAME/.ssh/id_rsa" #CREDENTIAL1="/home/$USERNAME/aws-credentialsEU/tpcw-kf.pem"
TXMUD_ROOT="/home/$USERNAME/devel/txmud" 			  #TXMUD_ROOT="/home/$USERNAME/devel/txmud-trunk"
TPCW_ROOT="$TXMUD_ROOT/src/applications/tpc-w-fenix"
TPCW_SCRIPTS="$TPCW_ROOT/scripts"
TPCW_OUTPUTDIR="/var/tmp/$USERNAME/output/tpcw"
TXMUD_OUTPUTDIR="/var/tmp/$USERNAME/output/txmud"
TPCW_BINARIES="$TPCW_OUTPUTDIR/dist"
TXMUD_BINARIES="$TXMUD_OUTPUTDIR/dist"
#TPCW PARAMETERS
EB=50    #pay attention to database file. it should match with the numbers chosen 
ITEM=10000 
TPCW_MIX=1 #1 browsing, 2 shopping, 3 ordering
TPCW_WARMUPTIME=60
TPCW_TEARDOWNTIME=60
TPCW_MEASUREMENTINTERVAL=300
TPCW_THINKTIME=0.0
BACKEND="mysql" #options: mysql, txmud, txmud_ssc, scratchpad
#RESULTFILE_TAG="TxMudRedBlue"  #it should be defined according to table color and the backend: TxMudAllBlue,TxMudRedBlue,Mysql
RESULTFILE_TAG="Mysql"  #it should be defined according to table color and the backend: TxMudAllBlue,TxMudRedBlue,Mysql 
DATABASETGZ="mysql-5.5.15.zero.3db.lc0-0-0.50eb10kitem.sharedcart.tuned.$USERNAME.tgz"
#DATABASE
DBPORT=53306
DBUSER="sa"
DBUSERPW=""
DATACENTERNUM=2  #total datacenters
STORAGESHIMNUM=1 #per datacenter
PROXYNUM=1 # per datacenter
DATABASENUM=$DATACENTERNUM # per datacenter 
###############AMAZON###############
####DATACENTER 0
TXM_DATABASE[0]="ec2-50-16-126-6.compute-1.amazonaws.com"
TXM_PROXY[0]="ec2-174-129-126-158.compute-1.amazonaws.com"
TXM_COORDINATOR[0]="ec2-50-19-45-23.compute-1.amazonaws.com"
TXM_STORAGESHIM[0]="ec2-50-19-45-23.compute-1.amazonaws.com"
TXM_USER[0]="ec2-50-19-45-23.compute-1.amazonaws.com"
####DATACENTER 1
TXM_DATABASE[1]="ec2-46-137-43-4.eu-west-1.compute.amazonaws.com"
TXM_PROXY[1]="ec2-46-137-43-4.eu-west-1.compute.amazonaws.com"
TXM_COORDINATOR[1]="ec2-46-137-43-4.eu-west-1.compute.amazonaws.com"
TXM_STORAGESHIM[1]="ec2-46-137-43-4.eu-west-1.compute.amazonaws.com"
TXM_USER[1]="ec2-46-137-149-20.eu-west-1.compute.amazonaws.com"
############THOR MPI################
####DATACENTER 0
#TXM_DATABASE[0]="139.19.158.72"  
#TXM_PROXY[0]="139.19.158.73"
#TXM_COORDINATOR[0]="139.19.158.74"
#TXM_STORAGESHIM[0]="139.19.158.75"
#TXM_USER[0]="139.19.158.76"
####DATACENTER 1
#TXM_DATABASE[1]="139.19.158.77"  
#TXM_PROXY[1]="139.19.158.78"
#TXM_COORDINATOR[1]="139.19.158.79"
#TXM_STORAGESHIM[1]="139.19.158.14"
#TXM_USER[1]="139.19.158.19"
#####################################
#TXM_DATABASE[0]="139.19.158.56"  
#TXM_PROXY[0]="139.19.158.62"
#TXM_COORDINATOR[0]="139.19.158.57"
#TXM_STORAGESHIM[0]="139.19.158.58"
#TXM_USER[0]="139.19.158.59
###DATACENTER 1
#TXM_DATABASE[1]="139.19.158.51"  
#TXM_PROXY[1]="139.19.158.52"
#TXM_COORDINATOR[1]="139.19.158.53"
#TXM_STORAGESHIM[1]="139.19.158.54"
#TXM_USER[1]="139.19.158.55"
#-----------------------------------------------------------------------------

##update the configuration files accordingly - they will be overwritten!!!
TOPOLOGYXMLFILENAME="tpcwtxmud_topology_${USERNAME}.${BACKEND}.${TPCW_MIX}.xml"
DATABASEXMLFILENAME="tpcwtxmud_dbschema_${USERNAME}.${BACKEND}.${TPCW_MIX}.xml"
#experiment tag
if [ $DATACENTERNUM -gt 1 ]; then
	EXPERIMENT_TAG="MultiDataCenter_${BACKEND}_${RESULTFILE_TAG}"
else
	EXPERIMENT_TAG="SingleDataCenter_${BACKEND}_${RESULTFILE_TAG}"
fi;
#-----------------------------------------------------------------------------
#topology file content
LOGICAL_CLOCK="0"
echo "<dataCenters dcNum='$DATACENTERNUM'>" > $TOPOLOGYXMLFILENAME 
for ((i=0;i<$DATACENTERNUM;i++)) do
	LOGICAL_CLOCK=$LOGICAL_CLOCK"-0"
	echo -e "																\n\
<dataCenter cdPort='60000' cdIP='${TXM_COORDINATOR[$i]}'> 					\n\
	<storageShims ssNum='1'> 												\n\
		<storageShim ssIP='${TXM_STORAGESHIM[$i]}' ssPort='60001'/> 		\n\
	</storageShims> 														\n\
	<webProxies wpNum='1'> 													\n\
		<webproxy wpPort='60002' wpIP='${TXM_PROXY[$i]}'/> 					\n\
	</webProxies> 															\n\
</dataCenter> " >> $TOPOLOGYXMLFILENAME 
done;
echo "</dataCenters>" >> $TOPOLOGYXMLFILENAME
#-----------------------------------------------------------------------------
#database file content
echo "<?xml version='1.0' encoding='UTF-8'?>" > $DATABASEXMLFILENAME
echo "<databases dbNum='$DATABASENUM'>" >> $DATABASEXMLFILENAME
for ((i=0;i<$DATACENTERNUM; i++)) do
echo -e "<database dcId='$i' dbId='0' dbHost='${TXM_DATABASE[$i]}' dbPort='$DBPORT'	dbUser='$DBUSER' dbPwd='$DBUSERPW' dbName='mysql_redblue_semantics' 	tableList='address,author,cc_xacts,country,customer,item,order_line,orders,shopping_cart,shopping_cart_line' 	tableLWW='address,author,cc_xacts,country,customer,order_line,shopping_cart_line,shopping_cart'		talbeOps=''		redTable='address,author,cc_xacts,country,customer,order_line,shopping_cart_line,shopping_cart' blueTable='orders,item' url_prefix='jdbc:mysql://' > </database>" >> $DATABASEXMLFILENAME
done;
echo "</databases>">> $DATABASEXMLFILENAME
#-----------------------------------------------------------------------------

#COMMANDS
CMD_INSTALL_DEPENDENCIES="$TPCW_SCRIPTS/tpcwtxmud_setup.sh deploy_dependencies"
CMD_BUILD_TPCW_IMAGES="cd $TPCW_ROOT && ant genimg -Dnum.eb=$EB -Dnum.item=$ITEM -DoutputDir=$TPCW_OUTPUTDIR"
CMD_INSTALL_TPCW_WEBSITE="cd $TPCW_ROOT && ant inst -DoutputDir=$TPCW_OUTPUTDIR"
#ATENTION - RESET LOGICAL CLOCK UNPACK THE ORIGINAL DATABASE -> TO MAKE SURE 
#THEY ARE ALL EQUAL IN THE BEGINNING
#HERE WE CMD_POPULATE_DATABASE, MIGHT BE DIFFERENT -- CAREFUL 
CMD_POPULATE_DATABASE="$TPCW_SCRIPTS/tpcwtxmud_setup.sh populate $BACKEND localhost  $DBPORT $EB $ITEM" 
#TODO fix the loop for more than one proxy per datacenter!
CMD_DBCLEANUP="rm -rf /tmp/mysql.sock /var/tmp/$USERNAME/mysql-5.5.15 && echo 'done'"
#CMD_DBDEPLOY="cd /var/tmp/$USERNAME && tar xzf $DATABASETGZ && echo 'done'"
CMD_DBDEPLOY="tar xzf /home/$USERNAME/$DATABASETGZ -C /var/tmp/$USERNAME && echo 'done'"

for ((i=0;i<$DATACENTERNUM;i++)) do
	#for ((j=0;j<$PROXYNUM;j++)) do
	echo "#TODO fix the loop for more than one proxy per datacenter!"
	CMD_CONFIGURE[$i]="cd $TPCW_ROOT && ant clean dist -DoutputDir=$TPCW_OUTPUTDIR -DdcId=$i \
			 -DproxyId=0 -Dtotaldc=$DATACENTERNUM -Dtotalproxy=$(($DATACENTERNUM*$PROXYNUM)) \
			 -Dnum.eb=$EB -Dnum.item=$ITEM -Dlogicalclock=$LOGICAL_CLOCK -Dbackend=$BACKEND \
			 -Dmysql_host=${TXM_DATABASE[$i]} -Dmysql_port=$DBPORT -Dtopologyfile=$TOPOLOGYXMLFILENAME \
			 -Dthinktime=$TPCW_THINKTIME -Djdbc.connPoolMax=500 && echo 2000000 > /proc/sys/fs/file-max && ulimit -n 10240"
done;
if [ -n $2 ]
	then
		for((i=0;i<$DATACENTERNUM;i++)) do
			CMD_START_EXPERIMENT[$i]="cd $TPCW_BINARIES && 	./rbe.sh -w http://${TXM_PROXY[0]}:8080/tpcw/ -b $RESULTFILE_TAG  	-l $i -t $TPCW_MIX -u $TPCW_WARMUPTIME  -d $TPCW_TEARDOWNTIME -i $TPCW_MEASUREMENTINTERVAL -n $2"
			CMD_WAIT_USERS[$i]="while  [ \`ps aux | grep $USERNAME | grep java | grep RBE | grep -v grep | wc -l\`  -ne 0 ]; do  echo 'waiting...' && sleep 10 ;  done"
		done;
else
	for ((i=0;i<$DATACENTERNUM;i++)) do
			CMD_START_EXPERIMENT[$i]="cd $TPCW_BINARIES && 	./rbe.sh -w http://${TXM_PROXY[0]}:8080/tpcw/ -b $RESULTFILE_TAG  	-l $i -t $TPCW_MIX -u $TPCW_WARMUPTIME  -d $TPCW_TEARDOWNTIME -i $TPCW_MEASUREMENTINTERVAL -n 100"
			CMD_WAIT_USERS[$i]="while  [ \`ps aux | grep $USERNAME | grep java | grep RBE | grep -v grep | wc -l\`  -ne 0 ]; do  echo 'waiting...' && sleep 10 ;  done"
		done;
fi
# StubStorage config.xml db.xml dcId stroageId threadcount tcnnodelay scratchpadNum
for ((i=0;i<$DATACENTERNUM;i++)) do
	if [ -n $2 ]
	then
		CMD_START_STORAGESHIM[$i]=" echo '' > /tmp/storageshim.$i.log && java -jar $TXMUD_BINARIES/storageshim-big.jar $TPCW_ROOT/$TOPOLOGYXMLFILENAME $TPCW_ROOT/$DATABASEXMLFILENAME $i 0 20 true $2 &> /tmp/storageshim.$i.log "
		CMD_WAIT_STORAGESHIM[$i]="while  [ \`tail /tmp/storageshim.$i.log  | grep 'Listening to' | wc -l\`  -ne 1 ]; do  echo 'waiting...' && sleep 10 ;  done"
			
	else
		CMD_START_STORAGESHIM[$i]="echo '' > /tmp/storageshim.$i.log && java -jar $TXMUD_BINARIES/storageshim-big.jar $TPCW_ROOT/$TOPOLOGYXMLFILENAME $TPCW_ROOT/$DATABASEXMLFILENAME $i 0 20 true 150 &> /tmp/storageshim.$i.log "
		CMD_WAIT_STORAGESHIM[$i]="while  [ \`tail /tmp/storageshim.$i.log  | grep 'Listening to' | wc -l\`  -ne 1 ]; do  echo 'waiting...' && sleep 10 ;  done"
	fi		
done;



#Coordinator config.xml dcId coordinatorId threadCount tokensize tcpnodelay blueTimeOut bluequittime
for ((i=0;i<$DATACENTERNUM;i++)) do
	CMD_START_COORDINATOR[$i]="java -jar $TXMUD_BINARIES/coordinator-big.jar $TPCW_ROOT/$TOPOLOGYXMLFILENAME $i 0 20 1000 true 1000000000 50000000  &> /tmp/coordinator.$i.log"
done;

#------------------------------------------------------------------------------
# help
# print out usage procedures
#------------------------------------------------------------------------------
help()
{
  cat <<HELP
Remember to edit this file first!!
Configuration parameters --- EXECUTE ONCE TIME ONLY:
	install_all | install_proxy |install_database | txmud   # cleanup and reinstall
	configure  #reconfigure all based of the parameters set in this file   
	website    #redeploy tpcw website according to the parameters in this file
	database   #populate the database - not tested whether the database would be exacly the same for multidatacenter! 

execute experiment -- EXPERIMENT ROUND TRIP:
	shutdown		
	reset_database | mysql_start  #restart mysql, mysql_start wont the database
	start_coordinator				 
	start_storageshim [num shims]
	start_tomcat  
	start_user [num users] 
	get        


if you want to change the experiment configuration edit this file	
	
	
HELP
  exit 0
}

#------------------------------------------------------------------------------
# install_txmud
# arg: host credential
#------------------------------------------------------------------------------
install_txmud(){ 
	python tpcwtxmud_remote_setup.py -d $1  -u $USERNAME $AUTH_MODE "$2" --run "$CMD_INSTALL_DEPENDENCIES"
}
#------------------------------------------------------------------------------
# install_database
# arg: host credential
#------------------------------------------------------------------------------
install_database(){ #host credential
	#download the already populated database from my home directory 
	#pay attention because the database location depends on the username used to compile it
	#we can use a parameter that says the url of the database and another one to check the md5 of it
	python tpcwtxmud_remote_setup.py -d $1  -u $USERNAME $AUTH_MODE "$2" --run "$TPCW_SCRIPTS/tpcwtxmud_setup.sh install_database"
}
#------------------------------------------------------------------------------
# install_proxy
# arg: host credential
#------------------------------------------------------------------------------
install_proxy(){
	 python tpcwtxmud_remote_setup.py -d $1  -u $USERNAME $AUTH_MODE "$2" --run "$TPCW_SCRIPTS/tpcwtxmud_setup.sh install_proxy"
}
#------------------------------------------------------------------------------
# install_all
#------------------------------------------------------------------------------
install_all(){
	for ((i=0;i<$DATACENTERNUM;i++)) do
		#install_database ${TXM_DATABASE[$i]} ${CREDENTIAL[$i]}
		install_proxy ${TXM_PROXY[$i]} ${CREDENTIAL[$i]}
		install_txmud ${TXM_PROXY[$i]} ${CREDENTIAL[$i]}
		
		install_proxy ${TXM_USER[$i]} ${CREDENTIAL[$i]}
		install_txmud ${TXM_USER[$i]} ${CREDENTIAL[$i]}
		
		install_txmud ${TXM_STORAGESHIM[$i]} ${CREDENTIAL[$i]}
		install_txmud ${TXM_COORDINATOR[$i]} ${CREDENTIAL[$i]}
	done;
}

increase_files_all(){
	CMD_OPENFILES="echo 2000000 > /proc/sys/fs/file-max"

for((i=0;i<$DATACENTERNUM;i++)) do
		python tpcwtxmud_remote_setup.py -d ${TXM_USER[$i]}  -u $USERNAME $AUTH_MODE "${CREDENTIAL[$i]}" --run "$CMD_OPENFILES"
		python tpcwtxmud_remote_setup.py -d ${TXM_PROXY[$i]}  -u $USERNAME $AUTH_MODE "${CREDENTIAL[$i]}" --run "$CMD_OPENFILES"
		python tpcwtxmud_remote_setup.py -d ${TXM_COORDINATOR[$i]}  -u $USERNAME $AUTH_MODE "${CREDENTIAL[$i]}" --run "$CMD_OPENFILES"
		python tpcwtxmud_remote_setup.py -d ${TXM_STORAGESHIM[$i]}  -u $USERNAME $AUTH_MODE "${CREDENTIAL[$i]}" --run "$CMD_OPENFILES"
	done;

}
#------------------------------------------------------------------------------
# isrunning check whether a remote process is running or not
# arg: host credential processname
#------------------------------------------------------------------------------	
isrunning(){
	if [ -z $1 ] || [ -z $2 ] || [ -z $3 ]  
	then 
		echo "process name is required"; 
		exit 0	
	fi
	file=`mktemp`
	python tpcwtxmud_remote_setup.py -d $1 -u $USERNAME $AUTH_MODE $2 --run "ps aux | grep $3 | grep -v grep" &> $file
	A=$(grep Success $file)
	rm $file
	 
	if [ -n "$A" ]
		then echo "$2 is running "
			return true;
	else
		echo "$2 is not running"
		return false;
	fi;
}
#------------------------------------------------------------------------------
# get - download all files from remote servers
# arg: none
#------------------------------------------------------------------------------
get(){
	mkdir -p result/$EXPERIMENT_TAG
	if [ $AUTH_MODE = "-k" ] 
	then
		CMD_SCP="scp -C -r -i "
	else
		CMD_SCP="scp -C -r "
	fi
	
	for((i=0;i<$DATACENTERNUM;i++)) do
		$CMD_SCP ${CREDENTIAL[$i]} ${USERNAME}"@"${TXM_USER[$i]}":"${TPCW_OUTPUTDIR}"/dist/results/*" result/$EXPERIMENT_TAG
		$CMD_SCP ${CREDENTIAL[$i]} ${USERNAME}"@"${TXM_COORDINATOR[$i]}":/tmp/coordinator.$i.log" result/$EXPERIMENT_TAG
		$CMD_SCP ${CREDENTIAL[$i]} ${USERNAME}"@"${TXM_STORAGESHIM[$i]}":/tmp/storageshim.$i.log" result/$EXPERIMENT_TAG
		$CMD_SCP ${CREDENTIAL[$i]} ${USERNAME}"@"${TXM_PROXY[$i]}":/tmp/storageshim.$i.log" result/$EXPERIMENT_TAG
		$CMD_SCP ${CREDENTIAL[$i]} ${USERNAME}"@"${TXM_PROXY[$i]}":/tmp/storageshim.$i.log" result/$EXPERIMENT_TAG
	done;
}
#------------------------------------------------------------------------------
# configure
# arg: configure all components of all datacenters
#------------------------------------------------------------------------------
configure(){
	if [ $AUTH_MODE = "-k" ]
	then
		CMD_SCP="scp -C -r -i "
	else
		CMD_SCP="scp -C -r "
	fi
	
	echo "deploying configuration files"
	for((i=0;i<$DATACENTERNUM;i++)) do
		
		$CMD_SCP  ${CREDENTIAL[$i]} $TOPOLOGYXMLFILENAME  $DATABASEXMLFILENAME ${USERNAME}"@"${TXM_PROXY[$i]}":"${TPCW_ROOT} 
		$CMD_SCP  ${CREDENTIAL[$i]} $TOPOLOGYXMLFILENAME  $DATABASEXMLFILENAME ${USERNAME}"@"${TXM_COORDINATOR[$i]}":"${TPCW_ROOT} 
		$CMD_SCP  ${CREDENTIAL[$i]} $TOPOLOGYXMLFILENAME  $DATABASEXMLFILENAME ${USERNAME}"@"${TXM_STORAGESHIM[$i]}":"${TPCW_ROOT}
	done;

	echo "recompile source code"
	for((i=0;i<$DATACENTERNUM;i++)) do
		python tpcwtxmud_remote_setup.py -d ${TXM_USER[$i]}  -u $USERNAME $AUTH_MODE "${CREDENTIAL[$i]}" --run "$CMD_INSTALL_DEPENDENCIES"
		python tpcwtxmud_remote_setup.py -d ${TXM_USER[$i]} -u $USERNAME $AUTH_MODE "${CREDENTIAL[$i]}" --run "${CMD_CONFIGURE[$i]}"
		python tpcwtxmud_remote_setup.py -d ${TXM_PROXY[$i]}  -u $USERNAME $AUTH_MODE "${CREDENTIAL[$i]}" --run "$CMD_INSTALL_DEPENDENCIES"
		python tpcwtxmud_remote_setup.py -d ${TXM_PROXY[$i]}  -u $USERNAME $AUTH_MODE "${CREDENTIAL[$i]}" --run "${CMD_CONFIGURE[$i]}"
		python tpcwtxmud_remote_setup.py -d ${TXM_COORDINATOR[$i]}  -u $USERNAME $AUTH_MODE "${CREDENTIAL[$i]}" --run "$CMD_INSTALL_DEPENDENCIES"
		python tpcwtxmud_remote_setup.py -d ${TXM_STORAGESHIM[$i]}  -u $USERNAME $AUTH_MODE "${CREDENTIAL[$i]}" --run "$CMD_INSTALL_DEPENDENCIES"
	done;
	increase_files_all;
}	
populate_remote_database(){
	python tpcwtxmud_remote_setup.py -d ${TXM_DATABASE[0]}  -u $USERNAME $AUTH_MODE "${CREDENTIAL[0]}" --run "$CMD_POPULATE_DATABASE"
	#python tpcwtxmud_remote_setup.py -d ${TXM_DATABASE[1]}  -u $USERNAME $AUTH_MODE "${CREDENTIAL[1]}" --run "$CMD_POPULATE_DATABASE" 
}		
deploy_tpcw_website(){
	for((i=0;i<$DATACENTERNUM;i++)) do
		#echo "generating images"
		#python tpcwtxmud_remote_setup.py -d ${TXM_PROXY[$i]}  -u $USERNAME $AUTH_MODE "${CREDENTIAL[$i]}" --run "$CMD_BUILD_TPCW_IMAGES"
		echo "=================================================================="
		echo "deploying website with images"
		echo "=================================================================="
		python tpcwtxmud_remote_setup.py -d ${TXM_PROXY[$i]}  -u $USERNAME $AUTH_MODE "${CREDENTIAL[$i]}" --run "$CMD_INSTALL_TPCW_WEBSITE"
	done;

}
reset_logical_clock(){
	for((i=0;i<$DATABASENUM;i++)) do
		echo "========================================================="
		echo "force database to shutdown"
		python tpcwtxmud_remote_setup.py -d ${TXM_DATABASE[$i]}  -u $USERNAME $AUTH_MODE "${CREDENTIAL[$i]}" -r storage --command "reset" 
		echo "========================================================="
		echo "cleanup database "
		python tpcwtxmud_remote_setup.py -d ${TXM_DATABASE[$i]}  -u $USERNAME $AUTH_MODE "${CREDENTIAL[$i]}" --run "$CMD_DBCLEANUP"
		echo "========================================================="
		echo "restore database "
		python tpcwtxmud_remote_setup.py -d ${TXM_DATABASE[$i]}  -u $USERNAME $AUTH_MODE "${CREDENTIAL[$i]}" --run "$CMD_DBDEPLOY"
	done;
	echo "Databases are clean"
}
reset_nodes(){
	for((i=0;i<$DATABASENUM;i++)) do
		echo "========================================================="
		echo "shutown all components of the datacenter $i "
		python tpcwtxmud_remote_setup.py -d ${TXM_STORAGESHIM[$i]}  -u $USERNAME $AUTH_MODE "${CREDENTIAL[$i]}" -r mshim --command "reset" 
		python tpcwtxmud_remote_setup.py -d ${TXM_COORDINATOR[$i]}  -u $USERNAME $AUTH_MODE "${CREDENTIAL[$i]}" -r coordinator --command "reset" 
		python tpcwtxmud_remote_setup.py -d ${TXM_DATABASE[$i]}  -u $USERNAME $AUTH_MODE "${CREDENTIAL[$i]}" -r storage --command "reset" 
		python tpcwtxmud_remote_setup.py -d ${TXM_PROXY[$i]}  -u $USERNAME $AUTH_MODE "${CREDENTIAL[$i]}" -r proxy --command "reset" 
		python tpcwtxmud_remote_setup.py -d ${TXM_USER[$i]}  -u $USERNAME $AUTH_MODE "${CREDENTIAL[$i]}" -r user --command "reset"
	done;
	echo "========================================================="
	echo "all components are shutdown "
	
}

update_src(){
	for((i=0;i<$DATABASENUM;i++)) do
		echo "========================================================="
		echo "update all components of the datacenter $i "
		python tpcwtxmud_remote_setup.py -d ${TXM_STORAGESHIM[$i]}  -u $USERNAME $AUTH_MODE "${CREDENTIAL[$i]}" -r mshim --run "cd $TPCW_ROOT && svn up"
		python tpcwtxmud_remote_setup.py -d ${TXM_COORDINATOR[$i]}  -u $USERNAME $AUTH_MODE "${CREDENTIAL[$i]}" -r coordinator --run "cd $TPCW_ROOT && svn up"
		python tpcwtxmud_remote_setup.py -d ${TXM_PROXY[$i]}  -u $USERNAME $AUTH_MODE "${CREDENTIAL[$i]}" -r proxy --run "cd $TPCW_ROOT && svn up"
		python tpcwtxmud_remote_setup.py -d ${TXM_USER[$i]}  -u $USERNAME $AUTH_MODE "${CREDENTIAL[$i]}" -r user --run "cd $TPCW_ROOT && svn up"
	done;
}
start_users(){
	echo "Starting all users"
	for((i=0;i<$DATABASENUM;i++)) do
			python tpcwtxmud_remote_setup.py -d ${TXM_USER[$i]}  -u $USERNAME $AUTH_MODE "${CREDENTIAL[$i]}" -r user --run "${CMD_START_EXPERIMENT[$i]}" &
	done;
	echo "All users started at "`date +%d/%m/%y_%H:%M:%S`
}
start_tomcat(){
	for((i=0;i<$DATACENTERNUM;i++)) do
		python tpcwtxmud_remote_setup.py -d ${TXM_PROXY[$i]}  -u $USERNAME $AUTH_MODE "${CREDENTIAL[$i]}" -r proxy --run "cd $TPCW_ROOT && ant tomcat-start" 	
	done;
	sleep 10
}	
start_coordinator(){
	for((i=0;i<$DATACENTERNUM;i++)) do	
		python tpcwtxmud_remote_setup.py -d ${TXM_COORDINATOR[$i]}  -u $USERNAME $AUTH_MODE "${CREDENTIAL[$i]}" -r coordinator --runbg "nohup ${CMD_START_COORDINATOR[$i]}  &" 
	done;
}																		
start_storageshim(){
	for((i=0;i<$DATACENTERNUM;i++)) do	
			python tpcwtxmud_remote_setup.py -d ${TXM_STORAGESHIM[$i]}  -u $USERNAME $AUTH_MODE "${CREDENTIAL[$i]}" -r mshim --runbg "nohup ${CMD_START_STORAGESHIM[$i]} &"    
	done;
				
}

wait_for_storageshim(){
	for((i=0;i<$DATACENTERNUM;i++)) do	
			python tpcwtxmud_remote_setup.py -d ${TXM_STORAGESHIM[$i]}  -u $USERNAME $AUTH_MODE "${CREDENTIAL[$i]}" -r mshim --run "${CMD_WAIT_STORAGESHIM[$i]}"    
	done;
}
wait_users_to_finish(){
	for((i=0;i<$DATACENTERNUM;i++)) do	
			python tpcwtxmud_remote_setup.py -d ${TXM_USER[$i]}  -u $USERNAME $AUTH_MODE "${CREDENTIAL[$i]}" -r mshim --run "${CMD_WAIT_USERS[$i]}"    
	done;
}

start_mysql(){
	for((i=0;i<$DATABASENUM;i++)) do
		python tpcwtxmud_remote_setup.py -d ${TXM_DATABASE[$i]}  -u $USERNAME $AUTH_MODE "${CREDENTIAL[$i]}" -r storage --run "cd $TPCW_ROOT && ant mysql-start" 	
	done;				
}
#-----------------------------------------------------------------------------
#MAIN				

case $1 in 
	"install_all") 			install_all;;						
	"install_proxy") 			install_proxy;;
	"install_database") 			install_database;;
	"install_txmud") 			install_txmud;;
	"get")					get;;
	"configure") 			configure;;
	"database") 			populate_remote_database;;	
	"website") 				deploy_tpcw_website;;
	"start_tomcat") 		start_tomcat;;
	"start_mysql") 			start_mysql;;
	"start_user") 			start_users;;	
	"start_coordinator") 	start_coordinator;;	
	"start_storageshim")	start_storageshim;;
	"wait_for_storageshim") wait_for_storageshim;;
	"wait_for_users_to_finish") wait_users_to_finish;;
	"reset_database") 	reset_logical_clock;;
	"shutdown") 				reset_nodes;;
	"update") 				update_src;;
	"openfiles")			increase_files_all;;
	"isrunning") 			isrunning $2 $3;;
	*) 						help;;
esac
echo "Experiment finished!"
