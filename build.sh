#!/bin/bash
set -e

SCRIPT_DIR=$(dirname ${BASH_SOURCE})

# build repo
"$SCRIPT_DIR/repo.sh" build $@ || exit $?
