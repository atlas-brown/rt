## binwalk
git clone https://github.com/devttys0/binwalk /tmp/binwalk
(cd /tmp/binwalk && python setup.py install)

# Although all run-time dependencies are optional, the python-lzma module is highly recommended for improving the reliability of signature scans
apt-get install -y python-lzma

# Multiple external utilties in order to automatically extract/decompress files and data
apt-get install -y mtd-utils gzip bzip2 tar arj lhasa p7zip p7zip-full cabextract cramfsprogs cramfsswap squashfs-tools

# pyqtgraph to generate graphs and visualizations
apt-get install -y libqt4-opengl python-opengl python-qt4 python-qt4-gl python-numpy python-scipy python-pip
pip install pyqtgraph

# Install X virtual framebuffertto graph entropy plots without running a graphical display
apt-get install -y xvfb

# Binwalk --disasm option requires the Capstone disassembly framework and its corresponding Python bindings
pip install capstone

# Install standard extraction utilities
git clone https://github.com/devttys0/sasquatch /tmp/sasquatch

# Install sasquatch to extract non-standard SquashFS images
apt-get install -y zlib1g-dev liblzma-dev liblzo2-dev
(cd /tmp/sasquatch && make && make install)

# Install jefferson to extract JFFS2 file systems
pip install cstruct
git clone https://github.com/sviehb/jefferson /tmp/jefferson
(cd /tmp/jefferson && python setup.py install)

# Install unstuff (closed source) to extract StuffIt archive files
(
  cd /tmp
  wget -O - http://my.smithmicro.com/downloads/files/stuffit520.611linux-i386.tar.gz | tar -zxv
  cp bin/unstuff /usr/local/bin/
)
