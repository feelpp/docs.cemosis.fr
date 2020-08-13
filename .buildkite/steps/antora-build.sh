#!/bin/bash

set -eo pipefail
#set -x

BRANCH=${BRANCH:-${BUILDKITE_BRANCH:master}}
echo "--- Install"
npm install
echo "--- Build"
npm run build
echo "--- Deploy"
rsync -avz --delete build/site/ $WEBSERVER:~/public_html/$PROJECT

#echo "running $NVM_BIN/antora..."
#$NVM_BIN/antora --fetch --html-url-extension-style=indexify site.yml
##ls -lrta
#echo "uploading artifact..."
#tar  -c -z -f site.tar.gz build
#buildkite-agent artifact upload site.tar.gz --job $BUILDKITE_JOB_ID
