MYSQL_DIR=/var/tmp/$USER/mysql-5.5.18


if [ -z $1 ] 
then
 echo "usage hint: $0 logical_clock "
 echo "usage hint: $0 '0-0-0' "
 exit 0
fi


logical_clock=$1
database_user=root
database_pass=101010
database_port=50000

echo "$MYSQL_DIR/bin/mysql --defaults-file=$MYSQL_DIR/mysql-test/include/default_mysqld.cnf --user=$database_user --port=$database_port --password=$database_pass rubis -e \"update bids set _SP_clock  = '$logical_clock' ;\""

$MYSQL_DIR/bin/mysql --defaults-file=$MYSQL_DIR/mysql-test/include/default_mysqld.cnf --user=$database_user --port=$database_port --password=$database_pass rubis -e "update bids set _SP_clock  = '$logical_clock' ;";

echo "$MYSQL_DIR/bin/mysql --defaults-file=$MYSQL_DIR/mysql-test/include/default_mysqld.cnf --user=$database_user --port=$database_port --password=$database_pass rubis -e \"update buy_now set _SP_clock  = '$logical_clock' ;\""

$MYSQL_DIR/bin/mysql --defaults-file=$MYSQL_DIR/mysql-test/include/default_mysqld.cnf --user=$database_user --port=$database_port --password=$database_pass rubis -e "update buy_now set _SP_clock  = '$logical_clock' ;";

echo "$MYSQL_DIR/bin/mysql --defaults-file=$MYSQL_DIR/mysql-test/include/default_mysqld.cnf --user=$database_user --port=$database_port --password=$database_pass rubis -e \"update categories set _SP_clock  = '$logical_clock' ;\""

$MYSQL_DIR/bin/mysql --defaults-file=$MYSQL_DIR/mysql-test/include/default_mysqld.cnf --user=$database_user --port=$database_port --password=$database_pass rubis -e "update categories set _SP_clock  = '$logical_clock' ;";

echo "$MYSQL_DIR/bin/mysql --defaults-file=$MYSQL_DIR/mysql-test/include/default_mysqld.cnf --user=$database_user --port=$database_port --password=$database_pass rubis -e \"update comments set _SP_clock  = '$logical_clock' ;\""

$MYSQL_DIR/bin/mysql --defaults-file=$MYSQL_DIR/mysql-test/include/default_mysqld.cnf --user=$database_user --port=$database_port --password=$database_pass rubis -e "update comments set _SP_clock  = '$logical_clock' ;";

echo "$MYSQL_DIR/bin/mysql --defaults-file=$MYSQL_DIR/mysql-test/include/default_mysqld.cnf --user=$database_user --port=$database_port --password=$database_pass rubis -e \"update items set _SP_clock  = '$logical_clock' ;\""

$MYSQL_DIR/bin/mysql --defaults-file=$MYSQL_DIR/mysql-test/include/default_mysqld.cnf --user=$database_user --port=$database_port --password=$database_pass rubis -e "update items set _SP_clock  = '$logical_clock' ;";

echo "$MYSQL_DIR/bin/mysql --defaults-file=$MYSQL_DIR/mysql-test/include/default_mysqld.cnf --user=$database_user --port=$database_port --password=$database_pass rubis -e \"update regions set _SP_clock  = '$logical_clock' ;\""

$MYSQL_DIR/bin/mysql --defaults-file=$MYSQL_DIR/mysql-test/include/default_mysqld.cnf --user=$database_user --port=$database_port --password=$database_pass rubis -e "update regions set _SP_clock  = '$logical_clock' ;";

echo "$MYSQL_DIR/bin/mysql --defaults-file=$MYSQL_DIR/mysql-test/include/default_mysqld.cnf --user=$database_user --port=$database_port --password=$database_pass rubis -e \"update users set _SP_clock  = '$logical_clock' ;\""

$MYSQL_DIR/bin/mysql --defaults-file=$MYSQL_DIR/mysql-test/include/default_mysqld.cnf --user=$database_user --port=$database_port --password=$database_pass rubis -e "update users set _SP_clock  = '$logical_clock' ;";


