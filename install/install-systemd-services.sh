#!/usr/bin/env bash
# Install systemd service

main_service=awesem-webapp.service

SKIP_ENABLE=false

usage()
{
    echo "usage: $BASH_SOURCE [--skip-enable]"
    echo "   -s, --skip-enable   Skip enabling the main systemd service"
}

while [ "$1" != "" ]; do
    case $1 in
        -s | --skip-enable )
            SKIP_ENABLE=true
            ;;

        * ) shift
            usage; exit
            ;;
    esac
    shift
done

# Check if script is run as root
if ! [ $(id -u) = 0 ]; then
    echo "Please run the script as root."
    exit 1
fi

cp $main_service /etc/systemd/system
echo "Copied $main_service to /etc/systemd/system"

if [ "$SKIP_ENABLE" = false ]; then
    echo "Enabling $main_service to start on reboot..."
    systemctl enable $main_service

    systemctl daemon-reload

    systemctl start $main_service
fi

echo "Finished."
