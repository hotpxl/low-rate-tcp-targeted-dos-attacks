#!/bin/bash
set -euo pipefail

if [[ "${UID}" != 0 ]]; then
  echo "You must be root to run this."
  exit 1
fi

usage() {
  printf "Usage: %s -t <target> [-p <TCP probe output>]\n" "$0"
  exit 1
}

PROBE_OUTPUT=
TARGET=
while getopts :p:t: OPT; do
  case "${OPT}" in
    p)
      PROBE_OUTPUT="${OPTARG}"
      ;;
    t)
      TARGET="${OPTARG}"
      ;;
    \?|:)
      usage
      ;;
  esac
done

if [[ -z "${TARGET}" ]]; then
  usage
fi

if [[ ! -z "${PROBE_OUTPUT}" ]]; then
  rmmod tcp_probe 2>/dev/null || true
  modprobe tcp_probe port=12345
  dd if=/proc/1/net/tcpprobe of="${PROBE_OUTPUT}" ibs=128 obs=128 status=none &
  PROBE_PID="$!"
  defer() {
    kill "${PROBE_PID}"
    rmmod tcp_probe
  }
  trap defer EXIT
fi

dd if=/dev/zero bs=2MB count=1 status=none | nc "${TARGET}" 12345

