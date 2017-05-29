#!/usr/bin/env python
# -*- coding: utf-8 -*-
from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
import os
import math
import sys
import matplotlib
matplotlib.use('agg')
import matplotlib.pyplot as plt
import numpy as np


def main():
    dir_names = [
        f for f in os.listdir('.')
        if f.startswith('results-') and os.path.isdir(f)
    ]
    plt.figure(figsize=(20, 10))
    for dir_name in dir_names:
        files = [i for i in os.listdir(dir_name) if i.startswith('cwnd-')]
        bursts = {}
        for fname in files:
            full_path = os.path.join(dir_name, fname)
            period, burst = tuple(map(float, fname[5:-4].split('-')))
            if period > 1.0 or int(period*100) % 10 != 0:
                continue
            bursts.setdefault(burst, [])
            with open(full_path) as f:
                tss = []
                snd_wnds = []
                for l in f.readlines()[:-1]:
                    ts, src, dst, length, snd_nxt, snd_una, snd_cwnd, ssthresh, snd_wnd, srtt, rcv_wnd = l.split(
                    )
                    # Measure only send flow.
                    if dst[-5:] == '12345':
                        tss.append(float(ts))
                        snd_wnds.append(float(snd_cwnd))
                if len(tss) != 0:
                    plt.plot(
                        tss,
                        snd_wnds,
                        label='burst: {}s, period: {}s'.format(burst, period))
        plt.xlabel('Time (s)')
        plt.ylabel('Congestion window size (MSS)')
        plt.legend(loc='best')
        plt.savefig('{}_cwnd.png'.format(dir_name), bbox_inches='tight')


if __name__ == '__main__':
    main()
