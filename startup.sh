#!/bin/sh

sh /home/pi/init_ttyAMA0.sh

# Note make sure to background these:
python /home/pi/watch_4_shutdown.py &

python /home/pi/take_pics.py > /home/pi/take_pics.log &

