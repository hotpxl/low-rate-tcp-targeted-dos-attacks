#!/bin/bash
set -euo pipefail

if [[ "${UID}" -ne 0 ]]; then
  echo "You must be root to run this."
  exit 1
fi

# "full" mode runs more period and burst combinations.
full=false
while getopts 'abfv' flag; do
  case "${flag}" in
    f) full=true ;;
    *) error "Use either 'sudo ./run.sh' or 'sudo ./run.sh -f'." ;;
  esac
done

max_burst=0.15
max_period=1.5
if [ "$full" = true ]; then
  max_burst=0.25
  max_period=2.0
fi

START_TIME=`date +%Y%m%d-%H%M%S`
HOSTNAME=`hostname`
echo "Run $START_TIME on $HOSTNAME started."

for burst in $(seq 0.15 0.05 ${max_burst}); do
  for period in $(seq 0.5 0.05 ${max_period}); do
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
