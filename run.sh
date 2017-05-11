#!/bin/bash

# Note: Mininet must be run as root.  So invoke this shell script
# using sudo.
if [[ "${UID}" -ne 0 ]]; then
    echo "You must be root to run this."
    exit 1
fi

# Do some cleanup first.
mn -c
killall -9 iperf
killall -9 ping

for period in $(seq 0 0.1 2); do
    python dos.py --period $period
done
