#!/usr/bin/env bash

# this script submits a PEM encoded csr to the discovery service and download the cert chain in a zip of der encoded files.

DEFAULT_URL="http://localhost:8080"
DISCOVERY_URL=${DEFAULT_URL}
DER_PATH="cordaclientca.der"
NAME_PATH="cordaclientca_name.txt"

function usage() {
  echo "Usage: ./approve.sh PATH_TO_PEM [DISCOVERY_BASE_PATH]"
  echo "Default DISCOVERY_BASE_PATH: ${DEFAULT_URL}"
}

if [ -z "$1" ]; then
  usage
  exit 1
fi
if [ -n "$2" ]; then
  DISCOVERY_URL="$2"
fi

PEM_PATH="$1"

if ! hash curl 2>&1 1>/dev/null; then
  echo "curl not found"
  exit 1
fi

if ! hash openssl 2>&1 1>/dev/null; then
  echo "openssl not found"
  exit 1
fi

# convert to der
openssl req -inform PEM -outform DER -in "${PEM_PATH}" -out "${DER_PATH}"

# upload and store curl
echo "uploading CSR to ${DISCOVERY_URL}/doorman/certificate"
if ! curl --data-binary "@${DER_PATH}" -H "Platform-Version: 4" -H "Client-Version: 1" -H "Content-Type: application/octet-stream" "${DISCOVERY_URL}/doorman/certificate" > ${NAME_PATH}
then
  echo "failed to upload DER encoded CSR to ${DISCOVERY_URL}"
  cat ${NAME_PATH}
  exit 1
fi

# approve
name=$(cat ${NAME_PATH})
echo "approving CSR via ${DISCOVERY_URL}/admin/certificates/signrequests/${name}/approve"
if ! curl -X PUT "${DISCOVERY_URL}/admin/certificates/signrequests/${name}/approve" > error
then
  echo "failed to approve CSR"
  cat error
  exit 1
fi

mkdir -p dist

# download certs
echo "downloading certificates from ${DISCOVERY_URL}/doorman/certificate/${name}"
curl "${DISCOVERY_URL}/doorman/certificate/${name}" > dist/certs.zip

# download networkMap/network-parameters
echo "downloading network-parameters from ${DISCOVERY_URL}/network-map/network-parameters/latest"
curl "${DISCOVERY_URL}/network-map/network-parameters/latest" > dist/network-parameters

# create package for uploader
# - certs/
# - networkParameters
# - conf/sslkeystore.conf

mkdir -p dist/certs dist/conf
unzip dist/certs.zip -d dist/certs
rm dist/certs.zip
cp "${BASH_SOURCE%/*}/../files/sslkeystore.conf" dist/conf/sslkeystore.conf

if hash gsed 2>&1 1>/dev/null; then
  DN=$(gsed 's/,/\n/g' cordaclientca_name.txt)
  echo "$DN" >> "dist/conf/sslkeystore.conf"
  gsed -i 's/(CN=.*)/\1_tls/g' sslkeystore.conf
else
  DN=$(sed 's/,/\n/g' cordaclientca_name.txt)
  echo "$DN" >> "dist/conf/sslkeystore.conf"
  sed -i 's/(CN=.*)/\1_tls/g' sslkeystore.conf
fi

zip -r dist dist

echo "The dist.zip file is ready!"
