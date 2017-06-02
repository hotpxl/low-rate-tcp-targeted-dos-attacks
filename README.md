# Low-Rate TCP-Targeted Denial of Service Attacks

This is a reproduction of [Low-Rate TCP-Targeted Denial of Service Attacks](http://www.cs.northwestern.edu/~akuzma/rice/doc/shrew.pdf).

## Steps to reproduce
1.  Create a fresh GCE virtual machine with Ubuntu 16.10, and set firewall
    rules to be able to access the HTTP server that will be started. We
    recommend that you use the following commands to create and connect to the
    instance.  Otherwise, you should perform the corresponding instance
    creation and firewall setup in the GCE web UI.

    ```bash
    gcloud compute instances create --image ubuntu-1610-yakkety-v20170502 --image-project ubuntu-os-cloud --machine-type n1-highcpu-8 --zone us-central1-c --tags http-server,https-server cs244
    gcloud compute firewall-rules create http --allow tcp:80
    gcloud compute ssh cs244
    ```
2.  In your GCE instance, execute the following:

    ```bash
    curl "https://cs.stanford.edu/people/rpropper/cs244/setup.sh" | /bin/bash
    ```

    This script will install Python dependencies (e.g. matplotlib), check out
    and install Mininet. Note: We provide this setup script as a separate step
    from the VM image for better clarity and transparency.  Feel free to
    inspect the script before running it.

3.  Clone our git repo:

    ```bash
    git clone https://github.com/hotpxl/low-rate-tcp-targeted-dos-attacks.git
    ```

4.  Now, `cd low-rate-tcp-targeted-dos-attacks` and `sudo ./run.sh` to run the
    experiment. Please be patient; a run takes between 1 to 2 hours.

5.  After the script runs, it will show you a URL where you can view the
    results. There should be two generated `.png` files in the root directory.
    One (`results-<hostname>-date_rate.png`) will show the normalized
    throughput, i.e., the primary figure we are trying to reproduce. The other
    shows the sender’s cwnd values, plotted over time, for various attack
    period values.

