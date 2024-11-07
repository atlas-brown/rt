##############################################################################
# rbe.sh to run the RBE from TPC-W Java Implementation.
# 2003 by Jan Kiefer.
#
# This file is distributed "as is". It comes with no warranty and the 
# author takes no responsibility for the consequences of its use.
#
# Usage, distribution and modification is allowed to everyone, as long 
# as reference to the author is given and this license note is included.
##############################################################################

#!/bin/sh

USER=dcfp
LOCAL_DIR=$PWD

TOMCAT_HOME=/var/tmp/$USER/txmud/tomcat6
TOMCAT_LIB=$TOMCAT_HOME/lib
TOMCAT_MEM=4G
TOMCAT_HOST=localhost

MYSQL_ROOT_PASS=101010
MYSQL_HOST=localhost
MYSQL_PORT=53306
MYSQL_PATH=/var/tmp/$USER/mysql-5.5.15/bin/
MYSQL_ROOT=/var/tmp/$USER/mysql-5.5.15
MYSQL_CMD="${MYSQL_PATH}mysql --defaults-file=${MYSQL_ROOT}/mysql-test/include/default_mysqld.cnf -h $MYSQL_HOST --port=$MYSQL_PORT -u root --password=$MYSQL_ROOT_PASS"

TPCW_DATABASE=$MYSQL_HOST:$MYSQL_PORT
#TPCW_SRC=/root/code/src/applications/tpc-w-fenix
TPCW_SRC=/home/dcfp/workspace/txmud_spd/src/applications/tpc-w-fenix
TXMUD_DEFAULT_LOGICAL_CLOCK=0-0
TXMUD_LIBPATH=/var/tmp/$USER/output/txmud/dist/jars
TXMUD_SRC=/home/dcfp/workspace/txmud_spd
##########################################################################
# Databases
##########################################################################
# scratchpad
function deploy_txmud_components(){
	mkdir -p /var/tmp/$USER/txmud/tomcat6/lib
	echo "cleanup old tomcat libraries "
	rm -f  $TOMCAT_LIB/jsqlparser.jar	$TOMCAT_LIB/netty-3.2.1.Final.jar	$TOMCAT_LIB/log4j-1.2.15.jar 
	echo "Compiling scratchpad driver"
	PDIR=`pwd`
	cd $TXMUD_SRC && ant clean dist
	echo "Deploying jdbc driver and dependencies to tomcat library path"
	cp $TXMUD_LIBPATH/jdbctxmud.jar $TOMCAT_LIB
	cp lib/jsqlparser.jar $TOMCAT_LIB
	cp lib/netty-3.2.1.Final.jar $TOMCAT_LIB
	cp lib/log4j-1.2.15.jar $TOMCAT_LIB
	cd $PDIR
	echo "Done"
	echo "----------------------------"
	
}
# coordinator


#------------------------------------------------------------------------
# JDBC Driver
#------------------------------------------------------------------------
function deploy_mysql_driver(){
	echo "------------------------------------------------------------"
	echo "Downloading mysql jdbc driver"
	wget -P /var/tmp/$USER -c http://ftp.gwdg.de/pub/misc/mysql/Downloads/Connector-J/mysql-connector-java-5.1.17.zip
	echo "Done"
	echo "----------------------------"
	echo "Deploying mysql driver on tomcat lib dir "
	mkdir -p $TOMCAT_LIB
	DIR_=`pwd`
	cd /var/tmp/$USER && unzip mysql-connector-java-5.1.17.zip > /dev/null
	cp /var/tmp/$USER/mysql-connector-java-5.1.17/mysql-connector-java-5.1.17-bin.jar $TOMCAT_LIB
	cp /var/tmp/$USER/mysql-connector-java-5.1.17/mysql-connector-java-5.1.17-bin.jar /tmp
	rm -rf /var/tmp/$USER/mysql-connector-java-5.1.17
	cd $DIR_
	echo "Done"
	echo "----------------------------"
}



#------------------------------------------------------------------------
# Mysql 5.5.15
#------------------------------------------------------------------------
function deploy_storage(){
	undeploy_storage;
	echo "Downloading mysql"
	wget -P /var/tmp/$USER -c http://vesta.informatik.rwth-aachen.de/mysql/Downloads/MySQL-5.5/mysql-5.5.15.tar.gz
	CURR_DIR=`pwd`
	echo "Unpacking mysql source"
	tar xzvf /var/tmp/$USER/mysql-5.5.15.tar.gz   -C /var/tmp/$USER/output > /dev/null
	echo "Configuring  mysql source"
cd /var/tmp/$USER/output/mysql-5.5.15 && cmake -DCMAKE_INSTALL_PREFIX=${MYSQL_ROOT} -DMYSQL_DATADIR=${MYSQL_ROOT}/data -DWITH_DEBUG=ON > /tmp/mysql-install.output 
	
	echo "Compiling mysql"
	make -j5 > /dev/null
	
	echo "Installing mysql at ${MYSQL_PATH}../"	
	make install > /dev/null
	echo "Initializing mysql internal database"
	cd ${MYSQL_ROOT} && scripts/mysql_install_db --defaults-file=${MYSQL_ROOT}/mysql-test/include/default_mysqld.cnf \
												    --basedir=${MYSQL_ROOT} \
												    --datadir=${MYSQL_ROOT}/data \
												    --user=$USER

												    
	echo "Starting mysql server"
	start_database;
	
	echo "wait while server wakes up"
	sleep 10
	echo "run mysql client to configure database access"
	sleep 2
	${MYSQL_ROOT}/bin/mysqladmin --defaults-file=${MYSQL_ROOT}/mysql-test/include/default_mysqld.cnf -u root password '101010';
	echo ""	
	${MYSQL_ROOT}/bin/mysql --defaults-file=${MYSQL_ROOT}/mysql-test/include/default_mysqld.cnf \
					   -u root --password='101010' -e	"grant all on *.* to root@'%' identified by '101010' with grant option"
	echo ""
	sleep 2
	${MYSQL_ROOT}/bin/mysqladmin --defaults-file=${MYSQL_ROOT}/mysql-test/include/default_mysqld.cnf -u root --password='101010' flush-privileges;
	echo "database deployed, TRY IT!:";
	echo ${MYSQL_ROOT}/bin/mysql --defaults-file=${MYSQL_ROOT}/mysql-test/include/default_mysqld.cnf -u root --password='101010' 
	#echo ${MYSQL_ROOT}/bin/mysql --defaults-file=${MYSQL_ROOT}/support-files/my-huge.cnf -u root --password='101010' 
	cd $CURR_DIR
	exit 0
}

function undeploy_storage(){
	stop_database;
	rm -rf /var/tmp/$USER/mysql-5.5.15
}

function start_database(){
	DIR_=`pwd`
	cd $TPCW_SRC && ant mysql-start
							
	#	cd ${MYSQL_ROOT}/bin && ./mysqld_safe --defaults-file=${MYSQL_ROOT}/mysql-test/include/default_mysqld.cnf --port=$MYSQL_PORT \
	#						--max_connections=10000 --max_user_connections=10000 --innodb_buffer_pool_size=2G \
	 						#--innodb_flush_method=O_DIRECT --skip-innodb_doublewrite --innodb_flush_log_at_trx_commit=0 \
							#--query_cache_size=512M --innodb_thread_concurrency=12 --innodb_file_per_table &
	cd $DIR_
echo ""
echo ""

#original
#${MYSQL_ROOT}/bin/mysqld_safe --defaults-file=${MYSQL_ROOT}/mysql-test/include/default_mysqld.cnf --port=$MYSQL_PORT \
#	 						--innodb_lock_wait_timeout=1 --max_connections=10000 --innodb_buffer_pool_size=1503238553 \
#	 						--innodb_flush_method=O_DIRECT --skip-innodb_doublewrite --innodb_flush_log_at_trx_commit=0 \
#							--query_cache_size=256M &
#

}
function stop_database(){
	killall -9 mysqld mysqld_safe
	rm /tmp/mysql.sock
}

#------------------------------------------------------------------------
# Database schemas
#------------------------------------------------------------------------
function setupDB_Test() {
	echo "------------------------------------------------------------"
	echo "Setting up tpcw test database"
	#echo $MYSQL_CMD  -e "drop database if exists testtpcw"; 
	#echo $MYSQL_CMD  -e "create database testtpcw"; 
	#echo $MYSQL_CMD  -e "grant all on testtpcw.* to sa@'%'"; 
	#echo $MYSQL_CMD  -e "grant all on testtpcw.* to sa"; 
	
	$MYSQL_CMD  -e "drop database if exists testtpcw";
	$MYSQL_CMD  -e "create database testtpcw";
	$MYSQL_CMD  -e "grant all on testtpcw.* to sa@'%'";
	$MYSQL_CMD  -e "grant all on testtpcw.* to sa@'localhost'";
	$MYSQL_CMD  -e "grant all on testtpcw.* to sa";
}
function setupDB_mysql_baseline() {
	echo "------------------------------------------------------------"
	echo "Setting up mysql_std database"
	$MYSQL_CMD  -e "drop database if exists mysql_std";
	$MYSQL_CMD  -e "create database mysql_std";
	$MYSQL_CMD  -e "grant all on mysql_std.* to sa@'%'";
	$MYSQL_CMD  -e "grant all on testtpcw.* to sa@'localhost'";
	$MYSQL_CMD  -e "grant all on mysql_std.* to sa";
}
function setupDB_mysql_spd_bypass() {
	echo "------------------------------------------------------------"
	echo "Setting up mysql_spd_bypass database"
	$MYSQL_CMD  -e "drop database if exists mysql_spd_bypass";
	$MYSQL_CMD  -e "create database mysql_spd_bypass";
	$MYSQL_CMD  -e "grant all on mysql_spd_bypass.* to sa@'%'";
	$MYSQL_CMD  -e "grant all on mysql_spd_bypass.* to sa@'localhost'";
	$MYSQL_CMD  -e "grant all on mysql_spd_bypass.* to sa";
}
function setupDB_mysql_redblue_semantics() {
	echo "------------------------------------------------------------"
	echo "Setting up mysql_redblue_semantics database"
	$MYSQL_CMD  -e "drop database if exists mysql_redblue_semantics";
	$MYSQL_CMD  -e "create database mysql_redblue_semantics";
	$MYSQL_CMD  -e "grant all on mysql_redblue_semantics.* to sa@'%'";
	$MYSQL_CMD  -e "grant all on mysql_redblue_semantics.* to sa@'localhost'";
	$MYSQL_CMD  -e "grant all on mysql_redblue_semantics.* to sa";
}
function tpcw_create_databases() {
	setupDB_Test;
	setupDB_mysql_baseline;
	setupDB_mysql_spd_bypass;
	setupDB_mysql_redblue_semantics;
}
#------------------------------------------------------------------------
# Populate data
#-----------------------------------------------------------------------
function tpcw_populate_database(){
echo "------------------------------------------------------------"
	ANT_CMD=""
	if [ -z $1 -o -z $2 -o -z $3 -o -z $4 -o -z $5 ];
	then
		echo "you have to define the target database to populate: txmud, mysql or scratchpad and the endpoint of the database users and items"
		echo "a valid list of parameters: populate txmud localhost 53306 10 1000"
		exit 0;
	else
		ANT_CMD="$ANT_CMD -Dbackend=$1 -Dmysql_host=$2 -Dmysql_port=$3 -Dnum.eb=$4 -Dnum.item=$5"
	fi
	tpcw_create_databases;
	
	echo "ant command: ant clean gendb $ANT_CMD"
	DIR=`pwd`
	cd $TPCW_SRC && ant clean gendb $ANT_CMD 
	cd $DIR
	echo "Done"
	echo "----------------------------"
		
}
function tpcw_reset_logicalclock(){
echo "------------------------------------------------------------"
	echo "cleanup scratchpad tables"
	$MYSQL_CMD  mysql_redblue_semantics -e "drop table if exists SCRATCHPAD_ID"
	$MYSQL_CMD  mysql_redblue_semantics -e "drop table if exists SCRATCHPAD_TRX"
	echo "stop the database to clean up temp tables"	
	stop_database;
	echo "restarting the database"
	sleep 5
	start_database;
	sleep 10
	echo "cleanup scratchpad tables"
	$MYSQL_CMD  mysql_redblue_semantics -e "drop table if exists SCRATCHPAD_ID"
	$MYSQL_CMD  mysql_redblue_semantics -e "drop table if exists SCRATCHPAD_TRX"
	
	echo "reset logical clock for table address"
	$MYSQL_CMD  mysql_redblue_semantics -e "update address set 	_SP_del=false,_SP_ts=0,_SP_clock='$TXMUD_DEFAULT_LOGICAL_CLOCK'"
	echo "reset logical clock for table author"
	$MYSQL_CMD  mysql_redblue_semantics -e "update author set 	_SP_del=false,_SP_ts=0,_SP_clock='$TXMUD_DEFAULT_LOGICAL_CLOCK'"
	echo "reset logical clock for table cc_xacts"
	$MYSQL_CMD  mysql_redblue_semantics -e "update cc_xacts set 	_SP_del=false,_SP_ts=0,_SP_clock='$TXMUD_DEFAULT_LOGICAL_CLOCK'"
	echo "reset logical clock for table country"
	$MYSQL_CMD  mysql_redblue_semantics -e "update country set 	_SP_del=false,_SP_ts=0,_SP_clock='$TXMUD_DEFAULT_LOGICAL_CLOCK'"
	echo "reset logical clock for table customer"
	$MYSQL_CMD  mysql_redblue_semantics -e "update customer set 	_SP_del=false,_SP_ts=0,_SP_clock='$TXMUD_DEFAULT_LOGICAL_CLOCK'"
	echo "reset logical clock for table item"
	$MYSQL_CMD  mysql_redblue_semantics -e "update item set 	_SP_del=false,_SP_ts=0,_SP_clock='$TXMUD_DEFAULT_LOGICAL_CLOCK'"
	echo "reset logical clock for table order_line"
	$MYSQL_CMD  mysql_redblue_semantics -e "update order_line set 	_SP_del=false,_SP_ts=0,_SP_clock='$TXMUD_DEFAULT_LOGICAL_CLOCK'"
	echo "reset logical clock for table orders"
	$MYSQL_CMD  mysql_redblue_semantics -e "update orders set 	_SP_del=false,_SP_ts=0,_SP_clock='$TXMUD_DEFAULT_LOGICAL_CLOCK'"
	echo "reset logical clock for table shopping_cart"
	$MYSQL_CMD  mysql_redblue_semantics -e "update shopping_cart set 	_SP_del=false,_SP_ts=0,_SP_clock='$TXMUD_DEFAULT_LOGICAL_CLOCK'"
	echo "reset logical clock for table shopping_cart_line"
	$MYSQL_CMD  mysql_redblue_semantics -e "update shopping_cart_line set 	_SP_del=false,_SP_ts=0,_SP_clock='$TXMUD_DEFAULT_LOGICAL_CLOCK'"
	echo "Done"
	echo "----------------------------"
}

##########################################################################
# WebProxy - Tomcat
#########################################################################
function deploy_dependencies(){
	deploy_mysql_driver;
	deploy_txmud_components;
	}
function deploy_webproxy(){
	echo "------------------------------------------------------------"
	undeploy_webproxy;
	mkdir -p /var/tmp/$USER/txmud/
	echo "Done"
	echo "----------------------------"
	echo "Downloading Tomcat6"
	wget -P /var/tmp/$USER -c http://www.bitlib.net/mirror/apache.org/tomcat/tomcat-6/v6.0.33/bin/apache-tomcat-6.0.33.tar.gz
	echo "Done"
	echo "----------------------------"
	echo "Installing Tomcat6"
	tar xzvf /var/tmp/$USER/apache-tomcat-6.0.33.tar.gz -C /var/tmp/$USER/txmud/  > /dev/null
	mv /var/tmp/$USER/txmud/apache-tomcat-6.0.33 /var/tmp/$USER/txmud/tomcat6
	echo "Done"
	deploy_dependencies;
	tune_tomcat;
	echo "----------------------------"
}
function undeploy_webproxy(){
	echo "Cleanup previous Tomcat6 installation"
	webproxy_shutdown;
	rm -rf /var/tmp/$USER/txmud/tomcat6
	echo "Done"
}	
	
function webproxy_shutdown(){
	DIR=`pwd`
	echo "ant command: ant tomcat-stop"
	cd $TPCW_SRC && ant tomcat-stop
	cd $DIR
	echo "Done"
	echo "----------------------------" 
}
function webproxy_startup(){ 
	DIR=`pwd`
	echo "ant command: ant tomcat-start"
	cd $TPCW_SRC && ant tomcat-start
	cd $DIR
	echo "Done"
	echo "----------------------------"
}
function tune_tomcat(){
	echo "Tunning tomcat server"
	sed  -i "2s/^/JAVA_OPTS=\"\$JAVA_OPTS -Xms${TOMCAT_MEM}\"/" /var/tmp/$USER/txmud/tomcat6/bin/catalina.sh
	sed -i  "/<Connector port=\"8080\" protocol=\"HTTP\/1\.1\"/{p;s/.*/maxThreads=\"10000\" minSpareThreads=\"200\"/;}"   /var/tmp/$USER/txmud/tomcat6/conf/server.xml
	echo "Done"connections
}

function deploy_loadbalacer(){

wget http://apache.mirror.iphh.net//httpd/httpd-2.2.20.tar.gz
tar xzvf httpd-2.2.20.tar.gz
cd httpd-2.2.20
./configure --prefix=/var/tmp/dcfp/apache2.2 --enable-mods-shared=all --enable-proxy --enable-proxy-connect --enable-proxy-balancer --enable-proxy-http --enable-proxy-scgi --enable-proxy-ajp --with-port=8000
make -j5
make install

cat >> /var/tmp/dcfp/apache2.2/conf/httpd-ajp.conf << EOF
<Location /balancer-manager>
        SetHandler balancer-manager
</Location>

<Proxy balancer://ajpCluster>
        BalancerMember ajp://thor41:8009 route=s1
        BalancerMember ajp://thor42:8009 route=s2
</Proxy>
<Location /tpcw>
        ProxyPass balancer://ajpCluster/tpcw stickysession=JSESSIONID
</Location>
EOF




}


##########################################################################
# TPCW - Application
#########################################################################
function deployTPCW(){
	echo "------------------------------------------------------------"
	echo "Deploying TPCW (The database is not included - scr files kept intact)"
	rm -rf /var/tmp/$USER/txmud/tomcat6/webapps/tpcw /var/tmp/$USER/txmud/tomcat6/webapps/tpcw.war
	echo `pwd`
	cd $TPCW_SRC && ant inst
	cd ../..
	echo "Done"
	echo "----------------------------"
	
}

function redeployTPCW(){
	echo "------------------------------------------------------------"
	echo "Redeploying the last configuration (src files wont be regenerated neigther the image files will be copied"
	webproxy_shutdown;
	echo "killing java"	
	killall -9 java
	echo "" > /var/tmp/$USER/txmud/tomcat6/logs/catalina.out
	echo "install new tpcw website"
	cd $TPCW_SRC && ant inst
	cd ../..
	#echo "reinstall scratchpad"
	#deploy_txmud_components;
	echo "Done"
	echo "----------------------------"
	webproxy_startup;
	#echo "Redeploying images directory"
	#sleep 15
	#cd $TPCW_SRC && ant instimg
	#cd ../..
	echo "check the deplyment at: tail -f /var/tmp/$USER/txmud/tomcat6/logs/catalina.out"  
}	
function tpcw_cleanup(){
	echo "------------------------------------------------------------"
	echo "Cleanup TPCW (The image files and the database are not included)"
	cd $TPCW_SRC && ant clean
	cd ../..
	echo "Done"
	echo "----------------------------"
	
	
}

function tpcw_generate_images(){
echo "------------------------------------------------------------"
	echo "Generating tpcw images (use redeploy to install them on the application server)"
	ANT_CMD=""
	if [ -n $1 ];
	then
		ANT_CMD="$ANT_CMD $1 "
	fi
		
	DIR=`pwd`
	echo "ant command: ant genimg $ANT_CMD"
	cd $TPCW_SRC && ant genimg $ANT_CMD
	cd $DIR
	echo "Done"
	echo "----------------------------"
}


function execTPCW(){
	chmod +x $TPCW_SRC/dist/rbe.sh
	echo "cd $TPCW_SRC/dist/"
}



# this fuction has the database name as a parameter
function deploy_tpcwapp(){
	echo "----------------------------------------------------------------------------------------"
	echo "Configuring tpcw parameters (users=${TPCW_USERS} and items=${TPCW_ITEMS})"
	ANT_CMD=""

	deploy_txmud_components;
	deploy_mysql_driver;

	STR=$1
	dcId=$2
	proxyId=$3

	if [ -n $2 ];
	then
		ANT_CMD="$ANT_CMD -DdcId=$2 "
	fi
    
    if [ -n $3 ];
	then
		ANT_CMD="$ANT_CMD -DproxyId=$3"
	fi

	ANT_CMD="$ANT_CMD -Dnum.eb=${TPCW_USERS} "
	ANT_CMD="$ANT_CMD -Dnum.items=${TPCW_ITEMS} "
	ANT_CMD="$ANT_CMD -Dlogicalclock=${TXMUD_DEFAULT_LOGICAL_CLOCK} "
	ANT_CMD="$ANT_CMD -Dbackend=${STR} "
	
	if [ -n $4 ];
	then
		ANT_CMD="$ANT_CMD $4 "
	fi 
		
	echo "ant command: clean inst  $ANT_CMD"	
	cd $TPCW_SRC && ant clean inst $ANT_CMD
	cd ../..
	echo "Done"
}


function deploy_tpcw_test(){
	deploy_txmud_components;
	deploy_mysql_driver;
	setupDB_Test;
	#mysql database extracted from a tpcw populated database (without scratchpad table created!): mysqldump -n -t -u root tpcwdb_mysql_scratchpad > tpcwbackup.sql
	echo "Download testing workload"
	wget -c www.mpi-sws.org/~dcfp/tpcwbackup.sql
	echo "Done"
	echo "Initialize database testtpcw (you must create a database called testtpcw and a grant full access to an user 'sa' without password)"
	#echo "java -cp    .:../lib/jsqlparser.jar:../lib/netty-3.2.1.Final.jar:../lib/log4j-1.2.15.jar:$TOMCAT_HOME/lib/mysql-connector-java-5.1.17-bin.jar txstore.scratchpad.rdbms.tests.InitTPCW tpcwbackup.sql"
	DIR=`pwd`
	cd ../build
	java -cp    .:../lib/jsqlparser.jar:../lib/netty-3.2.1.Final.jar:../lib/log4j-1.2.15.jar:$TOMCAT_HOME/lib/mysql-connector-java-5.1.17-bin.jar txstore.scratchpad.rdbms.tests.InitTPCW tpcwbackup.sql 
	echo "run the following command to execute the test..."
	
	echo "java -cp    .:../lib/jsqlparser.jar:../lib/netty-3.2.1.Final.jar:../lib/mysql-connector-java-5.1.17-bin.jar txstore.scratchpad.rdbms.tests.TestTPCW"
	cd $DIR
}


##########################################################################
# main
##########################################################################


#full applications
if [ $1 = "mysql" ] || [ $1 = "scratchpad" ] || [ $1 = "txmud" ];
	then deploy_tpcwapp "$1" "$2" "$3" "$4";

elif [ $1 = "tpcw_test" ]
	then deploy_tpcw_test;

elif [ $1 = "cleanup" ]
	then tpcw_cleanup;
	for i in `find ./ | grep .class | grep -v svn  | grep -v classpath`; do rm $i; done;
	rm $TPCW_SRC/jdbctxmud.jar
	rm txmud_coordinator.jar
	rm txmud_storageshim.jar

elif [ $1 = "redeploy" ]
	then redeployTPCW;
elif [ $1 = "images" ]
	then tpcw_generate_images $2;
#==================================
#infrastructure
#==================================		
elif [ $1 = "install_proxy" ]
	then 
		deploy_webproxy;
elif [ $1 = "uninstall_proxy" ]
	then 
		undeploy_webproxy;
elif [ $1 = "start_proxy" ]
	then 
		webproxy_startup;
elif [ $1 = "stop_proxy" ]
	then 
		webproxy_shutdown;
		
elif [ $1 = "txmud_components" ]
	then 
		deploy_txmud_components;
	
#-------------------------------		
elif [ $1 = "install_database" ]
	then
		deploy_storage;
elif [ $1 = "uninstall_database" ]
	then
		undeploy_storage;
elif [ $1 = "populate" ]
	then 
		tpcw_populate_database $2 $3 $4 $5 $6;
elif [ $1 = "start_database" ]
	then 
		start_database;
		echo "database started, TRY IT!:";
		echo ${MYSQL_ROOT}/bin/mysql --defaults-file=${MYSQL_ROOT}/mysql-test/include/default_mysqld.cnf -u root --password='101010' 
		#echo ${MYSQL_ROOT}/bin/mysql --defaults-file=${MYSQL_ROOT}/support-files/my-huge.cnf -u root --password='101010' 

elif [ $1 = "stop_database" ]
	then
		stop_database;
elif [ $1 = "reset_lc" ]
	then
		tpcw_reset_logicalclock;
		
elif [ $1 = "deploy_dependencies" ]
	then
		deploy_dependencies;
#-------------------------------
elif [ $1 = "client" ]
	then 
	cd $TPCW_SRC && ant  clean dist ;
	cd ../.. ;
#-------------------------------		
else
	echo "allowed parameters:"
	echo "TPCW configuration"
	echo "mysql - redeploy  tpcw website with the bypass scratchpad driver"
	echo "scratchpad -redeploy  tpcw website with the redblue semantics driver (implementing the reconciliation procedures for red operations)"
	echo "txmud - redeploy  tpcw website with original source code"
	echo "txmud_components - redeploy  tpcw website with original source code"
	echo ""
	echo "Proxy configuration"
	echo "install_proxy - install tomcat"
	echo "uninstall_proxy - remove tomcat"
	echo "start_proxy - install tomcat"
	echo "stop_proxy - remove tomcat"
	echo ""
	echo "Database configuration"
	echo "populate_database - run in the same host where the database is installed. deploy"
	echo "install_database - install mysql"
	echo "uninstall_database - remove mysql"
	echo "stop_database - stop mysql"
	echo "start_database - start mysql"
	echo ""
	echo "general usage: (change the parameters inside the $0 arg)"
	echo "	 $0 install_database"
	echo "	 $0 install_proxy"
	echo "   $0 cleanup"
	echo "	 $0 tpcw_mysql  or redeploy"
	echo "	 $0 populate_database"
	echo "	 $0 images"
	echo "	 $0 start_proxy"
fi

