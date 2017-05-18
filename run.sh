#!/bin/bash
set -euo pipefail

if [[ "${UID}" -ne 0 ]]; then
  echo "You must be root to run this."
  exit 1
fi

for period in $(seq 0.5 0.1 2.0); do
  for burst in $(seq 0.05 0.05 0.2); do
    mn -c 2> /dev/null
    killall -9 python dd nc tshark dumpcap || true
    python dos.py --rto=1000 --period "${period}" --burst "${burst}"
    killall -9 python dd nc tshark dumpcap || true
  done
done
