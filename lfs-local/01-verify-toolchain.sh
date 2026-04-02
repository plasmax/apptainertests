#!/usr/bin/env bash

source "$(dirname "$0")/common.sh"

echo "checking toolchain"
command -v git
command -v cmake
command -v ninja || command -v ninja-build
command -v nvcc
command -v "${CC}"
command -v "${CXX}"
command -v "${CUDAHOSTCXX}"
test -x "${VCPKG_ROOT}/vcpkg"
require_cuda_version

git --version
cmake --version | sed -n '1p'
ninja --version 2>/dev/null || ninja-build --version
nvcc --version | sed -n '1,4p'
"${CC}" --version | sed -n '1p'
"${CXX}" --version | sed -n '1p'
"${VCPKG_ROOT}/vcpkg" version
