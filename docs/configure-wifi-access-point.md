# Wifi Access Point Setup

Follow steps below to configure the Pi to serve its own wifi access point.

*Source: https://www.raspberrypi.org/documentation/configuration/wireless/access-point.md*

```
sudo apt install dnsmasq hostapd

sudo systemctl stop dnsmasq
sudo systemctl stop hostapd
```

## Configure Static IP

```
sudo vim /etc/dhcpcd.conf
```

Add the following to the end of the file:

```
interface wlan0
    static ip_address=192.168.4.1/24
    nohook wpa_supplicant
```

Restart the dhcpcd daemon:

```
sudo service dhcpcd restart
```

## Configure DHCP Server

```
sudo mv /etc/dnsmasq.conf /etc/dnsmasq.conf.orig
```

```
sudo vim /etc/dnsmasq.conf
```

Add to the bottom of the file:

```
interface=wlan0      # Use the require wireless interface - usually wlan0
dhcp-range=192.168.4.2,192.168.4.20,255.255.255.0,24h
```

```
sudo systemctl reload dnsmasq
```

## Configuring the access point host software (hostapd)

```
sudo vim /etc/hostapd/hostapd.conf
```

To use the 5 GHz band, you can change the operations mode from hw_mode=g to hw_mode=a. Possible values for hw_mode are:

- a = IEEE 802.11a (5 GHz)n
- b = IEEE 802.11b (2.4 GHz)
- g = IEEE 802.11g (2.4 GHz)
- ad = IEEE 802.11ad (60 GHz)

```
interface=wlan0
driver=nl80211
hw_mode=g
channel=7
wmm_enabled=0
macaddr_acl=0
auth_algs=1
ignore_broadcast_ssid=0
wpa=2
wpa_key_mgmt=WPA-PSK
wpa_pairwise=TKIP
rsn_pairwise=CCMP
ssid=NameOfNetwork
wpa_passphrase=SuperSecurePassword
```

We now need to tell the system where to find this configuration file.

```
sudo nano /etc/default/hostapd
```

Find the line with `#DAEMON_CONF`, and replace it with this:

```
DAEMON_CONF="/etc/hostapd/hostapd.conf"
```

## Start It Up

```
sudo systemctl unmask hostapd
sudo systemctl enable hostapd
sudo systemctl start hostapd
```

Check that it's running:

```
sudo systemctl status hostapd
sudo systemctl status dnsmasq
```

## Add Routing and Masquerade (Optional?)

```
sudo vim /etc/sysctl.conf
```

Uncomment this line:

```
net.ipv4.ip_forward=1
```

```bash
# Add a masquerade for outbound traffic on eth0
sudo iptables -t nat -A  POSTROUTING -o eth0 -j MASQUERADE

# Save the iptables rule.
sudo sh -c "iptables-save > /etc/iptables.ipv4.nat"

# Edit /etc/rc.local and add this just above "exit 0" to install these rules on boot.
iptables-restore < /etc/iptables.ipv4.nat
```

Reboot.
