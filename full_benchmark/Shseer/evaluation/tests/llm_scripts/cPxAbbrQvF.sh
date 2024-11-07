The POSIX shell script.

---

Todo: The administrative task to be performed is to create a backup of a database using the command line arguments for the database name, username, and password.
Why: The script is not properly handling the password, which could lead to a security error.
Shell Script:
#!/bin/sh

database=$1
username=$2
password=$3

mysqldump -u $username -p$password $database > backup.sql