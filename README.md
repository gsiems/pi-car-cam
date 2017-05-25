# pi-car-cam

The intent is to use a Rapberry Pi to take road-trip pictures that can
be used to create a time-lapse/stop-action video of a road-trip. Bonus
points for being able to correlate the GPS coordinates of the picture
and the time that the picture was taken.

### Available materials

* A raspberry Pi-2b running Raspbian Jessie

* A [Pi Camera](https://www.adafruit.com/product/3099) or
[Pi NoIR camera](https://www.adafruit.com/product/3100)

* An ["Ultimate GPS Hat"](https://www.adafruit.com/product/2324)
(would have used/preferred a USB GPS dongle or tty setup). The Hat is
nice but is was only purchased because there wasn't anything else on
the shelf at the time. I don't believe it to be as sensitive as a
dongle (could be wrong here and maybe that depends on the dongle) and
it does complicate the desired form-factor a little but it does work.

* A USB "Wi-Pi" dongle

* Miscellaneous other bits and pieces.

### Steps

* [WiFi setup](wifi-setup.md)
* [GPS setup](gps-setup.md)
* [Camera setup](camera-setup.md)
* Add button powered [shutdown](watch_4_shutdown.py) script
* Add the [Picture taking/GPS reading](take_pics.py) script
* [Boot setup](boot-setup.md)
