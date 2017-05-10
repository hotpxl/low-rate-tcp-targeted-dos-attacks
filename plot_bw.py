import matplotlib
matplotlib.use('agg')
import matplotlib.pyplot as plt
import numpy as np


def main():
    with open('txrate.txt') as f:
        # Skip last line because it might be incomplete.
        tss = []
        out_rates = []
        in_rates = []
        for l in f.readlines()[:-1]:
            ts, interface, out_rate, in_rate, total_rate = l.split(',')[:5]
            if interface == 'alice-eth0':
                tss.append(ts)
                out_rates.append(out_rate)
                in_rates.append(in_rate)
    plt.plot(tss, out_rates)
    plt.plot(tss, in_rates)
    plt.savefig('txrate.png', bbox_inches='tight')


if __name__ == '__main__':
    main()
