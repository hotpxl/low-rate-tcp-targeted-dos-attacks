#!/usr/bin/env python
# -*- coding: utf-8 -*-
from __future__ import absolute_import
from __future__ import print_function

import argparse
import socket
import os
import time
import subprocess
import signal
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
        self.addLink(alice, local_switch, bw=1000.0, max_queue_size=5)
        self.addLink(mallory, local_switch, bw=1000.0, max_queue_size=5)

        server_switch = self.addSwitch('s1')
        server = self.addHost('server')
        self.addLink(server, server_switch, bw=1000.0, max_queue_size=5)

        # This is the bottleneck link: s0 <-> s1
        self.addLink(local_switch, server_switch, bw=1.5, max_queue_size=10)


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


def start_tcpprobe(output_file='cwnd.txt'):
    subprocess.check_call(
        'rmmod tcp_probe; modprobe tcp_probe full=1', shell=True)
    return subprocess.Popen(
        'dd if=/proc/net/tcpprobe ibs=128 obs=128 > {}'.format(output_file),
        shell=True,
        preexec_fn=os.setsid)


def start_bw_monitor(net, output_file='txrate.txt', interval_sec=0.01):
    assert False, 'Disabled.'
    alice = net.get('alice')
    return alice.popen(
        'bwm-ng -t {} -o csv -u bits -T rate -C , > {}'.format(
            interval_sec * 1000, output_file),
        shell=True,
        preexec_fn=os.setsid)


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


def run_attacker(net, period, burst_length, shutdown_event):
    mallory = net.get('mallory')
    server = net.get('server')

    data = '0' * 1024

    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    print('Starting UDP flood: %s -> %s.' % (mallory.IP(), server.IP()))
    while not shutdown_event.wait(period):
        start_time = time.time()
        while time.time() - start_time < burst_length:
            sock.sendto(data, (server.IP(), 80))
    sock.close()


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

    probe = start_tcpprobe()
    shutdown_event = threading.Event()
    attack_thread = threading.Thread(
        target=run_attacker,
        args=(net, args.period, args.burst, shutdown_event))
    attack_thread.daemon = True
    attack_thread.start()

    t = run_flow(net)
    output_file = 'tx-{}-{}.txt'.format(args.period, args.burst)
    with open(output_file, 'w') as f:
        f.write(str(t))

    shutdown_event.set()
    attack_thread.join()
    os.killpg(os.getpgid(probe.pid), signal.SIGTERM)
    net.stop()


if __name__ == '__main__':
    main()
