# Cleanup
apt-get -y autoremove
apt-get clean
rm -f /etc/dpkg/dpkg.cfg.d/02apt-speedup
find /var/lib/apt/lists -mindepth 1 -delete -print
find /tmp /var/tmp -mindepth 2 -delete -print
find . -delete -print
