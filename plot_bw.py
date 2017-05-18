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


def main():
    files = [i for i in os.listdir('.') if i.startswith('t-')]
    if len(files) == 0:
        print('No input files.')
        sys.exit(1)
    bursts = {}
    for f in files:
        period, burst = tuple(map(float, f[2:-4].split('-')))
        bursts.setdefault(burst, [])
        with open(f) as f:
            # Transferred 8 Mbits.
            t = 8 / float(f.readline().strip())
            bursts[burst].append((period, t))
    for burst in bursts:
        plt.plot(*zip(*sorted(bursts[burst])), label='burst: {}'.format(burst))
    plt.xlabel('Period (s)')
    plt.ylabel('Average rate (Mbits/s)')
    plt.legend(loc='best')
    plt.savefig('tx.png', bbox_inches='tight')


if __name__ == '__main__':
    main()
