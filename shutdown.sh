#!/bin/sh

echo "#################################################################" >> /home/pi/data/dmesg.stop
date >> /home/pi/data/dmesg.stop
dmesg >> /home/pi/data/dmesg.stop

echo "#################################################################" >> /home/pi/data/messages.stop
date >> /home/pi/data/messages.stop
cat /var/log/messages >> /home/pi/data/messages.stop

echo "#################################################################" >> /home/pi/data/meminfo.stop
date >> /home/pi/data/meminfo.stop
cat /proc/meminfo >> /home/pi/data/meminfo.stop

sudo shutdown -h now
