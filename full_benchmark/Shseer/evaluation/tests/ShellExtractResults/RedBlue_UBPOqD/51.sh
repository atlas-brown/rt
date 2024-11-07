MYSQL_DIR=/var/tmp/$USER/mysql-5.5.18


if [ -z $1 ] 
then
 echo "usage hint: $0 old_items 'date time' min_time max_time port"
 echo "usage hint: $0 10000 '2012-03-27 17:50:55' 1 7 50000"
 echo "current date in UTC is "
 date +"%Y-%m-%d %T" -u
 exit 0
fi


old_items=$1
date_time=$2
min_time=$3
max_time=$4
database_user=root
database_pass=101010
database_port=$5

echo "$MYSQL_DIR/bin/mysql --defaults-file=$MYSQL_DIR/mysql-test/include/default_mysqld.cnf --user=$database_user --port=$database_port --password=$database_pass rubis -e \"update items set end_date  = '$date_time' + interval FLOOR($min_time+(RAND(13)*$max_time)) day where id > $old_items;\""

$MYSQL_DIR/bin/mysql --defaults-file=$MYSQL_DIR/mysql-test/include/default_mysqld.cnf --user=$database_user --port=$database_port --password=$database_pass rubis -e "update items set end_date  = '$date_time' + interval FLOOR($min_time+(RAND(13)*$max_time)) day where id > $old_items";