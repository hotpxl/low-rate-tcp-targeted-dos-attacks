#!/bin/bash

# Note: Mininet must be run as root.  So invoke this shell script
# using sudo.

# Do some cleanup first.
mn -c
killall -9 iperf
killall -9 ping

python dos.py
