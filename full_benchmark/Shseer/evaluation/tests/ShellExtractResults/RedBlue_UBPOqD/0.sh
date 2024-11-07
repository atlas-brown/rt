#!/bin/bash
USER=dcfp
LOCAL_DIR=$PWD
TOMCAT_HOME=/var/tmp/$USER/txmud/tomcat6
TOMCAT_LIB=$TOMCAT_HOME/lib
MYSQL_ROOT_PASS=101010
TPCW_USERS=1000
TPCW_ITEMS=1000
MYSQL_HOST=thor40
TOMCAT_HOST=thor41
MYSQL_PORT=53306
TPCW_DATABASE=$MYSQL_HOST:$MYSQL_PORT
MYSQL_PATH=/var/tmp/$USER/mysql-5.5.15/bin/
MYSQL_ROOT=/var/tmp/$USER/mysql-5.5.15

MYSQL_CMD="${MYSQL_PATH}mysql --defaults-file=${MYSQL_ROOT}/mysql-test/include/default_mysqld.cnf -h $MYSQL_HOST --port=$MYSQL_PORT -u root --password=$MYSQL_ROOT_PASS"
#MYSQL_CMD="${MYSQL_PATH}mysql --defaults-file=${MYSQL_PATH}../mysql-test/include/default_mysqld.cnf -u root "
#MYSQL_CMD="mysql -h $MYSQL_HOST --port=$MYSQL_PORT -u root --password=$MYSQL_ROOT_PASS"

 
##########################################################################
# Databases
##########################################################################
# scratchpad
function deploy_scratchpad_driver(){

	mkdir -p /var/tmp/$USER/txmud/tomcat6/lib
	echo "Compiling scratchpad driver"
	javac -cp .:../lib/jsqlparser.jar:../lib/netty-3.2.1.Final.jar:../lib/log4j-1.2.15.jar    \
		util/*.java \
		txstore/scratchpad/rdbms/jdbc/*.java \
		txstore/scratchpad/rdbms/*.java \
		txstore/scratchpad/resolution/*.java \
		txstore/scratchpad/resolution/*.java \
		txstore/scratchpad/rdbms/tests/*.java \
		txstore/util/*.java \
		txstore/proxy/*.java  \
		util/*.java
	echo "Done"
		echo "----------------------------"
	echo "Building and deploying jar library on tomcat lib dir (it includes the dependences jsqlparser, netty and log4g)"
	jar -cf jdbctxmud.jar \
		txstore/scratchpad \
		txstore/util \
		txstore/proxy \
		util/
	cp jdbctxmud.jar $TOMCAT_LIB
	cp ../lib/jsqlparser.jar $TOMCAT_LIB
	cp ../lib/netty-3.2.1.Final.jar $TOMCAT_LIB
	cp ../lib/log4j-1.2.15.jar $TOMCAT_LIB
	echo "Done"
		echo "----------------------------"
	
}
#------------------------------------------------------------------------
# JDBC Driver
#------------------------------------------------------------------------
function deploy_mysql_driver(){
	echo "------------------------------------------------------------"
	echo "Downloading mysql jdbc driver"
	wget -c http://ftp.gwdg.de/pub/misc/mysql/Downloads/Connector-J/mysql-connector-java-5.1.17.zip
	echo "Done"
	echo "----------------------------"
	echo "Deploying mysql driver on tomcat lib dir "
	mkdir -p $TOMCAT_LIB
	unzip mysql-connector-java-5.1.17.zip > /dev/null
	mv mysql-connector-java-5.1.17/mysql-connector-java-5.1.17-bin.jar $TOMCAT_LIB
	rm -rf mysql-connector-java-5.1.17
	echo "Done"
	echo "----------------------------"
}



#------------------------------------------------------------------------
# Mysql 5.5.15
#------------------------------------------------------------------------
function deploy_storage(){
	undeploy_storage;
	echo "Downloading mysql"
	wget -c http://vesta.informatik.rwth-aachen.de/mysql/Downloads/MySQL-5.5/mysql-5.5.15.tar.gz
	echo "Unpacking mysql source"
	tar xzvf mysql-5.5.15.tar.gz   > /dev/null
	echo "Configuring  mysql source"
	cd mysql-5.5.15 && cmake -DCMAKE_INSTALL_PREFIX=${MYSQL_ROOT} -DMYSQL_DATADIR=${MYSQL_ROOT}/data -DWITH_DEBUG=ON > /dev/null 
	
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
	sleep 5
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
}

function undeploy_storage(){
	stop_database;
	rm -rf /var/tmp/dcfp/mysql-5.5.15
}

function start_database(){
${MYSQL_ROOT}/bin/mysqld_safe --defaults-file=${MYSQL_ROOT}/mysql-test/include/default_mysqld.cnf --port=$MYSQL_PORT \
	 						--innodb_lock_wait_timeout=1 --max_connections=10000 --innodb_buffer_pool_size=1503238553 \
	 						--innodb_flush_method=O_DIRECT --skip-innodb_doublewrite --innodb_flush_log_at_trx_commit=0 &
}
function stop_database(){
	killall -9 mysqld mysqld_safe
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
	$MYSQL_CMD  -e "grant all on testtpcw.* to sa";
}
function setupDB_Mysql_new_queries {
	echo "------------------------------------------------------------"
	echo "Setting up mysql_new_queries database"
	$MYSQL_CMD  -e "drop database if exists mysql_new_queries";
	$MYSQL_CMD  -e "create database mysql_new_queries";
	$MYSQL_CMD  -e "grant all on mysql_new_queries.* to sa@'%'";
	$MYSQL_CMD  -e "grant all on mysql_new_queries.* to sa";
}
function setupDB_mysql_spd_bypass() {
	echo "------------------------------------------------------------"
	echo "Setting up mysql_spd_bypass database"
	$MYSQL_CMD  -e "drop database if exists mysql_spd_bypass";
	$MYSQL_CMD  -e "create database mysql_spd_bypass";
	$MYSQL_CMD  -e "grant all on mysql_spd_bypass.* to sa@'%'";
	$MYSQL_CMD  -e "grant all on mysql_spd_bypass.* to sa";
}
function setupDB_mysql_original() {
	echo "------------------------------------------------------------"
	echo "Setting up mysql_original database"
	$MYSQL_CMD  -e "drop database if exists mysql_original";
	$MYSQL_CMD  -e "create database mysql_original";
	$MYSQL_CMD  -e "grant all on mysql_original.* to sa@'%'";
	$MYSQL_CMD  -e "grant all on mysql_original.* to sa";
}
function setupDB_mysql_redblue_semantics() {
	echo "------------------------------------------------------------"
	echo "Setting up mysql_redblue_semantics database"
	$MYSQL_CMD  -e "drop database if exists mysql_redblue_semantics";
	$MYSQL_CMD  -e "create database mysql_redblue_semantics";
	$MYSQL_CMD  -e "grant all on mysql_redblue_semantics.* to sa@'%'";
	$MYSQL_CMD  -e "grant all on mysql_redblue_semantics.* to sa";
}
function tpcw_create_databases() {
	setupDB_Test;
	setupDB_Mysql_new_queries;
	setupDB_mysql_spd_bypass;
	setupDB_mysql_original;
	setupDB_mysql_redblue_semantics;
	#$MYSQL_PATH/mysqladmin -u root -h localhost flush-privileges
	#$MYSQL_PATH/mysqladmin -u root -h localhost  reload
}
#------------------------------------------------------------------------
# Populate data
#-----------------------------------------------------------------------
function tpcw_populate_database(){
echo "------------------------------------------------------------"
	
	tpcw_create_databases;
	#exit 0
	echo "Deploying TPCW (The image files and the database are not included)"
	echo "cd applications/tpc-w && ant clean gendb"
	cd applications/tpc-w && ant clean gendb
	cd ../..
	echo "Done"
	echo "----------------------------"
}
##########################################################################
# WebProxy - Tomcat
#########################################################################
function deploy_webproxy(){
	echo "------------------------------------------------------------"
	undeploy_webproxy;
	mkdir -p /var/tmp/$USER/txmud/
	echo "Done"
	echo "----------------------------"
	echo "Downloading Tomcat6"
	wget -c http://www.bitlib.net/mirror/apache.org/tomcat/tomcat-6/v6.0.33/bin/apache-tomcat-6.0.33.tar.gz
	echo "Done"
	echo "----------------------------"
	echo "Installing Tomcat6"
	tar xzvf apache-tomcat-6.0.33.tar.gz -C /var/tmp/$USER/txmud/  > /dev/null
	mv /var/tmp/$USER/txmud/apache-tomcat-6.0.33 /var/tmp/$USER/txmud/tomcat6
	echo "Done"
	echo "----------------------------"
	tpcw_generate_images;
}
function undeploy_webproxy(){
	echo "Cleanup previous Tomcat6 installation"
	webproxy_shutdown;
	rm -rf /var/tmp/$USER/txmud/tomcat6
	echo "Done"
}	
	
function webproxy_shutdown(){
	/var/tmp/$USER/txmud/tomcat6/bin/shutdown.sh 1&>2 >/dev/null 
}
function webproxy_startup(){ 
	/var/tmp/$USER/txmud/tomcat6/bin/startup.sh 
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
	echo "Deploying TPCW (The image files and the database are not included)"
	rm -rf /var/tmp/$USER/txmud/tomcat6/webapps/tpcw*
	cd applications/tpc-w && ant  inst
	cd ../..
	echo "Done"
	echo "----------------------------"
	
}
function tpcw_generate_src(){
	echo "------------------------------------------------------------"
	echo "Cleanup TPCW (The image files and the database are not included)"
	cd applications/tpc-w && ant clean
	cd ../..
	echo "Done"
	echo "----------------------------"
	
	
}

function tpcw_generate_images(){
echo "------------------------------------------------------------"
	echo "Deploying TPCW (The image files and the database are not included)"
	cd applications/tpc-w && ant genimg
	cd ../..
	echo "Done"
		echo "----------------------------"
}


function execTPCW(){
	chmod +x applications/tpc-w/dist/rbe.sh
	echo "cd applications/tpc-w/dist/"
}


function prepare_tpcw(){

	echo "Installing webproxy"
	deploy_webproxy;
	echo "Installing scratchpad jdbc driver"
	deploy_scratchpad_driver;
	echo "Installing mysql jdbc driver"
	deploy_mysql_driver;


	echo "Configuring tpcw parameters (users=${TPCW_USERS} and items=${TPCW_ITEMS})"
	sed "s/^num\.item=.*/num\.item=${TPCW_ITEMS}/g"   applications/tpc-w/tpcw.properties > tmpf   
	sed "s/^num\.eb=.*/num\.eb=${TPCW_USERS}/g"  tmpf > applications/tpc-w/tpcw.properties  
	sed "s/^numebs=.*/numebs=$TPCW_USERS/g"   applications/tpc-w/rbe.sh > tmpf
	cat tmpf > applications/tpc-w/rbe.sh
	rm -f tmpf
	
	tpcw_generate_src;
	tpcw_generate_images;
	tpcw_create_databases;
	tpcw_populate_database;	
}

# this fuction has the database name as a parameter
function deploy_tpcwapp_scratchpad(){
	echo "----------------------------------------------------------------------------------------"
	echo "Configuring tpcw with mysql driver"
	#main.properties
	#dbName=mysql_new_queries
	#sqlFilter=sql-mysql_new_queries.properties
	STR=$1
	sed "s/^dbName=.*/dbName=$STR/g" applications/tpc-w/main.properties > tmpf 
	sed "s/^sqlFilter=.*/sqlFilter=sql-$STR.properties/g" tmpf > applications/tpc-w/main.properties 
	rm -f tmpf
	
	echo "----------------------------------------------------------------------------------------"
	echo "Configuring tpcw parameters (users=${TPCW_USERS} and items=${TPCW_ITEMS})"
	sed "s/^num\.item=.*/num\.item=${TPCW_ITEMS}/g"   applications/tpc-w/tpcw.properties > tmpf   
	sed "s/^num\.eb=.*/num\.eb=${TPCW_USERS}/g"  tmpf > applications/tpc-w/tpcw.properties  
	rm -f tmpf
	
	sed "s/^numebs=.*/numebs=$TPCW_USERS/g"   applications/tpc-w/rbe.sh > tmpf
	sed "s/^url=.*/url=\"http:\/\/$TOMCAT_HOST:8080\/tpcw\/\"/g"  tmpf > applications/tpc-w/rbe.sh
	
	rm -f tmpf
	
	#tpcw.properties
	#jdbc.user=sa
	#jdbc.password=
	#jdbc.driver=txstore.scratchpad.rdbms.jdbc.TxMudDriver
	#jdbc.actualDriver=com.mysql.jdbc.Driver
	#jdbc.path=jdbc:txmud:mysql_new_queries
	#jdbc.actualPath=jdbc:mysql://localhost/mysql_new_queries
	#jdbc.scratchpadClass=txstore.scratchpad.rdbms.DBScratchpad
	

	#jdbc.driver=txstore.scratchpad.rdbms.jdbc.TxMudDriver
	sed "s/^jdbc\.driver=.*/jdbc\.driver=txstore\.scratchpad\.rdbms\.jdbc\.TxMudDriver/g" applications/tpc-w/tpcw.properties > tmpf
	#jdbc.path=jdbc:mysql:mysql_spd_bypass
	sed "s/^jdbc\.path=.*/jdbc\.path=jdbc:txmud:$STR/g"  tmpf > applications/tpc-w/tpcw.properties  

	
	#jdbc.actualPath=jdbc:mysql://localhost/mysql_spd_bypass
	sed "s/^jdbc\.actualPath=.*/jdbc\.actualPath=jdbc:mysql:\/\/$TPCW_DATABASE\/$STR/g"  applications/tpc-w/tpcw.properties  > tmpf
	cat  tmpf > applications/tpc-w/tpcw.properties  
	rm -f tmpf
		
	echo "----------------------------------------------------------------------------------------"	
	echo "Installing scratchpad jdbc driver"
	deploy_scratchpad_driver;
	echo "----------------------------------------------------------------------------------------"
	echo "Installing mysql jdbc driver"
	deploy_mysql_driver;
	deployTPCW;
	execTPCW;
	
}

function deploy_tpcwapp_mysql(){
	
	echo "----------------------------------------------------------------------------------------"
	echo "Configuring tpcw with mysql driver"
	#main.properties
	#dbName=mysql_new_queries
	#sqlFilter=sql-mysql_new_queries.properties
	STR=$1
	sed "s/^dbName=.*/dbName=$STR/g" applications/tpc-w/main.properties > tmpf 
	sed "s/^sqlFilter=.*/sqlFilter=sql-$STR.properties/g" tmpf > applications/tpc-w/main.properties 
	rm -f tmpf
	echo "----------------------------------------------------------------------------------------"
	echo "Configuring tpcw parameters (users=${TPCW_USERS} and items=${TPCW_ITEMS})"
	sed "s/^num\.item=.*/num\.item=${TPCW_ITEMS}/g"   applications/tpc-w/tpcw.properties > tmpf   
	sed "s/^num\.eb=.*/num\.eb=${TPCW_USERS}/g"  tmpf > applications/tpc-w/tpcw.properties  
	rm -f tmpf
	
	sed "s/^numebs=.*/numebs=$TPCW_USERS/g"   applications/tpc-w/rbe.sh > tmpf
	sed "s/^url=.*/url=\"http:\/\/$TOMCAT_HOST:8080\/tpcw\/\"/g"  tmpf > applications/tpc-w/rbe.sh
	
	rm -f tmpf
	
	#tpcw.properties
	#jdbc.user=sa
	#jdbc.password=
	#jdbc.driver=txstore.scratchpad.rdbms.jdbc.TxMudDriver
	#jdbc.actualDriver=com.mysql.jdbc.Driver
	#jdbc.path=jdbc:txmud:mysql_new_queries
	#jdbc.actualPath=jdbc:mysql://localhost/mysql_new_queries
	#jdbc.scratchpadClass=txstore.scratchpad.rdbms.DBScratchpad
	#jdbc.driver=txstore.scratchpad.rdbms.jdbc.TxMudDriver
	sed "s/^jdbc\.driver=.*/jdbc\.driver=com\.mysql\.jdbc\.Driver/g" applications/tpc-w/tpcw.properties > tmpf
	#jdbc:mysql://localhost/mysql_new_queries?user=sa&password=
	sed "s/^jdbc\.actualPath=.*/jdbc\.actualPath=jdbc:mysql:\/\/$TPCW_DATABASE\/$STR/g" tmpf > applications/tpc-w/tpcw.properties
	sed "s/^jdbc\.path=.*/jdbc\.path=jdbc:mysql:\/\/$TPCW_DATABASE\/$STR\?user=sa\&password=/g" applications/tpc-w/tpcw.properties > tmpf
	sed "s/^standardUrl=.*/standardUrl=http:\/\/$TOMCAT_HOST:8080\//g" tmpf > applications/tpc-w/tpcw.properties
	rm -f tmpf
	
	echo "----------------------------------------------------------------------------------------"	
	echo "Installing scratchpad jdbc driver"
	deploy_scratchpad_driver;
	echo "----------------------------------------------------------------------------------------"
	echo "Installing mysql jdbc driver"
	deploy_mysql_driver;
	deployTPCW;
	execTPCW;

	
}




function deploy_tpcw_test(){
	deploy_scratchpad_driver;
	deploy_mysql_driver;
	setupDB_Test;
	#mysql database extracted from a tpcw populated database (without scratchpad table created!): mysqldump -n -t -u root tpcwdb_mysql_scratchpad > tpcwbackup.sql
	echo "Download testing workload"
	wget -c www.mpi-sws.org/~dcfp/tpcwbackup.sql
	echo "Done"
	echo "Initialize database testtpcw (you must create a database called testtpcw and a grant full access to an user 'sa' without password)"
	#echo "java -cp    .:../lib/jsqlparser.jar:../lib/netty-3.2.1.Final.jar:../lib/log4j-1.2.15.jar:$TOMCAT_HOME/lib/mysql-connector-java-5.1.17-bin.jar txstore.scratchpad.rdbms.tests.InitTPCW tpcwbackup.sql"
	java -cp    .:../lib/jsqlparser.jar:../lib/netty-3.2.1.Final.jar:../lib/log4j-1.2.15.jar:$TOMCAT_HOME/lib/mysql-connector-java-5.1.17-bin.jar txstore.scratchpad.rdbms.tests.InitTPCW tpcwbackup.sql 
	echo "run the following command to execute the test..."
	echo "java -cp    .:../lib/jsqlparser.jar:../lib/netty-3.2.1.Final.jar:$TOMCAT_HOME/lib/mysql-connector-java-5.1.17-bin.jar txstore.scratchpad.rdbms.tests.TestTPCW"
	
}


##########################################################################
# main
##########################################################################


#full applications
if [ $1 = "tpcw_original" ] #original code
	then deploy_tpcwapp_mysql "mysql_original" ;
elif [ $1 = "tpcw_bypass" ] #bypass driver
	then deploy_tpcwapp_scratchpad "mysql_spd_bypass" ;
elif [ $1 = "tpcw_redblue" ] # redblue driver
	then deploy_tpcwapp_scratchpad "mysql_redblue_semantics" ;
elif [ $1 = "tpcw_mysql" ]   #new queries
	then deploy_tpcwapp_mysql "mysql_new_queries" ;
elif [ $1 = "tpcw_test" ]
	then deploy_tpcw_test;
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
		
		
#-------------------------------		
elif [ $1 = "install_database" ]
	then
		deploy_storage;
elif [ $1 = "uninstall_database" ]
	then
		undeploy_storage;
elif [ $1 = "populate_database" ]
	then 
		tpcw_populate_database;
elif [ $1 = "stop_database" ]
	then
		stop_database;
elif [ $1 = "start_database" ]
	then 
		start_database;
#-------------------------------
elif [ $1 = "tpcw_client" ]
	then 
	cd applications/tpc-w && ant  clean dist ;
	cd ../.. ;
#-------------------------------		
else
	echo "allowed parameters:"
	echo "TPCW configuration"
	echo "tpcw_original - redeploy  tpcw website with original source code"
	echo "tpcw_bypass - redeploy  tpcw website with the bypass scratchpad driver"
	echo "tpcw_redblue -redeploy  tpcw website with the redblue semantics driver (implementing the reconciliation procedures for red operations)"
	echo "tpcw_mysql - redeploy  tpcw website with mysql with the same queries valid on scratchpad"
	echo "tpcw_test -test the tpcw functions with scratchpad"
	echo "tpcw_client - compile tpcw client emulator"
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
	echo "	 $0 install_proxy"
	echo "	 $0 tpcw_mysql"
	#	echo "	$0 install_database"
	echo "	 $0 populate_database"
	echo "	 $0 start_proxy"
fi
