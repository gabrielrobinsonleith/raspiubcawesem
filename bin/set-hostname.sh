#!/bin/sh
# Script to set the hostname. Does not require reboot to take into effect.

usage()
{
    echo "usage: $BASH_SOURCE [HOSTNAME]"
}

if test $# -eq 0
then
    echo "Please provide a name."
    usage
    exit 1
fi

# Check if script is run as root
if ! [ $(id -u) = 0 ]; then
    echo "Please run the script as root."
    exit 1
fi

HOSTNAME=$1
echo "Using hostname: $HOSTNAME"

# Change hostname read on bootup (to make permamnent)
echo $HOSTNAME | tee /etc/hostname

# Edit hosts file
sed -i -E 's/^127.0.1.1.*/127.0.1.1\t'"$HOSTNAME"'/' /etc/hosts

# Change currently used hostname
hostnamectl set-hostname $HOSTNAME

# Restart mDNS daemon so other machines can respond to the new hostname
systemctl restart avahi-daemon

echo "Hostname set. Log out to see it on the command line"
