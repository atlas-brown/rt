#!/bin/bash

cmd="$1"
name="$2"

set -eu


usage()
{
  local app=$(basename "$0")
  cat >&2 <<EOF
Usage:

   $app save <name>     Save the current simulator state as <name>
   $app restore <name>  Restore the simulator state saved as <name>
   $app list            List all saved states
   $app ls              Ditto
   $app rm <name>       Delete the simulator state saved as <name>
   $app clean           Delete all saved simulator state
   $app pwd             Print the current app folder
   $app open            Open the current app folder in Finder

EOF
  exit 1
}


state_dir="$HOME/.ios-sim-manager"

app_dir=$(ls -td "$HOME/Library/Application Support/iPhone Simulator"/*/Applications/*/*.app | head -n1)
app_base_dir=$(dirname "$app_dir")
readable_app_base_dir=$(echo "$app_base_dir" | cut -d / -f 6-)
app_name=$(basename "$app_dir" ".app")
app_state_dir="$state_dir/$app_name"
instance_state_dir="$app_state_dir/$name"
readable_instance_state_dir="$app_name/$name"


check_name()
{
  if [ -z "$name" ]
  then
    usage
  fi

  if ! [[ $name =~ ^[-A-Za-z0-9_]+$ ]]
  then
    echo "Invalid name: needs to be alphanumeric with dashes or underscores." \
      >&2
    exit 1
  fi
}


restore_backup()
{
  local backup_dir="$1"
  echo -n "Restoring backup... "
  mv "$app_base_dir/$backup_dir" "$app_base_dir"
  echo "done."
  exit 1
}


cmd_save()
{
  check_name

  if [ -e "$instance_state_dir" ]
  then
    read -p "$instance_state_dir already exists; overwrite it? [yN] " -r
    if ! [[ $REPLY =~ ^[Yy]$ ]]
    then
      exit 1
    fi
  fi

  mkdir -p "$instance_state_dir"
  echo -n "Copying $readable_app_base_dir to $readable_instance_state_dir... "
  rsync -a --delete "$app_base_dir"/* "$instance_state_dir"
  echo "done."
}


cmd_restore()
{
  check_name

  if ! [ -d "$instance_state_dir" ]
  then
    echo "No such state $app_name/$name"
    exit 1
  fi

  # The backups are disabled because they slow things down,
  # and are really only useful when debugging this script.
  #local backup_date=$(date '+%Y-%m-%d-%H-%M-%S')
  #local backup_dir=".backup-$backup_date"
  echo -n "Copying $readable_instance_state_dir to $readable_app_base_dir... "
  #mkdir -p "$app_base_dir/$backup_dir"
  #mv "$app_base_dir"/* "$app_base_dir/$backup_dir"
  #trap "restore_backup $backup_dir" ERR
  rsync -a --delete "$instance_state_dir"/* "$app_base_dir"
  echo "done."
}


cmd_list()
{
  local dirs=$(ls -d "$app_state_dir"/* 2>/dev/null || true)
  for dir in $dirs
  do
    bn=$(basename "$dir")
    echo -ne "$bn:  "
    du -xsh "$dir" | cut -f 1
  done
}


cmd_rm()
{
  check_name
  read -p "Are you sure you want to delete $name? [yN] " -r
  if [[ $REPLY =~ ^[Yy]$ ]]
  then
    rm -R "$instance_state_dir"
  fi
  echo
}


cmd_clean()
{
  read -p "Are you sure you want to delete all saved simulator state? [yN] " -r
  if [[ $REPLY =~ ^[Yy]$ ]]
  then
    rm -R "$state_dir"
  fi
  echo
}


if [ "$cmd" = "save" ]
then
  cmd_save
elif [ "$cmd" = "restore" ]
then
  cmd_restore
elif [ "$cmd" = "list" ] || [ "$cmd" = "ls" ]
then
  cmd_list
elif [ "$cmd" = "rm" ]
then
  cmd_rm
elif [ "$cmd" = "clean" ]
then
  cmd_clean
elif [ "$cmd" = "pwd" ]
then
  echo "$app_dir"
elif [ "$cmd" = "open" ]
then
  open -R "$app_dir"
else
  usage
fi
