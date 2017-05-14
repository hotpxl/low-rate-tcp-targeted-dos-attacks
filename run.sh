#!/bin/bash
set -euo pipefail

if [[ "${UID}" -ne 0 ]]; then
  echo "You must be root to run this."
  exit 1
fi

for rto in 300 400 500 600 700 800 900 1000; do
  for burst in 0.15 0.3 0.45 0.6; do
    for period in $(seq 0.5 0.1 2); do
      mn -c 2> /dev/null
      killall -9 python || true
      python dos.py --rto "${rto}" --period "${period}" --burst "${burst}"
    done
  done
done
