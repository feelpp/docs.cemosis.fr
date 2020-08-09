#!/bin/bash

set -eo pipefail
set -x

export NVM_DIR="$HOME/.nvm"
[ -s "$NVM_DIR/nvm.sh" ] && \. "$NVM_DIR/nvm.sh"  # This loads nvm

BRANCH=${BRANCH:-${BUILDKITE_BRANCH:master}}
echo "--- Building $PROJECT..."
#git clone git@github.com:feelpp/swimmer.git toto

echo "running $NVM_BIN/antora..."
$NVM_BIN/antora --fetch --html-url-extension-style=indexify site.yml
#ls -lrta
echo "uploading artifact..."
tar  -c -z -f site.tar.gz build
buildkite-agent artifact upload site.tar.gz --job $BUILDKITE_JOB_ID
