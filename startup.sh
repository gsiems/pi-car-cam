#!/bin/sh

# Ensure that things are running and that other things are mounted...
# Note make sure to background the running things.

pgrep watch_4_shutdown.py || /home/pi/watch_4_shutdown.py &

[ -d /home/pi/data ] || mkdir -p /home/pi/data
mounted=`mount | grep /home/pi/data`
[ "$mounted" ] || mount /dev/sda1 /home/pi/data

pgrep take_pics.py || /home/pi/take_pics.py &
