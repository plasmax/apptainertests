#!/usr/bin/env bash

source "$(dirname "$0")/common.sh"

cd "${LFS_REPO_DIR}"
require_cuda_version

# Preserve vcpkg-installed artifacts if they already exist, but force CMake
# to re-detect compilers after the failed CUDA/GCC-14 configure.
rm -f build/CMakeCache.txt
rm -rf build/CMakeFiles

cmake -S . -B build -G Ninja \
  -DCMAKE_BUILD_TYPE=Release \
  -DCMAKE_TOOLCHAIN_FILE="${VCPKG_ROOT}/scripts/buildsystems/vcpkg.cmake" \
  -DCMAKE_C_COMPILER="${CC}" \
  -DCMAKE_CXX_COMPILER="${CXX}" \
  -DCMAKE_CUDA_HOST_COMPILER="${CUDAHOSTCXX}" \
  -DBUILD_PYTHON_STUBS=OFF
