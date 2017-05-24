#!/usr/bin/env python

# Uses pynmea2 rather than gpsd plus python-gps for obtaining the gps data
# https://github.com/Knio/pynmea2

import os, sys
import time
import serial
import re

from picamera import PiCamera
import pynmea2

gps_dev = '/dev/ttyAMA0'

def get_session_dir():
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

    dir_name = '/media/pi'
    session = 0
    int_re = re.compile(r"^\d+$")

    base_path = None
    for name in os.listdir(dir_name):
        # Grab the first non-numeric directory name. Note that this may
        # break if there are more than one non-numeric directory name
        # hanging off of /media/pi
        if int_re.match(str(name)) is None:
            base_path = os.path.join(dir_name, name)
            break

    if base_path is not None:
        for name in os.listdir(base_path):
            path = os.path.join(base_path, name)

            if os.path.isdir(path):
                if int_re.match(str(name)) is not None:
                    if int(name) > session:
                        session = int(name)

        session = session + 1

        path = os.path.join(base_path, "%04i" % session)

        if not os.path.exists(path):
            os.makedirs(path)

        if os.path.exists(path):
            return path

    print ("Unable to determine session directory")
    sys.exit()


print("Seeking session directory")
session_dir = get_session_dir()
print("Session directory is %s" % session_dir)

print("Initializing camera")
camera = PiCamera()
camera.start_preview()
camera.resolution = (1600, 1200)
time.sleep(10)


def main ():

    print("Opening GPS data stream")
    f = open(gps_dev)
    reader = pynmea2.NMEAStreamReader(f)

    # It seems that there may be a certain amount of flushing needed
    # initially to get the old values out of the stream. Reading data
    # for a couple of seconds works; one second may also work. What
    # doesn't work is relying on the GPS output. There is also the issue
    # where the first reading from the stream isn't a full NMEA string
    # and that can cause the reader to throw an exception. We don't
    # really care about any initial errors as long as we don't continue
    # to get errors-- if the errors continue then it may be necessary to
    # verify that /dev/ttyAMA0 has been initialized.
    t0 = time.time()
    while (time.time() - t0) < 2:
        try:
            reader.next()
        except:
            pass

    working_dir = session_dir
    idx = 0  # index number for naming the output files
    sdx = 0  # subdirectory index number for naming the subdirectories
    gga = '' # for holding the current $GPGGA output line
    gsa = '' # for holding the current $GPGSA output line
    rmc = '' # for holding the current $GPRMC output line
    zda = '' # for holding the current $GPZDA output line

    print("Reading GPS data stream")
    t1 = time.time()

    testing = False           # For short run testing purposes
    t0 = time.time()          # For short run testing purposes
    guard = time.time() - t0  # For short run testing purposes
    while True:

        # Are we testing and is the test over?
        guard = time.time() - t0
        if testing and guard > 60:
            print("Test run finished")
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
                print("Unable to create working directory %s" % working_dir)
                sys.exit()

            print("Working directory is now %s" % working_dir)

        try:
            for msg in reader.next():

                tst = str(msg)

                # For the GPS hat at least, the first line out for a
                # given point in time will be the $GPGGA line. Therefore
                # we can use that to ensure that the readings are all for
                # the same moment in time. That is, done't populate the
                # other values until we've seen the GGA value.
                if tst.find("GGA") > 0:
                    gga = tst
                elif tst.find("GSA") > 0 and len(gga) > 0:
                    gsa = tst
                elif tst.find("RMC") > 0 and len(gga) > 0:
                    rmc = tst
                elif tst.find("ZDA") > 0 and len(gga) > 0:
                    zda = tst

                if ( len(gga) > 0 and len(gsa) > 0 and len(rmc) > 0 and len(zda) > 0 ):

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
                        idx = idx + 1
                        gps_info = "%i\n%s\n%s\n%s\n%s\n\n" % (guard, gga, gsa, rmc, zda)
                        take_picture (working_dir, idx, gps_info)

                    gga = ''
                    gsa = ''
                    rmc = ''
                    zda = ''

        except:
            print ("guard: %i ERROR" % guard)
            pass

def take_picture( working_dir, idx, gps_info ):
    pic_file = ( '%s/%08i.jpg' % (working_dir, idx) )
    gps_file = ( '%s/%08i.gps' % (working_dir, idx) )

    try:
        camera.capture(pic_file)
        fo = open(gps_file, "w")
        fo.write(gps_info)
        fo.close()

    except:
        print ("Whoopsie! Could not take a picture for %s" % pic_file)
        throw

if __name__ == '__main__':
    main()
