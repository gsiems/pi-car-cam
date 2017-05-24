## WiFI Setup

Purpose: to configure the WiFi on the Pi to act as a WiFi end-point (or
dead-end hot spot) so the the Pi can be connected to from a
laptop/tablet/whatever when on the road and no other network is available.

I **think** the primary reference used was: https://learn.adafruit.com/setting-up-a-raspberry-pi-as-a-wifi-access-point?view=all

Note that there are some perl one-liners below-- this is nothing to get
too excited about. While it isn't necessary to use perl to perform file
edits, I tend to do just that as the edit is in-place, I find it easier
than schlepping things around with sed, and it is less ambiguous than
describing the edit to be made.

### Given

* A raspberry Pi-2b running Raspbian Jessie

* A USB "Wi-Pi" dongle

### Install the necessary software

```
apt-get install hostapd isc-dhcp-server
```

### Backup/edit /etc/dhcp/dhcpd.conf

```
cp -a /etc/dhcp/dhcpd.conf{,.orig}

cat <<'EOT'>>/etc/dhcp/dhcpd.conf

subnet 192.168.42.0 netmask 255.255.255.0 {
    range 192.168.42.10 192.168.42.50;
    option broadcast-address 192.168.42.255;
    option routers 192.168.42.1;
    default-lease-time 600;
    max-lease-time 7200;
    option domain-name "local";
    option domain-name-servers 8.8.8.8, 8.8.4.4;
}
EOT
```

### Backup/edit /etc/default/isc-dhcp-server

Set the interfaces to wlan0:

```
cp -a /etc/default/isc-dhcp-server{,.orig}

perl -pi -e 's/INTERFACES=""/INTERFACES="wlan0"/' /etc/default/isc-dhcp-server
```

### Backup/edit /etc/network/interfaces

```
cp -a /etc/network/interfaces{,.orig}

vi /etc/network/interfaces
```

Make the wlan0 section to look like:

```
allow-hotplug wlan0
iface wlan0 inet static
    address 192.168.42.1
    netmask 255.255.255.0
```

The file diff should look something like:

```
diff /etc/network/interfaces{,.orig}
15,17c15,16
< face wlan0 inet static
<     address 192.168.42.1
<     netmask 255.255.255.0
---
> iface wlan0 inet manual
>     wpa-conf /etc/wpa_supplicant/wpa_supplicant.conf
```

### Assign an IP to wlan0

```
ifconfig wlan0 192.168.42.1
```

### Create /etc/hostapd/hostapd.conf

Note that the driver may not actually be nl80211 (could be rtl871xdrv
or something else depending on the WiFi dongle used)

```
cat<<'EOT'>/etc/hostapd/hostapd.conf
interface=wlan0
driver=nl80211
ssid=MyPiFi
country_code=US
hw_mode=g
channel=6
macaddr_acl=0
auth_algs=1
ignore_broadcast_ssid=0
wpa=2
wpa_passphrase=ChangeMe
wpa_key_mgmt=WPA-PSK
wpa_pairwise=CCMP
wpa_group_rekey=86400
ieee80211n=1
wme_enabled=1
EOT
```

### Backup/edit /etc/default/hostapd

```
cp -a /etc/default/hostapd{,.orig}

perl -pi -e 's/#DAEMON_CONF=""/DAEMON_CONF="\/etc\/hostapd\/hostapd.conf"/' /etc/default/hostapd

perl -pi -e 's/DAEMON_CONF=/DAEMON_CONF=\/etc\/hostapd\/hostapd.conf/' /etc/init.d/hostapd
```

### Finally

```
reboot
```

At this point it should be possible to connect to the WiFi on the Pi from another device.
