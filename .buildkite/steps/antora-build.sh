#!/bin/bash

set -eo pipefail
set -x

BRANCH=${BRANCH:-${BUILDKITE_BRANCH:master}}
echo "--- Building $PROJECT..."
git clone git@github.com:feelpp/swimmer.git toto

#antora --html-url-extension-style=indexify site.yml
#ls -lrta

tar  --exclude='*.png' --exclude="*.jpg" --exclude="*.jpeg" -c -z -f site.tar.gz build
buildkite-agent artifact upload site.tar.gz --job $BUILDKITE_JOB_ID
