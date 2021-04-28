#!/bin/bash
# script for starting/stoping/restarting kronos
# the script receives 1 argument:
# $1 = start, stop, restart
# if [ "$HOSTNAME" != "sdss5-webapp" ]
# then
#   echo "Please run kronos from sdss5-webapp! You are currently:"
#   echo $HOSTNAME
#   exit 1
# fi

# if [ "$USER" != "sdss5" ]
# then
#   echo "Please run kronos as the sdss5 user!  You are currently:"
#   echo $USER
#   exit 1
# fi

module load kronos

if [ "$1" = "stop" ]
then
  STOP="true"
  START="false"
elif [ "$1" = "start" ]
then
  START="true"
  STOP="false"
elif [ "$1" = "restart" ]
then
  START="true"
  STOP="true"
else
  echo "must supply one of start, stop, or restart."
  echo "received: $1."
  exit 1
fi


if [ "$STOP" = "true" ]
then
  echo "stopping kronos"
  kill `cat $HOME/tmp/kronos.pid`
fi

if [ "$START" = "true" ]
then
  if [ "$STOP" = "true" ]
  then
    sleep 2
  fi
  echo "starting kronos"
  hypercorn --config $KRONOS_DIR/etc/kronos.toml $KRONOS_DIR/python/kronos/app:app > $HOME/tmp/kronos.log 2>&1 &
fi
