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
    plt.figure(figsize=(20, 40))
    files = [i for i in os.listdir('.') if i.startswith('tx-')]
    if len(files) == 0:
        print('No input files.')
        sys.exit(1)
    rows = int(math.sqrt(len(files)))
    cols = math.ceil(len(files) / rows)
    for idx, f in enumerate(files):
        period, burst = tuple(map(float, f[3:-4].split('-')))
        with open(f) as f:
            # Skip last line because it might be incomplete.
            tss = []
            out_rates = []
            start_ts = None
            for l in f.readlines()[:-1]:
                ts, interface, out_rate, in_rate, total_rate = l.split(',')[:5]
                if interface == 'alice-eth0':
                    if start_ts is None:
                        start_ts = int(ts)
                    tss.append(int(ts) - start_ts)
                    out_rates.append(min(float(out_rate), 5e6))
        plt.subplot(rows, cols, idx + 1)
        plt.plot(
            tss,
            out_rates,
            label='period: {}, burst: {}'.format(period, burst),
            lw=1)
        plt.legend()
    plt.savefig('tx.png', bbox_inches='tight')


if __name__ == '__main__':
    main()
