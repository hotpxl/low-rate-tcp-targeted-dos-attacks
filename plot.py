import matplotlib
matplotlib.use('agg')
import matplotlib.pyplot as plt
import numpy as np


def main():
    with open('cwnd.txt') as f:
        # Skip last line because it might be incomplete.
        tss = []
        cwnds = []
        rcv_wnds = []
        for l in f.readlines()[:-1]:
            ts, src, dst, length, snd_nxt, snd_una, snd_wnd, rcv_wnd, snd_cwnd, ssthresh, srtt = l.split(
            )
            tss.append(ts)
            cwnds.append(snd_cwnd)
    plt.plot(tss, cwnds)
    plt.savefig('cwnd.png', bbox_inches='tight')


if __name__ == '__main__':
    main()
