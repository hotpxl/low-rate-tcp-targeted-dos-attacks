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
        switch = self.addSwitch('s0')
        alice = self.addHost('h0')
        bob = self.addHost('h1')
        mallory = self.addHost('h2')
        self.addLink(alice, switch, bw=1.0, delay=100, max_queue_size=20)
        self.addLink(bob, switch, bw=1.0, delay=100, max_queue_size=20)
        self.addLink(mallory, switch, bw=1.0, delay=100, max_queue_size=20)


def start_tcpprobe(output_file='cwnd.txt'):
    subprocess.call('rmmod tcp_probe; modprobe tcp_probe full=1', shell=True)
    return subprocess.Popen(
        'dd if=/proc/net/tcpprobe ibs=128 obs=128 > {}'.format(output_file),
        shell=True)


def stop_tcpprobe(p):
    p.terminate()


def start_iperf(net):
    alice = net.get('h0')
    bob = net.get('h1')
    print('Starting iperf server on {}.'.format(alice.IP()))
    server = alice.popen('iperf -s > alice', shell=True)
    print('Starting iperf client on {}.'.format(bob.IP()))
    client = bob.popen(
        'iperf -c {} -t {} > bob'.format(alice.IP(), 600), shell=True)
    print('Iperf started on server and client.')
    return (client, server)


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
    time.sleep(10)
    stop_tcpprobe(probe)
    print('Cleaning up processes.')
    client.terminate()
    server.terminate()
    net.stop()


if __name__ == '__main__':
    main()
