#!/bin/bash
# Copyright (c) 2012 The Native Client Authors. All rights reserved.
# Use of this source code is governed by a BSD-style license that can be
# found in the LICENSE file.

ConfigureStep() {
  SetupCrossEnvironment

  local conf_host
  if [ "${NACL_ARCH}" = pnacl ]; then
    conf_host=pnacl
  else
    conf_host=${NACL_CROSS_PREFIX}
  fi

  LogExecute ${SRC_DIR}/configure \
    --enable-vp8 \
    --target=pnacl \
    --prefix=${PREFIX} \
    --disable-unit-tests \
    --disable-examples \
    --disable-runtime_cpu_detect 

  make clean
}

