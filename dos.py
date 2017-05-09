#!/usr/bin/env python
# -*- coding: utf-8 -*-
from __future__ import absolute_import
from __future__ import print_function
import os
import time
import subprocess
import mininet.topo
import mininet.net
import mininet.node


class Topo(mininet.topo.Topo):
    def build(self):
        alice = self.addHost('alice')
        mallory = self.addHost('mallory')
        local_switch = self.addSwitch('s0')
        self.addLink(alice, local_switch, bw=1000.0, delay=100,
                     max_queue_size=20)
        self.addLink(mallory, local_switch, bw=1000.0, delay=100,
                     max_queue_size=20)

        server_switch = self.addSwitch('s1')
        server = self.addHost('server')
        self.addLink(server, server_switch, bw=1000.0, delay=10,
                     max_queue_size=20)

        # This is the bottleneck link: s0 <-> s1
        self.addLink(local_switch, server_switch, bw=1.5, delay=100,
                     max_queue_size=20)


def start_tcpprobe(output_file='cwnd.txt'):
    subprocess.call('rmmod tcp_probe; modprobe tcp_probe full=1', shell=True)
    return subprocess.Popen(
        'dd if=/proc/net/tcpprobe ibs=128 obs=128 > {}'.format(output_file),
        shell=True)


def stop_tcpprobe(p):
    p.terminate()


def start_iperf(net):
    alice = net.get('alice')
    server = net.get('server')
    print('Starting iperf server on {}.'.format(alice.IP()))
    iperf_s = alice.popen('iperf -s > server', shell=True)
    print('Starting iperf client on {}.'.format(server.IP()))
    iperf_c = server.popen(
        'iperf -c {} -t {} > client'.format(alice.IP(), 600), shell=True)
    print('Iperf started on server and client.')
    return (iperf_c, iperf_s)


def main():
    subprocess.call(
        'sysctl -q -w net.ipv4.tcp_congestion_control=reno', shell=True)
    topo = Topo()
    net = mininet.net.Mininet(
        topo=topo, host=mininet.node.CPULimitedHost, link=mininet.link.TCLink)
    net.start()
    net.pingAll()
    client, server = start_iperf(net)
    probe = start_tcpprobe()
    for _ in range(60):
        time.sleep(10)
        mallory = net.get('mallory')
        server = net.get('server')

        print('Starting ICMP flood: %s -> %s' % (mallory.IP(), server.IP()))
        p = mallory.popen('ping -f {}'.format(server.IP()))

        time.sleep(2)
        p.terminate()
    stop_tcpprobe(probe)
    print('Cleaning up processes.')
    client.terminate()
    server.terminate()
    net.stop()


if __name__ == '__main__':
    main()
