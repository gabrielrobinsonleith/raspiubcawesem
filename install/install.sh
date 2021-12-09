#!/usr/bin/env bash
# Install script for Raspberry Pi

GREEN=`tput setaf 2`
RESET=`tput sgr0`

# Exit if any command fails
set -e

sudo apt-get update
sudo apt-get upgrade -y

echo "${GREEN}Installing general packages...${RESET}"
sudo apt-get install -y authbind dnsmasq hostapd

echo "${GREEN}Installing python packages...${RESET}"
sudo apt-get install -y python3 python3-pip

echo "${GREEN}Installing awesem python package...${RESET}"
cd ..
pip3 install -e .

# Optional: Fix locale settings
# echo "${GREEN}Updating locale to en_US.UTF-8...${RESET}"
# sudo perl -pi -e 's/# en_US.UTF-8 UTF-8/en_US.UTF-8 UTF-8/g' /etc/locale.gen
# sudo locale-gen en_US.UTF-8
# sudo update-locale en_US.UTF-8

echo "${GREEN}Configuring webapp to be hosted on port 80 without root access...${RESET}"
sudo touch /etc/authbind/byport/80
sudo chmod 777 /etc/authbind/byport/80

# Update PATH environment for current terminal session
source ~/.bashrc

echo "${GREEN}Please run `sudo raspi-config` to enable the I2C interface.${RESET}"

echo "${GREEN}Install completed.${RESET}"
