#!/bin/sh
USERNAME="root"
#AUTH_MODE="-p"
#CREDENTIAL=""
AUTH_MODE="-k"
CREDENTIAL0="/home/dcfp/EU/tpcw-kf.pem" 
CREDENTIAL1="/home/dcfp/US/tpcw-kf.pem"

TPCW_DIR="/root/code/src/applications/tpc-w-fenix"
TXMUD_SRC="/root/code"
TPCW_BIN="/var/tmp/$USERNAME/output/tpcw/dist"
TXMUD_JARS="/var/tmp/$USERNAME/output/txmud/dist"

BACKEND="mysql"

####DATACENTER 0
TXM_DATABASE0="ec2-79-125-67-119.eu-west-1.compute.amazonaws.com"  
TXM_PROXY0="ec2-79-125-46-12.eu-west-1.compute.amazonaws.com"
TXM_USER0="ec2-46-137-45-214.eu-west-1.compute.amazonaws.com"
####DATACENTER 1
TXM_USER1="ec2-50-19-2-86.compute-1.amazonaws.com"

#force kill later
PIDU0=""
PIDU1=""

##update the configuration files accordingly
TOPOLOGYXMLFILENAME="tpcwtxmud_multidc.xml"
DATABASEXMLFILENAME="tpcwtxmud_multidcdb.xml"


DEPENDENCIES="$TPCW_DIR/tpcwtxmud_setup.sh deploy_dependencies"
EB=50
ITEM=10000
DATABASETGZ="mysql-5.5.15.zero.2db.lc0-0-0.50eb10kitem.tgz"
#atention, if you change the number of proxies it has to be different for each proxy
PREPARE0="cd $TPCW_DIR && ant clean dist -DdcId=0  -DproxyId=0 -Dtotaldc=1 -Dtotalproxy=1  -Dnum.eb=$EB -Dnum.item=$ITEM -Dlogicalclock=0-0 -Dbackend=$BACKEND -Dmysql_host=$TXM_DATABASE0 -Dmysql_port=53306 -Dtopologyfile=$TOPOLOGYXMLFILENAME"



#ATENTION - RESET LOGICAL CLOCK UNPACK THE ORIGINAL DATABASE -> TO MAKE SURE THEY ARE ALL EQUAL IN THE BEGINNING
#HERE WE POPULATE, MIGHT BE DIFFERENT -- CAREFUL 
POPULATE="$TPCW_DIR/tpcwtxmud_setup.sh populate $BACKEND localhost  53306 $EB $ITEM" 

IMAGES="cd $TPCW_DIR && ant genimg -Dnum.eb=$EB -Dnum.item=$ITEM"
INST="cd $TPCW_DIR && ant inst "
START_EXPERIMENT=""
if [ -n $2 ]
	then
	START_EXPERIMENT0="cd $TPCW_BIN && ./rbe.sh -w http://$TXM_PROXY0:8080/tpcw/ -b Mysql  -l 0 -u 60 -d 60 -i 300 -n $2"
else
	START_EXPERIMENT0="cd $TPCW_BIN && ./rbe.sh -w http://$TXM_PROXY0:8080/tpcw/ -b Mysql -l 0 -u 60 -d 60 -i 300 -n 100"	

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
	#dc0 
	#python tpcwtxmud_remote_setup.py -d $TXM_DATABASE0  -u $USERNAME $AUTH_MODE "$CREDENTIAL0" --run "$TPCW_DIR/tpcwtxmud_setup.sh install_proxy"
	#python tpcwtxmud_remote_setup.py -d $TXM_DATABASE0  -u $USERNAME $AUTH_MODE "$CREDENTIAL0" --run "$TPCW_DIR/tpcwtxmud_setup.sh install_database" 
	python tpcwtxmud_remote_setup.py -d $TXM_PROXY0  -u $USERNAME $AUTH_MODE "$CREDENTIAL0" --run "$TPCW_DIR/tpcwtxmud_setup.sh install_proxy"
	#python tpcwtxmud_remote_setup.py -d $TXM_USER0  -u $USERNAME $AUTH_MODE "$CREDENTIAL0" --run "$TPCW_DIR/tpcwtxmud_setup.sh install_proxy"
	#python tpcwtxmud_remote_setup.py -d $TXM_COORDINATOR0  -u $USERNAME $AUTH_MODE "$CREDENTIAL0" --run "$DEPENDENCIES"
	#python tpcwtxmud_remote_setup.py -d $TXM_STORAGESHIM0 -u $USERNAME $AUTH_MODE "$CREDENTIAL0" --run "$DEPENDENCIES"
	#dc1 
	#python tpcwtxmud_remote_setup.py -d $TXM_DATABASE1  -u $USERNAME $AUTH_MODE "$CREDENTIAL1" --run "$TPCW_DIR/tpcwtxmud_setup.sh install_proxy"
	#python tpcwtxmud_remote_setup.py -d $TXM_DATABASE1  -u $USERNAME $AUTH_MODE "$CREDENTIAL1" --run "$TPCW_DIR/tpcwtxmud_setup.sh install_database" 
	python tpcwtxmud_remote_setup.py -d $TXM_PROXY1  -u $USERNAME $AUTH_MODE "$CREDENTIAL1" --run "$TPCW_DIR/tpcwtxmud_setup.sh install_proxy"
	#python tpcwtxmud_remote_setup.py -d $TXM_USER1  -u $USERNAME $AUTH_MODE "$CREDENTIAL1" --run "$TPCW_DIR/tpcwtxmud_setup.sh install_proxy"
	#python tpcwtxmud_remote_setup.py -d $TXM_COORDINATOR1  -u $USERNAME $AUTH_MODE "$CREDENTIAL1" --run "$DEPENDENCIES"
	#python tpcwtxmud_remote_setup.py -d $TXM_STORAGESHIM1  -u $USERNAME $AUTH_MODE "$CREDENTIAL1" --run "$DEPENDENCIES"
	
	
elif [ $1 = "get" ];	
	then 
	local_results0="results_${TXM_USER0}_dc0"
	local_results1="results_${TXM_USER1}_dc1"
	mkdir -p $local_results0
	mkdir -p $local_results1
	#dc0
	scp -i ${CREDENTIAL0} -C -r ${USERNAME}"@"${TXM_USER0}":"${TPCW_BIN}"/results/*" ${local_results0}
	#scp -i ${CREDENTIAL0} -C -r ${USERNAME}"@"${TXM_COORDINATOR0}":/tmp/c0.out" ${local_results0}
	#scp -i ${CREDENTIAL0} -C -r ${USERNAME}"@"${TXM_STORAGESHIM0}":/tmp/s0.out" ${local_results0}
	#dc1
	scp -i ${CREDENTIAL1} -C -r ${USERNAME}"@"${TXM_USER1}":"${TPCW_BIN}"/results/*" ${local_results1}
	#scp -i ${CREDENTIAL1} -C -r ${USERNAME}"@"${TXM_COORDINATOR1}":/tmp/c1.out" ${local_results1}
	#scp -i ${CREDENTIAL1} -C -r ${USERNAME}"@"${TXM_STORAGESHIM1}":/tmp/s1.out" ${local_results1}
	
elif [ $1 = "configure" ]; #prepare all nodes with experiment parameters
	then
	# scp the topology and database files
	echo "updating configuration files"
	#dc0
	scp -i ${CREDENTIAL0} $TOPOLOGYXMLFILENAME  $DATABASEXMLFILENAME ${USERNAME}"@"${TXM_USER0}":"${TPCW_DIR}  
	scp -i ${CREDENTIAL0} $TOPOLOGYXMLFILENAME  $DATABASEXMLFILENAME ${USERNAME}"@"${TXM_DATABASE0}":"${TPCW_DIR} 
	scp -i ${CREDENTIAL0} $TOPOLOGYXMLFILENAME  $DATABASEXMLFILENAME ${USERNAME}"@"${TXM_PROXY0}":"${TPCW_DIR} 
	#dc1
	scp -i ${CREDENTIAL1} $TOPOLOGYXMLFILENAME  $DATABASEXMLFILENAME ${USERNAME}"@"${TXM_USER1}":"${TPCW_DIR}  
	
	echo "recompile source code"
	#dc0
	python tpcwtxmud_remote_setup.py -d $TXM_DATABASE0  -u $USERNAME $AUTH_MODE "$CREDENTIAL0" --run "$PREPARE0"
	python tpcwtxmud_remote_setup.py -d $TXM_USER0  -u $USERNAME $AUTH_MODE "$CREDENTIAL0" --run "$PREPARE0"
	python tpcwtxmud_remote_setup.py -d $TXM_PROXY0  -u $USERNAME $AUTH_MODE "$CREDENTIAL0" --run "$PREPARE0"
	#dc1
	python tpcwtxmud_remote_setup.py -d $TXM_USER1  -u $USERNAME $AUTH_MODE "$CREDENTIAL1" --run "$PREPARE0"

	
	
elif [ $1 = "database" ]; #populate database
	then	
	python tpcwtxmud_remote_setup.py -d $TXM_DATABASE0  -u $USERNAME $AUTH_MODE "$CREDENTIAL0" --run "$POPULATE" 


elif [ $1 = "website" ]; #tpcw tomcat
	then
	#DC0
	python tpcwtxmud_remote_setup.py -d $TXM_PROXY0  -u $USERNAME $AUTH_MODE "$CREDENTIAL0" --run "$DEPENDENCIES"
	#python tpcwtxmud_remote_setup.py -d $TXM_PROXY0  -u $USERNAME $AUTH_MODE "$CREDENTIAL0" --run "$IMAGES"
	python tpcwtxmud_remote_setup.py -d $TXM_PROXY0  -u $USERNAME $AUTH_MODE "$CREDENTIAL0" --run "$INST"
	
elif [ $1 = "tomcat_start" ];
	then
	python tpcwtxmud_remote_setup.py -d $TXM_PROXY0  -u $USERNAME $AUTH_MODE "$CREDENTIAL0" -r proxy --run "cd $TPCW_DIR && ant tomcat-start"
	
elif [ $1 = "mysql_start" ];
	then	
	python tpcwtxmud_remote_setup.py -d $TXM_DATABASE0  -u $USERNAME $AUTH_MODE "$CREDENTIAL0" -r storage --run "cd $TPCW_DIR && ant mysql-start"

elif [ $1 = "user_start" ];
	then	
	python tpcwtxmud_remote_setup.py -d $TXM_USER0  -u $USERNAME $AUTH_MODE "$CREDENTIAL0" -r user --run "$START_EXPERIMENT0" &
	PIDU0=$!
	python tpcwtxmud_remote_setup.py -d $TXM_USER1  -u $USERNAME $AUTH_MODE "$CREDENTIAL1" -r user --run "$START_EXPERIMENT0" 
	PIDU1=$!
elif [ $1 = "mysql_reset_clock" ];
	then	
	#DECOMPRESS DE ORIGNAL DATABASE INSTEAD OF CLEAN UP THE STRUCTURES. - > ENSURE THEY ARE EQUAL
	DBCLEANUP="rm -rf /tmp/mysql.sock /var/tmp/$USERNAME/mysql-5.5.15 && echo 'done'"
	DBDEPLOY="cd /var/tmp/$USERNAME && tar xzf $DATABASETGZ && echo 'done'"
	python tpcwtxmud_remote_setup.py -d $TXM_DATABASE0  -u $USERNAME $AUTH_MODE "$CREDENTIAL0" -r storage --command "reset" 
	python tpcwtxmud_remote_setup.py -d $TXM_DATABASE1  -u $USERNAME $AUTH_MODE "$CREDENTIAL1" -r storage --command "reset" 
	echo "========================================================="
	echo "cleanup database "
	echo "========================================================="
	python tpcwtxmud_remote_setup.py -d $TXM_DATABASE0  -u $USERNAME $AUTH_MODE "$CREDENTIAL0" --run "$DBCLEANUP"
	echo "========================================================="
	echo "restore database "
	echo "========================================================="
	python tpcwtxmud_remote_setup.py -d $TXM_DATABASE0  -u $USERNAME $AUTH_MODE "$CREDENTIAL0" --run "$DBDEPLOY"
	
elif [ $1 = "reset" ];
	then
	#dc0
	python tpcwtxmud_remote_setup.py -d $TXM_DATABASE0  -u $USERNAME $AUTH_MODE "$CREDENTIAL0" -r storage --command "reset" 
	python tpcwtxmud_remote_setup.py -d $TXM_PROXY0  -u $USERNAME $AUTH_MODE "$CREDENTIAL0" -r proxy --command "reset" 
	python tpcwtxmud_remote_setup.py -d $TXM_USER0  -u $USERNAME $AUTH_MODE "$CREDENTIAL0" -r user --command "reset" 
	
	
elif [ $1 = "update" ];
	then
	#dc0
	python tpcwtxmud_remote_setup.py -d $TXM_DATABASE0  -u $USERNAME $AUTH_MODE "$CREDENTIAL0" -r storage --run "cd $TPCW_DIR && svn up"
	python tpcwtxmud_remote_setup.py -d $TXM_PROXY0  -u $USERNAME $AUTH_MODE "$CREDENTIAL0" -r proxy --run "cd $TPCW_DIR && svn up"
	python tpcwtxmud_remote_setup.py -d $TXM_USER0  -u $USERNAME $AUTH_MODE "$CREDENTIAL0" -r user --run "cd $TPCW_DIR && svn up"
	python tpcwtxmud_remote_setup.py -d $TXM_USER1  -u $USERNAME $AUTH_MODE "$CREDENTIAL1" -r user --run "cd $TPCW_DIR && svn up"
	
else [ -n $1 ] || [ $1 = "-h" ] || [ $1 = "h" ] || [ $1 = "--help" ];
	help
fi



echo "done"
