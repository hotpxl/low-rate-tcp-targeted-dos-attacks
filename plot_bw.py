import os
import matplotlib
matplotlib.use('agg')
import matplotlib.pyplot as plt
import numpy as np


def main():
    plt.figure(figsize=(20, 40))
    files = [i for i in os.listdir() if i.startswith('tx-')]
    for idx, f in enumerate(files):
        period = float(f[3:-4])
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
        plt.subplot(7, 3, idx + 1)
        plt.plot(tss, out_rates, label=str(period), lw=1)
        plt.legend()
    plt.savefig('tx.png', bbox_inches='tight')


if __name__ == '__main__':
    main()
