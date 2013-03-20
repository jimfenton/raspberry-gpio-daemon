#!/usr/bin/python

# gpiod.py - Daemon to process Raspberry Pi GPIO calls
#              for non-root processes such as Apache
#
# Copyright (c) 2013 Jim Fenton
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to
# deal in the Software without restriction, including without limitation the
# rights to use, copy, modify, merge, publish, distribute, sublicense, and/or
# sell copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in
# all copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL
# THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.
#

__version__="0.1.0"

import sys
import os
import socket
import stat
import traceback
import time
import daemon
import syslog
import signal
import lockfile
import RPi.GPIO as GPIO

# Commands:
# - All commands are initiated by the client program and are terminated by a newline character.
# - *port* is the pin number on the RPi connector, not the Broadcom channel number.
# - One response is generated per command, also terminated by a newline character.
# - Commands are case-independent.
#- Lines beginning with # are treated as comments
#
# Command syntax
#
# SETUP *port* OUT [LOW|HIGH]
#
# Sets *port* as output. Optional parameter LOW or HIGH specifies the initial state of the port. Responds with 'ok' or an error message.
#
# SETUP *port* IN [PULLUP|PULLDOWN]
#
# Sets *port* as input. Optional parameter PULLUP or PULLDOWN specifies whether a pull up or pull down resistor is configured on the port; the default is no pull up or pull down. Responds with 'ok' or an error message.
#
# OUTPUT *port* LOW|HIGH
#
# Sets the state of the specified output port, and responds with 'ok' or an error message.
#
# INPUT *port*
#
# Reads the specified input port, and responds with its state: 'true' or 'false' or an error message.
#
# Examples
#
#    SETUP 16 IN PULLUP
#    OUTPUT 11 HIGH
#    INPUT 16


def gpio_command(cmd):
    token = cmd[0:-1].lower().split(' ')

    try:
        port = int(token[1])
    except ValueError:
        return "error Invalid port number"
    except IndexError:
        return "error Port number not found"

    if token[0] == 'output':
        if len(token) != 3:
            return "error Command syntax error: "+cmd[0:-1]

        if token[2] == 'low':
            cmd1 = GPIO.LOW
        elif token[2] == 'high':
            cmd1 = GPIO.HIGH
        else:
            return "error Command syntax error: "+cmd[0:-1]

        try:
            GPIO.output(port, cmd1)
        except GPIO.WrongDirectionException:
            return "error Wrong direction exception"
        return 'ok'

    elif token[0] == 'input':
        if len(token) != 2:
            return "error Command syntax error: "+cmd[0:-1]

        try:
            if (GPIO.input(port)):
                return 'true'
            else:
                return 'false'
        except GPIO.WrongDirectionException:
            return "error Wrong direction exception"

    elif token[0] == 'setup':
        if len(token) < 3 or len(token) > 4:
            return "error Command syntax error: "+cmd[0:-1]

        if token[2] == 'out':
            if len(token) == 3:
                GPIO.setup(port, GPIO.OUT)
                return 'ok'

            else:
                if token[3] == 'low':
                    cmd1 = GPIO.LOW
                elif token[3] == 'high':
                    cmd1 == GPIO.HIGH
                else:
                    return "error Command syntax error: "+cmd[0:-1]
                GPIO.setup(port, GPIO.OUT, initial=cmd1)
                return 'ok'

        elif token[2] == 'in':
            if len(token) == 3:
                GPIO.setup(port, GPIO.IN)
                return 'ok'

            else:
                if token[3] == 'pullup':
                    cmd1 = GPIO.PUD_UP
                elif token[3] == 'pulldown':
                    cmd1 = GPIO.PUD_DOWN
                else:
                    return "error Command syntax error: "+cmd[0:-1]
                GPIO.setup(port, GPIO.IN, pull_up_down=cmd1)
                return 'ok'

    else:
        return "error Command syntax error: "+cmd[0:-1]

def gpio_main():

    syslog.syslog("gpiod: starting gpio_main")

    GPIO.setmode(GPIO.BOARD)
    GPIO.setwarnings(False)

# Read initialization commands from /etc/gpiod.cfg

    try:
        with open("/etc/gpiod.cfg","r") as f:
            cmd = "#"
            while cmd:
                if cmd[0] != "#":
                    response = gpio_command(cmd)
                    if response[0:4] == "error":
                        syslog.syslog("gpiod: "+response)
                cmd=f.readline()
    except IOError:
        pass

# End initialization. Open socket and wait for connections with further commands

    s = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
    sockfile = "/var/run/gpiod.sock"
    try:
        os.remove(sockfile)
    except OSError:
        pass
    s.bind(sockfile)
    os.chmod(sockfile, stat.S_IRUSR | stat.S_IWUSR | stat.S_IRGRP | stat.S_IWGRP | stat.S_IROTH | stat.S_IWOTH)
    s.listen(1)
    conn, addr = s.accept()

    try:
        while True:
            cmd = ""
            while not cmd or cmd[-1] != '\n':
                c = conn.recv(64)  #commands are all short, so 64 should be plenty
                while not c:       #handle closed socket, discard any partial command
                    s.listen(1)
                    conn, addr = s.accept()
                    c = conn.recv(64)
                    cmd = ""
                cmd += c

            response = gpio_command(cmd)

            conn.send(response+'\n')                
    
    except:
        conn.close()
        syslog.syslog("gpiod: Unexpected error:" + traceback.format_exc())
        raise

def program_cleanup():
    conn.close()
    syslog.syslog("gpiod: exiting on signal")
    quit()
  

context = daemon.DaemonContext(
    pidfile=lockfile.FileLock('/var/run/gpiod.pid'),
    )

context.signal_map = {
    signal.SIGHUP: program_cleanup,
    }

with context:
    gpio_main()
