#!/usr/bin/env python

# No longer uses pynmea2 (https://github.com/Knio/pynmea2) for obtaining
# the gps data. Doesn't user gpsd plus python-gps either. Simply uses
# serial to read the GPS dev output.

import os, sys
import time
import serial
import re
from picamera import PiCamera

gps_dev = '/dev/ttyAMA0'
log_file = '/home/pi/take_pics.log'
data_dir = '/home/pi/data'
pic_int = 2 # seconds between pictures
testing = False           # For short run testing purposes

camera = PiCamera()

class GPStream:
    # Ref: http://doschman.blogspot.com/2013/01/parsing-nmea-sentences-from-gps-with.html

    def __init__(self, serialport, baudratespeed, sl):

        self.gpsdevice = serial.Serial(port=serialport, baudrate=baudratespeed, timeout=10)
        self.serialport = serialport
        self.baudratespeed = baudratespeed
        self.sl = sl
        self.error_count = 0

        self.init()

    def reopen(self):
        self.gpsdevice.close()
        self.gpsdevice = serial.Serial(port=self.serialport, baudrate=self.baudratespeed, timeout=5)
        self.init()

    def init(self):
        if self.isOpen():
            return True

        return False

    def open(self):
        self.gpsdevice.open()

    def close(self):
        self.gpsdevice.close()

    def isOpen(self):
        return self.gpsdevice.isOpen()

    def readBuffer(self):
        data = ''
        try:
            data = self.gpsdevice.read(1)
            n = self.gpsdevice.inWaiting()
            if n:
                data = data + self.gpsdevice.read(n)

        except Exception, e:
            sl.write("Big time read error, what happened:\n")
            sl.write(e)
            sl.write("\n")
            sl.flush()
            self.error_count = self.error_count + 1

            if self.error_count < 10:
                self.reopen()
            else:
                sys.exit(1)

        return data


def loggit (sl, msg):
    sl.write(msg)
    sl.write("\n")
    sl.flush()

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
        #loggit(sl, "Checking path %s" % path)

        if os.path.isdir(path):
            #loggit(sl, "   path %s is directory" % path)

            if int_re.match(str(name)) is not None:
                #loggit(sl, "   name %s is numeric" % name)

                if int(name) > session:
                    session = int(name)
                    #loggit(sl, "      session %i" % session)

    session = session + 1

    path = os.path.join(dir_name, "%04i" % session)

    if not os.path.exists(path):
        os.makedirs(path)

    if os.path.exists(path):
        loggit(sl, "Session path is: %s" % path)
        return path

    loggit(sl, "Unable to determine session directory")
    sys.exit(1)


def main ():

    sl = open(log_file, 'w+')
    loggit(sl, "Seeking session directory")
    session_dir = get_session_dir(sl, data_dir)
    loggit(sl, "Session directory is %s" % session_dir)

    sess_log_file = ( '%s/session.log' % session_dir )
    sl.close()
    sl = open(sess_log_file, 'w+')


    loggit(sl, "Initializing camera")
    camera.start_preview()
    camera.resolution = (1600, 1200)
    time.sleep(10)
    #camera.capture('test_pic.jpg')

    loggit(sl, "Opening GPS data stream")

    reader = GPStream(gps_dev, 9600, sl)
    if not reader.isOpen():
        loggit(sl, "ERROR!: Could not open GPS data stream")
        sys.exit(1)

    # It seems that there may be a certain amount of flushing needed
    # initially to get the old values out of the stream. We don't want
    # to immediately take a slew of pictures just because of "old" data
    reader.readBuffer()

    working_dir = session_dir
    idx = 0  # index number for naming the output files
    sdx = 0  # subdirectory index number for naming the subdirectories
    gps_data = ''
    buf = ''
    line = ''

    loggit(sl, "Reading GPS data stream")

    t0 = time.time()
    t1 = time.time()
    while reader.isOpen():

        # Are we testing and is the test over?
        if testing and idx > 10:
            loggit(sl, "Test run finished")
            sys.exit()

        # Set the working dir to sub-directory to keep the files per
        # directory to a reasonable quantity. Half an hour should result
        # in 1800 files (900 images and 900 GPS data files).
        if int ( idx / 900 ) + 1 != sdx:
            sdx = int ( idx / 900 ) + 1

            working_dir = os.path.join(session_dir, "%04i" % sdx)

            if not os.path.exists(working_dir):
                os.makedirs(working_dir)

            if not os.path.exists(working_dir):
                loggit(sl, "Unable to create working directory %s" % working_dir)
                sys.exit(1)

            loggit(sl, "Working directory is now %s" % working_dir)

        # Feed the buffer
        buf = buf + reader.readBuffer()

        # Have we read one or more nmea lines into our buffer?
        while re.search("\n", buf):

            # Grab the first line from the buffer
            line, buf = buf.split("\n", 1)

            # For the GPS hat at least, the first line out for a
            # given point in time will be the $GPGGA line. Therefore
            # we can use that to ensure that the readings are all for
            # the same moment in time.
            if line.find("GGA") > 0:

                # Remember that we only want to take a picture every
                # pic_int seconds

                # We want to take a picture every pic_int seconds.
                # Testing indicates that pic_int == 2 and if we
                # compare >= 2 then it will sometimes be three seconds
                # between pictures and if we compare > 1 then it will
                # sometimes be only one second between pictures.
                # Testing against a value just a bit under 2 (like 1.9)
                # should work just fine.
                if (time.time() - t1) * 1.0 >= pic_int * 1.0 - 0.1:

                    # Write the previous GPS data
                    t_run = time.time() - t0
                    write_gps_data (working_dir, idx, gps_data, sl)

                    # Start accumulating the current GPS data
                    gps_data = "%i\r\n" % t_run

                    # Take the current picture
                    idx = idx + 1
                    take_picture (working_dir, idx, sl)

                    # Reset our timer value t1
                    t1 = time.time()

            gps_data = gps_data + line + "\n"

def take_picture( working_dir, idx, sl ):
    pic_file = ( '%s/%08i.jpg' % (working_dir, idx) )

    try:
        camera.capture(pic_file)

    except Exception, e:
        loggit(sl, "ERROR! Could not take a picture for %s" % pic_file)
        loggit(sl, e)
        throw

def write_gps_data( working_dir, idx, gps_info, sl ):
    gps_file = ( '%s/%08i.gps' % (working_dir, idx) )

    try:
        fo = open(gps_file, "w")
        fo.write(gps_info)
        fo.close()

    except Exception, e:
        loggit(sl, "ERROR! Could not store GPS data for %s" % gps_file)
        loggit(sl, e)
        throw


if __name__ == '__main__':
    main()
