#!/bin/sh

sudo stty -F /dev/ttyAMA0 raw 9600 cs8 clocal -cstopb

# wow, that was exciting... time for a short nap. Not sure if this is
# needed but it seems that the chmod doesn't always take (timing issue
# or race condition?)
sleep 2

sudo chmod o+r /dev/ttyAMA0
