#!/usr/bin/env bash

source "$(dirname "$0")/common.sh"

cd "${LFS_REPO_DIR}"

cmake --build build --parallel "$(nproc)"
