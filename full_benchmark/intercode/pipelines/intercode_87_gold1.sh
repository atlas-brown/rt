# Query: Compresses all the files in the /system folder with default depth to /backup using cpio.

find /system -depth -print | cpio -dump /backup