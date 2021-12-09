#!/bin/bash

rm screenlog.0

if [ -z "$1" ]
then
  echo please ever serial adapter location. ie: ./term.sh USB0 you have the following devices.
  ls /dev/ | grep USB
  ls /dev/ | grep ACM 
  exit
fi

screen -L /dev/tty${1} 115200
