#!/bin/bash
echo "Riak post install"
echo "  - backup files"
# backup files 
cp .dpkg/usr/sbin/riak              .dpkg/usr/sbin/riak.back
cp .dpkg/usr/lib/riak/lib/env.sh    .dpkg/usr/lib/riak/lib/env.sh.back
cp .dpkg/etc/riak/riak.conf         .dpkg/etc/riak/riak.conf.back
# deploy new files
echo "  - deploy new files"
cp riak_script/riak        .dpkg/usr/sbin/riak
cp riak_script/env.sh      .dpkg/usr/lib/riak/lib/env.sh
cp riak_script/riak.conf   .dpkg/etc/riak/riak.conf