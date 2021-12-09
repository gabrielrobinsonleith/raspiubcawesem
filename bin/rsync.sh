#!/usr/bin/env bash

HOSTNAME=pi@ubcawesem.local
SOURCE_DIR=../
REMOTE_DIR=/home/pi/awesem

GREEN=`tput setaf 2`
YELLOW=`tput setaf 3`
CYAN=`tput setaf 6`
RESET=`tput sgr0`

show_help() {
  echo "Sync repository to remote pi every 5s. Script must be run from the containing directory."
  echo "Use --once flag to only run rsync once."
}

usage="$(basename "$0") [-h] [-o] Sync repository to remote pi. Script must be run from the containing directory.

Arguments:
    -o, --once   Only run rsync once"

run_rsync() {
    echo "${GREEN}$(date)${RESET}"
    rsync -avz $SOURCE_DIR $HOSTNAME:$REMOTE_DIR \
        --exclude "env/" \
        --exclude ".git/" \
        --exclude "*__pycache__*" \
        --exclude "*.pyc" \
        --exclude "awesem.egg-info/"
    echo ""
}

while :; do
    case $1 in
        -h|-\?|--help)
            echo "$usage"
            exit
            ;;
        -o|--once) flag_once="SET"
        ;;
        -i|--install) flag_install="SET"
        ;;
        *) break
    esac
    shift
done

if [ "$flag_once" ]; then
  run_rsync
elif [ "$flag_install" ]; then
  echo "${YELLOW}Uploading software...${RESET}"
  run_rsync

  echo "${YELLOW}Installing files and reloading services (this may take a while)...${RESET}"
  RESULTS=$(ssh $HOSTNAME '\
cd ~/awesem/; pip3 install -e .')
  echo "$RESULTS"

  echo "${CYAN}Update complete.${RESET}"

else
  while true; do
    run_rsync
    sleep 2
  done
fi
