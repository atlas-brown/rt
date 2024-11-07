#!/bin/bash
# SPDX-license-identifier: Apache-2.0
##############################################################################
# Copyright (c) 2019
# All rights reserved. This program and the accompanying materials
# are made available under the terms of the Apache License, Version 2.0
# which accompanies this distribution, and is available at
# http://www.apache.org/licenses/LICENSE-2.0
##############################################################################

set -o errexit
set -o pipefail

if ! command -v docker; then
    KRD_ACTIONS=("install_docker")
    curl -fsSL https://raw.githubusercontent.com/electrocucaracha/krd/master/aio.sh | KRD_ACTIONS_DECLARE=$(declare -p KRD_ACTIONS) bash
fi

sudo git clone --depth 1 https://github.com/kubernetes/kubernetes -b v1.15.3 /opt/kubernetes

export KUBERNETES_HTTP_PROXY=$HTTP_PROXY
export KUBERNETES_HTTPS_PROXY=$HTTPS_PROXY
export KUBERNETES_NO_PROXY=$NO_PROXY

pushd /opt/kubernetes/build
sudo -E ./run.sh make
popd
mkdir -p k8s_bin/
cp /opt/kubernetes/_output/dockerized/bin/linux/amd64/* k8s_bin/

sudo docker build -t my-kube-scheduler:1.0 .
