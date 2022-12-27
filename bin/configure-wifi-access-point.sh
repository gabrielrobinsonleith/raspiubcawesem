#!/bin/bash
# Script to change the wifi access point name and passphrase.

usage()
{
    echo "usage: $BASH_SOURCE [-s NAME] [-p PASSPHRASE]"
    echo "   -s, --ssid ACCESS_POINT_NAME   Name of wifi access point (must be less than 32 characters)"
    echo "   -p, --passphrase PASSPHRASE    Access point passphrase"
    echo "   -n, --no-restart               Disable restarting the hostapd service"
    echo "   -v, --verbose                  Enable verbose mode"
}

CONF_FILE=/etc/hostapd/hostapd.conf
RESTART_HOSTAPD=true
VERBOSE=false

# Check if script is run as root
if ! [ $(id -u) = 0 ]; then
    echo "Please run the script as root."
    exit 1
fi

# Exit if no arguments are provided
if [ -z "$1" ]; then
    usage
    exit 1
fi

while [ "$1" != "" ]; do
    case $1 in
        -s | --ssid ) shift
            ACCESS_POINT_NAME=$1
            ;;

        -p | --passphrase ) shift
            PASSPHRASE=$1
            ;;

        -n | --no-restart )
            RESTART_HOSTAPD=false
            ;;

        -v | --verbose )
            VERBOSE=true
            ;;

        * ) shift
            usage; exit
            ;;
    esac
    shift
done

if [ "$VERBOSE" = true ]; then
    echo "--- Old file ---"
    cat $CONF_FILE
    echo "----------------"
fi

if [ ! -z "$ACCESS_POINT_NAME" ]; then
    sudo sed -i "s/^ssid=.*/ssid=$ACCESS_POINT_NAME/" $CONF_FILE
    echo "SSID changed to $ACCESS_POINT_NAME"
fi

if [ ! -z "$PASSPHRASE" ]; then
    sudo sed -ie "^wpa_passphrase=*\\/wpa_passphrase=$PASSPHRASE/" $CONF_FILE
    echo "WPA Passphrase changed to $PASSPHRASE"
fi

if [ "$VERBOSE" = true ]; then
    echo ""
    echo "--- New file ---"
    cat $CONF_FILE
    echo "----------------"
fi

if [ "$RESTART_HOSTAPD" = true ]; then
    echo "Restarting the hostapd service. Please check your wifi connection and reconnect to the updated network."
    sudo systemctl restart hostapd
else
    echo "hostapd service not restarted."
fi

