#!/bin/bash
set -euo pipefail
if [[ $# -ne 1 ]]; then
  printf "Usage: %s <target>\n" $0
  exit 1
fi

dd if=/dev/zero bs=1MB count=10 | nc "$1" 12345
