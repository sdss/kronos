#!/bin/bash
# script for starting/stoping/restarting petunia
# the script receives 1 argument:
# $1 = start, stop, restart
if [ "$HOSTNAME" != "sdss4-db" ]
then
  echo "Please run petunia from sdss4-db! You are currently:"
  echo $HOSTNAME
  exit 1
fi

if [ "$USER" != "sdss4" ]
then
  echo "Please run petunia as the sdss4 user!  You are currently:"
  echo $USER
  exit 1
fi

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
  echo "stopping petunia"
  uwsgi --stop /var/www/petunia/current/uwsgi_petunia.pid
fi

if [ "$START" = "true" ]
then
  if [ "$STOP" = "true" ]
  then
    sleep 2
  fi
  echo "starting petunia"
  # gather everything on the pythonpath and pass it to uwsgi
  # this obscure thing replaces each : in PYTHONPATH with a <space>--pythonpath<space>
  # in this way each thing on the path now (eg after a module load) gets passed to uwsgi
  ppath=${PYTHONPATH//":/"/" --pythonpath /"}
  #remove the last trailing :
  ppath=${ppath//":"}
  fullcmd="$PETUNIA_DIR/python/petunia/uwsgi_conf_files/uwsgi_sdssdb4_production.ini --pythonpath $ppath"
  #echo "full cmd: $fullcmd"
  uwsgi $fullcmd
fi
