#!/usr/bin/env bash

set -euo pipefail

if [[ "${LFS_LOCAL_COMMON_SH:-0}" == "1" ]]; then
    return 0
fi
export LFS_LOCAL_COMMON_SH=1

export LFS_WORK_ROOT="${LFS_WORK_ROOT:-/mnt/scratch/mlast/lichtfeld-build}"
export LFS_REPO_DIR="${LFS_REPO_DIR:-${LFS_WORK_ROOT}/LichtFeld-Studio}"
export LFS_LOG_DIR="${LFS_LOG_DIR:-${LFS_WORK_ROOT}/logs}"
export VCPKG_ROOT="${VCPKG_ROOT:-/home/ubuntu/vcpkg}"
export PATH="${VCPKG_ROOT}:${PATH}"
export CC="${CC:-/usr/bin/gcc}"
export CXX="${CXX:-/usr/bin/g++}"
export CUDAHOSTCXX="${CUDAHOSTCXX:-${CXX}}"
export LFS_REQUIRED_CUDA_VERSION="${LFS_REQUIRED_CUDA_VERSION:-12.8.0}"

mkdir -p "${LFS_WORK_ROOT}" "${LFS_LOG_DIR}"

if [[ "${LFS_LOCAL_LOGGING_ENABLED:-0}" != "1" ]]; then
    export LFS_LOCAL_LOGGING_ENABLED=1
    script_name="$(basename "$0" .sh)"
    timestamp="$(date +%Y%m%d-%H%M%S)"
    export LFS_LOG_FILE="${LFS_LOG_DIR}/${timestamp}_${script_name}.log"
    exec > >(tee -a "${LFS_LOG_FILE}") 2>&1
fi

echo "log: ${LFS_LOG_FILE}"
echo "work root: ${LFS_WORK_ROOT}"
echo "repo dir: ${LFS_REPO_DIR}"
echo "VCPKG_ROOT: ${VCPKG_ROOT}"
echo "CC: ${CC}"
echo "CXX: ${CXX}"
echo "CUDAHOSTCXX: ${CUDAHOSTCXX}"
echo "required CUDA: ${LFS_REQUIRED_CUDA_VERSION}"

version_ge() {
    [[ "$(printf '%s\n%s\n' "$(normalize_version "$2")" "$(normalize_version "$1")" | sort -V | head -n 1)" == "$(normalize_version "$2")" ]]
}

normalize_version() {
    local major minor patch extra
    IFS=. read -r major minor patch extra <<<"$1"
    printf '%s.%s.%s\n' "${major:-0}" "${minor:-0}" "${patch:-0}"
}

require_cuda_version() {
    local detected
    detected="$(nvcc --version | sed -n 's/.*release \([0-9][0-9.]*\),.*/\1/p' | head -n 1)"
    if [[ -z "${detected}" ]]; then
        echo "ERROR: could not parse CUDA version from nvcc --version" >&2
        return 1
    fi
    echo "detected CUDA: ${detected}"
    if ! version_ge "${detected}" "${LFS_REQUIRED_CUDA_VERSION}"; then
        echo "ERROR: CUDA ${detected} is too old. Need >= ${LFS_REQUIRED_CUDA_VERSION}." >&2
        return 1
    fi
}
