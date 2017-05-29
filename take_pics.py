#!/usr/bin/env python

# Uses pynmea2 rather than gpsd plus python-gps for obtaining the gps data
# https://github.com/Knio/pynmea2

import os, sys
import time
import serial
import re
import traceback

from picamera import PiCamera
import pynmea2

gps_dev = '/dev/ttyAMA0'
log_file = '/home/pi/take_pics.log'

camera = PiCamera()

def loggit (sl, msg):
    sl.write(msg)
    sl.write("\n")
    sl.flush()

def get_session_dir(sl):
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

    dir_name = '/home/pi/data'
    session = 0
    int_re = re.compile(r"^\d+$")

    for name in os.listdir(dir_name):
        path = os.path.join(dir_name, name)
        loggit(sl, "Checking path %s" % path)

        if os.path.isdir(path):
            loggit(sl, "   path %s is directory" % path)

            if int_re.match(str(name)) is not None:
                loggit(sl, "   name %s is numeric" % name)

                if int(name) > session:
                    session = int(name)
                    loggit(sl, "      session %i" % session)

    session = session + 1

    path = os.path.join(dir_name, "%04i" % session)

    if not os.path.exists(path):
        os.makedirs(path)

    if os.path.exists(path):
        return path

    loggit(sl, "Unable to determine session directory")
    sys.exit()


def main ():

    sl = open(log_file, 'w+')
    loggit(sl, "Seeking session directory")
    session_dir = get_session_dir(sl)
    loggit(sl, "Session directory is %s" % session_dir)

    loggit(sl, "Initializing camera")
    camera.start_preview()
    camera.resolution = (1600, 1200)
    time.sleep(10)
    camera.capture('test_pic.jpg')

    loggit(sl, "Opening GPS data stream")

    f = open(gps_dev)
    reader = pynmea2.NMEAStreamReader(f)

    # It seems that there may be a certain amount of flushing needed
    # initially to get the old values out of the stream. Reading data for
    # a couple of seconds works; one second may also work. What doesn't
    # work is relying on the GPS output to indicate when the stream is
    # "ready". There is also the issue where the first reading from the
    # stream isn't always a full NMEA string and that can cause the
    # reader to throw an exception. We don't really care about any
    # initial errors as long as we don't continue to get errors-- if the
    # errors continue then it may be necessary to verify that
    # /dev/ttyAMA0 has been initialized.

    t0 = time.time()
    while (time.time() - t0) < 2:
        try:
            reader.next()
        except:
            pass

    working_dir = session_dir
    idx = 0  # index number for naming the output files
    sdx = 0  # subdirectory index number for naming the subdirectories
    tst = None
    gps_data = ''

    loggit(sl, "Reading GPS data stream")
    t1 = time.time()

    testing = True           # For short run testing purposes
    t0 = time.time()          # For short run testing purposes
    t_run = time.time() - t0  # For short run testing purposes
    while True:

        # Are we testing and is the test over?
        t_run = time.time() - t0
        if testing and t_run > 20:
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
                sys.exit()

            loggit(sl, "Working directory is now %s" % working_dir)

        try:
            for msg in reader.next():

                tst = str(msg)

                # For the GPS hat at least, the first line out for a
                # given point in time will be the $GPGGA line. Therefore
                # we can use that to ensure that the readings are all for
                # the same moment in time. That is, done't populate the
                # other values until we've seen the GGA value.
                if tst.find("GGA") > 0:

                    # We want to take a picture every two seconds.
                    # Testing indicates that if we compare >= 2 then it
                    # will sometimes be three seconds between pictures
                    # and if we compare > 1 then it will sometimes be
                    # only one second between pictures. Testing against
                    # a value just a bit under 2 (like 1.9) should work
                    # just fine.
                    if (time.time() - t1) * 1.0 >= 1.9:
                        # At this point we want to take a picture and
                        # reset our timer value t1
                        t1 = time.time()

                        # Write the previous GPS data
                        if idx > 0:
                            gps_info = "%i\n%s\n\n" % (t_run, gps_data)
                            write_gps_data (working_dir, idx, gps_info, sl)

                        # Take the current picture
                        idx = idx + 1
                        take_picture (working_dir, idx, sl)

                    gps_data = tst + "\n"

                else:
                    gps_data = gps_data + tst + "\n"

        except:
            loggit(sl, "ERROR! t_run = %i" % t_run)
            loggit(sl, traceback.format_exc())
            pass

def take_picture( working_dir, idx, sl ):
    pic_file = ( '%s/%08i.jpg' % (working_dir, idx) )

    try:
        camera.capture(pic_file)

    except:
        loggit(sl, "ERROR! Could not take a picture for %s" % pic_file)
        loggit(sl, traceback.format_exc())
        throw

def write_gps_data( working_dir, idx, gps_info, sl ):
    gps_file = ( '%s/%08i.gps' % (working_dir, idx) )

    try:
        fo = open(gps_file, "w")
        fo.write(gps_info)
        fo.close()

    except:
        loggit(sl, "ERROR! Could not store GPS data for %s" % gps_file)
        loggit(sl, traceback.format_exc())
        throw


if __name__ == '__main__':
    main()
