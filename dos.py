#!/usr/bin/env python
# -*- coding: utf-8 -*-
from __future__ import absolute_import
from __future__ import division
from __future__ import print_function

import argparse
import os
import time
import subprocess
import signal

import numpy as np
import mininet.topo
import mininet.net
import mininet.node


class Topo(mininet.topo.Topo):
    def build(self):
        # Topology:
        #  alice ---------+
        #                [s0]----[s1]----- bob
        #  mallory -------+
        local_switch = self.addSwitch('s0')
        alice = self.addHost('alice')
        self.addLink(
            alice, local_switch, bw=100, delay='1ms', max_queue_size=10)
        mallory = self.addHost('mallory')
        self.addLink(
            mallory, local_switch, bw=100, delay='1ms', max_queue_size=10)

        # bob is the recipient of both the normal flow and the
        # malicious attack flow...
        server_switch = self.addSwitch('s1')
        bob = self.addHost('bob')
        self.addLink(
            bob, server_switch, bw=100, delay='1ms', max_queue_size=10)
        self.addLink(
            server_switch, local_switch, bw=1.5, delay='20ms',
            max_queue_size=1000)


# "In these experiments, we again consider the scenario of Figure 2 but
# with a single TCP flow.4 The TCP Reno flow has minRTO = 1 second and
# satisfies conditions (C1) and (C2)."
def set_interface(net, min_rto_ms):
    # From: https://serverfault.com/questions/529347/how-to-apply-rto-min-to-a-certain-host-in-centos
    for host in ['alice', 'bob']:
        node = net.get(host)
        current_config = node.cmd('ip route show').strip()
        new_config = '%s rto_min %dms' % (current_config, min_rto_ms)
        node.cmd('ip route change %s' % new_config, shell=True)
        node.cmd('ethtool -K {}-eth0 tso off gso off gro off'.format(host))


def run_flow(net):
    alice = net.get('alice')
    bob = net.get('bob')
    print('Starting receiver on {}.'.format(bob.IP()))
    s = bob.popen('./run_receiver.sh', shell=True)
    # Wait for receiver to start listening.
    time.sleep(1.0)
    print('Starting sender on {}.'.format(alice.IP()))
    start = time.time()
    c = alice.popen('./run_sender.sh {}'.format(bob.IP()), shell=True)
    print('TCP flow started on Alice and Bob.')
    r = c.wait()
    assert r == 0
    r = s.wait()
    assert r == 0
    return time.time() - start


def start_attack(net, period, burst):
    mallory = net.get('mallory')
    bob = net.get('bob')
    print('UDP attack started from {} to {}.'.format(mallory.IP(), bob.IP()))
    return mallory.popen([
        'python', 'run_attacker.py', '--period', str(period), '--burst',
        str(burst), '--destination', bob.IP()
    ])


def main():
    parser = argparse.ArgumentParser(description="TCP DoS simulator.")
    parser.add_argument(
        '--burst',
        '-b',
        help="Burst duration in seconds of each DoS attack.",
        type=float,
        default=0.15)
    parser.add_argument(
        '--cong', help="Congestion control algorithm to use.", default='reno')
    parser.add_argument(
        '--suffix', '-s', help="Suffix for output directory",
        type=str, default='')
    parser.add_argument(
        '--period',
        '-p',
        help="Seconds between low-rate DoS attacks, e.g. 0.5",
        type=float,
        default=0.5)
    parser.add_argument(
        '--rto', '-r', help="rto_min value, in ms", type=int, default=1000)
    args = parser.parse_args()

    # Initialize kernel parameters.
    subprocess.check_call(
        'sysctl -q -w net.ipv4.tcp_congestion_control=%s' % args.cong,
        shell=True)
    subprocess.check_call('sysctl -q -w net.ipv4.tcp_sack=0', shell=True)
    subprocess.check_call('sysctl -q -w net.ipv4.tcp_dsack=0', shell=True)
    subprocess.check_call('sysctl -q -w net.ipv4.tcp_fack=0', shell=True)

    topo = Topo()
    net = mininet.net.Mininet(
        topo=topo, host=mininet.node.CPULimitedHost, link=mininet.link.TCLink)
    net.start()
    set_interface(net, args.rto)
    print('Alice\'s IP is {}.'.format(net.get('alice').IP()))
    print('Bob\'s IP is {}.'.format(net.get('bob').IP()))
    print('Mallory\'s IP is {}.'.format(net.get('mallory').IP()))
    print('')

    attack = start_attack(net, args.period, args.burst)

    t = run_flow(net)
    print('Sending completed in %.4f seconds.' % t)

    output_dir = 'results'
    if args.suffix:
        output_dir += '-' + args.suffix

    if not os.path.isdir(output_dir):
        os.mkdir(output_dir)
    fname = os.path.join(output_dir,
                         't-{}-{}.txt'.format(args.period, args.burst))
    with open(fname, 'w') as f:
        f.write(str(t) + '\n')

    attack.terminate()
    net.stop()


if __name__ == '__main__':
    main()
