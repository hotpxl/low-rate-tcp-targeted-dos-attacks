#!/usr/bin/python
"CS244 Spring 2017 Assignment 3: Initcwnd"

from mininet.topo import Topo
from mininet.node import CPULimitedHost
from mininet.link import TCLink
from mininet.net import Mininet
from mininet.log import lg, info
from mininet.util import dumpNodeConnections
from mininet.cli import CLI

from subprocess import Popen, PIPE
from time import sleep, time
from multiprocessing import Process
from argparse import ArgumentParser

import numpy as np

import sys
import os
import math

parser = ArgumentParser(description="Bufferbloat tests")
parser.add_argument('--time', '-t',
                    help="Duration (sec) to run the experiment",
                    type=int,
                    default=10)

parser.add_argument('--cwnd',
                    type=int,
                    help="Initial cwnd size in packets.",
                    default=4)

# From the paper: " The front-end servers run Linux with a reasonably
# standards compliant TCP implementation [6] (the congestion control algorithm
# used is TCP CUBIC), and the initial congestion window is
# configured using the initcwnd option in the ip route command."
parser.add_argument('--cong',
                    help="Congestion control algorithm to use",
                    default="cubic")

# Expt parameters
args = parser.parse_args()

HOST_SPEEDS = [56, 256, 512, 1000]  # Kbps


class InitCwndTopo(Topo):
    "Simple topology for initcwnd experiment."

    def build(self):
        # Here I have created a switch.  If you change its name, its
        # interface names will change from s0-eth1 to newname-eth1.
        switch = self.addSwitch('s0')

        delay_str = '250ms'

        # create n hosts
        hosts = ['h%s' % speed for speed in HOST_SPEEDS]
        hosts.append('server')
        for host in hosts:
            self.addHost(host)
            print '** created: %s' % host

        # Add links with appropriate characteristics.
        print 'adding links, delay=%s' % delay_str
        for speed in HOST_SPEEDS:
            host_id = 'h%s' % speed
            bw = speed / 1000.
            self.addLink(host_id, switch, bw=bw, delay=delay_str)
            print '** created %s <-> s0, bw=%.2f Mbps, delay=%s' % (
                host_id, bw, delay_str)
        self.addLink('server', switch, bw=10, delay='50ms')
        print '** created server <-> s0, bw=10 Mbps, delay=50ms'


def start_webserver(net):
    server = net.get('server')
    print "Starting webserver on: %s" % server.IP()
    proc = server.popen("python http/webserver.py", shell=True)
    sleep(1)
    return [proc]


def main():
    os.system("sysctl -w net.ipv4.tcp_congestion_control=%s" % args.cong)
    topo = InitCwndTopo()
    net = Mininet(topo=topo, host=CPULimitedHost, link=TCLink)
    net.start()
    # This dumps the topology and how nodes are interconnected through
    # links.
    dumpNodeConnections(net.hosts)
    # This performs a basic all pairs ping test.
    net.pingAll()

    # Start iperf, webservers, etc. Keep a dict of function name ->
    # Popen() processes started so we can kill them later.
    procs = {}
    for fn in (start_webserver,):
      procs[fn.__name__] = fn(net)

    # Adjust cwnd on the server: "Our experiments consist of enabling a
    # larger initial congestion window on front-end servers in several
    # data centers at geographically diverse locations. We compare the
    # results using the larger window against data from the same data centers
    # using the standard initial congestion window as a baseline."
    server = net.get('server')
    current_config = server.cmd('ip route show').strip()
    print 'Initial ip route config: %s' % current_config

    new_config = '%s initcwnd %d' % (current_config, args.cwnd)
    print 'Setting new config: %s' % new_config
    server.cmd('sudo ip route change %s' % new_config, shell=True)

    for speed in HOST_SPEEDS:
      host = net.get('h%s' % speed)
      print 'Testing %d Kbps download times with initcwnd=%d' % (
          speed, args.cwnd)

      # Test each host 5 times.
      fetch_times = []
      for _ in xrange(5):
        measured_time = float(host.cmd(
            'curl -o /dev/null -s -w %%{time_total} '
            '%s/http/index.html' % server.IP()))
        print '   fetch time: %.2f sec' % measured_time
        fetch_times.append(measured_time)
        sleep(1)

      avg_fetch = np.mean(fetch_times)
      stddev_fetch = np.std(fetch_times)
      print '  Mean fetch time:  %.4f sec' % avg_fetch
      print 'Stddev fetch time:  %.4f sec' % stddev_fetch

    net.stop()
    # Ensure that all processes you create within Mininet are killed.
    # Sometimes they require manual killing.
    print 'Cleaning up processes...'
    for proc_name, proc_list in procs.iteritems():
      print '* Killing %s (%d processes)' % (proc_name, len(proc_list))
      for proc in proc_list:
        proc.terminate()
    Popen("pgrep -f webserver.py | xargs kill -9", shell=True).wait()

if __name__ == "__main__":
    main()
