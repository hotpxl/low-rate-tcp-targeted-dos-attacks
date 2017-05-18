#!/bin/bash
set -euo pipefail

if [[ "${UID}" -ne 0 ]]; then
  echo "You must be root to run this."
  exit 1
fi

for period in $(seq 1.6 0.1 2.0); do
    mn -c 2> /dev/null
    killall -9 python dd nc tshark dumpcap || true
    python dos.py --rto=1000 --period "${period}" --burst 0.1
    killall -9 python dd nc tshark dumpcap || true
done
