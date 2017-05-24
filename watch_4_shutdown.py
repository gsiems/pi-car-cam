#!/usr/bin/python

import RPi.GPIO as gpio
import os
from time import sleep

# testing-- really shutdown or just "talk" about it
testing = False

# Pin number to plug the button into. The other side of the button
# connects to ground.
btn=13

# Time (in milliseconds) to require the button to be pressed before
# shutting down.
press_limit=2000

# Set pin numbering to board numbering
gpio.setmode(gpio.BOARD)

# Ensure the the button pin is pulled high lest the system shut down as
# soon as the script is started.
gpio.setup(btn, gpio.IN, pull_up_down=gpio.PUD_UP)

def main ():
    chk = True
    while (chk):
        if testing:
            print ("Waiting\n")
        gpio.wait_for_edge(btn, gpio.FALLING)
        chk = check_btn()

    # Shutdown
    gpio.cleanup(btn)
    if testing:
        print ("Goodbye\n")
    else:
        os.system('sudo shutdown now -h')

    exit

def check_btn ():
    if testing:
        print ("Checking\n")

    press_time = 0
    while press_time < press_limit:
        sleep(0.1)
        if gpio.input(btn) == 0:
            press_time = press_time + 100
        else:
            return True

    return False

if __name__ == '__main__':
    main()
