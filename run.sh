#!/bin/bash
set -euo pipefail

if [[ "${UID}" -ne 0 ]]; then
  echo "You must be root to run this."
  exit 1
fi

START_TIME=`date +%Y%m%d-%H%M%S`
HOSTNAME=`hostname`
echo "Run $START_TIME on $HOSTNAME started."

for burst in $(seq 0.15 0.05 0.25); do
  for period in $(seq 0.5 0.1 2.0); do
    mn -c 2> /dev/null
    killall -9 python dd nc tshark dumpcap || true

   echo ""
   echo "Starting attack, burst=${burst}, period=${period}"

    python dos.py --rto=1000 --period "${period}" --burst "${burst}" \
                  --suffix "${HOSTNAME}-${START_TIME}"
    killall -9 python dd nc tshark dumpcap || true

    echo ""
    echo "Done."

    sleep 5s
  done
done

su $SUDO_USER -c ./plot_bw.py
