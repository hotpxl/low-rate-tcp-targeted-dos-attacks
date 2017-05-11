#!/bin/bash
set -euo pipefail

if [[ "${UID}" -ne 0 ]]; then
    echo "You must be root to run this."
    exit 1
fi

for period in $(seq 0 0.1 2); do
    mn -c 2> /dev/null
    killall -9 iperf 2> /dev/null || true
    killall -9 ping 2> /dev/null || true
    python dos.py --period "${period}"
done
