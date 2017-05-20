#!/usr/bin/env python
# -*- coding: utf-8 -*-
from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
import os
import math
import matplotlib
matplotlib.use('agg')
import matplotlib.pyplot as plt
import numpy as np
import sys


def main():
    dir_names = [f for f in os.listdir('.')
                 if f.startswith('results-') and os.path.isdir(f)]
    for dir_name in dir_names:
        files = [i for i in os.listdir(dir_name) if i.startswith('t-')]

        bursts = {}
        for fname in files:
            full_path = os.path.join(dir_name, fname)
            period, burst = tuple(map(float, fname[2:-4].split('-')))
            bursts.setdefault(burst, [])
            with open(full_path) as f:
                # Transferred 2MBytes = 16 Mbits.
                t = 16 / float(f.readline().strip())
                bursts[burst].append((period, t))
        for burst in bursts:
            plt.plot(*zip(*sorted(bursts[burst])),
                     label='burst: {}'.format(burst))
        plt.xlabel('Period (s)')
        plt.ylabel('Average rate (Mbits/s)')
        plt.legend(loc='best')
        plt.savefig('%s.png' % dir_name, bbox_inches='tight')


if __name__ == '__main__':
    main()
