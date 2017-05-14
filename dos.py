#!/usr/bin/env python
# -*- coding: utf-8 -*-
from __future__ import absolute_import
from __future__ import print_function

import argparse
import numpy as np
import os
import time
import subprocess
import signal

import mininet.topo
import mininet.net
import mininet.node


class Topo(mininet.topo.Topo):
    def build(self):
        # Topology:
        #  A (alice) ------+                    +---- server
        #                  |--[s0]----[s1]------|
        #  B (bob)  -------+                    +---- mallory (attacker)
        local_switch = self.addSwitch('s0')

        alice = self.addHost('alice')
        self.addLink(alice, local_switch, bw=15, delay='1ms')

        bob = self.addHost('bob')
        self.addLink(bob, local_switch, bw=15, delay='1ms')

        server_switch = self.addSwitch('s1')

        server = self.addHost('server')
        self.addLink(server, server_switch, bw=15, delay='1ms')

        mallory = self.addHost('mallory')
        self.addLink(mallory, server_switch, bw=15, delay='1ms')

        # This is the bottleneck link: s0 <-> s1
        self.addLink(local_switch, server_switch, bw=1.5,
                     delay='50ms', max_queue_size=20000)


def terminate_process(p):
    assert False, 'Disabled.'
    pid_set = set()
    pid_set.add(os.getpgid(p.pid))
    pids = subprocess.check_output(
        'ps -o pid= --ppid {}'.format(p.pid), shell=True)
    for pp in pids.strip().split('\n'):
        pid_set.add(os.getpgid(int(pp)))
    for i in pid_set:
        print('kill ', i)
        os.killpg(i, signal.SIGTERM)
        time.sleep(1)


def start_webserver(net):
    server = net.get('server')
    print('Starting webserver on: %s' % server.IP())
    proc = server.popen("python http/webserver.py", shell=True)
    time.sleep(1)
    return proc


# "In these experiments, we again consider the scenario of Figure 2 but
# with a single TCP flow.4 The TCP Reno flow has minRTO = 1 second and
# satisfies conditions (C1) and (C2)."
def set_rto_min(net, min_rto_ms):
    # From: https://serverfault.com/questions/529347/how-to-apply-rto-min-to-a-certain-host-in-centos
    for host in ['alice', 'server']:
        node = net.get(host)
        current_config = node.cmd('ip route show').strip()
        print('Initial ip route config: %s' % current_config)

        new_config = '%s rto_min %dms' % (current_config, min_rto_ms)
        print('Setting new config for %s (%s): %s' %
              (host, node.IP(), new_config))
        node.cmd('sudo ip route change %s' % new_config, shell=True)


def run_flow(net):
    alice = net.get('alice')
    server = net.get('server')
    print('Starting receiver on {}.'.format(server.IP()))
    s = server.popen('nc -l -p 12345 > /dev/null', shell=True)
    # Wait for receiver to start listening.
    time.sleep(1)
    print('Starting sender on {}.'.format(alice.IP()))
    start = time.time()
    c = alice.popen('./run_sender.sh {}'.format(server.IP()), shell=True)
    print('TCP flow started on server and client.')
    r = c.wait()
    assert r == 0
    r = s.wait()
    assert r == 0
    return time.time() - start


def start_attack(net, period, burst):
    mallory = net.get('mallory')
    victim = net.get('bob')

    return mallory.popen([
        'python', 'run_attacker.py', '--period', str(period), '--burst',
        str(burst), '--destination', victim.IP()
    ])


def run_download(net):
    server = net.get('server')
    host = net.get('alice')
    measured_bps = []

    filename = 'http/cat.png'

    for i in xrange(5):
        time.sleep(2)

        start = time.time()
        print('Run %d. Starting download of: %s' % (i + 1, filename))
        host.cmd(
            'curl -o /dev/null --progress-bar --verbose '
            '%s/%s' % (server.IP(), filename), shell=True)
        end = time.time()
        measured_time = end - start
        file_size = os.stat(filename).st_size
        bps = (file_size * 8.0) / measured_time

        print('   fetch time: %.2f sec, %.2f bps' % (measured_time, bps))
        measured_bps.append(bps)

    return np.mean(measured_bps)


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
    parser.add_argument(
        '--rto', '-r', help="rto_min value, in ms", type=int, default=1000)
    args = parser.parse_args()

    subprocess.call(
        'sysctl -q -w net.ipv4.tcp_congestion_control=%s' % args.cong,
        shell=True)

    topo = Topo()
    net = mininet.net.Mininet(
        topo=topo, host=mininet.node.CPULimitedHost, link=mininet.link.TCLink)
    net.start()
    net.pingAll()
    set_rto_min(net, args.rto)

    webserver = start_webserver(net)

    attack = start_attack(net, args.period, args.burst)

    mean_bps = run_download(net)
    print('rto %d period %.2f: %.4f bps' % (args.rto, args.period, mean_bps))

    webserver.terminate()
    attack.terminate()
    net.stop()


if __name__ == '__main__':
    main()
