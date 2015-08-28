#! /usr/bin/python
# -*- coding: utf-8 -*-
"""
PiSlideshow
===========

Authors: Gary Fletcher, Barnaby Shearer

© 2015 GPLv2
"""
from __future__ import division, absolute_import, print_function, unicode_literals

RIGHT_BUTTON = 15
LEFT_BUTTON = 14
SD_MOUNT_NAME = "/media/SECRET/"
IMAGES = "/usr/share/nginx/www/images/"

import logging
import dbus
import ctypes
from logging.handlers import SysLogHandler
import RPi.GPIO as GPIO
from os.path import isdir
from os import remove, rmdir
from glob import glob
from time import sleep
from shutil import copyfile
import uinput
libc = ctypes.CDLL("libc.so.6")

#Log to syslog
log = logging.getLogger(__name__)
log.setLevel(logging.DEBUG)
log.addHandler(SysLogHandler(address='/dev/log', facility=SysLogHandler.LOG_DAEMON))

#Create a virtual keyboard
keyboard = uinput.Device([uinput.KEY_LEFT, uinput.KEY_RIGHT, uinput.KEY_F5])

def left(_):
    log.info("Left button pressed")
    keyboard.emit_click(uinput.KEY_LEFT)

def right(_):
    log.info("Right button pressed")
    keyboard.emit_click(uinput.KEY_RIGHT)

def setup():
    #Register edge detection inteturpts using the CPUs hardware debounce
    GPIO.setmode(GPIO.BCM)
    GPIO.setwarnings(False)
    GPIO.setup(LEFT_BUTTON, GPIO.IN, GPIO.PUD_UP)
    GPIO.setup(RIGHT_BUTTON, GPIO.IN, GPIO.PUD_UP)
    GPIO.add_event_detect(LEFT_BUTTON, GPIO.FALLING, callback=left, bouncetime=500)
    GPIO.add_event_detect(RIGHT_BUTTON, GPIO.FALLING, callback=right, bouncetime=500)

def unmount(device_file):
    libc.sync()
    for dev in [
            dbus.SystemBus().get_object(
                'org.freedesktop.UDisks',
                disk
            )
        for
            disk
        in
            dbus.Interface(
                dbus.SystemBus().get_object(
                    'org.freedesktop.UDisks',
                    '/org/freedesktop/UDisks'
                ),
                'org.freedesktop.UDisks'
            ).EnumerateDevices()
        ]:
        if dbus.Interface(
            dev,
            'org.freedesktop.DBus.Properties'
        ).Get(
            '',
            'DeviceFile'
        ) == device_file:
            dbus.Interface(
                dev,
                'org.freedesktop.DBus.UDisks.Device'
            ).get_dbus_method(
                'FilesystemUnmount',
                dbus_interface='org.freedesktop.UDisks.Device'
            )([])

setup()

#Loop forever
while True:
    sleep(2)
    #If the automounter mounts a SD card with the right label
    if isdir(SD_MOUNT_NAME):
        log.info("found usb")
        file_count = 0
        for filename in glob(SD_MOUNT_NAME + "*.jpg"):
            log.info(filename)
            if file_count == 0:
                #Remove old files
                for oldfile in glob(IMAGES + "*.jpg"):
                    remove(oldfile)
            file_count += 1
            #Copy new file
            copyfile(filename, IMAGES + filename[len(SD_MOUNT_NAME):])
        #log.info("Unmounting")
        unmount("/dev/sda1")
        rmdir(SD_MOUNT_NAME)
        #log.info("Refreshing Browser")
        keyboard.emit_click(uinput.KEY_F5)
