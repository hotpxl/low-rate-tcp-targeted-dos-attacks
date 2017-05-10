#!/usr/bin/env python
# -*- coding: utf-8 -*-
from __future__ import absolute_import
from __future__ import print_function

import argparse
import os
import time
import subprocess
import threading

import mininet.topo
import mininet.net
import mininet.node


class Topo(mininet.topo.Topo):
    def build(self):
        # Topology:
        #  A (alice) ------+
        #                  |--[s0]----[s1]----server
        #  M (mallory) ----+
        alice = self.addHost('alice')
        mallory = self.addHost('mallory')
        local_switch = self.addSwitch('s0')
        self.addLink(
            alice, local_switch, bw=1000.0, delay=100, max_queue_size=20)
        self.addLink(
            mallory, local_switch, bw=1000.0, delay=100, max_queue_size=20)

        server_switch = self.addSwitch('s1')
        server = self.addHost('server')
        self.addLink(
            server, server_switch, bw=1000.0, delay=10, max_queue_size=20)

        # This is the bottleneck link: s0 <-> s1
        self.addLink(
            local_switch, server_switch, bw=1.5, delay=100, max_queue_size=200)


def start_tcpprobe(output_file='cwnd.txt'):
    subprocess.call('rmmod tcp_probe; modprobe tcp_probe full=1', shell=True)
    return subprocess.Popen(
        'dd if=/proc/net/tcpprobe ibs=128 obs=128 > {}'.format(output_file),
        shell=True)


def stop_tcpprobe(p):
    p.terminate()


# "In these experiments, we again consider the scenario of Figure 2 but
# with a single TCP flow.4 The TCP Reno flow has minRTO = 1 second and
# satisfies conditions (C1) and (C2)."
def set_rto_min(net):
    # From: https://serverfault.com/questions/529347/how-to-apply-rto-min-to-a-certain-host-in-centos
    alice = net.get('alice')
    current_config = alice.cmd('ip route show').strip()
    print('Initial ip route config: %s' % current_config)

    new_config = '%s rto_min 1s' % current_config
    print('Setting new config for alice (%s): %s' % (alice.IP(), new_config))
    alice.cmd('sudo ip route change %s' % new_config, shell=True)


def start_iperf(net):
    alice = net.get('alice')
    server = net.get('server')
    print('Starting iperf server on {}.'.format(server.IP()))
    iperf_s = server.popen('iperf -s > server', shell=True)
    print('Starting iperf client on {}.'.format(alice.IP()))
    iperf_c = alice.popen(
        'iperf -c {} -t {} > client'.format(server.IP(), 60), shell=True)
    print('Iperf started on server and client.')
    return (iperf_c, iperf_s)


def start_attacker(net, period, burst_length):
    mallory = net.get('mallory')
    server = net.get('server')

    print('Starting ICMP flood: %s -> %s' % (mallory.IP(), server.IP()))
    while True:
        print('  ** ping burst!')
        p = mallory.popen('ping -f {}'.format(server.IP()))
        time.sleep(burst_length)
        p.terminate()

        # Now wait for the period-between-bursts to do the square wave attack
        time.sleep(period)


def main():
    parser = argparse.ArgumentParser(description="TCP DoS simulator.")
    parser.add_argument(
        '--burst',
        '-b',
        help="Burst duration in seconds of each DoS attack.",
        type=float,
        default=0.15)
    parser.add_argument(
        '--cong', help="Congestion control algorithm to use.", default="reno")
    parser.add_argument(
        '--period',
        '-p',
        help="Seconds between low-rate DoS attacks, e.g. 0.5",
        type=float,
        default=0.5)
    args = parser.parse_args()

    subprocess.call(
        'sysctl -q -w net.ipv4.tcp_congestion_control=%s' % args.cong,
        shell=True)

    topo = Topo()
    net = mininet.net.Mininet(
        topo=topo, host=mininet.node.CPULimitedHost, link=mininet.link.TCLink)
    net.start()
    net.pingAll()

    set_rto_min(net)

    client, server = start_iperf(net)
    probe = start_tcpprobe()

    attack_thread = threading.Thread(
        target=start_attacker, args=(net, args.period, args.burst))
    attack_thread.daemon = True
    attack_thread.start()

    client.communicate()

    stop_tcpprobe(probe)
    print('Cleaning up processes.')
    server.terminate()
    net.stop()


if __name__ == '__main__':
    main()
