#!/bin/sh

# Ensure that things are running and that other things are mounted...

[ -d /home/pi/data ] || mkdir -p /home/pi/data
mounted=`mount | grep /home/pi/data`
[ "$mounted" ] || mount /dev/sda1 /home/pi/data

# Note make sure to background the running things.
tst=`ps -ef | grep \[w]atch_4_shutdown\.py`
if [ -z "$tst" ]; then
    echo "" >> /home/pi/data/watch_4_shutdown.out
    date >> /home/pi/data/watch_4_shutdown.out
    /home/pi/watch_4_shutdown.py >> /home/pi/data/watch_4_shutdown.out 2>&1 &
fi

#pgrep take_pics.py || /home/pi/take_pics.py &
tst=`ps -ef | grep \[t]ake_pics\.py`
if [ -z "$tst" ]; then
    echo "" >> /home/pi/data/take_pics.out
    date >> /home/pi/data/take_pics.out
    /home/pi/take_pics.py >> /home/pi/data/take_pics.out 2>&1 &
fi
