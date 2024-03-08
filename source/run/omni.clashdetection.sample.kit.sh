#!/bin/bash
set -e
SCRIPT_DIR=$(dirname ${BASH_SOURCE})
${EXEC:-exec} "$SCRIPT_DIR/kit/kit" "$SCRIPT_DIR/apps/omni.clashdetection.sample.kit"  "$@"
