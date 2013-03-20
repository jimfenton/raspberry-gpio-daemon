raspberry-gpio-daemon
=====================

## About

This is a simple daemon that facilitates access to the Raspberry Pi (RPi) GPIO ports from processes that are not running as root. This daemon, running as root, waits for connections on a Unix domain socket and implements a very simple command/response protocol to permit input and output from the GPIO ports. A typical application would be for a Web CGI script that needs access to the GPIO interface, since it's strongly advised not to run a web server as root.

### Python requirements

* [python-daemon](https://pypi.python.org/pypi/python-daemon/) 1.5.5
* [raspberry-gpio-python](https://pypi.python.org/pypi/RPi.GPIO) 0.5.0

## Commands

### General

- All commands are initiated by the client program and are terminated by a newline character.
- *port* is the pin number on the RPi connector, not the Broadcom channel number.
- One response is generated per command, also terminated by a newline character.
- Commands are case-independent.
- Lines beginning with # are treated as comments


### Command syntax

`SETUP` *port* `OUT [LOW|HIGH]`

Sets *port* as output. Optional parameter LOW or HIGH specifies the initial state of the port. Responds with 'ok' or an error message.

`SETUP` *port* `IN [PULLUP|PULLDOWN]`

Sets *port* as input. Optional parameter PULLUP or PULLDOWN specifies whether a pull up or pull down resistor is configured on the port; the default is no pull up or pull down. Responds with 'ok' or an error message.

`OUTPUT` *port* `LOW|HIGH`

Sets the state of the specified output port, and responds with 'ok' or an error message.

`INPUT` *port*

Reads the specified input port, and responds with its state: 'true' or 'false' or an error message.

### Examples

    SETUP 16 IN PULLUP
    OUTPUT 11 HIGH
    INPUT 16

## Installation

- Copy `gpiod.py` to a suitable location, such as /usr/local/sbin
- copy `gpiod` (the init script) to /etc/init.d
- Ensure that the modules listed above under Python Requirements have been installed
- Start the daemon and test with gpiotest.py
- If you want to initialize the interface when the daemon starts, create a script with gpiod commands at /etc/gpiod.cfg

## Future work

Some ideas for enhancements include:

- More comprehensive support of the GPIO port capabilities, such as event detection (although this may also imply changes to the socket protocol).
- Better initialization using a pidfile
- Ability to specify a duration for timed output pulses

## Change Log

### 0.1.0

- Initial version

