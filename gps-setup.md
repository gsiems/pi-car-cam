## GPS setup

### Before attaching the GPS hat

* Ref: https://learn.adafruit.com/adafruit-ultimate-gps-hat-for-raspberry-pi

```
cat <<'EOT'>/boot/cmdline.txt
dwc_otg.lpm_enable=0 console=tty1 root=/dev/mmcblk0p2 rootfstype=ext4 elevator=deadline fsck.repair=yes rootwait
EOT

systemctl disable serial-getty@ttyAMA0.service

systemctl disable serial-getty@ttyAMA0.service
```

### Attach the GPS hat

### Install python-pynmea2

Having no guarantee that good a GPS signal will always be available,
and having decided that the best trigger for starting a new reading is
directly from the GPS hat output (there is an output every second
regardless of having a fix or not) we're going to use pynmea2 rather
than gpsd plus python-gps for obtaining the gps data.

* Ref: https://github.com/Knio/pynmea2

```
apt-get install python-pynmea2
```

Create the [init_ttyAMA0.sh](init_ttyAMA0.sh) script.


### NMEA Notes

The intent is to store all the NMEA data for each picture taken. The
Wi-Pi USB dongle streams four NMEA lines per reading:

* $GPGGA,
* $GPGSA,
* $GPRMC, and
* $GPZDA

* To quote from http://www.gpsinformation.org/dale/nmea.htm:

#### GGA

Essential fix data which provide 3D location and accuracy data.

```
$GPGGA,123519,4807.038,N,01131.000,E,1,08,0.9,545.4,M,46.9,M,,*47
```

Where:

```
     GGA          Global Positioning System Fix Data
     123519       Fix taken at 12:35:19 UTC
     4807.038,N   Latitude 48 deg 07.038' N
     01131.000,E  Longitude 11 deg 31.000' E
     1            Fix quality: 0 = invalid
                               1 = GPS fix (SPS)
                               2 = DGPS fix
                               3 = PPS fix
                               4 = Real Time Kinematic
                               5 = Float RTK
                               6 = estimated (dead reckoning) (2.3 feature)
                               7 = Manual input mode
                               8 = Simulation mode
     08           Number of satellites being tracked
     0.9          Horizontal dilution of position
     545.4,M      Altitude, Meters, above mean sea level
     46.9,M       Height of geoid (mean sea level) above WGS84 ellipsoid
     (empty field) time in seconds since last DGPS update
     (empty field) DGPS station ID number
     *47          the checksum data, always begins with *
```

If the height of geoid is missing then the altitude should be suspect.
Some non-standard implementations report altitude with respect to the
ellipsoid rather than geoid altitude. Some units do not report negative
altitudes at all. This is the only sentence that reports altitude.

### GSA

GPS DOP and active satellites. This sentence provides details on the
nature of the fix. It includes the numbers of the satellites being used
in the current solution and the DOP. DOP (dilution of precision) is an
indication of the effect of satellite geometry on the accuracy of the
fix. It is a unitless number where smaller is better. For 3D fixes
using 4 satellites a 1.0 would be considered to be a perfect number,
however for overdetermined solutions it is possible to see numbers
below 1.0.

```
$GPGSA,A,3,04,05,,09,12,,,24,,,,,2.5,1.3,2.1*39
```

Where:

```
     GSA      Satellite status
     A        Auto selection of 2D or 3D fix (M = manual)
     3        3D fix - values include: 1 = no fix
                                       2 = 2D fix
                                       3 = 3D fix
     04,05... PRNs of satellites used for fix (space for 12)
     2.5      PDOP (dilution of precision)
     1.3      Horizontal dilution of precision (HDOP)
     2.1      Vertical dilution of precision (VDOP)
     *39      the checksum data, always begins with *
```

### RMC

NMEA has its own version of essential gps pvt (position, velocity,
time) data. It is called RMC, The Recommended Minimum, which will look
similar to:

```
$GPRMC,123519,A,4807.038,N,01131.000,E,022.4,084.4,230394,003.1,W*6A
```

Where:

```
     RMC          Recommended Minimum sentence C
     123519       Fix taken at 12:35:19 UTC
     A            Status A=active or V=Void.
     4807.038,N   Latitude 48 deg 07.038' N
     01131.000,E  Longitude 11 deg 31.000' E
     022.4        Speed over the ground in knots
     084.4        Track angle in degrees True
     230394       Date - 23rd of March 1994
     003.1,W      Magnetic Variation
     *6A          The checksum data, always begins with *
```

Note that, as of the 2.3 release of NMEA, there is a new field in the
RMC sentence at the end just prior to the checksum. For more
information on this field see [here](http://www.gpsinformation.org/dale/nmea.htm#2.3).

### ZDA

Data and Time

```
$GPZDA,hhmmss.ss,dd,mm,yyyy,xx,yy*CC
$GPZDA,201530.00,04,07,2002,00,00*60
```

where:

```
    hhmmss    HrMinSec(UTC)
        dd,mm,yyy Day,Month,Year
        xx        local zone hours -13..13
        yy        local zone minutes 0..59
        *CC       checksum
```

### Steps

* [WiFi setup](wifi-setup.md)
* *GPS setup*
* [Camera setup](camera-setup.md)
* Add button powered [shutdown](watch_4_shutdown.py) script
* Add the [Picture taking/GPS reading](take_pics.py) script
* [Boot setup](boot-setup.md)
