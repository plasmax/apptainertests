#!/usr/bin/env bash

source "$(dirname "$0")/common.sh"

mkdir -p "${LFS_WORK_ROOT}"
cd "${LFS_WORK_ROOT}"

if [[ -d "${LFS_REPO_DIR}/.git" ]]; then
    echo "repo already exists: ${LFS_REPO_DIR}"
    git -C "${LFS_REPO_DIR}" status --short --branch
    exit 0
fi

git clone --recursive --depth 1 --shallow-submodules https://github.com/MrNeRF/LichtFeld-Studio.git
cd "${LFS_REPO_DIR}"
git status --short --branch
