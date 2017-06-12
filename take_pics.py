#!/usr/bin/env python

# No longer uses pynmea2 (https://github.com/Knio/pynmea2) for obtaining
# the gps data. Doesn't user gpsd plus python-gps either. Simply uses
# serial to read the GPS dev output.

import os, sys
import time
import serial
import re
from picamera import PiCamera
import RPi.GPIO as gpio

log_file = '/home/pi/take_pics.log'
data_dir = '/home/pi/data'
pic_int = 2 # seconds between pictures
testing = False           # For short run testing purposes

led_pin = 16

camera = PiCamera()

class Logger:

    def __init__(self, log_file):

        self.log_file = log_file
        self.sl = open(self.log_file, 'w+')


    def close(self):
        self.sl.close()

    def switchFile(self, log_file):
        try:
            self.sl.close()
        except:
            pass

        self.log_file = log_file
        self.sl = open(self.log_file, 'w+')

    def write(self, message):
        self.sl.write(message)
        self.sl.flush()

    def say(self, message):
        self.sl.write(message + "\n")
        self.sl.flush()

class LED:

    def __init__(self, pin_no):

        self.pin_no = pin_no

        gpio.setwarnings(False)
        gpio.setmode(gpio.BOARD)
        gpio.setup(self.pin_no, gpio.OUT)
        self.flash()

    def flash(self, duration=0.1):
        self.on()
        time.sleep(duration)
        self.off()

    def off(self):
        gpio.output(self.pin_no, False)

    def on(self):
        gpio.output(self.pin_no, True)

class GPStream:


    def __init__(self, sl):

        self.port = '/dev/ttyAMA0'
        self.baudrate = 9600
        self.timeout = 5
        self.sl = sl
        self.error_count = 0

        try:
            self.gpsdevice = serial.Serial(port=self.port, baudrate=self.baudrate, timeout=self.timeout)

        except serial.SerialException as e:
            self.sl.say("Could not open GPS device '{}': {}".format(self.port, e))

#    def init(self):
#        if self.isOpen():
#            return True
#
#        return False

    def isOpen(self):
        try:
            if self.gpsdevice.isOpen():
                return True
        except serial.SerialException as e:
            self.sl.say("Could not check GPS device status '{}': {}".format(self.port, e))

        return False

    def reopen(self):
        try:
            self.gpsdevice.close()
        except:
            pass

        try:
            time.sleep(0.1)
            self.gpsdevice.open()

        except serial.SerialException as e:
            self.sl.say("Could not reopen GPS device '{}': {}".format(self.port, e))

    def readBuffer(self):
        data = ''
        if self.isOpen():
            try:
                n = self.gpsdevice.inWaiting()
                if n:
                    data = self.gpsdevice.read(n)

            except Exception as e:
            #except serial.SerialException as e:
                self.sl.say("Read error on GPS device '{}': {}".format(self.port, e))
                self.reopen()

        else:
            self.reopen()

        return data

def get_session_dir(sl, dir_name):
    """ The idea here is to write the files to an external drive. On
    the Pi2 there are numbered directories under /media/pi-- we don't
    want to write to any of them. Instead, we want to write to the
    drive that has a non-numeric label as that is asserted to be the
    singular USB drive that we've plugged into the Pi. If there should
    be more than one non-numbered directory then this needs revisiting
    (possibly using results of `mount`?).

    Each time a new session is started then that session needs to get a
    sub-directory on the USB drive for just that session. We want the
    directory names to be sequentially numbered so it is both easier to
    determine/create the next session directory also so that the
    natural sort order of the directories reflects the chronology of
    the sessions.
    """

    session = 0
    int_re = re.compile(r"^\d+$")

    for name in os.listdir(dir_name):
        path = os.path.join(dir_name, name)
        #sl.say("Checking path %s" % path)

        if os.path.isdir(path):
            #sl.say("   path %s is directory" % path)

            if int_re.match(str(name)) is not None:
                #sl.say("   name %s is numeric" % name)

                if int(name) > session:
                    session = int(name)
                    #sl.say("      session %i" % session)

    session = session + 1

    path = os.path.join(dir_name, "%04i" % session)

    if not os.path.exists(path):
        os.makedirs(path)

    if os.path.exists(path):
        sl.say("Session path is: %s" % path)
        return path

    sl.say("Unable to determine session directory")
    sys.exit(1)


def main ():

    sl = Logger(log_file)
    sl.say("Seeking session directory")
    session_dir = get_session_dir(sl, data_dir)
    sl.say("Session directory is %s" % session_dir)

    sess_log_file = ( '%s/session.log' % session_dir )
    sl.switchFile(sess_log_file)

    sess_gps_file = ( '%s/session.gps' % session_dir )
    gpsl = Logger(sess_gps_file)

    led=LED(led_pin)

    sl.say("Initializing camera")
    camera.start_preview()
    camera.resolution = (1600, 1200)
    time.sleep(10)
    #camera.capture('test_pic.jpg')

    sl.say("Opening GPS data stream")

    reader = GPStream(sl)
    if not reader.isOpen():
        sl.say("ERROR!: Could not open GPS data stream")
        sys.exit(1)

    # It seems that there may be a certain amount of flushing needed
    # initially to get the old values out of the stream. We don't want
    # to immediately take a slew of pictures just because of "old" data
    # or have the picture associated with the wrong GPS data.
    reader.readBuffer()

    working_dir = session_dir
    idx = 0  # index number for naming the output files
    sdx = 0  # subdirectory index number for naming the subdirectories
    buf = ''
    line = ''

    sl.say("Reading GPS data stream")

    t0 = time.time()
    t1 = time.time()
    while True:

        # Are we testing and is the test over?
        if testing and idx > 10:
            sl.say("Test run finished")
            sys.exit()

        # Set the working dir to sub-directory to keep the files per
        # directory to a reasonable quantity. 1800 pictures should
        # correspond to one hour of data so there *should* end up being
        # one directory for every hour (or portion thereof) of data.
        if int ( idx / 1800 ) + 1 != sdx:
            sdx = int ( idx / 1800 ) + 1

            working_dir = os.path.join(session_dir, "%04i" % sdx)

            if not os.path.exists(working_dir):
                os.makedirs(working_dir)

            if not os.path.exists(working_dir):
                sl.say("Unable to create working directory %s" % working_dir)
                sys.exit(1)

            sl.say("Working directory is now %s" % working_dir)

        # Feed the buffer
        buf = buf + reader.readBuffer()

        # Have we read one or more lines data into our buffer?
        while re.search("\n", buf):

            # Grab the first line from the buffer
            line, buf = buf.split("\n", 1)

            # For the GPS hat at least, the first line out for a
            # given point in time will be the $GPGGA line. Therefore
            # we can use that to ensure that the readings are all for
            # the same moment in time. This assumes of course that the
            # GPS hat is behaving and that there is good output from the
            # serial reader (NOT always guaranteed).
            # If we aren't getting GPS data then we would still like a
            # picture every pic_int seconds...
            tdiff = time.time() - t1

            if ( line.find("GGA") > 0 and tdiff >= pic_int - 0.1 ) or ( tdiff >= pic_int + 0.1 ):
                # We either have read a "GGA" line and the time is close
                # enough OR we haven't read a "GGA" line and the time is
                # over the time limit.

                # Reset the timer value t1. Do this first so the time to
                # take the picture doesn't skew the time between pictures.
                t1 = time.time()

                # Take the current picture
                idx = idx + 1
                pic_file = ( '%s/%08i.jpg' % (working_dir, idx) )
                gpsl.say("PICTURE:" + pic_file)
                gpsl.say("TDIFF: {}".format(tdiff))

                try:
                    camera.capture(pic_file)
                    led.flash()

                except Exception, e:
                    sl.say("ERROR! Could not take a picture for '{}': {}".format(pic_file, e))
                    pass

                led.off()

            gpsl.say(line)

if __name__ == '__main__':
    main()
