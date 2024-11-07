#!/bin/bash
USER=root
LOCAL_DIR=$PWD
TOMCAT_HOME=/var/tmp/$USER/txmud/tomcat6
TOMCAT_LIB=$TOMCAT_HOME/lib
MYSQL_ROOT_PASS=
TPCW_USERS=500
TPCW_ITEMS=1000
TPCW_DATABASE=localhost:3306
MYSQL_CMD="/usr/local/mysql/bin/mysql -h localhost -P 3306 -u root --password=$MYSQL_ROOT_PASS"

#remove
#mysql -u root --password=$MYSQL_ROOT_PASS  -e "drop database tpcwdb_mysql_scratchpad" > /dev/null

##########################################################################
# tomcat
#########################################################################
function deployTomcat6(){
	echo "------------------------------------------------------------"
	echo "Cleanup previous Tomcat6 installation"
	rm -rf /var/tmp/$USER/txmud/tomcat6
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
}
##########################################################################
# scratchpad
#########################################################################
function deployScratchpad(){

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


##########################################################################
# TPCW
#########################################################################
function deployTPCW(){
	echo "------------------------------------------------------------"
	echo "Deploying TPCW (The image files and the database are not included)"
	cd applications/tpc-w && ant  inst
	cd ../..
	echo "Done"
	echo "----------------------------"
	
}


function flushCodeTPCW(){
	echo "------------------------------------------------------------"
	echo "Cleanup TPCW (The image files and the database are not included)"
	cd applications/tpc-w && ant clean
	cd ../..
	echo "Done"
		echo "----------------------------"
	
}

function buildImagesTPCW(){
echo "------------------------------------------------------------"
	echo "Deploying TPCW (The image files and the database are not included)"
	cd applications/tpc-w && ant genimg
	cd ../..
	echo "Done"
		echo "----------------------------"
}


function populateDBTPCW(){
echo "------------------------------------------------------------"
	echo "Deploying TPCW (The image files and the database are not included)"
	cd applications/tpc-w && ant gendb
	cd ../..
	echo "Done"
	echo "----------------------------"
}

function execTPCW(){
	$TOMCAT_HOME/bin/shutdown.sh 2>&1 > /dev/null
	$TOMCAT_HOME/bin/startup.sh
	chmod +x applications/tpc-w/dist/rbe.sh
	echo "cd applications/tpc-w/dist/"
}



##########################################################################
# Setup databases
#########################################################################
function setupDB_Test() {
	echo "------------------------------------------------------------"
	echo "Setting up tpcw test database"
	$MYSQL_CMD  -e "drop database if exists testtpcw";
	$MYSQL_CMD  -e "create database testtpcw";
	$MYSQL_CMD  -e "grant all on testtpcw.* to sa";
}
function setupDB_Mysql_new_queries {
	echo "------------------------------------------------------------"
	echo "Setting up mysql_spd_bypass database"
	$MYSQL_CMD  -e "drop database if exists mysql_new_queries";
	$MYSQL_CMD  -e "create database mysql_new_queries";
	$MYSQL_CMD  -e "grant all on mysql_new_queries.* to sa";
}
function setupDB_mysql_spd_bypass() {
	echo "------------------------------------------------------------"
	echo "Setting up mysql_spd_bypass database"
	$MYSQL_CMD  -e "drop database if exists mysql_spd_bypass";
	$MYSQL_CMD  -e "create database mysql_spd_bypass";
	$MYSQL_CMD  -e "grant all on mysql_spd_bypass.* to sa";
}
function setupDB_mysql_original() {
	echo "------------------------------------------------------------"
	echo "Setting up mysql_original database"
	$MYSQL_CMD  -e "drop database if exists mysql_original";
	$MYSQL_CMD  -e "create database mysql_original";
	$MYSQL_CMD  -e "grant all on mysql_original.* to sa";
}
function setupDB_mysql_redblue_semantics() {
	echo "------------------------------------------------------------"
	echo "Setting up mysql_redblue_semantics database"
	$MYSQL_CMD  -e "drop database if exists mysql_redblue_semantics";
	$MYSQL_CMD  -e "create database mysql_redblue_semantics";
	$MYSQL_CMD  -e "grant all on mysql_redblue_semantics.* to sa";
}
function setupAllDatabases() {
	setupDB_Test;
	setupDB_Mysql_new_queries;
	setupDB_mysql_spd_bypass;
	setupDB_mysql_original;
	setupDB_mysql_redblue_semantics;
}


##########################################################################
# setup testing functions enviroment
#########################################################################
function deployMysqlJDBCConnector(){
	echo "------------------------------------------------------------"
	echo "Downloading mysql jdbc driver"
	wget -c http://ftp.gwdg.de/pub/misc/mysql/Downloads/Connector-J/mysql-connector-java-5.1.17.zip
	echo "Done"
		echo "----------------------------"
	echo "Deploying mysql driver on tomcat lib dir "
	unzip mysql-connector-java-5.1.17.zip > /dev/null
	mv mysql-connector-java-5.1.17/mysql-connector-java-5.1.17-bin.jar $TOMCAT_LIB
	rm -rf mysql-connector-java-5.1.17
	echo "Done"
	echo "----------------------------"
	
	
}

##########################################################################
# deploy tpcw
#########################################################################
function prepare_tpcw(){
	sed "s/^num\.item=.*/num\.item=${TPCW_ITEMS}/g"   applications/tpc-w/tpcw.properties > tmpf   
	sed "s/^num\.eb=.*/num\.eb=${TPCW_USERS}/g"  tmpf > applications/tpc-w/tpcw.properties  
	
	sed "s/^numebs=.*/numebs=$TPCW_USERS/g"   applications/tpc-w/rbe.sh > tmpf
	cat tmpf > applications/tpc-w/rbe.sh
	rm -f tmpf
	deployTomcat6;
	deployScratchpad;
	deployMysqlJDBCConnector;
	flushCodeTPCW;
	buildImagesTPCW;
	setupAllDatabases;
	populateDBTPCW;	
}

# this fuction has the database name as a parameter
function deploy_scratchpad(){
	#main.properties
	#dbName=mysql_new_queries
	#sqlFilter=sql-mysql_new_queries.properties
	STR=$1
	sed "s/^dbName=.*/dbName=$STR/g" applications/tpc-w/main.properties > tmpf 
	sed "s/^sqlFilter=.*/sqlFilter=sql-$STR.properties/g" tmpf > applications/tpc-w/main.properties 
	rm -f tmpf
	
	#tpcw.properties
	#jdbc.user=sa
	#jdbc.password=
	#jdbc.driver=txstore.scratchpad.rdbms.jdbc.TxMudDriver
	#jdbc.actualDriver=com.mysql.jdbc.Driver
	#jdbc.path=jdbc:txmud:mysql_new_queries
	#jdbc.actualPath=jdbc:mysql://localhost/mysql_new_queries
	#jdbc.scratchpadClass=txstore.scratchpad.rdbms.DBScratchpad
	
	tmpf=`mktemp`
	#jdbc.driver=txstore.scratchpad.rdbms.jdbc.TxMudDriver
	sed "s/^jdbc\.driver=.*/jdbc\.driver=txstore\.scratchpad\.rdbms\.jdbc\.TxMudDriver/g" applications/tpc-w/tpcw.properties > tmpf
	#jdbc.path=jdbc:mysql:mysql_spd_bypass
	sed "s/^jdbc\.path=.*/jdbc\.path=jdbc:txmud:$STR/g"  tmpf > applications/tpc-w/tpcw.properties  

	
	#jdbc.actualPath=jdbc:mysql://localhost/mysql_spd_bypass
	sed "s/^jdbc\.actualPath=.*/jdbc\.actualPath=jdbc:mysql:\/\/$TPCW_DATABASE\/$STR/g"  applications/tpc-w/tpcw.properties  > tmpf
	cat  tmpf > applications/tpc-w/tpcw.properties  
	rm -f tmpf
		
	prepare_tpcw;
	deployTPCW;
	execTPCW;
	
}

function deploy_mysql(){
	#main.properties
	#dbName=mysql_new_queries
	#sqlFilter=sql-mysql_new_queries.properties

	STR=$1
	tmpf=`mktemp`
	sed "s/^dbName=.*/dbName=$STR/g" applications/tpc-w/main.properties > tmpf 
	sed "s/^sqlFilter=.*/sqlFilter=sql-$STR.properties/g" tmpf > applications/tpc-w/main.properties 
	rm -f tmpf


	#tpcw.properties
	#jdbc.user=sa
	#jdbc.password=
	#jdbc.driver=txstore.scratchpad.rdbms.jdbc.TxMudDriver
	#jdbc.actualDriver=com.mysql.jdbc.Driver
	#jdbc.path=jdbc:txmud:mysql_new_queries
	#jdbc.actualPath=jdbc:mysql://localhost/mysql_new_queries
	#jdbc.scratchpadClass=txstore.scratchpad.rdbms.DBScratchpad
	
	tmpf=`mktemp`
	#jdbc.driver=txstore.scratchpad.rdbms.jdbc.TxMudDriver
	sed "s/^jdbc\.driver=.*/jdbc\.driver=com\.mysql\.jdbc\.Driver/g" applications/tpc-w/tpcw.properties > tmpf
	#jdbc:mysql://localhost/mysql_new_queries?user=sa&password=
	sed "s/^jdbc\.actualPath=.*/jdbc\.actualPath=jdbc:mysql:\/\/$TPCW_DATABASE\/$STR/g" tmpf > applications/tpc-w/tpcw.properties
	sed "s/^jdbc\.path=.*/jdbc\.path=jdbc:mysql:\/\/$TPCW_DATABASE\/$STR\?user=sa\&password=/g" applications/tpc-w/tpcw.properties > tmpf 
	cat tmpf > applications/tpc-w/tpcw.properties
	 
	rm -f tmpf
	prepare_tpcw;
	deployTPCW;
	execTPCW;
	
}




function deploy_test(){
	deployScratchpad;
	deployMysqlJDBCConnector;
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
#########################################################################

if [ $1 = "original" ] #original code
	then deploy_mysql "mysql_original" ;
elif [ $1 = "bypass" ] #bypass driver
	then deploy_scratchpad "mysql_spd_bypass" ;
elif [ $1 = "redblue" ] # redblue driver
	then deploy_scratchpad "mysql_redblue_semantics" ;
elif [ $1 = "mysql" ]   #new queries
	then deploy_mysql "mysql_new_queries" ;
elif [ $1 = "test" ]
	then deploy_test;
elif [ $1 = "website" ]
	then 
		deployTomcat6;
		deployScratchpad;
		deployTPCW;	
elif [ $1 = "database" ]
	then 
		deployScratchpad;
		deployTPCW;		
		setupAllDatabases;
		populateDBTPCW;
else
	echo "allowed parameters:"
	echo "original -setup the experiment enviroment with  the original code of tpcw without any modification"
	echo "bypass -setup the experiment enviroment with the bypass scratchpad driver"
	echo "redblue -setup the experiment enviroment with the redblue semantics driver (implementing the reconciliation procedures for red operations)"
	echo "mysql -setup the experiment enviroment with mysql with the same queries valid on scratchpad"
	echo "test -test the tpcw functions with scratchpad"
	echo "website -redeploy only the website with the last configuration"
	echo "database -redeploy only the database with the last configuration"
fi;





