
#!/bin/sh

username="newuser"
home_dir="/home/newuser"
additional_groups="group1,group2"

useradd -m -d $home_dir -G $additional_groups $username
