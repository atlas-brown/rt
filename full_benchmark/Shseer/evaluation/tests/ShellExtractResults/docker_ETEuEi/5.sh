#!/bin/sh

# Check to see if we should get the nginx uid/gid from the "app" root
if [ "$APP_UID_FROM_ROOT" = "1" ]
then
    APP_UID_FROM="$APP_ROOT"
fi
if [ "$APP_GID_FROM_ROOT" = "1" ]
then
    APP_GID_FROM="$APP_ROOT"
fi
if [ "$APP_UID_GID_FROM_ROOT" = "1" ]
then
    APP_UID_GID_FROM="$APP_ROOT"
fi

# If not already set, see if there's a path to get the uid from
if [ -n "$APP_UID_FROM" ]
then
    if [ -z "$APP_UID" ]
    then
        APP_UID=`stat -c '%u' $APP_UID_FROM`
    fi
fi

# If not already set, see if there's a path to get the gid from
if [ -n "$APP_GID_FROM" ]
then
    if [ -z "$APP_GID" ]
    then
        APP_GID=`stat -c '%g' $APP_GID_FROM`
    fi
fi

# if not already set, conigure the uid
if [ -n "$APP_UID_GID_FROM" ]
then
    if [ -z "$APP_GID" ]
    then
        APP_GID=`stat -c '%g' $APP_UID_GID_FROM`
    fi

    if [ -z "$APP_UID" ]
    then
        APP_UID=`stat -c '%u' $APP_UID_GID_FROM`
    fi
fi
